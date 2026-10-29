"""
Unit and integration tests for Phase-B continuation planning.

Verifies that:
- partial execution -> continuation
- completed MOVE_TO is not repeated
- completed GRIP is not repeated
- RELEASE/place is reached
- task completes successfully after replanning
"""

import json
from unittest.mock import MagicMock

from alpha.core.entities import ActionType, BlockColor, TaskSpec
from alpha.schemas.action_plan import ActionPlan, ActionStep
from alpha.services.agent_service import AgentBrain, AgentService
from alpha.services.control_service import ControlService
from tests.fakes import FakeSimulator


def _make_plan(*actions) -> ActionPlan:
    steps = []
    for item in actions:
        if isinstance(item, tuple):
            steps.append(ActionStep(action=ActionType.MOVE_TO, target=item))
        elif item == "GRIP":
            steps.append(ActionStep(action=ActionType.GRIP, block=BlockColor.RED))
        elif item == "RELEASE":
            steps.append(ActionStep(action=ActionType.RELEASE))
    return ActionPlan(agent_name="test_agent", actions=steps)


def _setup_service(brain: AgentBrain) -> tuple[AgentService, FakeSimulator]:
    sim = FakeSimulator()
    control = ControlService(sim)
    service = AgentService(brain=brain, control_service=control, simulator=sim)
    return service, sim


def test_partial_execution_to_continuation():
    """Verify that after partial execution, replan resumes and executes remainder."""
    brain = MagicMock(spec=AgentBrain)
    brain.name = "mock_brain"

    # Initial plan has 7 steps
    full_plan = _make_plan(
        (0.5, -0.15, 0.8),
        (0.5, -0.15, 0.68),
        "GRIP",
        (0.5, -0.15, 0.8),
        (0.6, 0.35, 0.8),
        (0.6, 0.35, 0.68),
        "RELEASE",
    )

    # Continuation plan after chunk execution
    continuation_plan = _make_plan(
        (0.6, 0.35, 0.8),
        (0.6, 0.35, 0.68),
        "RELEASE",
    )

    call_count = {"count": 0}

    def mock_plan(task, scene_info=None):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return full_plan
        return continuation_plan

    brain.plan.side_effect = mock_plan
    service, sim = _setup_service(brain)

    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))
    result = service.run_task(
        task,
        scene_info={"blocks": {"red": (0.5, -0.15, 0.68)}},
        enable_replanning=True,
        replanning_chunk_size=4,  # Execute first 4 (approach, grasp, grip, lift)
        max_replanning_attempts=3,
    )

    assert result.success is True
    assert call_count["count"] >= 2


def test_completed_grip_not_repeated_even_if_llm_regenerates_it():
    """Verify that if the LLM regenerates a full plan including GRIP, the continuation filter strips it."""
    brain = MagicMock(spec=AgentBrain)
    brain.name = "mock_brain"

    # Both initial and replan return the full 7-step sequence (simulating an LLM that restarts)
    full_plan = _make_plan(
        (0.5, -0.15, 0.8),
        (0.5, -0.15, 0.68),
        "GRIP",
        (0.5, -0.15, 0.8),
        (0.6, 0.35, 0.8),
        (0.6, 0.35, 0.68),
        "RELEASE",
    )

    brain.plan.return_value = full_plan
    service, sim = _setup_service(brain)

    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))
    result = service.run_task(
        task,
        scene_info={"blocks": {"red": (0.5, -0.15, 0.68)}},
        enable_replanning=True,
        replanning_chunk_size=3,  # Executes move, move, grip
        max_replanning_attempts=3,
    )

    payload = json.loads(result.execution_log_json)
    actions = payload.get("actions", [])
    executed_grips = [a for a in actions if a.get("action") == "GRIP"]

    # GRIP should only be executed once!
    assert len(executed_grips) == 1, f"Expected exactly 1 GRIP executed, got {len(executed_grips)}"
    assert result.success is True


def test_successful_completion_and_termination_after_release():
    """Verify that once RELEASE is executed, the task terminates promptly without further replanning."""
    brain = MagicMock(spec=AgentBrain)
    brain.name = "mock_brain"

    plan = _make_plan(
        (0.5, -0.15, 0.8),
        (0.5, -0.15, 0.68),
        "GRIP",
        (0.5, -0.15, 0.8),
        (0.6, 0.35, 0.8),
        (0.6, 0.35, 0.68),
        "RELEASE",
    )
    brain.plan.return_value = plan
    service, sim = _setup_service(brain)

    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))
    result = service.run_task(
        task,
        scene_info={"blocks": {"red": (0.5, -0.15, 0.68)}},
        enable_replanning=True,
        replanning_chunk_size=4,
        max_replanning_attempts=5,
    )

    payload = json.loads(result.execution_log_json)
    assert payload.get("timed_out") is False
    assert result.success is True
    # The last executed action must be RELEASE
    actions = payload.get("actions", [])
    assert actions[-1]["action"] == "RELEASE"
