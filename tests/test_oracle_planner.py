"""Unit tests for ScriptedOraclePlanner."""

from alpha.core.entities import ActionType, BlockColor, TaskSpec
from alpha.services.oracle_planner import ScriptedOraclePlanner


def test_oracle_planner_full_plan():
    planner = ScriptedOraclePlanner()
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))
    scene_info = {"blocks": {"red": (0.5, -0.15, 0.68)}}

    plan = planner.plan(task, scene_info)

    assert plan.agent_name == "scripted_oracle"
    actions = plan.actions
    assert len(actions) == 7

    # Verify canonical structure
    assert actions[0].action == ActionType.MOVE_TO
    assert actions[1].action == ActionType.MOVE_TO
    assert actions[2].action == ActionType.GRIP
    assert actions[2].block == BlockColor.RED
    assert actions[3].action == ActionType.MOVE_TO
    assert actions[4].action == ActionType.MOVE_TO
    assert actions[5].action == ActionType.MOVE_TO
    assert actions[6].action == ActionType.RELEASE


def test_oracle_planner_continuation_plan():
    planner = ScriptedOraclePlanner()
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))
    scene_info = {
        "blocks": {"red": (0.5, -0.15, 0.68)},
        "block_gripped": True,
        "task_phase": "place",
    }

    plan = planner.plan(task, scene_info)

    assert plan.agent_name == "scripted_oracle"
    actions = plan.actions
    # Continuation should only contain transfer and release
    assert len(actions) == 3
    assert actions[0].action == ActionType.MOVE_TO
    assert actions[1].action == ActionType.MOVE_TO
    assert actions[2].action == ActionType.RELEASE
