# Alpha: Systematic Fault Injection and Robustness Evaluation for LLM-Driven Embodied Manipulation

[![arXiv](https://img.shields.io/badge/arXiv-2610.30197-b31b1b.svg)](https://arxiv.org/abs/2610.30197)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests: 130 Passing](https://img.shields.io/badge/Tests-130%20Passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official code, experiment runners, telemetry datasets, and reproducibility pipeline for the preprint:  
**"Alpha: Systematic Fault Injection and Robustness Evaluation for LLM-Driven Embodied Manipulation"** ([arXiv:2610.30197](https://arxiv.org/abs/2610.30197)).

---

## Overview

Embodied artificial intelligence increasingly pairs probabilistic Large Language Model (LLM) reasoning with physical robotic execution stacks. However, standard benchmarks evaluate aggregate end-to-end task success in nominal, unperturbed environments, making it difficult to isolate whether failures originate from sensor lag, actuator dynamics, kinematic reach constraints, or prompt-to-JSON serialization errors.

**Alpha** is a systematic chaos-engineering and fault-injection test harness for embodied robotic manipulation in PyBullet simulation. It introduces:
1. **Calibrated Faults across Four Boundaries:** Perception (sensor lag), actuation (gripper slip), kinematics (unreachable IK targets), and planning (planner-output JSON corruption), plus concurrent fault conditions.
2. **Matched Evaluation Methodology:** Pairs an LLM planner (`llama3:latest` via Ollama) against a deterministic Scripted Oracle planner evaluated under identical task seeds, workspace geometries, contact dynamics, and safety criteria across a balanced 150-episode matrix (75 episodes per planner).
3. **Discard-Bias Transparency Audit:** Comprehensive accounting of all 169 historical pilot attempts to ensure zero post-hoc selective filtering.

![Architecture Diagram](figures/fig1_architecture.png)

---

## Key Experimental Findings

* **Equivalent Physical Robustness:** Excluding planner-output corruption, performance across all physical and kinematic conditions (F1 lag, F2 slip, F3 unreachable IK) is **strictly identical**: **55.0% (33/60)** for both LLM and Oracle planners, yielding zero discordant pairs (paired McNemar $p = 1.00$).
* **Isolated Serialization Vulnerability:** The overall performance gap across the full matrix (64.0% Oracle vs. 44.0% LLM, McNemar $p = 3.01 \times 10^{-4}$) is driven entirely by planner-output corruption (100% Oracle vs. 0% LLM). This proves the primary bottleneck lies in prompt-to-JSON serialization and schema validation, not intrinsic reasoning deficits.
* **Empirical Monotonicity:** Task success monotonically degrades with calibrated fault intensity across grip slip ($p_{\text{slip}} \in [0.30, 0.70]$) and unreachable kinematic targets ($\Delta z \in [0.15, 0.35]\,\text{m}$).

---

## Fault Taxonomy (The 4 Boundaries)

| Fault Class | Boundary | Injection Hook | Calibrated Intensities | Target Failure Signature |
| :--- | :--- | :--- | :--- | :--- |
| **F1: Sensor Lag** | Perception | `wrap_observation()` | $\Delta t \in \{0.50, 0.75, 1.00\}\,\text{s}$ | Stale divergence, replan saturation |
| **F2: Grip Slip** | Actuation | `step_simulation()` | $p \in \{0.30, 0.50, 0.70\}$ | Mid-transfer object drop |
| **F3: Unreachable IK**| Kinematics | `move_end_effector()` | $\Delta z \in \{0.15, 0.25, 0.35\}\,\text{m}$ | Joint-limit violation, safety stop |
| **F4: Output Corrupt**| Planning | `intercept_planner_output()` | $p \in \{0.20, 0.50, 0.80\}$ | Pydantic schema validation rejection |
| **Concurrent** | Multi-Boundary| Combined hooks | e.g., F1 ($0.50\,\text{s}$) + F2 ($0.30$) | Dual-fault interaction signatures |

---

## Repository Structure

```
├── artifacts/                  # Statistical summaries, accounting reports, and figure dumps
│   ├── accounting_report.md    # Complete 169-attempt pilot audit breakdown
│   ├── analysis_summary.json   # Machine-readable McNemar and degradation statistics
│   └── comparison_table.md     # Side-by-side Oracle vs. LLM metrics table
├── configs/                    # Simulation and experiment configuration files
│   └── experiments/            # Calibrated intensity parameters and pilot YAMLs
├── data/
│   ├── experiments/            # Full 150-episode raw and processed telemetry dataset
│   │   └── final_150_matrix/   # Combined JSONL episodes, CSV traces, and logs
│   ├── processed/              # Spot-check and validation processed runs
│   └── raw/                    # Raw JSONL episode telemetry
├── figures/                    # High-resolution manuscript figures (PNG)
├── scripts/                    # CLI tools for running, calibrating, and analyzing
│   ├── calibrate_fault_intensities.py  # Empirically tunes fault intensity parameters
│   ├── run_experiment_matrix.py       # Executes the balanced multi-arm matrix
│   ├── analyze_experiments.py         # Computes McNemar tests, tables, and metrics
│   ├── generate_manuscript_figures.py # Regenerates all paper figures (Figs 1–7)
│   ├── run_pilot_gates.py             # Validates pre-flight qualification gates G1–G8
│   └── run_spot_check.py              # Single-episode debugging and visualization CLI
├── src/alpha/                  # Core package source
│   ├── clients/                # Simulation client, chaos wrapper, safety monitor, LLM
│   ├── core/                   # Domain entities and abstract interfaces
│   ├── models/                 # Pydantic configuration and state models
│   ├── schemas/                # Strict telemetry and action schemas
│   └── services/               # Matrix runners, Oracle planner, accounting service
└── tests/                      # 130 unit and integration tests (100% passing)
```

---

## Quickstart & Installation

### 1. Clone & Set Up Environment

Requires **Python 3.10+** (Python 3.11 recommended):

```bash
git clone https://github.com/jonajoy142/embodied-agent-chaos.git
cd embodied-agent-chaos

python3 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate

pip install --upgrade pip
pip install -e ".[dev]"
```

### 2. Verify Installation

Run the complete test suite (130 automated tests):

```bash
pytest
```

---

## Reproducing Paper Results

All findings, tables, and figures from the paper can be reproduced using the bundled scripts or the top-level `Makefile`.

### One-Command Pipeline

```bash
make all
```

This sequentially executes the calibration check, attempt accounting audit, unit tests, pilot qualification gates, and statistical analysis.

### Step-by-Step Reproduction

#### 1. Fault Intensity Calibration
Validates monotonicity and non-triviality across fault parameters:
```bash
python scripts/calibrate_fault_intensities.py
# or: make calibrate
```

#### 2. Pilot Gate Verification (G1–G8)
Validates safety monitoring, lag bounds, slip physics, IK clamps, and schema rejection:
```bash
python scripts/run_pilot_gates.py
# or: make gates
```

#### 3. Attempt Accounting Audit
Reproduces the complete 169-attempt historical audit:
```bash
python -m alpha.services.attempt_accounting
# or: make audit
```

#### 4. Run the Experiment Matrix
To run the full 150-episode matrix (or run sample episodes):
```bash
# Deterministic Scripted Oracle:
python scripts/run_experiment_matrix.py --agent scripted_oracle --episodes-per-variation 5

# LLM Planner (requires local Ollama with llama3):
ollama run llama3:latest
python scripts/run_experiment_matrix.py --agent ollama --episodes-per-variation 5
```

#### 5. Statistical Analysis & Paper Tables
Computes exact paired McNemar contingency tables, success percentages, and metrics:
```bash
python scripts/analyze_experiments.py
# or: make analyze
```

#### 6. Regenerate Manuscript Figures
Regenerates Figures 1 through 7 in `figures/`:
```bash
python scripts/generate_manuscript_figures.py
```

---

## Safety Monitoring Architecture

Alpha enforces active real-time safety bounds independent of planner output:
* **Workspace Enclosure:** Clamps gripper positions to safe tabletop bounds:
  $$\mathcal{W} = [0.15, 0.95] \times [-0.45, 0.55] \times [0.55, 1.25]\,\text{m}$$
* **Kinematic Limits:** Detects joint-limit saturation and unreachable IK targets.
* **Near-Miss & Collision Detection:** Triggers safety halts before physical collisions exceed safety thresholds ($d < 0.03\,\text{m}$, force thresholds).
* **De-duplicated Telemetry:** Automatically debounces repeated safety events across simulation steps to prevent artificial metric inflation.

---

## Citation

If you use Alpha in your research or find this benchmark helpful, please cite our preprint:

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
