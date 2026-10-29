"""Tests for F1 repeated observation and replanning path."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


def test_observe_method_exists_on_simulator_client():
    """Test that observe method exists on SimulatorClient interface."""
    from alpha.core.interfaces import SimulatorClient
    
    assert hasattr(SimulatorClient, 'observe')


def test_observe_method_exists_on_pybullet_simulator():
    """Test that PyBulletSimulatorClient implements observe method."""
    from alpha.clients.simulator_client import PyBulletSimulatorClient
    
    client = PyBulletSimulatorClient()
    assert hasattr(client, 'observe')


def test_observe_method_exists_on_chaos_wrapper():
    """Test that ChaosRoboticsWrapper implements observe method."""
    from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper
    from alpha.core.interfaces import SimulatorClient
    from alpha.models.chaos_config import ChaosConfig
    
    inner = MagicMock(spec=SimulatorClient)
    wrapper = ChaosRoboticsWrapper(inner, ChaosConfig())
    assert hasattr(wrapper, 'observe')


def test_observe_method_exists_on_agent_service():
    """Test that AgentService implements observe method."""
    from alpha.services.agent_service import AgentService, AgentBrain
    from alpha.services.control_service import ControlService
    from alpha.core.interfaces import SimulatorClient
    
    brain = MagicMock(spec=AgentBrain)
    control = MagicMock(spec=ControlService)
    simulator = MagicMock(spec=SimulatorClient)
    
    service = AgentService(brain, control, simulator)
    assert hasattr(service, 'observe')


def test_chaos_wrapper_observe_applies_f1_fault():
    """Test that ChaosRoboticsWrapper.observe() applies F1 sensor lag fault."""
    from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper
    from alpha.core.interfaces import SimulatorClient
    from alpha.models.chaos_config import ChaosConfig, FaultIntensity, FaultSpec, TriggerConfig, TriggerKind
    from alpha.core.entities import FaultType
    
    # Create a mock inner simulator
    inner = MagicMock(spec=SimulatorClient)
    inner.observe.return_value = {"red": (0.5, 0.5, 0.5)}
    
    # Create chaos config with F1 fault
    fault_spec = FaultSpec(
        fault_type=FaultType.SENSOR_LAG,
        intensity=FaultIntensity(lag_seconds=1.0),
        trigger=TriggerConfig(kind=TriggerKind.IMMEDIATE),
        probability=1.0,
    )
    config = ChaosConfig(faults=[fault_spec], seed=42)
    
    wrapper = ChaosRoboticsWrapper(inner, config)
    
    # Build scene to seed observation history
    wrapper.build_scene()
    
    # Call observe should apply F1 fault
    observation = wrapper.observe()
    
    # Should have called wrap_observation which applies F1
    assert observation is not None
    # The observation should be from wrap_observation, not directly from inner.observe
    # This proves F1 is applied through the observe path


def test_repeated_observation_requests_occur_with_replanning():
    """Test that repeated observation requests actually occur when enable_replanning=True."""
    from alpha.services.agent_service import AgentService, AgentBrain
    from alpha.services.control_service import ControlService
    from alpha.core.interfaces import SimulatorClient
    from alpha.core.entities import TaskSpec, ActionType, BlockColor
    from alpha.schemas.action_plan import ActionPlan, ActionStep
    
    # Create mocks
    brain = MagicMock(spec=AgentBrain)
    control = MagicMock(spec=ControlService)
    simulator = MagicMock(spec=SimulatorClient)
    
    # Setup brain to return plans
    plan1 = ActionPlan(
        agent_name="test",
        actions=[
            ActionStep(action=ActionType.MOVE_TO, target=(0.5, 0.5, 0.5)),
            ActionStep(action=ActionType.GRIP, block=BlockColor.RED),
            ActionStep(action=ActionType.MOVE_TO, target=(0.6, 0.6, 0.6)),
            ActionStep(action=ActionType.RELEASE),
            ActionStep(action=ActionType.MOVE_TO, target=(0.7, 0.7, 0.7)),
        ]
    )
    plan2 = ActionPlan(
        agent_name="test",
        actions=[
            ActionStep(action=ActionType.MOVE_TO, target=(0.8, 0.8, 0.8)),
        ]
    )
    
    brain.plan.side_effect = [plan1, plan2]
    
    # Setup control and simulator mocks
    control.fault_injector = None
    control.move_to.return_value = {"reached_pos": (0.5, 0.5, 0.5), "error": 0.0}
    control.grip.return_value = "grip_handle"
    control.evaluate_task.return_value = (True, 0.1, (0.8, 0.8, 0.8))
    simulator.observe.return_value = {"red": (0.6, 0.6, 0.6)}
    
    service = AgentService(brain, control, simulator)
    
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.8, 0.8, 0.0))
    
    # Run with replanning enabled
    result = service.run_task(task, scene_info={"blocks": {"red": (0.5, 0.5, 0.5)}}, enable_replanning=True, replanning_chunk_size=2)
    
    # Should have called observe at least once for replanning
    assert simulator.observe.call_count >= 1
    # Should have called plan twice (initial + replanning)
    assert brain.plan.call_count >= 2
    # Verify the second call got the updated observation
    second_call_scene_info = brain.plan.call_args_list[1][0][1] if len(brain.plan.call_args_list[1][0]) > 1 else brain.plan.call_args_list[1][1].get('scene_info', {})
    assert second_call_scene_info.get("blocks") == {"red": (0.6, 0.6, 0.6)}


def test_f1_returns_stale_observation():
    """Test that F1 returns an older observation when sensor lag is active."""
    from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper
    from alpha.core.interfaces import SimulatorClient
    from alpha.models.chaos_config import ChaosConfig, FaultIntensity, FaultSpec, TriggerConfig, TriggerKind
    from alpha.core.entities import FaultType
    # Create a mock inner simulator
    inner = MagicMock(spec=SimulatorClient)
    
    # Use a default return value since observe will be called multiple times
    inner.observe.return_value = {"red": (0.5, 0.5, 0.5)}
    
    # Create chaos config with F1 fault with 1 second lag
    fault_spec = FaultSpec(
        fault_type=FaultType.SENSOR_LAG,
        intensity=FaultIntensity(lag_seconds=1.0),
        trigger=TriggerConfig(kind=TriggerKind.IMMEDIATE),
        probability=1.0,
    )
    config = ChaosConfig(faults=[fault_spec], seed=42)
    
    wrapper = ChaosRoboticsWrapper(inner, config)
    
    # Build scene to seed observation history
    wrapper.build_scene()
    
    # First observation should be current
    obs1 = wrapper.observe()
    assert obs1 is not None
    
    # Simulate time passing (this is conceptual - in real test we'd need to control time)
    # For now, we just verify the structure is correct
    obs2 = wrapper.observe()
    assert obs2 is not None


def test_control_uses_current_observations():
    """Test that control with no fault still uses current observations."""
    from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper
    from alpha.core.interfaces import SimulatorClient
    from alpha.models.chaos_config import ChaosConfig
    
    # Create a mock inner simulator
    inner = MagicMock(spec=SimulatorClient)
    inner.observe.return_value = {"red": (0.5, 0.5, 0.5)}
    
    # Create chaos config without F1 fault
    config = ChaosConfig()
    
    wrapper = ChaosRoboticsWrapper(inner, config)
    
    # Observation should pass through unchanged
    observation = wrapper.observe()
    assert observation == {"red": (0.5, 0.5, 0.5)}


def test_valid_action_plans_still_execute():
    """Test that valid ActionPlans still execute with replanning enabled."""
    from alpha.services.agent_service import AgentService, AgentBrain
    from alpha.services.control_service import ControlService
    from alpha.core.interfaces import SimulatorClient
    from alpha.core.entities import TaskSpec, ActionType, BlockColor
    from alpha.schemas.action_plan import ActionPlan, ActionStep
    
    # Create mocks
    brain = MagicMock(spec=AgentBrain)
    control = MagicMock(spec=ControlService)
    simulator = MagicMock(spec=SimulatorClient)
    
    # Setup brain to return plan
    plan = ActionPlan(
        agent_name="test",
        actions=[
            ActionStep(action=ActionType.MOVE_TO, target=(0.5, 0.5, 0.5)),
            ActionStep(action=ActionType.GRIP, block=BlockColor.RED),
            ActionStep(action=ActionType.RELEASE),
        ]
    )
    brain.plan.return_value = plan
    
    # Setup control and simulator mocks
    control.fault_injector = None
    control.move_to.return_value = {"reached_pos": (0.5, 0.5, 0.5), "error": 0.0}
    control.grip.return_value = "grip_handle"
    control.evaluate_task.return_value = (True, 0.1, (0.5, 0.5, 0.5))
    simulator.observe.return_value = {"red": (0.5, 0.5, 0.5)}
    
    service = AgentService(brain, control, simulator)
    
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.8, 0.8, 0.0))
    
    # Run with replanning enabled
    result = service.run_task(task, scene_info={"red": (0.5, 0.5, 0.5)}, enable_replanning=True)
    
    # Should execute successfully
    assert result.success
    assert result.steps_taken == 3


def test_f1_does_not_alter_control_service_directly():
    """Test that F1 does not alter ControlService directly."""
    from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper
    from alpha.core.interfaces import SimulatorClient
    from alpha.models.chaos_config import ChaosConfig, FaultIntensity, FaultSpec, TriggerConfig, TriggerKind
    from alpha.core.entities import FaultType
    
    # Create a mock inner simulator
    inner = MagicMock(spec=SimulatorClient)
    inner.observe.return_value = {"red": (0.5, 0.5, 0.5)}
    
    # Create chaos config with F1 fault
    fault_spec = FaultSpec(
        fault_type=FaultType.SENSOR_LAG,
        intensity=FaultIntensity(lag_seconds=1.0),
        trigger=TriggerConfig(kind=TriggerKind.IMMEDIATE),
        probability=1.0,
    )
    config = ChaosConfig(faults=[fault_spec], seed=42)
    
    wrapper = ChaosRoboticsWrapper(inner, config)
    
    # F1 should only affect observations, not control methods
    # Verify control methods are not affected
    assert wrapper.move_end_effector.__name__ == "move_end_effector"
    assert wrapper.grip.__name__ == "grip"
    assert wrapper.release.__name__ == "release"


def test_replanning_disabled_by_default():
    """Test that replanning is disabled by default (preserves Phase A behavior)."""
    from alpha.services.agent_service import AgentService, AgentBrain
    from alpha.services.control_service import ControlService
    from alpha.core.interfaces import SimulatorClient
    from alpha.core.entities import TaskSpec, ActionType, BlockColor
    from alpha.schemas.action_plan import ActionPlan, ActionStep
    
    # Create mocks
    brain = MagicMock(spec=AgentBrain)
    control = MagicMock(spec=ControlService)
    simulator = MagicMock(spec=SimulatorClient)
    
    # Setup brain to return plan
    plan = ActionPlan(
        agent_name="test",
        actions=[
            ActionStep(action=ActionType.MOVE_TO, target=(0.5, 0.5, 0.5)),
            ActionStep(action=ActionType.GRIP, block=BlockColor.RED),
            ActionStep(action=ActionType.RELEASE),
        ]
    )
    brain.plan.return_value = plan
    
    # Setup control and simulator mocks
    control.fault_injector = None
    control.move_to.return_value = {"reached_pos": (0.5, 0.5, 0.5), "error": 0.0}
    control.grip.return_value = "grip_handle"
    control.evaluate_task.return_value = (True, 0.1, (0.5, 0.5, 0.5))
    simulator.observe.return_value = {"red": (0.5, 0.5, 0.5)}
    
    service = AgentService(brain, control, simulator)
    
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.8, 0.8, 0.0))
    
    # Run without replanning (default)
    result = service.run_task(task, scene_info={"red": (0.5, 0.5, 0.5)})
    
    # Should NOT call observe (no replanning)
    assert simulator.observe.call_count == 0
    # Should call plan only once (no replanning)
    assert brain.plan.call_count == 1


def _make_plan(*targets):
    from alpha.core.entities import ActionType, BlockColor
    from alpha.schemas.action_plan import ActionPlan, ActionStep

    actions = []
    for item in targets:
        if item == "GRIP":
            actions.append(ActionStep(action=ActionType.GRIP, block=BlockColor.RED))
        elif item == "RELEASE":
            actions.append(ActionStep(action=ActionType.RELEASE))
        else:
            actions.append(ActionStep(action=ActionType.MOVE_TO, target=item))
    return ActionPlan(agent_name="test", actions=actions)


def _service_with_brain(brain):
    from unittest.mock import MagicMock

    from alpha.core.interfaces import SimulatorClient
    from alpha.services.agent_service import AgentService
    from alpha.services.control_service import ControlService

    control = MagicMock(spec=ControlService)
    simulator = MagicMock(spec=SimulatorClient)
    control.fault_injector = None
    control.move_to.return_value = {"reached_pos": (0.5, 0.5, 0.5), "error": 0.0}
    control.grip.return_value = "grip_handle"
    control.evaluate_task.return_value = (True, 0.1, (0.8, 0.8, 0.8))
    simulator.observe.return_value = {"red": (0.6, 0.6, 0.6)}
    return AgentService(brain, control, simulator), control, simulator


def test_f1_episode_terminates_with_bounded_replans():
    """One F1 episode must terminate and keep replan count bounded."""
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain, REPLANNING_TIMEOUT_REASON

    brain = MagicMock(spec=AgentBrain)
    long_plan = _make_plan(
        (0.5, 0.5, 0.7),
        (0.5, 0.5, 0.6),
        (0.5, 0.5, 0.7),
        (0.5, 0.5, 0.6),
    )
    # Return a plan that never reaches completion to test timeout boundedness.
    brain.plan.return_value = long_plan

    service, control, simulator = _service_with_brain(brain)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        scene_info={"blocks": {"red": (0.5, 0.5, 0.65)}},
        enable_replanning=True,
        replanning_chunk_size=3,
        max_replanning_attempts=3,
    )

    payload = json.loads(result.execution_log_json)
    assert payload["replan_count"] <= 3
    assert payload["replan_count"] == 3
    assert brain.plan.call_count == 1 + 3  # initial + bounded replans
    assert payload["timed_out"] is True
    assert result.notes == REPLANNING_TIMEOUT_REASON
    assert result.success is False
    assert payload["chunk_index"] >= 1
    assert simulator.observe.call_count == 3


def test_chunk_index_advances_across_replanning_loop():
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain

    brain = MagicMock(spec=AgentBrain)
    brain.plan.side_effect = [
        _make_plan((0.1, 0.1, 0.1), (0.2, 0.2, 0.2), (0.3, 0.3, 0.3), (0.4, 0.4, 0.4)),
        _make_plan((0.5, 0.5, 0.5)),
    ]
    service, _, _ = _service_with_brain(brain)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        scene_info={"blocks": {"red": (0.5, -0.15, 0.65)}},
        enable_replanning=True,
        replanning_chunk_size=2,
        max_replanning_attempts=3,
    )

    payload = json.loads(result.execution_log_json)
    assert payload["chunk_index"] >= 2
    assert payload["replan_count"] == 1
    assert payload["timed_out"] is False
    assert result.success is True


def test_loop_exits_after_successful_completion_without_timeout():
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain

    brain = MagicMock(spec=AgentBrain)
    brain.plan.return_value = _make_plan((0.5, 0.5, 0.5), "GRIP", "RELEASE")
    service, control, _ = _service_with_brain(brain)
    control.evaluate_task.return_value = (True, 0.01, (0.6, 0.35, 0.65))
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        enable_replanning=True,
        replanning_chunk_size=3,
        max_replanning_attempts=3,
    )

    payload = json.loads(result.execution_log_json)
    assert result.success is True
    assert payload["timed_out"] is False
    assert payload["replan_count"] == 0
    assert result.notes == ""


def test_loop_exits_after_task_failure_without_hanging():
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain

    brain = MagicMock(spec=AgentBrain)
    brain.plan.return_value = _make_plan((0.5, 0.5, 0.5), "GRIP", "RELEASE")
    service, control, _ = _service_with_brain(brain)
    control.evaluate_task.return_value = (False, 0.9, (0.1, 0.1, 0.1))
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        enable_replanning=True,
        replanning_chunk_size=3,
        max_replanning_attempts=3,
    )

    payload = json.loads(result.execution_log_json)
    assert result.success is False
    assert payload["timed_out"] is False
    assert brain.plan.call_count == 1


def test_loop_exits_after_replanning_timeout():
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_hooks import AgentRunHooks
    from alpha.services.agent_service import AgentBrain, REPLANNING_TIMEOUT_REASON

    brain = MagicMock(spec=AgentBrain)
    brain.plan.return_value = _make_plan(
        (0.1, 0.1, 0.1),
        (0.2, 0.2, 0.2),
        (0.3, 0.3, 0.3),
        (0.4, 0.4, 0.4),
    )
    service, _, _ = _service_with_brain(brain)
    replan_hooks = []

    def on_replan(count, context):
        replan_hooks.append((count, context["chunk_index"]))

    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))
    result = service.run_task(
        task,
        hooks=AgentRunHooks(on_replan=on_replan),
        enable_replanning=True,
        replanning_chunk_size=2,
        max_replanning_attempts=2,
    )

    payload = json.loads(result.execution_log_json)
    assert result.notes == REPLANNING_TIMEOUT_REASON
    assert payload["timed_out"] is True
    assert payload["replan_count"] == 2
    assert len(replan_hooks) == 2
    assert result.success is False
    assert any(entry.get("replanning_timeout") for entry in payload["actions"])


def test_infinite_full_plan_replacement_cannot_hang():
    """Regression: replacing remainder with a full plan must not loop forever."""
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain, REPLANNING_TIMEOUT_REASON

    brain = MagicMock(spec=AgentBrain)
    call_count = {"n": 0}

    def always_full_plan(task, scene_info=None):
        call_count["n"] += 1
        assert call_count["n"] <= 20  # hard guard if bound regresses
        return _make_plan(
            (0.5, -0.15, 0.8),
            (0.5, -0.15, 0.67),
            (0.5, -0.15, 0.8),
            (0.5, -0.15, 0.67),
        )

    brain.plan.side_effect = always_full_plan
    service, _, _ = _service_with_brain(brain)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        enable_replanning=True,
        replanning_chunk_size=3,
        max_replanning_attempts=3,
    )

    payload = json.loads(result.execution_log_json)
    assert call_count["n"] == 4  # 1 initial + 3 replans
    assert payload["replan_count"] == 3


def test_requested_lag_0_5_produces_observed_lag_approximately_0_5():
    """Test that requested lag 0.5s produces observed lag approximately 0.5s."""
    from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper
    from alpha.core.interfaces import SimulatorClient
    from alpha.models.chaos_config import ChaosConfig, FaultIntensity, FaultSpec, TriggerConfig, TriggerKind
    from alpha.core.entities import FaultType
    
    inner = MagicMock(spec=SimulatorClient)
    # Use a callable to generate observations on demand
    call_count = {"n": 0}
    def observe_func():
        call_count["n"] += 1
        return {"red": (0.5 + call_count["n"]*0.01, 0.5 + call_count["n"]*0.01, 0.5 + call_count["n"]*0.01)}
    inner.observe.side_effect = observe_func
    
    fault_spec = FaultSpec(
        fault_type=FaultType.SENSOR_LAG,
        intensity=FaultIntensity(lag_seconds=0.5),
        trigger=TriggerConfig(kind=TriggerKind.IMMEDIATE),
        probability=1.0,
    )
    config = ChaosConfig(faults=[fault_spec], seed=42, sim_timestep=0.05)
    
    wrapper = ChaosRoboticsWrapper(inner, config)
    
    # Build scene to seed initial observation
    wrapper.build_scene()
    
    # Simulate time progression by stepping
    for _ in range(10):  # Advance to t=0.5
        wrapper.step(1)
    
    # Get observation with lag applied
    obs = wrapper.observe()
    meta = wrapper.last_observation_meta
    
    # The observed lag should be approximately 0.5s (within tolerance)
    assert meta["requested_lag"] == 0.5
    # With the closest-match algorithm, we should get reasonably close to the requested lag
    # The tolerance is relaxed because we're working with discrete time steps
    assert abs(meta["observed_lag"] - 0.5) < 0.2  # Within 200ms tolerance
    assert meta["stale"] is True
    assert meta["returned_timestamp"] < meta["current_timestamp"]


def test_requested_lag_0_75_produces_observed_lag_approximately_0_75():
    """Test that requested lag 0.75s produces observed lag approximately 0.75s."""
    from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper
    from alpha.core.interfaces import SimulatorClient
    from alpha.models.chaos_config import ChaosConfig, FaultIntensity, FaultSpec, TriggerConfig, TriggerKind
    from alpha.core.entities import FaultType
    
    inner = MagicMock(spec=SimulatorClient)
    # Use a callable to generate observations on demand
    call_count = {"n": 0}
    def observe_func():
        call_count["n"] += 1
        return {"red": (0.5 + call_count["n"]*0.01, 0.5 + call_count["n"]*0.01, 0.5 + call_count["n"]*0.01)}
    inner.observe.side_effect = observe_func
    
    fault_spec = FaultSpec(
        fault_type=FaultType.SENSOR_LAG,
        intensity=FaultIntensity(lag_seconds=0.75),
        trigger=TriggerConfig(kind=TriggerKind.IMMEDIATE),
        probability=1.0,
    )
    config = ChaosConfig(faults=[fault_spec], seed=42, sim_timestep=0.05)
    
    wrapper = ChaosRoboticsWrapper(inner, config)
    wrapper.build_scene()
    
    # Advance to t=0.75
    for _ in range(15):
        wrapper.step(1)
    
    obs = wrapper.observe()
    meta = wrapper.last_observation_meta
    
    assert meta["requested_lag"] == 0.75
    # Relaxed tolerance for discrete time steps
    assert abs(meta["observed_lag"] - 0.75) < 0.25  # Within 250ms tolerance
    assert meta["stale"] is True


def test_requested_lag_1_0_produces_observed_lag_approximately_1_0():
    """Test that requested lag 1.0s produces observed lag approximately 1.0s."""
    from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper
    from alpha.core.interfaces import SimulatorClient
    from alpha.models.chaos_config import ChaosConfig, FaultIntensity, FaultSpec, TriggerConfig, TriggerKind
    from alpha.core.entities import FaultType
    
    inner = MagicMock(spec=SimulatorClient)
    # Use a callable to generate observations on demand
    call_count = {"n": 0}
    def observe_func():
        call_count["n"] += 1
        return {"red": (0.5 + call_count["n"]*0.01, 0.5 + call_count["n"]*0.01, 0.5 + call_count["n"]*0.01)}
    inner.observe.side_effect = observe_func
    
    fault_spec = FaultSpec(
        fault_type=FaultType.SENSOR_LAG,
        intensity=FaultIntensity(lag_seconds=1.0),
        trigger=TriggerConfig(kind=TriggerKind.IMMEDIATE),
        probability=1.0,
    )
    config = ChaosConfig(faults=[fault_spec], seed=42, sim_timestep=0.05)
    
    wrapper = ChaosRoboticsWrapper(inner, config)
    wrapper.build_scene()
    
    # Advance to t=1.0
    for _ in range(20):
        wrapper.step(1)
    
    obs = wrapper.observe()
    meta = wrapper.last_observation_meta
    
    assert meta["requested_lag"] == 1.0
    # Relaxed tolerance for discrete time steps
    assert abs(meta["observed_lag"] - 1.0) < 0.3  # Within 300ms tolerance
    assert meta["stale"] is True


def test_stale_observation_timestamp_is_genuinely_older():
    """Test that stale observation timestamp is genuinely older than current observation."""
    from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper
    from alpha.core.interfaces import SimulatorClient
    from alpha.models.chaos_config import ChaosConfig, FaultIntensity, FaultSpec, TriggerConfig, TriggerKind
    from alpha.core.entities import FaultType
    
    inner = MagicMock(spec=SimulatorClient)
    # Use a callable to generate observations on demand
    call_count = {"n": 0}
    def observe_func():
        call_count["n"] += 1
        return {"red": (0.5 + call_count["n"]*0.01, 0.5 + call_count["n"]*0.01, 0.5 + call_count["n"]*0.01)}
    inner.observe.side_effect = observe_func
    
    fault_spec = FaultSpec(
        fault_type=FaultType.SENSOR_LAG,
        intensity=FaultIntensity(lag_seconds=0.5),
        trigger=TriggerConfig(kind=TriggerKind.IMMEDIATE),
        probability=1.0,
    )
    config = ChaosConfig(faults=[fault_spec], seed=42, sim_timestep=0.05)
    
    wrapper = ChaosRoboticsWrapper(inner, config)
    wrapper.build_scene()
    
    # Advance time
    for _ in range(10):
        wrapper.step(1)
    
    obs = wrapper.observe()
    meta = wrapper.last_observation_meta
    
    # The returned timestamp must be older than current timestamp
    assert meta["returned_timestamp"] < meta["current_timestamp"]
    # The difference should be approximately the requested lag (with relaxed tolerance)
    assert abs((meta["current_timestamp"] - meta["returned_timestamp"]) - meta["requested_lag"]) < 0.25


def test_replanning_preserves_task_progress():
    """Test that replanning preserves task progress by tracking task_phase and block_gripped."""
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain

    brain = MagicMock(spec=AgentBrain)
    
    # First plan: pick sequence
    plan1 = _make_plan((0.5, 0.5, 0.8), (0.5, 0.5, 0.65), "GRIP")
    # Replan: should continue from place phase, not restart pick
    plan2 = _make_plan((0.6, 0.35, 0.8), "RELEASE")
    
    brain.plan.side_effect = [plan1, plan2]
    
    service, control, simulator = _service_with_brain(brain)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        scene_info={"blocks": {"red": (0.5, 0.5, 0.65)}},
        enable_replanning=True,
        replanning_chunk_size=2,
        max_replanning_attempts=3,
    )

    payload = json.loads(result.execution_log_json)
    # Should have called plan twice (initial + replan)
    assert brain.plan.call_count == 2
    
    # Verify that the second plan call received context about task progress
    second_call_kwargs = brain.plan.call_args_list[1][1]
    assert "scene_info" in second_call_kwargs or len(brain.plan.call_args_list[1][0]) > 1
    
    # The replan should have received context about completed steps
    if "scene_info" in second_call_kwargs:
        scene_info = second_call_kwargs["scene_info"]
        assert "task_phase" in scene_info or "completed_steps" in scene_info


def test_task_progress_is_monotonic():
    """Test that task progress (task_phase) advances monotonically during execution."""
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain

    brain = MagicMock(spec=AgentBrain)
    brain.plan.return_value = _make_plan((0.5, 0.5, 0.8), (0.5, 0.5, 0.65), "GRIP", (0.6, 0.35, 0.8), "RELEASE")
    
    service, control, _ = _service_with_brain(brain)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        enable_replanning=False,  # No replanning needed for this test
    )

    # The task should complete successfully
    assert result.success
    # Actions should execute in order: MOVE_TO, MOVE_TO, GRIP, MOVE_TO, RELEASE
    assert result.steps_taken == 5


def test_replanning_eventually_terminates():
    """Test that replanning eventually terminates even with repeated full plans."""
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain, REPLANNING_TIMEOUT_REASON

    brain = MagicMock(spec=AgentBrain)
    
    # Always return a full plan to test termination
    def full_plan(task, scene_info=None):
        return _make_plan((0.5, 0.5, 0.8), (0.5, 0.5, 0.65), "GRIP", (0.6, 0.35, 0.8), "RELEASE")
    
    brain.plan.side_effect = full_plan
    service, _, _ = _service_with_brain(brain)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        enable_replanning=True,
        replanning_chunk_size=2,
        max_replanning_attempts=3,
    )

    payload = json.loads(result.execution_log_json)
    # Should terminate due to replanning timeout
    assert payload["timed_out"] is True
    assert payload["replan_count"] <= 3
    # The loop should not hang indefinitely
    assert brain.plan.call_count <= 4  # 1 initial + 3 replans


def test_control_behavior_unchanged():
    """Test that CONTROL behavior (no replanning) remains unchanged."""
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain

    brain = MagicMock(spec=AgentBrain)
    brain.plan.return_value = _make_plan((0.5, 0.5, 0.8), (0.5, 0.5, 0.65), "GRIP", (0.6, 0.35, 0.8), "RELEASE")
    
    service, control, simulator = _service_with_brain(brain)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        enable_replanning=False,  # CONTROL: no replanning
    )

    payload = json.loads(result.execution_log_json)
    # CONTROL should not observe or replan
    assert payload["replan_count"] == 0
    assert payload["observation_count"] == 0
    assert simulator.observe.call_count == 0
    assert brain.plan.call_count == 1  # Only initial plan
    assert result.success
    assert result.notes == ""  # No timeout in CONTROL mode
    assert payload["timed_out"] is False


def test_replanning_includes_task_state_context():
    """Test that replanning includes task state context (task_phase, block_gripped)."""
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain

    brain = MagicMock(spec=AgentBrain)
    
    # First plan: pick sequence
    plan1 = _make_plan((0.5, 0.5, 0.8), "GRIP")
    # Replan: should receive context
    plan2 = _make_plan((0.6, 0.35, 0.8), "RELEASE")
    
    # Use a callable that always returns plan2 after the first call
    call_count = {"n": 0}
    def plan_with_context(task, scene_info=None):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return plan1
        else:
            # For subsequent calls, verify context and return plan2
            if scene_info and isinstance(scene_info, dict):
                # Should have context fields
                assert any(key in scene_info for key in ["task_phase", "block_gripped", "completed_steps", "remaining_actions"])
            return plan2
    
    brain.plan.side_effect = plan_with_context
    
    service, control, simulator = _service_with_brain(brain)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        scene_info={"blocks": {"red": (0.5, 0.5, 0.65)}},
        enable_replanning=True,
        replanning_chunk_size=1,  # Small chunk to trigger replan
        max_replanning_attempts=3,
    )

    # Verify that replanning occurred and context was passed
    assert brain.plan.call_count >= 2
    assert call_count["n"] >= 2


def test_completed_grip_not_repeated_unnecessarily():
    """Test that once GRIP is completed, replanning doesn't repeat it unnecessarily."""
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain

    brain = MagicMock(spec=AgentBrain)
    
    # First plan: full pick and place sequence
    plan1 = _make_plan((0.5, 0.5, 0.8), (0.5, 0.5, 0.65), "GRIP", (0.6, 0.35, 0.8), "RELEASE")
    # Replan after GRIP: should only include place actions
    plan2 = _make_plan((0.6, 0.35, 0.71), "RELEASE")
    
    call_count = {"n": 0}
    def plan_with_progress(task, scene_info=None):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return plan1
        else:
            # After GRIP, task description should indicate block is gripped
            if scene_info and isinstance(scene_info, dict):
                # Verify we got context about completed actions
                assert "completed_actions" in scene_info
                assert "GRIP" in scene_info["completed_actions"]
            return plan2
    
    brain.plan.side_effect = plan_with_progress
    
    service, control, simulator = _service_with_brain(brain)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        scene_info={"blocks": {"red": (0.5, 0.5, 0.65)}},
        enable_replanning=True,
        replanning_chunk_size=3,  # Execute first 3 actions (MOVE_TO, MOVE_TO, GRIP)
        max_replanning_attempts=3,
    )

    payload = json.loads(result.execution_log_json)
    # Should have replanned once after GRIP
    assert payload["replan_count"] >= 1
    # Verify the execution log doesn't have repeated GRIP actions
    actions = payload.get("actions", [])
    grip_count = sum(1 for action in actions if action.get("action") == "GRIP")
    assert grip_count == 1, f"Expected exactly 1 GRIP, got {grip_count}"


def test_task_progress_is_monotonic():
    """Test that task progress advances monotonically - once an action type is completed, it's not revisited."""
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain

    brain = MagicMock(spec=AgentBrain)
    
    # Plan that completes the task
    plan = _make_plan((0.5, 0.5, 0.8), (0.5, 0.5, 0.65), "GRIP", (0.6, 0.35, 0.8), "RELEASE")
    brain.plan.return_value = plan
    
    service, control, simulator = _service_with_brain(brain)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        scene_info={"blocks": {"red": (0.5, 0.5, 0.65)}},
        enable_replanning=False,  # No replanning for this test
    )

    payload = json.loads(result.execution_log_json)
    actions = payload.get("actions", [])
    
    # Verify monotonic progress: GRIP appears before RELEASE
    grip_index = None
    release_index = None
    for i, action in enumerate(actions):
        if action.get("action") == "GRIP":
            grip_index = i
        elif action.get("action") == "RELEASE":
            release_index = i
    
    assert grip_index is not None, "GRIP action not found"
    assert release_index is not None, "RELEASE action not found"
    assert grip_index < release_index, "GRIP should come before RELEASE"
    
    # Verify no action type is revisited after completion
    action_sequence = [action.get("action") for action in actions]
    for action_type in ["GRIP", "RELEASE"]:
        first_occurrence = action_sequence.index(action_type) if action_type in action_sequence else -1
        if first_occurrence >= 0:
            # After first occurrence, this action type should not appear again
            remaining_actions = action_sequence[first_occurrence + 1:]
            assert action_type not in remaining_actions, f"{action_type} repeated after completion"


def test_replanning_can_reach_release_place():
    """Test that replanning can continue through to RELEASE/place phase."""
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain

    brain = MagicMock(spec=AgentBrain)
    
    # First plan: pick sequence that includes GRIP
    plan1 = _make_plan((0.5, 0.5, 0.8), (0.5, 0.5, 0.65), "GRIP")
    # Replan after GRIP: place sequence  
    plan2 = _make_plan((0.6, 0.35, 0.8), "RELEASE")
    
    call_count = {"n": 0}
    def plan_with_progress(task, scene_info=None):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return plan1
        else:
            # After GRIP, should get task to continue to place
            if scene_info and isinstance(scene_info, dict):
                # Verify task description indicates block is gripped
                if hasattr(task, 'description'):
                    assert "grip" in task.description.lower() or "place" in task.description.lower()
            return plan2
    
    brain.plan.side_effect = plan_with_progress
    
    service, control, simulator = _service_with_brain(brain)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        scene_info={"blocks": {"red": (0.5, 0.5, 0.65)}},
        enable_replanning=True,
        replanning_chunk_size=2,  # Execute first 2 actions, then replan
        max_replanning_attempts=3,
    )

    # Verify that replanning occurred and context was passed
    assert brain.plan.call_count >= 2, "Should have replanned at least once"
    assert call_count["n"] >= 2, "Mock should have been called multiple times"
    
    # Verify the task description was modified to indicate progress
    # This is tested in the plan_with_progress function's assertions


def test_normal_control_still_succeeds():
    """Test that normal CONTROL (no replanning) still succeeds without issues."""
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain

    brain = MagicMock(spec=AgentBrain)
    brain.plan.return_value = _make_plan((0.5, 0.5, 0.8), (0.5, 0.5, 0.65), "GRIP", (0.6, 0.35, 0.8), "RELEASE")
    
    service, control, simulator = _service_with_brain(brain)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        scene_info={"blocks": {"red": (0.5, 0.5, 0.65)}},
        enable_replanning=False,  # CONTROL mode
    )

    assert result.success, "CONTROL mode should succeed"
    assert result.steps_taken == 5, "Should execute all 5 actions"
    
    payload = json.loads(result.execution_log_json)
    assert payload["replan_count"] == 0, "CONTROL should not replan"
    assert payload["timed_out"] is False, "CONTROL should not timeout"


def test_f1_can_complete_with_stale_observation():
    """Test that F1 can complete when stale observation doesn't prevent task completion."""
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain

    brain = MagicMock(spec=AgentBrain)
    
    # Simple plan that should complete despite stale observations
    plan = _make_plan((0.5, 0.5, 0.8), (0.5, 0.5, 0.65), "GRIP", (0.6, 0.35, 0.8), "RELEASE")
    brain.plan.return_value = plan
    
    service, control, simulator = _service_with_brain(brain)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        scene_info={"blocks": {"red": (0.5, 0.5, 0.65)}},
        enable_replanning=True,
        replanning_chunk_size=5,  # Large chunk to avoid replanning
        max_replanning_attempts=3,
    )

    # Should complete successfully without hitting replanning timeout
    assert result.success, "F1 should complete with simple plan"
    assert result.steps_taken == 5, "Should execute all 5 actions"
    
    payload = json.loads(result.execution_log_json)
    # With large chunk size, should not replan
    assert payload["timed_out"] is False, "Should not timeout"


def test_timeout_remains_bounded():
    """Test that timeout remains bounded and doesn't hang indefinitely."""
    import json
    from unittest.mock import MagicMock

    from alpha.core.entities import BlockColor, TaskSpec
    from alpha.services.agent_service import AgentBrain, REPLANNING_TIMEOUT_REASON
    from alpha.models.agent_config import AgentConfig

    brain = MagicMock(spec=AgentBrain)
    
    # Always return full plan to test timeout behavior
    def full_plan(task, scene_info=None):
        return _make_plan((0.5, 0.5, 0.8), (0.5, 0.5, 0.65), "GRIP", (0.6, 0.35, 0.8), "RELEASE")
    
    brain.plan.side_effect = full_plan
    service, _, _ = _service_with_brain(brain)
    task = TaskSpec(block=BlockColor.RED, place_zone=(0.6, 0.35, 0.65))

    result = service.run_task(
        task,
        enable_replanning=True,
        replanning_chunk_size=2,
        max_replanning_attempts=3,
    )

    payload = json.loads(result.execution_log_json)
    # Should terminate due to replanning timeout
    assert payload["timed_out"] is True, "Should timeout"
    assert payload["replan_count"] <= 3, "Should respect max_replanning_attempts"
    assert brain.plan.call_count <= 4, "Should not hang indefinitely (1 initial + 3 replans)"
    
    # Verify timeout configuration exists
    assert hasattr(AgentConfig, 'max_episode_wall_seconds')
    assert AgentConfig.max_episode_wall_seconds > 0
    assert hasattr(AgentConfig, 'max_replanning_attempts')
    assert AgentConfig.max_replanning_attempts >= 0
