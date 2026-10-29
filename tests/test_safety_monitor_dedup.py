"""
Unit tests for Safety Monitor temporal deduplication and sensitivity analysis.
"""

from alpha.clients.safety_monitor import PyBulletSafetyMonitor, SafetyMonitorConfig


def test_safety_monitor_config_specification():
    """Verify machine-readable SafetyMonitorConfig contains all required fields."""
    cfg = SafetyMonitorConfig()
    assert cfg.contact_force_threshold_newtons == 3000.0
    assert cfg.sampling_frequency_hz == 240.0
    assert cfg.deduplication_window_steps == 15
    assert "IIWA arm links" in cfg.links_included_description
    assert cfg.force_units == "Newtons (N)"
    assert cfg.distance_units == "meters (m)"
    assert len(cfg.workspace_bounds) == 3
    assert len(cfg.place_zone_center) == 3
    assert cfg.place_zone_radius_meters == 0.18
    assert "unique_incident_count > 0" in cfg.episode_safety_violation_definition


def test_sustained_contact_merges_into_single_incident():
    """Verify that multiple continuous observations of contact yield exactly 1 unique incident."""
    monitor = PyBulletSafetyMonitor(deduplication_window_steps=15)

    # 30 consecutive steps of violent arm-block contact
    for step in range(30):
        monitor._begin_scan(sim_step=step)
        monitor._record(
            "violent_arm_block_contact",
            "arm:1-block:2",
            {"force": 3500.0},
        )
        monitor._finalize_scan()

    assert len(monitor.incidents) == 1
    incident = monitor.incidents[0]
    assert incident.raw_observations == 30
    assert incident.start_step == 0
    assert incident.end_step == 29
    assert incident.duration_steps == 30


def test_intermittent_contact_within_window_merges():
    """Verify that contact flickering with gap < deduplication_window_steps remains 1 incident."""
    monitor = PyBulletSafetyMonitor(deduplication_window_steps=10)

    # Contact at step 0..3
    for step in range(4):
        monitor._begin_scan(sim_step=step)
        monitor._record("violent_arm_block_contact", "arm:1-block:2", {"force": 3500.0})
        monitor._finalize_scan()

    # Gap of 5 steps (steps 4..8), no contact
    for step in range(4, 9):
        monitor._begin_scan(sim_step=step)
        monitor._finalize_scan()

    # Contact again at step 9..12 (gap was 5 steps, which is < 10 step window)
    for step in range(9, 13):
        monitor._begin_scan(sim_step=step)
        monitor._record("violent_arm_block_contact", "arm:1-block:2", {"force": 3500.0})
        monitor._finalize_scan()

    # Should still be 1 unique incident because the gap was smaller than the window
    assert len(monitor.incidents) == 1
    assert monitor.incidents[0].raw_observations == 8


def test_intermittent_contact_exceeding_window_creates_new_incident():
    """Verify that contact gap >= deduplication_window_steps closes the incident and creates a new one."""
    monitor = PyBulletSafetyMonitor(deduplication_window_steps=5)

    # Contact at step 0..2
    for step in range(3):
        monitor._begin_scan(sim_step=step)
        monitor._record("violent_arm_block_contact", "arm:1-block:2", {"force": 3500.0})
        monitor._finalize_scan()

    # Gap of 10 steps (steps 3..12), no contact (exceeds window of 5)
    for step in range(3, 13):
        monitor._begin_scan(sim_step=step)
        monitor._finalize_scan()

    # Contact again at step 13..15
    for step in range(13, 16):
        monitor._begin_scan(sim_step=step)
        monitor._record("violent_arm_block_contact", "arm:1-block:2", {"force": 3500.0})
        monitor._finalize_scan()

    # Should be 2 distinct incidents
    assert len(monitor.incidents) == 2


def test_deduplication_sensitivity_analysis():
    """Perform sensitivity analysis across window sizes."""
    # Pattern: contact at 0..2, gap 3..6 (4 steps), contact 7..9, gap 10..20 (11 steps), contact 21..23
    obs_by_step = {
        0: [("violent_arm_block_contact", "arm:1-block:2", {"force": 3500.0})],
        1: [("violent_arm_block_contact", "arm:1-block:2", {"force": 3500.0})],
        2: [("violent_arm_block_contact", "arm:1-block:2", {"force": 3500.0})],
        7: [("violent_arm_block_contact", "arm:1-block:2", {"force": 3500.0})],
        8: [("violent_arm_block_contact", "arm:1-block:2", {"force": 3500.0})],
        9: [("violent_arm_block_contact", "arm:1-block:2", {"force": 3500.0})],
        21: [("violent_arm_block_contact", "arm:1-block:2", {"force": 3500.0})],
        22: [("violent_arm_block_contact", "arm:1-block:2", {"force": 3500.0})],
        23: [("violent_arm_block_contact", "arm:1-block:2", {"force": 3500.0})],
    }

    results = PyBulletSafetyMonitor.run_sensitivity_analysis(
        obs_by_step, window_sizes=(1, 5, 15, 30)
    )

    # At window=1: each cluster is separated -> 3 incidents
    assert results[1] == 3
    # At window=5: gap of 4 is bridged -> first 2 clusters merge -> 2 incidents
    assert results[5] == 2
    # At window=15: gap of 11 is also bridged -> all 3 clusters merge -> 1 incident
    assert results[15] == 1
    assert results[30] == 1
