"""
Week 2 Brain/Body orchestration.

The Brain produces a validated ActionPlan. The Body is still ControlService;
this service only coordinates planning, validation, execution, and result
recording.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from pydantic import ValidationError

from alpha.clients.llm_client import LLMClient
from alpha.core.entities import ActionType, EpisodeResult, FaultType, TaskSpec
from alpha.core.interfaces import AgentPlanner, SimulatorClient
from alpha.models.agent_config import AgentConfig
from alpha.schemas.action_plan import ActionPlan
from alpha.services.agent_hooks import AgentRunHooks
from alpha.services.control_service import ControlService

logger = logging.getLogger(__name__)

# Controlled experiment timeout when the replanning bound is exceeded.
REPLANNING_TIMEOUT_REASON = "phase_b_replanning_timeout"


class AgentBrain(AgentPlanner):
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    @property
    def name(self) -> str:
        return self.llm_client.name

    def plan(self, task: TaskSpec, scene_info: dict | None = None) -> ActionPlan:
        return self.llm_client.generate_action_plan(task, scene_info)


class AgentService:
    def __init__(
        self,
        brain: AgentBrain,
        control_service: ControlService,
        simulator: SimulatorClient,
    ) -> None:
        self.brain = brain
        self.control_service = control_service
        self.simulator = simulator

    def observe(self) -> dict[str, Any]:
        """Return current scene observation in the planner ``blocks`` schema."""
        raw = self.simulator.observe()
        return self._normalize_observation(raw)

    @staticmethod
    def _normalize_observation(raw: dict[str, Any] | None) -> dict[str, Any]:
        if not raw:
            return {"blocks": {}}
        if "blocks" in raw and isinstance(raw["blocks"], dict):
            return {"blocks": dict(raw["blocks"])}
        # Simulator backends may return a flat color -> position map.
        return {"blocks": dict(raw)}

    def plan_task(self, task: TaskSpec, scene_info: dict[str, Any] | None = None) -> ActionPlan:
        plan = self.brain.plan(task, scene_info)
        return ActionPlan.validate_raw_plan(plan, agent_name=self.brain.name)

    def run_task(
        self,
        task: TaskSpec,
        scene_info: dict[str, Any] | None = None,
        hooks: AgentRunHooks | None = None,
        enable_replanning: bool = False,
        replanning_chunk_size: int = 3,
        max_replanning_attempts: int | None = None,
    ) -> EpisodeResult:
        if max_replanning_attempts is None:
            max_replanning_attempts = AgentConfig.max_replanning_attempts
        if max_replanning_attempts < 0:
            raise ValueError("max_replanning_attempts must be >= 0")
        if enable_replanning and replanning_chunk_size < 1:
            raise ValueError("replanning_chunk_size must be >= 1 when replanning is enabled")

        try:
            plan = self.plan_task(task, scene_info)
        except ValidationError:
            raise

        # Handle empty action plan as controlled planner failure
        if not plan.actions:
            fault_injector = self.control_service.fault_injector
            if hooks is not None and hooks.fault_events_provider is not None:
                fault_log = hooks.fault_events_provider()
                fault_type = hooks.fault_type
                fault_seed = hooks.fault_seed
            elif fault_injector is not None:
                fault_log = fault_injector.event_log()
                fault_type = fault_injector.fault_type
                fault_seed = fault_injector.seed
            else:
                fault_log = []
                fault_type = FaultType.NONE
                fault_seed = None
            fault_occurred = any(event.get("fault_applied") for event in fault_log)

            return EpisodeResult(
                task=task,
                success=False,
                final_error=float('inf'),  # Use infinity to indicate planner failure
                final_position=(0.0, 0.0, 0.0),  # Default position when no execution occurs
                fault_type=fault_type,
                steps_taken=0,
                agent_name=plan.agent_name,
                action_plan_json=json.dumps(plan.model_dump(mode="json")),
                execution_log_json=json.dumps(
                    {
                        "actions": [],
                        "fault_events": fault_log,
                    },
                    default=str,
                ),
                fault_occurred=fault_occurred,
                fault_seed=fault_seed,
                notes="planner_output_corruption",  # Specific failure reason for F4
            )

        execution_log: list[dict[str, Any]] = []
        grip_handle = None
        current_plan = list(plan.actions)
        total_steps_taken = 0
        replan_count = 0
        observation_count = 0
        chunk_index = 0
        timed_out = False
        episode_start_time = time.monotonic()
        # Track task state for replanning context
        task_phase = "pick"  # Initial phase: picking up the block
        block_gripped = False
        place_moves_completed = 0
        # Hard ceiling: initial plan drain + one chunk cycle per allowed replan.
        max_chunks = max_replanning_attempts + 1 if enable_replanning else 1
        if enable_replanning:
            # Allow draining a replaced plan after the final permitted replan.
            max_chunks = (max_replanning_attempts + 1) * 2

        while current_plan:
            # Check wall-time timeout to prevent indefinite hangs
            elapsed_wall_time = time.monotonic() - episode_start_time
            if elapsed_wall_time > AgentConfig.max_episode_wall_seconds:
                timed_out = True
                logger.warning(
                    "Episode terminating: wall-time timeout exceeded "
                    "(elapsed=%s max=%s chunk_index=%s replan_count=%s steps=%s)",
                    elapsed_wall_time,
                    AgentConfig.max_episode_wall_seconds,
                    chunk_index,
                    replan_count,
                    total_steps_taken,
                )
                execution_log.append(
                    {
                        "wall_time_timeout": True,
                        "reason": "episode_wall_time_timeout",
                        "elapsed_seconds": elapsed_wall_time,
                        "chunk_index": chunk_index,
                        "replan_count": replan_count,
                        "at_step": total_steps_taken,
                    }
                )
                break

            if enable_replanning and chunk_index >= max_chunks:
                timed_out = True
                logger.warning(
                    "F1 loop terminating: max_chunks exceeded "
                    "(chunk_index=%s max_chunks=%s replan_count=%s steps=%s)",
                    chunk_index,
                    max_chunks,
                    replan_count,
                    total_steps_taken,
                )
                execution_log.append(
                    {
                        "replanning_timeout": True,
                        "reason": REPLANNING_TIMEOUT_REASON,
                        "chunk_index": chunk_index,
                        "replan_count": replan_count,
                        "at_step": total_steps_taken,
                    }
                )
                break

            chunk = current_plan[:replanning_chunk_size] if enable_replanning else current_plan
            remaining_before = current_plan[replanning_chunk_size:] if enable_replanning else []
            current_plan = remaining_before

            logger.info(
                "F1 loop chunk start: chunk_index=%s actions_in_chunk=%s "
                "remaining_after_slice=%s replan_count=%s observation_count=%s "
                "steps_taken=%s enable_replanning=%s",
                chunk_index,
                len(chunk),
                len(current_plan),
                replan_count,
                observation_count,
                total_steps_taken,
                enable_replanning,
            )

            for index, step in enumerate(chunk):
                if hooks is not None and hooks.on_before_action is not None:
                    hooks.on_before_action(total_steps_taken + index, step, grip_handle)

                if step.action == ActionType.MOVE_TO:
                    assert step.target is not None
                    if block_gripped:
                        place_moves_completed += 1
                    move_result = self.control_service.move_to(step.target)
                    execution_log.append(
                        {
                            "index": total_steps_taken + index,
                            "action": step.action.value,
                            "requested_target": move_result.get("requested_target", step.target),
                            "executed_target": move_result.get("executed_target", step.target),
                            "reached_pos": move_result.get("reached_pos"),
                            "error": move_result.get("error"),
                        }
                    )
                elif step.action == ActionType.GRIP:
                    assert step.block is not None
                    grip_handle = self.control_service.grip(step.block)
                    block_gripped = grip_handle is not None
                    if block_gripped:
                        task_phase = "place"  # Transition to placement phase after successful grip
                    execution_log.append(
                        {
                            "index": total_steps_taken + index,
                            "action": step.action.value,
                            "block": step.block.value,
                            "grip_acquired": block_gripped,
                        }
                    )
                elif step.action == ActionType.RELEASE:
                    self.control_service.release(grip_handle)
                    block_gripped = False
                    task_phase = "complete"  # Task complete after release
                    execution_log.append({"index": total_steps_taken + index, "action": step.action.value})

                if hooks is not None and hooks.on_after_action is not None:
                    hooks.on_after_action(total_steps_taken + index, step, grip_handle)

            total_steps_taken += len(chunk)
            chunk_index += 1

            if task_phase == "complete":
                logger.info("Task completed (RELEASE executed); terminating execution loop.")
                current_plan = []
                break

            # Re-observe and optionally replan if more actions remain.
            # A successful replan replaces the remaining suffix with a fresh plan;
            # without a replan bound that replacement can grow forever.
            if enable_replanning and current_plan:
                if replan_count >= max_replanning_attempts:
                    timed_out = True
                    logger.warning(
                        "F1 loop terminating: max_replanning_attempts exceeded "
                        "(replan_count=%s max=%s chunk_index=%s remaining=%s steps=%s)",
                        replan_count,
                        max_replanning_attempts,
                        chunk_index,
                        len(current_plan),
                        total_steps_taken,
                    )
                    execution_log.append(
                        {
                            "replanning_timeout": True,
                            "reason": REPLANNING_TIMEOUT_REASON,
                            "chunk_index": chunk_index,
                            "replan_count": replan_count,
                            "remaining_actions": len(current_plan),
                            "at_step": total_steps_taken,
                        }
                    )
                    current_plan = []
                    break

                observation_count += 1
                logger.info(
                    "F1 observe before replan: observation_count=%s chunk_index=%s "
                    "replan_count=%s steps=%s remaining=%s",
                    observation_count,
                    chunk_index,
                    replan_count,
                    total_steps_taken,
                    len(current_plan),
                )
                fresh_observation = self.observe()
                logger.info(
                    "F1 LLM replan call starting: replan_index=%s observation_blocks=%s",
                    replan_count + 1,
                    list((fresh_observation.get("blocks") or {}).keys()),
                )
                try:
                    # Pass task state context to preserve progress during replanning
                    scene_info_with_context = dict(fresh_observation)
                    scene_info_with_context["task_phase"] = task_phase
                    scene_info_with_context["block_gripped"] = block_gripped
                    scene_info_with_context["completed_steps"] = total_steps_taken
                    scene_info_with_context["remaining_actions"] = len(current_plan)
                    
                    # Add explicit completed actions summary to guide replanning
                    completed_actions_summary = []
                    if execution_log:
                        for action_entry in execution_log:
                            if "action" in action_entry:
                                completed_actions_summary.append(action_entry["action"])
                    
                    scene_info_with_context["completed_actions"] = completed_actions_summary
                    scene_info_with_context["completed_actions_count"] = len(completed_actions_summary)
                    
                    # Modify task description based on current progress to guide replanning
                    # The key insight: ask the LLM to continue from where we left off
                    replan_task = task
                    if task_phase == "place" and block_gripped:
                        # If we've gripped the block, ask planner to complete placement
                        from alpha.core.entities import TaskSpec
                        replan_task = TaskSpec(
                            block=task.block,
                            place_zone=task.place_zone,
                            description="continue: place the gripped block in the place zone - block is already gripped, move to place zone and release"
                        )
                    elif task_phase == "pick" and not block_gripped:
                        # Count how many MOVE_TOs we've done
                        move_to_count = completed_actions_summary.count("MOVE_TO")
                        if move_to_count >= 2:
                            # We've done enough positioning, now ask for GRIP
                            from alpha.core.entities import TaskSpec
                            replan_task = TaskSpec(
                                block=task.block,
                                place_zone=task.place_zone,
                                description="continue: grip the red block - you have already positioned the arm, now grip the block"
                            )
                        else:
                            # Still need to position
                            from alpha.core.entities import TaskSpec
                            actions_str = ", ".join(completed_actions_summary[-3:]) if completed_actions_summary else "none"
                            replan_task = TaskSpec(
                                block=task.block,
                                place_zone=task.place_zone,
                                description=f"continue: position arm to grip the red block - already completed: {actions_str}"
                            )
                    
                    new_plan = self.plan_task(replan_task, scene_info_with_context)
                    logger.info(
                        "F1 LLM replan call returned: replan_index=%s new_actions=%s task_phase=%s block_gripped=%s completed=%s",
                        replan_count + 1,
                        len(new_plan.actions),
                        task_phase,
                        block_gripped,
                        len(completed_actions_summary),
                    )
                    if new_plan.actions:
                        continuation_actions = list(new_plan.actions)
                        if block_gripped:
                            # If block is already gripped, drop any redundant pick/grip actions
                            grip_indices = [i for i, a in enumerate(continuation_actions) if a.action == ActionType.GRIP]
                            if grip_indices:
                                continuation_actions = continuation_actions[grip_indices[-1] + 1 :]
                            continuation_actions = [a for a in continuation_actions if a.action != ActionType.GRIP]

                            # If replan provided a full 2+ move place sequence, drop the already completed place moves
                            move_count_in_plan = sum(1 for a in continuation_actions if a.action == ActionType.MOVE_TO)
                            if move_count_in_plan >= 2 and place_moves_completed > 0:
                                moves_to_drop = min(place_moves_completed, move_count_in_plan)
                                dropped = 0
                                filtered = []
                                for a in continuation_actions:
                                    if a.action == ActionType.MOVE_TO and dropped < moves_to_drop:
                                        dropped += 1
                                    else:
                                        filtered.append(a)
                                continuation_actions = filtered

                        if continuation_actions:
                            replan_count += 1
                            current_plan = continuation_actions
                            execution_log.append(
                                {
                                    "replanning": True,
                                    "at_step": total_steps_taken,
                                    "replan_count": replan_count,
                                    "chunk_index": chunk_index,
                                    "remaining_actions": len(current_plan),
                                }
                            )
                        if hooks is not None and hooks.on_replan is not None:
                            hooks.on_replan(
                                replan_count,
                                {
                                    "at_step": total_steps_taken,
                                    "chunk_index": chunk_index,
                                    "remaining_actions": len(current_plan),
                                    "observation_count": observation_count,
                                },
                            )
                        logger.info(
                            "F1 loop continues after replan: replan_count=%s "
                            "new_plan_actions=%s chunk_index=%s",
                            replan_count,
                            len(current_plan),
                            chunk_index,
                        )
                    else:
                        logger.info(
                            "F1 replan returned empty plan; continuing original remainder "
                            "(remaining=%s)",
                            len(current_plan),
                        )
                except ValidationError:
                    # If replanning fails, continue with remaining original plan
                    logger.info(
                        "F1 replan validation failed; continuing original remainder "
                        "(remaining=%s)",
                        len(current_plan),
                    )

            elif not current_plan:
                logger.info(
                    "F1 loop terminating: plan drained "
                    "(chunk_index=%s replan_count=%s steps=%s)",
                    chunk_index,
                    replan_count,
                    total_steps_taken,
                )

        self.simulator.step(60)
        success, final_error, final_position = self.control_service.evaluate_task(task)
        if timed_out:
            success = False

        fault_injector = self.control_service.fault_injector
        if hooks is not None and hooks.fault_events_provider is not None:
            fault_log = hooks.fault_events_provider()
            fault_type = hooks.fault_type
            fault_seed = hooks.fault_seed
        elif fault_injector is not None:
            fault_log = fault_injector.event_log()
            fault_type = fault_injector.fault_type
            fault_seed = fault_injector.seed
        else:
            fault_log = []
            fault_type = FaultType.NONE
            fault_seed = None
        fault_occurred = any(event.get("fault_applied") for event in fault_log)

        # Determine timeout reason for notes
        timeout_reason = ""
        if timed_out:
            for entry in execution_log:
                if entry.get("wall_time_timeout"):
                    timeout_reason = "episode_wall_time_timeout"
                    break
                elif entry.get("replanning_timeout"):
                    timeout_reason = REPLANNING_TIMEOUT_REASON
                    break

        elapsed_wall_time = time.monotonic() - episode_start_time

        return EpisodeResult(
            task=task,
            success=success,
            final_error=final_error,
            final_position=final_position,
            fault_type=fault_type,
            steps_taken=total_steps_taken,
            agent_name=plan.agent_name,
            action_plan_json=json.dumps(plan.model_dump(mode="json")),
            execution_log_json=json.dumps(
                {
                    "actions": execution_log,
                    "fault_events": fault_log,
                    "replan_count": replan_count,
                    "observation_count": observation_count,
                    "chunk_index": chunk_index,
                    "timed_out": timed_out,
                    "elapsed_wall_seconds": elapsed_wall_time,
                },
                default=str,
            ),
            fault_occurred=fault_occurred,
            fault_seed=fault_seed,
            notes=timeout_reason,
        )
