"""
Tests for F1 Sensor Lag in Dynamic / State-Changing Scenes.

Proves that:
1. When environment state changes over time (block moves), fresh observation != delayed observation.
2. The measurable observation difference (Euclidean distance) is accurately computed and logged.
3. requested lag, applied lag, observed lag, observation timestamp, and environment timestamp are all recorded.
"""

from unittest.mock import MagicMock
from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper
from alpha.core.entities import BlockColor, FaultType
from alpha.core.interfaces import SimulatorClient
from alpha.models.chaos_config import ChaosConfig, FaultIntensity, FaultSpec, TriggerConfig, TriggerKind


def test_f1_dynamic_observation_divergence():
    """Verify that when block positions change dynamically, fresh != delayed and difference > 0."""
    inner = MagicMock(spec=SimulatorClient)

    # Simulate dynamic movement of the RED block across time
    # At t=0: pos=(0.5, -0.15, 0.68)
    # At t=0.5: pos=(0.5, -0.10, 0.68) [moved 0.05m along y]
    # At t=1.0: pos=(0.5, -0.05, 0.68) [moved 0.10m along y]
    snapshots = [
        {"blocks": {"red": (0.5, -0.15, 0.68)}},
        {"blocks": {"red": (0.5, -0.10, 0.68)}},
        {"blocks": {"red": (0.5, -0.05, 0.68)}},
    ]

    current_idx = [0]

    def mock_observe():
        idx = min(current_idx[0], len(snapshots) - 1)
        return snapshots[idx]

    inner.observe.side_effect = mock_observe
    inner.step.return_value = None

    spec = FaultSpec(
        fault_type=FaultType.SENSOR_LAG,
        enabled=True,
        trigger=TriggerConfig(kind=TriggerKind.IMMEDIATE),
        intensity=FaultIntensity(lag_seconds=0.5),
        probability=1.0,
    )
    config = ChaosConfig(seed=42, faults=[spec])
    wrapper = ChaosRoboticsWrapper(inner=inner, config=config)

    # Initial step at t=0
    wrapper.context.elapsed_seconds = 0.0
    wrapper.context.sim_step_count = 0
    obs0 = wrapper.observe()  # records sample at t=0
    assert obs0["blocks"]["red"] == (0.5, -0.15, 0.68)

    # Advance simulation to t=0.5s (block has moved to -0.10)
    current_idx[0] = 1
    wrapper.context.elapsed_seconds = 0.5
    wrapper.context.sim_step_count = 120
    obs1 = wrapper.observe()

    # Advance simulation to t=1.0s (block has moved to -0.05)
    current_idx[0] = 2
    wrapper.context.elapsed_seconds = 1.0
    wrapper.context.sim_step_count = 240
    obs2 = wrapper.observe()

    # With lag=0.5s at t=1.0s, the delayed observation should be from t=0.5s!
    # Fresh observation would be (0.5, -0.05, 0.68), delayed is (0.5, -0.10, 0.68)
    assert obs2["blocks"]["red"] != snapshots[2]["blocks"]["red"]
    assert obs2["blocks"]["red"] == (0.5, -0.10, 0.68)

    meta = wrapper.last_observation_meta
    assert meta["stale"] is True
    assert meta["requested_lag"] == 0.5
    assert abs(meta["observed_lag"] - 0.5) < 1e-3
    assert abs(meta["applied_lag"] - 0.5) < 1e-3
    assert meta["current_timestamp"] == 1.0
    assert meta["returned_timestamp"] == 0.5

    # Measurable Euclidean difference: |-0.05 - (-0.10)| = 0.05m
    assert abs(meta["observation_difference"] - 0.05) < 1e-4
    assert wrapper.observation_difference > 0.0

    # Verify event log captures all required fields
    events = [e for e in wrapper.event_log() if e.get("fault_type") == FaultType.SENSOR_LAG]
    assert len(events) >= 1
    last_event = events[-1]
    assert last_event["requested_lag"] == 0.5
    assert last_event["applied_lag"] == 0.5
    assert last_event["observed_lag_seconds"] == 0.5
    assert last_event["observation_timestamp"] == 0.5
    assert last_event["environment_timestamp"] == 1.0
    assert abs(last_event["observation_difference"] - 0.05) < 1e-4
