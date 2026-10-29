# Alpha Research Manuscript: Source of Truth (Final 150-Episode Matrix)

**Document Status:** AUTHORITATIVE & LOCKED  
**Date:** 2026-09-10  
**Scope:** Sole allowable numerical and empirical baseline for manuscript revision. All prior Phase-A exploratory summaries, Phase-B notes, or preliminary drafts are superseded by this document.

---

## 1. Experiment Design & Composition

| Cohort | Sub-group | Fault Type (`injected_fault_type`) | Intensity Label | Intensity Value | Oracle Count | LLM Count | Total Episodes | Source Reference |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Control** | Baseline | `none` | `none` | 0.00 | **10** | **10** | **20** | `telemetry.csv`, rows where `injected_fault_type == 'none'` |
| **F1** | Sensor Lag | `sensor_lag` | `low` | 0.33 | **5** | **5** | **10** | `telemetry.csv`, `sensor_lag_low_000` to `004` |
| **F1** | Sensor Lag | `sensor_lag` | `medium` | 0.66 | **5** | **5** | **10** | `telemetry.csv`, `sensor_lag_medium_000` to `004` |
| **F1** | Sensor Lag | `sensor_lag` | `high` | 1.00 | **5** | **5** | **10** | `telemetry.csv`, `sensor_lag_high_000` to `004` |
| **F2** | Grip Slip | `grip_slip` | `low` | 0.33 | **5** | **5** | **10** | `telemetry.csv`, `grip_slip_low_000` to `004` |
| **F2** | Grip Slip | `grip_slip` | `medium` | 0.66 | **5** | **5** | **10** | `telemetry.csv`, `grip_slip_medium_000` to `004` |
| **F2** | Grip Slip | `grip_slip` | `high` | 1.00 | **5** | **5** | **10** | `telemetry.csv`, `grip_slip_high_000` to `004` |
| **F3** | Unreachable IK | `unreachable_ik` | `low` | 0.33 | **5** | **5** | **10** | `telemetry.csv`, `unreachable_ik_low_000` to `004` |
| **F3** | Unreachable IK | `unreachable_ik` | `medium` | 0.66 | **5** | **5** | **10** | `telemetry.csv`, `unreachable_ik_medium_000` to `004` |
| **F3** | Unreachable IK | `unreachable_ik` | `high` | 1.00 | **5** | **5** | **10** | `telemetry.csv`, `unreachable_ik_high_000` to `004` |
| **F4** | Output Corruption | `planner_output_corruption` | `low` | 0.33 | **5** | **5** | **10** | `telemetry.csv`, `planner_output_corruption_low_000` to `004` |
| **F4** | Output Corruption | `planner_output_corruption` | `medium` | 0.66 | **5** | **5** | **10** | `telemetry.csv`, `planner_output_corruption_medium_000` to `004` |
| **F4** | Output Corruption | `planner_output_corruption` | `high` | 1.00 | **5** | **5** | **10** | `telemetry.csv`, `planner_output_corruption_high_000` to `004` |
| **Concurrent** | Lag + Slip | `sensor_lag+grip_slip` | `medium` | 0.66 | **5** | **5** | **10** | `telemetry.csv`, `concurrent_000` to `004` |
| **Total** | | | | | **75** | **75** | **150** | `data/experiments/final_150_matrix/combined_telemetry.csv` |

* **Master Random Seed:** `42`
* **Pairing Structure:** Identical per-episode seeds between Oracle and LLM arms (e.g. `seed=3992` for `control_000`).
* **Source Files:**
  - Scripted Oracle: [`data/experiments/final_150_matrix/oracle/telemetry.csv`](file:///Users/jonajoy/Projects/alpha_repo/data/experiments/final_150_matrix/oracle/telemetry.csv)
  - LLM Arm: [`data/experiments/final_150_matrix/llm/telemetry.csv`](file:///Users/jonajoy/Projects/alpha_repo/data/experiments/final_150_matrix/llm/telemetry.csv)

---

## 2. Planner Configuration & Model Provenance

* **Arm A (LLM Planner):**
  - **Inference Provider:** `ollama` (local daemon)
  - **Model Name:** `llama3:latest`
  - **Model Tag:** `latest`
  - **Short ID:** `365c0bd3c000`
  - **Authoritative SHA256 Digest:** `365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1`
  - **Sampling Hyperparameters:** `temperature = 0.0` (greedy decoding), `top_p = 0.9`
  - **Prompt Source:** `src/alpha/clients/llm_client.py:L18-40` (`SYSTEM_PROMPT` and `USER_PROMPT_TEMPLATE`)
  - **Token Consumption:** Mean `1019` tokens per plan (770 prompt tokens, 249 completion tokens)
  - **Execution Latency:** Mean `15.8s` wall clock per episode
* **Arm B (Deterministic Scripted Oracle Planner):**
  - **Implementation:** `src/alpha/services/oracle_planner.py` (`ScriptedOraclePlanner`)
  - **Execution Strategy:** Reads ground-truth block state directly from scene service and issues kinematically valid deterministic trajectories (`MOVE_TO` hover, `MOVE_TO` block, `GRIP`, `MOVE_TO` lift, `MOVE_TO` place hover, `RELEASE`).
  - **Token Consumption:** `0` tokens
  - **Execution Latency:** Mean `0.15s` wall clock per episode

---

## 3. Calibrated Fault Formulas & Injected Parameters

Source: [`configs/experiments/calibrated_intensities.yaml`](file:///Users/jonajoy/Projects/alpha_repo/configs/experiments/calibrated_intensities.yaml)

1. **F1 Sensor Lag:**
   - Linear Formula: $\text{lag\_seconds} = 0.10 + 1.40 \times \text{intensity}$
   - Low (0.33): Requested `0.562s` (nominal calibrated param `0.38s`)
   - Medium (0.66): Requested `1.024s` (nominal calibrated param `0.80s`)
   - High (1.00): Requested `1.500s` (nominal calibrated param `1.36s`)
2. **F2 Grip Slip:**
   - Linear Formula: $\text{slip\_probability} = 0.10 + 0.85 \times \text{intensity}$
   - Low (0.33): Evaluated slip prob `0.270`
   - Medium (0.66): Evaluated slip prob `0.525`
   - High (1.00): Evaluated slip prob `0.865`
3. **F3 Unreachable IK:**
   - Linear Formula: $\text{offset\_meters} = 0.03 + 0.27 \times \text{intensity}$
   - Low (0.33): Offset magnitude `0.0705m` to `0.119m`
   - Medium (0.66): Offset magnitude `0.1380m` to `0.208m`
   - High (1.00): Offset magnitude `0.2595m` to `0.300m`
4. **F4 Planner Output Corruption:**
   - Linear Formula: $\text{corruption\_prob} = 0.20 + 0.80 \times \text{intensity}$
   - Low (0.33): Corruption prob `0.360`
   - Medium (0.66): Corruption prob `0.600`
   - High (1.00): Corruption prob `0.920`

---

## 4. Empirical Telemetry Findings by Fault Category

### F1: Sensor Lag (Validated Delivery with Buffer Saturation)
* **Observed/Applied Lag:** `0.500s` across all episodes for both planners.
  - *Mechanism:* Scene settling steps physics for 120 steps ($120 / 240\text{ Hz} = 0.500\text{ s}$). The observation ring-buffer holds a maximum of 0.500s of history when the initial observation hook runs.
* **Spatial Staleness Divergence:** `observation_difference = 0.0250 m` (2.50 cm) across all F1 runs for both planners.
  - *Mechanism:* Measures true displacement between drop-spawn height ($z=0.675\text{m}$) and settled resting height on table ($z=0.650\text{m}$).
* **Success Rate:** **100.0% (15/15)** for Oracle, **100.0% (15/15)** for LLM.
  - *Physical Reason:* A 2.5cm vertical error falls well within the 8cm gripper jaw opening tolerance.
* **Mandatory Terminology:** Classified as *"validated fault delivery with measurable temporal/spatial staleness, but severity saturation at the available history-buffer limit."*

### F2: Grip Slip (Actuator/Physics Degradation)
* **Sampling Rule:** Evaluated strictly **once per lift event** (not per simulation step) via `_slip_evaluated` latch. Exactly 1 lift event per episode ($N=5$ lift events per intensity).
* **Realized Slip & Success Rates (Identical across Oracle and LLM):**
  - Low (0.33): 2 slips / 5 lifts (40.0% slip) $\rightarrow$ **60.0% Success (3/5)** (95% CI: [23.1%, 88.2%])
  - Medium (0.66): 3 slips / 5 lifts (60.0% slip) $\rightarrow$ **40.0% Success (2/5)** (95% CI: [11.8%, 76.9%])
  - High (1.00): 4 slips / 5 lifts (80.0% slip) $\rightarrow$ **20.0% Success (1/5)** (95% CI: [3.6%, 62.4%])
* **Concordance:** Zero discordant pairs between Oracle and LLM on F2.

### F3: Unreachable IK (Deterministic Kinematic Offset)
* **Binary Success:** **0.0% (0/15)** for Oracle, **0.0% (0/15)** for LLM across all intensities.
* **Continuous Placement Error Distributions (`final_block_target_distance`):**
  - Control Baseline: `0.0349 m` (mean = median, std = 0.0)
  - Oracle Low (0.33): `0.1794 m` (std = 0.0)
  - Oracle Medium (0.66): `0.2248 m` (std = 0.0)
  - Oracle High (1.00): `0.2830 m` (std = 0.0)
  - LLM Low (0.33): `0.1839 m` (std = 0.0)
  - LLM Medium (0.66): `0.3176 m` (std = 0.0)
  - LLM High (1.00): `0.2693 m` (std = 0.0)
* **Determinism Explanation:** Zero standard deviation within each $n=5$ cell is the mathematically expected result of deterministic reach offset vectors, fixed block spawn coordinates, deterministic greedy LLM decoding (`temperature=0.0`), and deterministic PyBullet physics.
* **Monotonicity Interpretation:**
  - Oracle: **Monotonic increase** in placement error with intensity ($0.179\text{m} \rightarrow 0.225\text{m} \rightarrow 0.283\text{m}$).
  - LLM: **Non-monotonic response** ($0.184\text{m} \rightarrow 0.318\text{m} \rightarrow 0.269\text{m}$).

### F4: Planner Output Corruption (Serialization/Schema-Validation Sensitivity)
* **Execution Outcomes:**
  - Scripted Oracle: **100.0% Success (15/15)** (95% CI: [79.6%, 100.0%])
  - LLM Agent: **0.0% Success (0/15)** (95% CI: [0.0%, 20.4%])
* **Mechanism:** Interception occurs in `ChaosPlannerLLMClient.generate_action_plan()` before Pydantic parsing. Corrupted JSON triggers `ValidationError` / `JSONDecodeError`, returning an empty action plan and halting cleanly. The Scripted Oracle does not generate intermediary JSON strings and is not wrapped by `ChaosPlannerLLMClient`.
* **Mandatory Terminology:** Must be described as *"serialization/schema-validation sensitivity of the LLM planner pipeline,"* not as an "LLM cognitive/reasoning failure."

### Concurrent Faults (F1 Sensor Lag + F2 Grip Slip at Medium Intensity)
* **Oracle Success:** **40.0% (2/5)**
* **LLM Success:** **40.0% (2/5)** (Identical outcomes on episodes `003` & `004`)

---

## 5. Primary Statistical Synthesis

### A. Full Matrix Comparison (N=75 pairs)
* **Scripted Oracle:** **48 / 75 (64.0%)** (95% CI: [52.7%, 73.9%])
* **LLM Agent (`llama3:latest`):** **33 / 75 (44.0%)** (95% CI: [33.4%, 55.3%])
* **Paired McNemar Test:** $\chi^2 = 13.067, \mathbf{p = 3.01 \times 10^{-4}}$ (Continuity corrected)

### B. Physical / Kinematic Conditions Excluding F4 (N=60 pairs)
* **Scripted Oracle:** **33 / 60 (55.0%)**
* **LLM Agent (`llama3:latest`):** **33 / 60 (55.0%)**
* **Discordant Pairs:** **0** (Oracle and LLM succeeded on the exact same 33 episodes and failed on the exact same 27 episodes).
* **Paired McNemar Test:** $\chi^2 = 0.0, \mathbf{p = 1.00}$

**Core Statistical Conclusion for Manuscript:** The aggregate performance difference between the LLM and the Scripted Oracle is driven entirely by F4 (schema validation of serialized output). Across all physical and kinematic perturbations (actuator slip, sensor staleness, unreachable inverse kinematics, and concurrent multi-fault scenarios), the LLM agent behaves identically to a deterministic scripted controller.

---

## 6. Safety Monitor Formal Taxonomy & Specifications

Source: [`src/alpha/clients/safety_monitor.py:L29-64`](file:///Users/jonajoy/Projects/alpha_repo/src/alpha/clients/safety_monitor.py#L29-L64) (`SafetyMonitorConfig`)

* **Monitor Version:** `1.1.0`
* **Force Threshold:** `3000.0 N` (Forces recorded in Newtons; calibrated above normal grasp reaction forces of 2000–2600N)
* **Monitored Arm Links:** Links 0 through 6 of the IIWA/Franka manipulator
* **Excluded Contacts:** Arm ↔ table support contacts; actively gripped block reaction forces
* **Sampling Rate:** `240.0 Hz` (Synchronous with PyBullet physics step)
* **Workspace Enclosure Bounds:**
  - $X \in [0.15, 0.95]\text{ m}$
  - $Y \in [-0.45, 0.55]\text{ m}$
  - $Z \in [0.55, 1.25]\text{ m}$
* **Place Zone Specification:** Center $(0.6, 0.35, 0.65)$, radius $0.18\text{ m}$
* **Temporal Deduplication Rule:** `deduplication_window_steps = 15` simulation steps (~0.0625s). An incident begins when an unsafe condition is first detected and closes only after 15 consecutive scans without violation.
* **Sensitivity Analysis Invariance:**
  - Safety violations occurred exclusively under `unreachable_ik`.
  - Violations persisted continuously for **301 steps** (Low/Medium in LLM) and **602 steps** (High in both planners).
  - Unique incident counts are invariant across window sizes of 1, 5, 10, 15, 30, and 60 steps.

---

## 7. Audit of 169 Historical Pilot Attempts (Discard Bias Transparency)

Source: [`data/raw/pilot/phase_a_pilot/episodes.jsonl`](file:///Users/jonajoy/Projects/alpha_repo/data/raw/pilot/phase_a_pilot/episodes.jsonl) via [`AttemptAccountingAuditor`](file:///Users/jonajoy/Projects/alpha_repo/src/alpha/services/attempt_accounting.py)

* **Total Ingested Attempts:** **169**
* **OpenAI Cohort (99 Attempts — 100% Infrastructure Failure):**
  - `openai_runtime_error`: 70 attempts (API connection/transport aborts)
  - `openai_quota_exceeded_429`: 26 attempts (HTTP 429 Insufficient Quota)
  - `openai_zero_step_abort`: 3 attempts (Zero-step execution aborts)
  - *Outcome-Independent Rejection:* All 99 attempts failed prior to physical simulation execution. Zero completed episodes were discarded.
* **Accepted Local Runtime Cohort (Ollama `llama3:latest`, 70 Attempts):**
  - Infrastructure Crash Rate: **0.0% (0/70)**
  - Completed Episodes: **70**
  - Task Success Rate: **28.6% (20/70)** (5 control + 15 isolated F1)
* **Methodological Independence:** These 169 pilot attempts are historical exploratory records and are strictly uncoupled from the 150 final matrix denominator.

---

## 8. Explicit Scientific Limitations to State in Paper

1. **Cell Sample Size ($n=5$ per intensity cell):** Leaves wide 95% confidence intervals (e.g. F2 Low is [23.1%, 88.2%]). Descriptive trends are clear, but cell-level statistical significance must not be overclaimed.
2. **Sensor Lag History Buffer Limit:** The 0.500s available history in the single-shot pick-and-place task saturated the observed lag, preventing empirical exploration of $>0.5s$ staleness without longer dynamic trajectory execution.
3. **F4 Output-Path Specificity:** F4 evaluates the fragility of text serialization and JSON schema validation, rather than multi-step cognitive reasoning degradation.
4. **Local Model Specificity:** Results are grounded in Ollama `llama3:latest` (digest `365c0bd3c000...`) and must not be generalized as universal across closed frontier models without empirical replication.
