"""
Tests for F2 Grip Slip probability calibration and logging.

Verifies that:
1. Low slip probability (e.g. 0.20) does NOT collapse to 100% slip due to per-step evaluation.
2. configured_slip_probability and slip_triggered are accurately recorded in event logs.
3. Realized slip rate over multiple seeded runs approximates the configured probability.
"""

from unittest.mock import MagicMock
from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper
from alpha.core.entities import BlockColor, FaultType
from alpha.core.interfaces import SimulatorClient
from alpha.models.chaos_config import ChaosConfig, FaultIntensity, FaultSpec, TriggerConfig, TriggerKind


def test_f2_low_intensity_does_not_become_100_percent_slip():
    """Verify that a 20% slip probability only slips ~20% of the time across episodes."""
    slip_count = 0
    total_episodes = 50

    for seed in range(total_episodes):
        inner = MagicMock(spec=SimulatorClient)
        inner.grip.return_value = 42  # valid grip handle
        inner.step.return_value = None

        spec = FaultSpec(
            fault_type=FaultType.GRIP_SLIP,
            enabled=True,
            trigger=TriggerConfig(kind=TriggerKind.IMMEDIATE),
            intensity=FaultIntensity(slip_probability=0.20, weaken_force_factor=0.0),
            probability=1.0,
        )
        config = ChaosConfig(seed=seed, faults=[spec])
        wrapper = ChaosRoboticsWrapper(inner=inner, config=config)

        # Grip block
        handle = wrapper.grip(BlockColor.RED)
        assert handle == 42
        assert wrapper.grip_is_active is True

        # Simulate moving/lifting with 240 simulation steps
        for _ in range(240):
            wrapper.step(1)

        # Check if dropped
        if not wrapper.grip_is_active:
            slip_count += 1

        # Check event logging
        events = [e for e in wrapper.event_log() if e.get("fault_type") == FaultType.GRIP_SLIP]
        assert len(events) >= 1
        event = events[0]
        assert event["configured_slip_probability"] == 0.20
        assert "slip_triggered" in event

    realized_rate = slip_count / total_episodes
    # With 20% probability, realized rate should be around 0.10 to 0.35, definitely NOT 1.0 (100%)
    assert 0.05 <= realized_rate <= 0.40, f"Realized slip rate was {realized_rate}, expected ~0.20"


def test_f2_high_intensity_slips_reliably():
    """Verify that a 90% slip probability slips most of the time."""
    slip_count = 0
    total_episodes = 50

    for seed in range(total_episodes):
        inner = MagicMock(spec=SimulatorClient)
        inner.grip.return_value = 42
        inner.step.return_value = None

        spec = FaultSpec(
            fault_type=FaultType.GRIP_SLIP,
            enabled=True,
            trigger=TriggerConfig(kind=TriggerKind.IMMEDIATE),
            intensity=FaultIntensity(slip_probability=0.90, weaken_force_factor=0.0),
            probability=1.0,
        )
        config = ChaosConfig(seed=seed, faults=[spec])
        wrapper = ChaosRoboticsWrapper(inner=inner, config=config)

        wrapper.grip(BlockColor.RED)
        for _ in range(240):
            wrapper.step(1)

        if not wrapper.grip_is_active:
            slip_count += 1

    realized_rate = slip_count / total_episodes
    assert realized_rate >= 0.75, f"Realized slip rate was {realized_rate}, expected >= 0.75"
