"""
Unit tests for the second task family (constrained multi-block).
"""

from alpha.core.entities import ActionType, BlockColor, TaskFamily, TaskSpec
from alpha.services.oracle_planner import ScriptedOraclePlanner


def test_constrained_multi_block_oracle_plan():
    """Oracle planner should clear the secondary obstacle block before placing the primary block."""
    planner = ScriptedOraclePlanner()
    task = TaskSpec(
        block=BlockColor.RED,
        place_zone=(0.6, 0.35, 0.65),
        task_family=TaskFamily.CONSTRAINED_MULTI_BLOCK,
        secondary_block=BlockColor.BLUE,
        clearance_zone=(0.4, -0.3, 0.65),
    )

    plan = planner.plan(task, scene_info={
        "blocks": {
            "red": (0.5, -0.15, 0.68),
            "blue": (0.5, 0.15, 0.68),
        }
    })

    # Should contain two grip actions: first blue, then red
    grip_actions = [a for a in plan.actions if a.action == ActionType.GRIP]
    assert len(grip_actions) == 2
    assert grip_actions[0].block == BlockColor.BLUE
    assert grip_actions[1].block == BlockColor.RED

    # Should contain two releases
    release_actions = [a for a in plan.actions if a.action == ActionType.RELEASE]
    assert len(release_actions) == 2

