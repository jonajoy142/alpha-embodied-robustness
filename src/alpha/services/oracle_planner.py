"""
Scripted / Oracle Planner for Embodied Manipulation.

Provides a clean, deterministic oracle planner that produces valid ActionPlan
schemas matching the exact Brain/Body contract used by the LLM planner.
Enables direct scientific comparison: LLM Planner vs. Scripted Oracle Planner
under identical environmental conditions, seeds, and fault injection.
"""

from __future__ import annotations

from typing import Any

from alpha.config import settings
from alpha.core.entities import ActionType, BlockColor, TaskSpec, Vec3
from alpha.core.interfaces import AgentPlanner
from alpha.schemas.action_plan import ActionPlan, ActionStep


class ScriptedOraclePlanner(AgentPlanner):
    """
    Oracle planner that computes canonical pick-and-place waypoints
    directly from ground-truth or observed task and scene information.
    """

    def __init__(self, name: str = "scripted_oracle") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def plan(
        self,
        task: TaskSpec,
        scene_info: dict[str, Any] | None = None,
    ) -> ActionPlan:
        """
        Generate an ActionPlan.

        If scene_info indicates the block is already gripped (during replanning / continuation),
        generates only the remaining transfer and release actions.
        Otherwise, generates the full canonical pick-and-place sequence based on observed block position.
        """
        block_pos = self._extract_block_position(task.block, scene_info)
        place_pos = task.place_zone

        # Standard table grasp offsets relative to block position:
        # Gripper grasping frame requires end-effector z = 0.70 (+0.045 over settled block z~0.655)
        # Approach and lift height requires end-effector z = 0.83 (+0.175 over settled block)
        above_block: Vec3 = (block_pos[0], block_pos[1], max(block_pos[2] + 0.175, 0.83))
        grasp_pos: Vec3 = (block_pos[0], block_pos[1], max(block_pos[2] + 0.045, 0.70))
        above_place: Vec3 = (place_pos[0], place_pos[1], place_pos[2] + 0.15)
        release_pos: Vec3 = (
            place_pos[0],
            place_pos[1],
            place_pos[2] + settings.PLACE_RELEASE_HEIGHT_OFFSET,
        )

        actions: list[ActionStep] = []

        is_gripped = False
        if scene_info and isinstance(scene_info, dict):
            is_gripped = bool(scene_info.get("block_gripped", False))

        if is_gripped:
            # Continuation: block already in hand -> transfer to place zone and release
            actions.append(ActionStep(action=ActionType.MOVE_TO, target=above_place))
            actions.append(ActionStep(action=ActionType.MOVE_TO, target=release_pos))
            actions.append(ActionStep(action=ActionType.RELEASE))
        else:
            # Full pick-and-place plan
            actions.append(ActionStep(action=ActionType.MOVE_TO, target=above_block))
            actions.append(ActionStep(action=ActionType.MOVE_TO, target=grasp_pos))
            actions.append(ActionStep(action=ActionType.GRIP, block=task.block))
            actions.append(ActionStep(action=ActionType.MOVE_TO, target=above_block))
            actions.append(ActionStep(action=ActionType.MOVE_TO, target=above_place))
            actions.append(ActionStep(action=ActionType.MOVE_TO, target=release_pos))
            actions.append(ActionStep(action=ActionType.RELEASE))

        return ActionPlan(agent_name=self.name, actions=actions)

    def _extract_block_position(
        self,
        block: BlockColor,
        scene_info: dict[str, Any] | None,
    ) -> Vec3:
        if scene_info and isinstance(scene_info, dict):
            blocks = scene_info.get("blocks")
            if isinstance(blocks, dict) and block.value in blocks:
                pos = blocks[block.value]
                if isinstance(pos, (list, tuple)) and len(pos) == 3:
                    return (float(pos[0]), float(pos[1]), float(pos[2]))
            # Also check flat color key
            if block.value in scene_info:
                pos = scene_info[block.value]
                if isinstance(pos, (list, tuple)) and len(pos) == 3:
                    return (float(pos[0]), float(pos[1]), float(pos[2]))

        # Fall back to default spawn position if not in scene_info
        return settings.BLOCK_SPAWN_POSITIONS[block]
