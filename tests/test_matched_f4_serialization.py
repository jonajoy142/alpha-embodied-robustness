"""
Unit tests for matched F4 serialization, corruption probability roll, and mitigation arms.
"""

import json
from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper
from alpha.clients.simulator_client import PyBulletSimulatorClient
from alpha.core.entities import BlockColor, FaultType, TaskSpec
from alpha.models.chaos_config import ChaosConfig, FaultIntensity, FaultSpec, TriggerConfig, TriggerKind
from alpha.plugins.planner_adapter import (
    MitigationStrategy,
    OraclePlannerAdapter,
)
from alpha.schemas.action_plan import ActionPlan
from alpha.services.oracle_planner import ScriptedOraclePlanner


def test_oracle_plan_serialized_and_validated():
    """Oracle plan must serialize to ActionPlan JSON schema and validate successfully."""
    planner = OraclePlannerAdapter()
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))
    plan = planner.plan(task, scene_info={"blocks": {"red": (0.5, -0.15, 0.68)}})

    assert isinstance(plan, ActionPlan)
    assert len(plan.actions) > 0
    assert plan.agent_name == "scripted_oracle"
    assert planner.last_validation_error is None


def test_f4_corruption_probability_respected():
    """
    F4 corruption must respect corruption_probability (not unconditionally corrupt 100% of the time).
    When corruption_probability is 0.0, output should not be corrupted.
    When corruption_probability is 1.0, output should be corrupted.
    """
    config_zero = ChaosConfig(
        faults=[
            FaultSpec(
                fault_type=FaultType.PLANNER_OUTPUT_CORRUPTION,
                enabled=True,
                trigger=TriggerConfig(kind=TriggerKind.IMMEDIATE),
                intensity=FaultIntensity(corruption_probability=0.0),
                probability=1.0,
            )
        ]
    )
    wrapper_zero = ChaosRoboticsWrapper(PyBulletSimulatorClient(), config_zero)
    raw = json.dumps({"agent_name": "test", "actions": [{"action": "move_to", "target": [0, 0, 0]}]})
    out_zero = wrapper_zero.intercept_planner_output(raw)
    assert out_zero == raw  # No corruption when prob=0.0

    config_one = ChaosConfig(
        faults=[
            FaultSpec(
                fault_type=FaultType.PLANNER_OUTPUT_CORRUPTION,
                enabled=True,
                trigger=TriggerConfig(kind=TriggerKind.IMMEDIATE),
                intensity=FaultIntensity(corruption_probability=1.0, keys_to_delete=["target"]),
                probability=1.0,
            )
        ]
    )
    wrapper_one = ChaosRoboticsWrapper(PyBulletSimulatorClient(), config_one)
    out_one = wrapper_one.intercept_planner_output(raw)
    assert out_one != raw
    assert "target" not in json.loads(out_one)["actions"][0]


def test_matched_f4_oracle_subjected_to_corruption():
    """When F4 corruption is active, Oracle plan must be intercepted and rejected by validator."""
    config = ChaosConfig(
        faults=[
            FaultSpec(
                fault_type=FaultType.PLANNER_OUTPUT_CORRUPTION,
                enabled=True,
                trigger=TriggerConfig(kind=TriggerKind.IMMEDIATE),
                intensity=FaultIntensity(corruption_probability=1.0, keys_to_delete=["target"]),
                probability=1.0,
            )
        ]
    )
    wrapper = ChaosRoboticsWrapper(PyBulletSimulatorClient(), config)
    planner = OraclePlannerAdapter(chaos_wrapper=wrapper)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))
    plan = planner.plan(task, scene_info={"blocks": {"red": (0.5, -0.15, 0.68)}})

    # Empty actions signals controlled validation rejection
    assert len(plan.actions) == 0
    assert planner.last_validation_error is not None


def test_mitigation_retry_with_feedback_recovery():
    """MitigationStrategy.RETRY_WITH_FEEDBACK attempts re-prompting on failure."""
    class FlakyPlanner(OraclePlannerAdapter):
        def __init__(self):
            super().__init__(mitigation=MitigationStrategy.RETRY_WITH_FEEDBACK, max_retries=2)
            self.calls = 0

        def generate_raw_plan_text(self, task, scene_info=None, feedback=None):
            self.calls += 1
            if self.calls == 1:
                return "MALFORMED_JSON{"
            # On retry with feedback, return valid plan
            return json.dumps({"agent_name": "flaky", "actions": [{"action": "RELEASE"}]})

    planner = FlakyPlanner()
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))
    plan = planner.plan(task)

    assert planner.calls == 2
    assert planner.mitigation_recovered is True
    assert planner.retry_count == 1
    assert len(plan.actions) == 1
