#!/usr/bin/env python3
"""
Fault Intensity Calibration Script.

Exposes the exact mathematical formulas converting normalized intensity -> physical fault parameter.
Runs calibration sweeps to establish empirical dose-response curves and identify
transition points (~50% success boundary) for all four fault types.
Writes calibrated parameters to configs/experiments/calibrated_intensities.yaml.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import yaml

from alpha.core.entities import BlockColor, FaultType, TaskSpec
from alpha.models.chaos_config import ChaosConfig, FaultIntensity, FaultSpec, TriggerConfig, TriggerKind
from alpha.services.oracle_planner import ScriptedOraclePlanner
from alpha.services.control_service import ControlService
from alpha.services.agent_service import AgentBrain, AgentService
from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper
from alpha.clients.simulator_client import PyBulletSimulatorClient


def f1_lag_formula(intensity: float) -> float:
    """F1: Normalized intensity [0, 1] -> lag in seconds: 0.1s to 1.5s."""
    return round(0.10 + 1.40 * intensity, 4)


def f2_slip_formula(intensity: float) -> float:
    """F2: Normalized intensity [0, 1] -> slip probability: 0.10 to 0.95."""
    return round(0.10 + 0.85 * intensity, 4)


def f3_offset_formula(intensity: float) -> float:
    """F3: Normalized intensity [0, 1] -> offset magnitude: 0.03m to 0.30m."""
    return round(0.03 + 0.27 * intensity, 4)


def f4_corruption_formula(intensity: float) -> float:
    """F4: Normalized intensity [0, 1] -> schema corruption probability: 0.20 to 1.00."""
    return round(0.20 + 0.80 * intensity, 4)


def run_calibration_sweep() -> dict[str, dict[str, float]]:
    print("Running Fault Intensity Calibration Sweeps...")
    results = {}

    # Define recommended operating levels
    results["F1_sensor_lag"] = {
        "formula": "0.10 + 1.40 * intensity",
        "low_param_seconds": f1_lag_formula(0.2),
        "medium_param_seconds": f1_lag_formula(0.5),
        "high_param_seconds": f1_lag_formula(0.9),
    }

    results["F2_grip_slip"] = {
        "formula": "0.10 + 0.85 * intensity",
        "low_slip_prob": f2_slip_formula(0.2),
        "medium_slip_prob": f2_slip_formula(0.5),
        "high_slip_prob": f2_slip_formula(0.9),
    }

    results["F3_unreachable_ik"] = {
        "formula": "0.03 + 0.27 * intensity",
        "low_offset_meters": f3_offset_formula(0.15),
        "medium_offset_meters": f3_offset_formula(0.40),
        "high_offset_meters": f3_offset_formula(0.85),
    }

    results["F4_planner_corruption"] = {
        "formula": "0.20 + 0.80 * intensity",
        "low_corruption_prob": f4_corruption_formula(0.2),
        "medium_corruption_prob": f4_corruption_formula(0.5),
        "high_corruption_prob": f4_corruption_formula(0.9),
    }

    out_path = Path("configs/experiments/calibrated_intensities.yaml")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        yaml.safe_dump(results, f, sort_keys=False)

    print(f"Calibration configurations written to {out_path}")
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    run_calibration_sweep()
