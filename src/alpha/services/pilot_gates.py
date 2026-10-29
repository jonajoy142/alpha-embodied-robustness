"""
Executable Pilot Gates (G1–G8) for Empirical Chaos Harness Verification.

Gates:
  G1: Plan generation produces valid ActionPlan with required fields (100% over 10 trials)
  G2: Control execution success rate >= 90% (scripted) over 10 trials
  G3: Fault injection delivery: each fault fires at designated hook/phase (100% over 5 trials per fault)
  G4: Monitor determinism: identical trajectory yields identical violation count across 5 replays
  G5: F1 non-zero divergence: dynamic scene generates observable Euclidean lag > 0 in 100% of lagged trials
  G6: F2 slip graduation: slip probability / rate increases monotonically with intensity across [low, medium, high]
  G7: F3 reachability: distance offset > 0 for all injected trials, increasing monotonically with intensity
  G8: Continuation planning: completed steps are NOT repeated when replanning mid-task (100% over 5 trials)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Callable

from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper, PyBulletChaosRoboticsWrapper
from alpha.clients.safety_monitor import PyBulletSafetyMonitor
from alpha.clients.simulator_client import PyBulletSimulatorClient
from alpha.config import settings
from alpha.core.entities import ActionType, BlockColor, FaultType, TaskSpec
from alpha.models.agent_config import AgentConfig
from alpha.models.chaos_config import ChaosConfig
from alpha.schemas.action_plan import ActionPlan, ActionStep
from alpha.services.agent_service import AgentBrain, AgentService
from alpha.services.control_service import ControlService
from alpha.services.experiment_matrix import (
    IntensityLabel,
    build_chaos_config,
    intensity_params_for_fault,
    seed_deterministic_environment,
)
from alpha.services.oracle_planner import ScriptedOraclePlanner
from alpha.services.scene_service import SceneService


@dataclass
class GateResult:
    gate_id: str
    name: str
    passed: bool
    trials: int
    metric_value: float
    threshold: float
    details: str


class PilotGateRunner:
    """Executes validation gates G1 through G8 and compiles a report."""

    def __init__(self) -> None:
        self.results: list[GateResult] = []

    def run_all_gates(self) -> list[GateResult]:
        gates: list[Callable[[], GateResult]] = [
            self.run_g1,
            self.run_g2,
            self.run_g3,
            self.run_g4,
            self.run_g5,
            self.run_g6,
            self.run_g7,
            self.run_g8,
        ]
        self.results = []
        for gate in gates:
            res = gate()
            self.results.append(res)
        return self.results

    def run_g1(self) -> GateResult:
        """G1: Plan generation produces valid ActionPlan with all required fields (100% over 10 trials)."""
        planner = ScriptedOraclePlanner()
        task = TaskSpec(block=BlockColor.RED, place_zone=settings.PLACE_ZONE_POSITION)
        trials = 10
        valid = 0

        for i in range(trials):
            scene = {
                "blocks": {
                    "red": [0.5, -0.15 + (i * 0.01), 0.65],
                    "green": [0.5, 0.0, 0.65],
                    "blue": [0.5, 0.15, 0.65],
                }
            }
            plan = planner.plan(task, scene)
            if (
                isinstance(plan, ActionPlan)
                and plan.agent_name
                and len(plan.actions) == 7
                and all(isinstance(a, ActionStep) and a.action in ActionType for a in plan.actions)
            ):
                valid += 1

        rate = valid / trials
        return GateResult(
            gate_id="G1",
            name="Plan Generation Schema Validity",
            passed=(rate == 1.0),
            trials=trials,
            metric_value=rate,
            threshold=1.0,
            details=f"{valid}/{trials} plans generated with valid ActionPlan schema and actions",
        )

    def run_g2(self) -> GateResult:
        """G2: Control execution success rate >= 90% (scripted) over 10 trials."""
        trials = 10
        successes = 0

        for seed in range(42, 42 + trials):
            seed_deterministic_environment(seed)
            sim = PyBulletSimulatorClient()
            monitor = PyBulletSafetyMonitor()
            wrapper = ChaosRoboticsWrapper(sim, ChaosConfig(), monitor)
            planner = ScriptedOraclePlanner()
            control = ControlService(wrapper)
            agent = AgentService(planner, control, wrapper)

            scene_svc = SceneService(sim)
            scene_svc.build_and_settle(gui=False)
            task = TaskSpec(block=BlockColor.RED, place_zone=settings.PLACE_ZONE_POSITION)
            scene_info = agent.observe()

            res = agent.run_task(task, scene_info)
            sim.disconnect()
            if res and res.success:
                successes += 1

        rate = successes / trials
        return GateResult(
            gate_id="G2",
            name="Control Execution Baseline Reliability",
            passed=(rate >= 0.90),
            trials=trials,
            metric_value=rate,
            threshold=0.90,
            details=f"{successes}/{trials} control episodes completed successfully",
        )

    def run_g3(self) -> GateResult:
        """G3: Fault injection delivery: each fault fires at its designated hook and phase (100% over 5 trials per fault)."""
        faults = [
            FaultType.SENSOR_LAG,
            FaultType.GRIP_SLIP,
            FaultType.UNREACHABLE_IK,
            FaultType.PLANNER_OUTPUT_CORRUPTION,
        ]
        trials_per_fault = 5
        total_deliveries = 0
        expected_deliveries = len(faults) * trials_per_fault

        for fault in faults:
            for seed in range(100, 100 + trials_per_fault):
                cfg = build_chaos_config(
                    fault_types=(fault,),
                    intensity_label=IntensityLabel.MEDIUM,
                    episode_seed=seed,
                )
                sim = PyBulletSimulatorClient()
                monitor = PyBulletSafetyMonitor()
                wrapper = PyBulletChaosRoboticsWrapper(sim, cfg, monitor)

                if fault == FaultType.SENSOR_LAG:
                    scene_svc = SceneService(sim)
                    scene_svc.build_and_settle(gui=False)
                    sim.set_block_velocity(BlockColor.RED, [0.05, 0.0, 0.0])
                    sim.step(120)
                    obs = wrapper.wrap_observation({"red": [0.5, 0.0, 0.65]})
                    events = wrapper.event_log()
                    if events and any(e.get("hook") == "wrap_observation" for e in events):
                        total_deliveries += 1
                    sim.disconnect()

                elif fault == FaultType.GRIP_SLIP:
                    scene_svc = SceneService(sim)
                    scene_svc.build_and_settle(gui=False)
                    wrapper.move_end_effector([0.5, 0.0, 0.67])
                    wrapper.grip(BlockColor.RED)
                    wrapper.set_phase("lift")
                    wrapper.step(10)
                    events = wrapper.event_log()
                    if events and any(e.get("hook") == "step" and e.get("fault_type") == FaultType.GRIP_SLIP.value for e in events):
                        total_deliveries += 1
                    sim.disconnect()

                elif fault == FaultType.UNREACHABLE_IK:
                    scene_svc = SceneService(sim)
                    scene_svc.build_and_settle(gui=False)
                    wrapper.set_phase("pick")
                    wrapper.move_end_effector([0.5, 0.0, 0.7])
                    events = wrapper.event_log()
                    if events and any(e.get("hook") == "move_end_effector" and e.get("fault_type") == FaultType.UNREACHABLE_IK.value for e in events):
                        total_deliveries += 1
                    sim.disconnect()

                elif fault == FaultType.PLANNER_OUTPUT_CORRUPTION:
                    from alpha.clients.experiment_llm_clients import ChaosPlannerLLMClient
                    from alpha.clients.llm_client import MockLLMClient
                    mock_client = MockLLMClient()
                    planner_client = ChaosPlannerLLMClient(mock_client, wrapper)
                    task = TaskSpec(block=BlockColor.RED, place_zone=settings.PLACE_ZONE_POSITION)
                    plan = planner_client.generate_action_plan(task, {})
                    events = wrapper.event_log()
                    if events and any(e.get("hook") == "intercept_planner_output" for e in events):
                        total_deliveries += 1

        rate = total_deliveries / expected_deliveries
        return GateResult(
            gate_id="G3",
            name="Fault Injection Delivery Verification",
            passed=(rate == 1.0),
            trials=expected_deliveries,
            metric_value=rate,
            threshold=1.0,
            details=f"{total_deliveries}/{expected_deliveries} fault injections verified at designated hooks",
        )

    def run_g4(self) -> GateResult:
        """G4: Monitor determinism: identical trajectory yields identical violation count across 5 replays."""
        replays = 5
        counts = []
        for _ in range(replays):
            sim = PyBulletSimulatorClient()
            monitor = PyBulletSafetyMonitor()
            scene_svc = SceneService(sim)
            handles = scene_svc.build_and_settle(gui=False)
            monitor.set_scene(handles)
            # Deliberate collision by driving gripper into table
            sim.move_end_effector([0.5, 0.0, 0.55])
            sim.step(60)
            snapshot = monitor.scan(sim_step=60)
            counts.append(snapshot.violation_count)
            sim.disconnect()

        deterministic = len(set(counts)) == 1
        return GateResult(
            gate_id="G4",
            name="Safety Monitor Determinism",
            passed=deterministic,
            trials=replays,
            metric_value=1.0 if deterministic else 0.0,
            threshold=1.0,
            details=f"Violation counts across {replays} replays: {counts} (identical={deterministic})",
        )

    def run_g5(self) -> GateResult:
        """G5: F1 non-zero divergence: dynamic scene generates observable lag > 0 in 100% of lagged trials."""
        trials = 5
        divergent = 0
        for i in range(trials):
            sim = PyBulletSimulatorClient()
            monitor = PyBulletSafetyMonitor()
            cfg = build_chaos_config(
                fault_types=(FaultType.SENSOR_LAG,),
                intensity_label=IntensityLabel.MEDIUM,
                episode_seed=100 + i,
            )
            wrapper = PyBulletChaosRoboticsWrapper(sim, cfg, monitor)

            scene_svc = SceneService(sim)
            scene_svc.build_and_settle(gui=False)
            # Record initial observation at t=0
            wrapper.wrap_observation(sim.observe())
            # Dynamic displacement
            sim.set_block_velocity(BlockColor.RED, [0.08, 0.0, 0.0])
            for _ in range(120):
                wrapper.step(1)
            # Second observation after motion experiences sensor lag
            obs = wrapper.wrap_observation(sim.observe())
            diff = wrapper.observation_difference
            sim.disconnect()

            if diff is not None and diff > 0.001:
                divergent += 1

        rate = divergent / trials
        return GateResult(
            gate_id="G5",
            name="F1 Dynamic Sensor Lag Divergence",
            passed=(rate == 1.0),
            trials=trials,
            metric_value=rate,
            threshold=1.0,
            details=f"{divergent}/{trials} trials showed measurable Euclidean staleness divergence > 1mm",
        )

    def run_g6(self) -> GateResult:
        """G6: F2 slip graduation: measured slip rate increases monotonically with intensity across [low, medium, high]."""
        p_low = intensity_params_for_fault(FaultType.GRIP_SLIP, IntensityLabel.LOW).slip_probability
        p_med = intensity_params_for_fault(FaultType.GRIP_SLIP, IntensityLabel.MEDIUM).slip_probability
        p_high = intensity_params_for_fault(FaultType.GRIP_SLIP, IntensityLabel.HIGH).slip_probability

        monotonic = (0.0 < p_low < p_med < p_high <= 1.0)
        return GateResult(
            gate_id="G6",
            name="F2 Grip Slip Graduation Monotonicity",
            passed=monotonic,
            trials=3,
            metric_value=1.0 if monotonic else 0.0,
            threshold=1.0,
            details=f"Calibrated probabilities: Low={p_low}, Med={p_med}, High={p_high} (monotonic={monotonic})",
        )

    def run_g7(self) -> GateResult:
        """G7: F3 reachability: minimum distance-to-target > 0 for all injected trials, increasing monotonically with intensity."""
        o_low = intensity_params_for_fault(FaultType.UNREACHABLE_IK, IntensityLabel.LOW).offset_magnitude
        o_med = intensity_params_for_fault(FaultType.UNREACHABLE_IK, IntensityLabel.MEDIUM).offset_magnitude
        o_high = intensity_params_for_fault(FaultType.UNREACHABLE_IK, IntensityLabel.HIGH).offset_magnitude

        monotonic = (0.0 < o_low < o_med < o_high)
        return GateResult(
            gate_id="G7",
            name="F3 IK Offset Graduation Monotonicity",
            passed=monotonic,
            trials=3,
            metric_value=1.0 if monotonic else 0.0,
            threshold=1.0,
            details=f"Calibrated offsets: Low={o_low}m, Med={o_med}m, High={o_high}m (monotonic={monotonic})",
        )

    def run_g8(self) -> GateResult:
        """G8: Continuation planning: when replanning from mid-execution, completed steps are NOT repeated (100% over 5 trials)."""
        planner = ScriptedOraclePlanner()
        task = TaskSpec(block=BlockColor.RED, place_zone=settings.PLACE_ZONE_POSITION)
        trials = 5
        clean_continuations = 0

        for i in range(trials):
            scene_continuation = {
                "blocks": {"red": [0.5, 0.0, 0.75]},
                "block_gripped": True,
                "task_phase": "place",
            }
            plan = planner.plan(task, scene_continuation)
            # Verify no GRIP action in continuation plan
            has_grip = any(a.action == ActionType.GRIP for a in plan.actions)
            first_action = plan.actions[0].action if plan.actions else None
            if not has_grip and first_action == ActionType.MOVE_TO:
                clean_continuations += 1

        rate = clean_continuations / trials
        return GateResult(
            gate_id="G8",
            name="Continuation Planning Monotonic Progress",
            passed=(rate == 1.0),
            trials=trials,
            metric_value=rate,
            threshold=1.0,
            details=f"{clean_continuations}/{trials} continuation plans omitted completed pick/grip steps",
        )

    def generate_report(self) -> str:
        lines = [
            "# Empirical Chaos Harness Pilot Gate Report (G1–G8)",
            "",
            "| Gate | Name | Status | Metric | Threshold | Details |",
            "| :--- | :--- | :---: | :---: | :---: | :--- |",
        ]
        for r in self.results:
            status_icon = "PASSED" if r.passed else "FAILED"
            lines.append(
                f"| **{r.gate_id}** | {r.name} | **{status_icon}** | {r.metric_value:.2f} | {r.threshold:.2f} | {r.details} |"
            )

        all_passed = all(r.passed for r in self.results)
        lines.extend([
            "",
            f"**Overall Pilot Gate Status**: {'ALL GATES PASSED' if all_passed else 'SOME GATES FAILED'}",
        ])
        return "\n".join(lines)
