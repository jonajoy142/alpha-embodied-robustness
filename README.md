# Alpha: A Reusable Fault-Injection Framework for LLM-Driven Manipulation

[![arXiv](https://img.shields.io/badge/arXiv-2610.30197-b31b1b.svg)](https://arxiv.org/abs/2610.30197)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests: 138 Passing](https://img.shields.io/badge/Tests-138%20Passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Alpha** is an open, modular fault-injection and chaos-engineering test harness for embodied robotic agents. It systematically tests, benchmarks, and diagnoses failure modes in Large Language Model (LLM) planners and physical control stacks across four operational boundaries: **Perception**, **Actuation**, **Kinematics**, and **Planning**.

Read the foundational paper:  
**"Alpha: Systematic Fault Injection and Robustness Evaluation for LLM-Driven Embodied Manipulation"** ([arXiv:2610.30197](https://arxiv.org/abs/2610.30197)).

---

## 5-Minute Quickstart

### 1. Installation

Requires **Python 3.10+** (Python 3.11 recommended):

```bash
git clone https://github.com/jonajoy142/alpha-embodied-robustness.git
cd alpha-embodied-robustness

python3 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate

pip install --upgrade pip
pip install -e ".[dev]"
```

Verify the installation with the automated test suite (138 tests):
```bash
pytest
```

### 2. Run Experiments via CLI

Execute a single episode under sensor lag:
```bash
alpha run --agent scripted_oracle --fault sensor_lag
```

Run with an LLM planner (requires local [Ollama](https://ollama.ai) with `llama3`):
```bash
alpha run --agent ollama --fault grip_slip
```

Run a constrained multi-block task with obstacle clearance:
```bash
alpha run --agent scripted_oracle --task-family constrained_multi_block
```

Run with validation-feedback self-correction mitigation:
```bash
alpha run --agent scripted_oracle --fault planner_output_corruption --mitigation retry_with_feedback
```

### 3. Generate Evaluation Report

Generate a standalone HTML report with per-layer failure attribution and TOST equivalence analysis:
```bash
alpha report -o artifacts/experiment_report.html
```

---

## Architecture & Core Pipeline

Alpha enforces strict decoupling between high-level reasoning, serialization/validation, chaos injection middleware, and physics execution.

```text
+------------------------------------------------------------------------+
|                            PLANNER ADAPTER                             |
|  - LLMPlannerAdapter (Ollama / OpenAI / Custom)                        |
|  - OraclePlannerAdapter (Deterministic Scripted Baseline)              |
|  - Mitigation: Retry with Error Feedback | Structured Decoding         |
+------------------------------------------------------------------------+
                                   |
                         [Raw JSON ActionPlan]
                                   v
+------------------------------------------------------------------------+
|                     CHAOS ROBOTICS MIDDLEWARE                          |
|  - F1 (Perception):   wrap_observation()         -> Injects Lag        |
|  - F2 (Actuation):    step_simulation()          -> Injects Slip       |
|  - F3 (Kinematics):   move_end_effector()        -> Injects Target IK  |
|  - F4 (Planning):     intercept_planner_output() -> Corrupts Schema    |
+------------------------------------------------------------------------+
                                   |
                        [Validated ActionPlan]
                                   v
+------------------------------------------------------------------------+
|                           SIMULATOR ADAPTER                            |
|  - PyBulletSimulatorAdapter (KUKA LBR iiwa 7-DOF)                      |
|  - Domain Randomization (Spawn jitter ±2cm, friction [0.3, 1.2])       |
|  - Extensible to Isaac Sim / MuJoCo backends                           |
+------------------------------------------------------------------------+
                                   |
                                   v
+------------------------------------------------------------------------+
|                     SAFETY MONITOR & TELEMETRY                         |
|  - Real-time workspace boundary enforcement                            |
|  - Collision & near-miss detection (force thresholds in Newtons)       |
|  - Pre-registered TOST (Two One-Sided Tests) Equivalence Service       |
+------------------------------------------------------------------------+
```

---

## Fault Taxonomy (The 4 Boundaries)

| Fault Class | Operational Boundary | Injection Hook | Calibrated Intensities | Target Failure Signature |
| :--- | :--- | :--- | :--- | :--- |
| **F1: Sensor Lag** | Perception | `wrap_observation()` | $\Delta t \in \{0.50, 0.75, 1.00\}\,\text{s}$ | Stale divergence, replanning loops |
| **F2: Grip Slip** | Actuation | `step_simulation()` | $p_{\text{slip}} \in \{0.30, 0.50, 0.70\}$ | Mid-transfer object drop |
| **F3: Unreachable IK** | Kinematics | `move_end_effector()` | $\Delta x \in \{0.05, 0.12, 0.25\}\,\text{m}$ | Joint-limit saturation, kinematic stop |
| **F4: Output Corruption**| Planning / Interface | `intercept_planner_output()` | $p_{\text{corrupt}} \in \{0.30, 0.50, 0.80\}$ | Pydantic schema validation rejection |
| **Concurrent** | Multi-Boundary | Combined hooks | e.g. F1 ($0.50\,\text{s}$) + F2 ($0.30$) | Compound failure modes |

---

## Extensibility Guide

Alpha is designed as a modular, extensible plugin framework. You can plug in custom planners, simulators, and fault classes in just a few lines of code.

### 1. Adding a Custom Planner
Subclass `PlannerAdapter` from `alpha.plugins`:

```python
from typing import Any
from alpha.core.entities import TaskSpec
from alpha.plugins import PlannerAdapter

class MyCustomPlanner(PlannerAdapter):
    def __init__(self, **kwargs):
        super().__init__(name="my_custom_planner", **kwargs)

    def generate_raw_plan_text(
        self,
        task: TaskSpec,
        scene_info: dict[str, Any] | None = None,
        feedback: str | None = None,
    ) -> str:
        # If feedback is provided, adapt prompt to correct previous schema failure
        prompt = f"Plan pick-and-place for {task.block.value}."
        if feedback:
            prompt += f"\nPrevious error: {feedback}"
        return '{"agent_name": "custom", "actions": [{"action": "MOVE_TO", "target": [0.5, 0.0, 0.7]}]}'
```

### 2. Adding a Custom Simulator Backend
Subclass `SimulatorAdapter` from `alpha.plugins`:

```python
from alpha.plugins import SimulatorAdapter, SceneRandomizationConfig

class IsaacSimAdapter(SimulatorAdapter):
    def configure_scene_randomization(self, config: SceneRandomizationConfig) -> None:
        self._config = config

    def connect(self, gui: bool = False) -> None:
        # Initialize custom physics engine
        pass

    def get_contact_forces(self) -> list[float]:
        # Return contact normal forces in Newtons
        return [0.0]
```

### 3. Adding a Custom Fault Plugin
Subclass `FaultPlugin` and register with `FaultRegistry`:

```python
from typing import Any
from alpha.core.entities import FaultType
from alpha.plugins import FaultPlugin, FaultRegistry

class TorqueNoiseFault(FaultPlugin):
    @property
    def fault_type(self) -> FaultType:
        return FaultType.NONE  # Or custom enum

    @property
    def boundary(self) -> str:
        return "Actuation"

    def apply(self, target: Any, intensity: Any, rng: Any) -> Any:
        noise = rng.gauss(0, intensity.magnitude)
        return [t + noise for t in target]

FaultRegistry.register("torque_noise", TorqueNoiseFault)
```

---

## Mitigation Strategies

Alpha includes built-in mitigation arms to benchmark recovery techniques against unmitigated baselines:

1. **`none` (Unmitigated Baseline):** Raw planner output is validated. If schema validation fails (e.g. from F4 corruption), the episode terminates as a validation failure ($0\%$ completion).
2. **`retry_with_feedback`:** When validation fails, the exact error (e.g. missing required field, JSON decode error) is formatted as feedback and passed back to the planner to re-generate the plan (up to $K=3$ attempts).
3. **`structured_decoding`:** Syntactic and structural healing is applied to repair unclosed braces, truncated JSON, or enforce schema conformity before validation.

---

## Reproducibility & Rigor

* **Matched Experimental Seeds:** Python, NumPy, and PyBullet physics are seeded deterministically per episode using SHA256 run-ID hashing.
* **Pre-registered TOST Equivalence:** Includes Two One-Sided Tests (TOST) with a pre-registered equivalence margin ($\pm 15\%$) to verify equivalence between deterministic controllers and LLM planners on physical faults.
* **Continuous Metrics:** Telemetry tracks continuous placement error (Euclidean distance to goal in meters), contact forces (Newtons), and safety violation durations.
* **Provenance Tracking:** Every telemetry record logs model name, model digest, git commit hash, and safety monitor version.

---

## Limitations

* **Simulation Only:** All evaluations are conducted in PyBullet physics simulation; transfer to physical hardware remains subject to real-world sim-to-real gaps.
* **Tested Models:** Benchmark baselines focus on open-weight Llama-3 (8B) via Ollama and deterministic Scripted Oracle controllers.
* **Task Geometries:** Evaluated on tabletop pick-and-place and 2-block obstacle clearance environments.

---

## Citation

If you use Alpha in your research or wish to cite the benchmark, please use the following BibTeX entry:

```bibtex
@article{jona2026alpha,
  title={Alpha: Systematic Fault Injection and Robustness Evaluation for LLM-Driven Embodied Manipulation},
  author={Jona},
  journal={arXiv preprint arXiv:2610.30197},
  year={2026},
  url={https://arxiv.org/abs/2610.30197}
}
```

---

## License

This project is licensed under the [MIT License](LICENSE).
