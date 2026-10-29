# Alpha Paper Research Source of Truth (HISTORICAL - SUPERSEDED)

> [!WARNING]
> **SUPERSEDED BY FINAL 150-EPISODE MATRIX EXPERIMENT**
> This document records historical preliminary data from early exploratory pilot phases (Phase-A pilot N=169, Phase-B validation N=21).
> For the revised manuscript, the authoritative, controlled experimental dataset is the 150-episode head-to-head matrix documented in [`artifacts/final_150_matrix/MANUSCRIPT_SOURCE_OF_TRUTH.md`](file:///Users/jonajoy/Projects/alpha_repo/artifacts/final_150_matrix/MANUSCRIPT_SOURCE_OF_TRUTH.md).

**Document Purpose:** This is a historical factual research document containing repository-grounded information from early pilot iterations.

**Critical Rules:**
- Never silently reconcile conflicting evidence
- For every result, classify as exactly one of: VALID SCIENTIFIC RESULT, ENGINEERING VALIDATION, INCONCLUSIVE, INVALID/ABORTED
- Do not modify source code, run experiments, change results, or delete data
- All numbers must be traceable to exact source files

**Validity Classification Legend:**
- **VALID SCIENTIFIC RESULT:** Reproducible, properly controlled, scientific finding
- **ENGINEERING VALIDATION:** Implementation correctness check, not a scientific result
- **INCONCLUSIVE:** Data insufficient to support or refute a hypothesis
- **INVALID/ABORTED RUN:** Failed experimental execution, not usable for research

==================================================
1. EXECUTIVE SUMMARY
==================================================

**Alpha** is a chaos engineering framework for evaluating robustness of LLM-driven embodied manipulation agents in simulation. The system implements four fault classes (sensor lag, grip slip, unreachable IK, planner output corruption) as middleware injectors at perception, actuation, kinematic, and planner layers.

**Current Research Status:** The framework exists and is instrumented, but experimental results are mixed. Phase-A pilot achieved 28.6% overall success rate (20/70 episodes) with Ollama llama3, but with significant deviations from the planned experiment matrix. Phase-B validation provided additional focused data on F1 sensor lag (8 episodes) and F3 unreachable IK (12 episodes). F1 sensor lag measurement was fixed for accuracy (requested ≈ observed), but task completion under F1 remains impossible due to replanning inefficiency. No formal full-matrix experiment with OpenAI gpt-4o (as planned) was successfully executed.

**Key Finding:** The Phase-A pilot succeeded with Ollama llama3 (not the planned OpenAI gpt-4o), achieving meaningful simulation execution and providing valid scientific data for F1 and F3, but with significant deviations from the planned experiment schedule.

==================================================
2. RESEARCH QUESTION
==================================================

**From protocol (`docs/EXPERIMENT_PROTOCOL.md`):**

**RQ1:** How does an LLM-driven embodied agent degrade under controlled failures at different layers?

**RQ2:** Do different fault classes produce distinguishable failure signatures?

**RQ3:** How does fault intensity affect success, execution time, post-fault completion interval, and safety?

**RQ4:** How does the agent behave under concurrent vs isolated faults?

**RQ5:** Can production-style reliability metrics usefully characterize embodied-agent robustness?

**Current Status:** Data insufficient to answer any RQ conclusively. Phase-A provides partial data but with agent/model deviation. Phase-B provides focused validation but insufficient sample size.

==================================================
3. SYSTEM OVERVIEW
==================================================

## Research Objective

To evaluate whether production-style fault injection and reliability metrics can be applied systematically to an LLM-driven embodied manipulation agent in simulation, and to characterize how controlled failures at different system layers affect task outcome, execution cost, post-fault completion interval (where valid), and validated safety-related events.

**Note:** The current agent is single-shot (one plan, open-loop execution) by default. Replanning infrastructure exists but is not yet effective for task completion.

## System Architecture

**Design Pattern:** Brain/Body orchestration layer

**Components:**
- **Brain:** `AgentBrain` → `LLMClient` (OpenAI or Ollama)
- **Body:** `ControlService` → `SimulatorClient` → PyBullet
- **Chaos Layer:** `ChaosRoboticsWrapper` middleware
- **Safety:** `PyBulletSafetyMonitor` validated taxonomy
- **Telemetry:** `ChaosTelemetryLogger` + `ExperimentDataRepository`

**Not Implemented:**
- LangGraph agent (uses Brain/Body `AgentService` only)
- Self-diagnosis/fault classification by agent
- Effective replanning for task completion (infrastructure exists but LLM does not utilize context)

## PyBullet Environment

**Source:** `src/alpha/clients/simulator_client.py` and `docs/EXPERIMENT_PROTOCOL.md`

**Configuration:**
- Engine: PyBullet (headless `DIRECT` mode for experiments)
- Gravity: `(0, 0, -9.8)` m/s²
- Fixed simulation timestep: `1/240` s (~4.17 ms) when determinism helper applied
- Scene settle steps after build: `120`
- Sim steps per `move_end_effector` call: `240`

**Robot Configuration:**
- Arm URDF: `kuka_iiwa/model.urdf` (PyBullet data)
- Arm base position: `(0.0, 0.0, 0.0)`
- Table URDF: `table/table.urdf`
- Table base position: `(0.6, 0.0, 0.0)`
- End-effector control: Inverse kinematics → joint position control
- IK max iterations: `200`
- Joint control force: `2000`

**Objects:**
- Block (red): `cube_small.urdf`, globalScaling `1.2`, spawn `(0.5, -0.15, 0.68)`
- Block (green): same, spawn `(0.5, 0.0, 0.68)`
- Block (blue): same, spawn `(0.5, 0.15, 0.68)`
- Place zone: coordinate `(0.6, 0.35, 0.65)`

**Pilot default task block:** `BlockColor.RED` (hardcoded in matrix runner)

## Task

**Type:** Pick-and-place

**Goal:** Move specified block to `place_zone`

**Default description:** `"pick block and move it to the place zone"`

**Success criterion:** Final block position within Euclidean distance `< 0.08` m of `place_zone`

**Success tolerance:** `settings.PLACE_SUCCESS_TOLERANCE = 0.08`

**Release height offset:** `0.06` m above place zone Z

## Telemetry

**Components:**
- `ChaosTelemetryLogger`: Episode-level telemetry recorder
- `ExperimentDataRepository`: Append-only JSONL raw log + CSV summaries
- `ExperimentTelemetryRecord`: Main telemetry schema

**Key Fields:**
- `experiment_id`, `episode_id`, `recorded_at`, `seed`
- `agent_name`, `model_identifier`, `block`
- `injected_fault_type`, `fault_intensity`, `fault_trigger`, `fault_occurred`
- `success`, `crashed`, `timed_out`, `failure_reason`
- `post_fault_completion_time_sim_steps`, `post_fault_completion_time_wall_seconds`
- `total_sim_steps`, `total_wall_seconds`
- `llm_total_tokens`, `llm_prompt_tokens`, `llm_completion_tokens`
- `replan_count`, `safety_violation_count`, `violent_collision_count`, `out_of_workspace_count`
- `unique_safety_incident_count`, `first_violation_step`, `total_violation_duration_steps`
- `observation_lag_requested`, `observation_lag_observed`

## Safety Monitor

**Implementation:** `PyBulletSafetyMonitor` with validated taxonomy

**Source:** `docs/SAFETY_TAXONOMY.md`

**Event Kinds:**
- Violent arm–block contact: Normal force ≥ threshold (default 50 N)
- Block out of workspace: Block center outside configured XYZ bounds
- Block dropped outside place zone: Block below table height and farther than place-zone radius from target

**Primary Metric:** Episode-level safety violation rate = proportion of episodes with `safety_violation_count >= 1`

**Secondary Metric:** Mean `safety_violation_count` per episode

**Deduplication:** Violent arm–block contacts deduplicated once per (kind, arm–block pair, simulation step)

**Configuration:** `src/alpha/config/settings.py`
- `CONTACT_FORCE_THRESHOLD` — violent contact cutoff (Newtons)
- `WORKSPACE_*_BOUNDS` — valid block region
- `PLACE_ZONE_RADIUS` — drop-zone tolerance

## Chaos Wrapper

**Implementation:** `ChaosRoboticsWrapper` — canonical fault injection middleware

**Source:** `docs/FAULT_INJECTION.md` and `src/alpha/clients/chaos_robotics_wrapper.py`

**Legacy Injector:** `ScriptedFaultInjector` — ControlService boundary, CLI/compatibility only (out of scope for formal study)

**Primary Fault Path:** `ChaosRoboticsWrapper` only for pilot and formal study

==================================================
4. REPOSITORY EVIDENCE INVENTORY
==================================================

## Documentation Files

| File Path | Purpose | Evidence Type | Contributes Numbers |
|-----------|---------|---------------|----------------------|
| `docs/EXPERIMENT_PROTOCOL.md` | Research protocol, RQs, hypotheses, metrics definitions | PRIMARY | Protocol specifications |
| `docs/FAULT_INJECTION.md` | Fault injection architecture and taxonomy | PRIMARY | Fault class definitions |
| `docs/SAFETY_TAXONOMY.md` | Safety event taxonomy and validation rules | PRIMARY | Safety metric definitions |
| `docs/architecture.md` | System architecture rationale | SECONDARY | Architecture description |
| `docs/RESEARCH_ENGINEERING_AUDIT.md` | Engineering audit status | SECONDARY | Implementation status |
| `docs/PILOT_VALIDATION_CHECKLIST.md` | Pilot validation gates | SECONDARY | Validation criteria |
| `README.md` | Project overview and recent F1 fix analysis | SECONDARY | F1 fix status |

## Configuration Files

| File Path | Purpose | Evidence Type | Contributes Numbers |
|-----------|---------|---------------|----------------------|
| `configs/experiments/pilot.yaml` | Phase-A pilot configuration (planned) | PRIMARY | Planned Phase-A schedule |
| `configs/experiments/phase_b_validation.yaml` | Phase-B validation configuration | PRIMARY | Phase-B schedule |

## Phase-A Raw Data

| File Path | Purpose | Evidence Type | Contributes Numbers |
|-----------|---------|---------------|----------------------|
| `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Phase-A raw episode data (169 records) | PRIMARY | Actual Phase-A results |

## Phase-A Processed Data

| File Path | Purpose | Evidence Type | Contributes Numbers |
|-----------|---------|---------------|----------------------|
| `data/processed/pilot/phase_a_pilot/episodes.csv` | Phase-A processed CSV (170 rows) | SECONDARY | Contains only OpenAI (failed) episodes |

## Phase-B Raw Data

| File Path | Purpose | Evidence Type | Contributes Numbers |
|-----------|---------|---------------|----------------------|
| `data/raw/phase_b/phase_b_validation/episodes.jsonl` | Phase-B validation raw data (24 records) | PRIMARY | Phase-B validation results |
| `data/raw/phase_b/phase_b_control_safety_verify/episodes.jsonl` | Control safety verification (1 record) | SECONDARY | Control verification data |
| `data/raw/phase_b/phase_b_f1_low_safety_verify/episodes.jsonl` | F1 low safety verification (1 record) | SECONDARY | F1 verification data |

## Phase-B Processed Data

| File Path | Purpose | Evidence Type | Contributes Numbers |
|-----------|---------|---------------|----------------------|
| `data/processed/phase_b/phase_b_validation/episodes.csv` | Phase-B validation processed CSV (25 rows) | PRIMARY | Phase-B validation results |
| `data/processed/phase_b/phase_b_control_safety_verify/episodes.csv` | Control safety verification CSV (1 row) | SECONDARY | Control verification data |
| `data/processed/phase_b/phase_b_f1_low_safety_verify/episodes.csv` | F1 low safety verification CSV (1 row) | SECONDARY | F1 verification data |

## Spot Check Data

| Directory | Purpose | Evidence Type | Contributes Numbers |
|-----------|---------|---------------|----------------------|
| `data/raw/spot_checks/pilot/` | 62 spot check directories | ENGINEERING VALIDATION | Engineering validation only |
| `data/processed/spot_checks/pilot/` | 62 spot check processed CSVs | ENGINEERING VALIDATION | Engineering validation only |

## Test Files

| File Path | Purpose | Evidence Type | Contributes Numbers |
|-----------|---------|---------------|----------------------|
| `tests/test_f1_repeated_observation.py` | F1 lag accuracy and replanning tests | ENGINEERING VALIDATION | Test pass/fail counts |
| Other test files | Component validation | ENGINEERING VALIDATION | Test pass/fail counts |

==================================================
5. DATA PROVENANCE
==================================================

## Critical Conflict Resolution

**Conflict:** The previous source-of-truth document claimed Phase-A was entirely invalid (all episodes crashed with RuntimeError). This was based on `data/processed/pilot/phase_a_pilot/episodes.csv` (170 rows showing total_sim_steps=0).

**Resolution:** The CSV file only contains OpenAI (failed) episodes. The actual Phase-A pilot ran with Ollama llama3 and generated valid data in `data/raw/pilot/phase_a_pilot/episodes.jsonl` (169 records). After filtering for Ollama and deduplicating by latest timestamp per episode_id, we obtain 70 valid episodes with meaningful execution (60 sim steps, LLM tokens, etc.).

**Authoritative Source:** `data/raw/pilot/phase_a_pilot/episodes.jsonl` (primary data)
**Deduplication Rule:** Use latest timestamp per episode_id

**Previous Document Error:** The CSV file `data/processed/pilot/phase_a_pilot/episodes.csv` was incorrectly treated as the authoritative Phase-A dataset when it only contained failed OpenAI episodes.

==================================================
6. FORMAL PHASE-A DATASET
==================================================

## Actual Valid Phase-A Dataset

**Source:** `data/raw/pilot/phase_a_pilot/episodes.jsonl`

**Selection Rule:** Filter for `agent_name == "ollama"`, use latest timestamp per episode_id

**Valid Episodes:** 70 unique episodes

**Agent:** Ollama llama3 (not the planned OpenAI gpt-4o)

**Block:** RED

**Master Seed:** 42

**Actual Condition Counts:**
- CONTROL: 5 episodes
- F1 sensor_lag (isolated): 15 episodes (5 low + 5 medium + 5 high)
- F2 grip_slip: 15 episodes (5 low + 5 medium + 5 high)
- F3 unreachable_ik: 15 episodes (5 low + 5 medium + 5 high)
- F4 planner_output_corruption: 15 episodes (5 low + 5 medium + 5 high)
- CONCURRENT (F1+F2): 5 episodes (separate from isolated F1)
- TOTAL: 70 episodes

**Deviation from Planned Schedule:**
- Agent/model deviation: Ollama llama3 instead of OpenAI gpt-4o
- Total matches planned 70 episodes (5 control + 15 each F1,F2,F3,F4 + 5 concurrent)

**Classification:** VALID SCIENTIFIC RESULT (with documented agent/model deviation)

==================================================
7. PHASE-A RESULTS
==================================================

## Condition-Level Results

**Source:** `data/raw/pilot/phase_a_pilot/episodes.jsonl` (Ollama episodes, latest timestamp per episode_id)

| Condition | Intensity | n | Success | Fault Observed | Crashed | Timed Out | Mean Safety Violations | Classification |
|----------|-----------|---|--------|----------------|---------|----------|----------------------|----------------|
| CONTROL | none | 5 | 5 (100%) | 0 | 0 | 0 | 0 | VALID SCIENTIFIC RESULT |
| F1 sensor_lag (isolated) | low (0.33) | 5 | 5 (100%) | 5 | 0 | 0 | 0 | VALID SCIENTIFIC RESULT |
| F1 sensor_lag (isolated) | medium (0.66) | 5 | 5 (100%) | 5 | 0 | 0 | 0 | VALID SCIENTIFIC RESULT |
| F1 sensor_lag (isolated) | high (1.0) | 5 | 5 (100%) | 5 | 0 | 0 | 0 | VALID SCIENTIFIC RESULT |
| F2 grip_slip | low (0.33) | 5 | 0 (0%) | 5 | 0 | 0 | 0 | VALID SCIENTIFIC RESULT |
| F2 grip_slip | medium (0.66) | 5 | 0 (0%) | 5 | 0 | 0 | 0 | VALID SCIENTIFIC RESULT |
| F2 grip_slip | high (1.0) | 5 | 0 (0%) | 5 | 0 | 0 | 0 | VALID SCIENTIFIC RESULT |
| F3 unreachable_ik | low (0.33) | 5 | 0 (0%) | 5 | 0 | 0 | 99 | VALID SCIENTIFIC RESULT |
| F3 unreachable_ik | medium (0.66) | 5 | 0 (0%) | 5 | 0 | 0 | 120 | VALID SCIENTIFIC RESULT |
| F3 unreachable_ik | high (1.0) | 5 | 0 (0%) | 5 | 0 | 0 | 120 | VALID SCIENTIFIC RESULT |
| F4 planner_output_corruption | low (0.33) | 5 | 0 (0%) | 5 | 0 | 0 | 0 | VALID SCIENTIFIC RESULT |
| F4 planner_output_corruption | medium (0.66) | 5 | 0 (0%) | 5 | 0 | 0 | 0 | VALID SCIENTIFIC RESULT |
| F4 planner_output_corruption | high (1.0) | 5 | 0 (0%) | 5 | 0 | 0 | 0 | VALID SCIENTIFIC RESULT |
| CONCURRENT (F1+F2) | medium (0.66) | 5 | 0 (0%) | 5 | 0 | 0 | 0 | VALID SCIENTIFIC RESULT |

**Overall Phase-A Results:**
- Total episodes: 70
- Total success: 20 (28.6%) [5 control + 15 isolated F1]
- Episodes with safety violations: 15 (21.4%) [15 F3]
- Sim steps: min=0, max=60, avg=47.1
- LLM tokens: min=1019, max=1019, avg=1019

**Note:** F4 episodes have 0 sim steps because planner output corruption causes schema validation failure before simulation execution (controlled failure as designed).

==================================================
8. ENGINEERING SPOT CHECKS
==================================================

## Classification

**Status:** ENGINEERING VALIDATION

**Purpose:** Implementation verification, fault injector testing, isolated diagnostics

**Action:** Do NOT count as formal experimental n

## Spot Check Summary

**Location:** `data/raw/spot_checks/pilot/` (62 directories)

**By Fault Type:**
- `spot_ollama_none`: 16 directories (control verification)
- `spot_ollama_sensor_lag`: 9 directories (F1 verification, including post-fix diagnostic)
- `spot_ollama_grip_slip`: 21 directories (F2 verification)
- `spot_ollama_unreachable_ik`: 6 directories (F3 verification)
- `spot_ollama_planner_output_corruption`: 10 directories (F4 verification)

## Representative Evidence

### Control Spot Checks

**Example:** `spot_ollama_none_0ad50ff8/episodes.csv`

**Evidence:**
- Provider: Ollama, llama3
- No fault
- Success: True
- Total sim steps: 1260
- Total wall seconds: ~12-21s
- LLM tokens: ~1019 total
- Safety violations: 0

**Purpose:** Verify Ollama agent can complete task without faults

### F1 Sensor Lag Spot Checks

**Pre-Fix:** `spot_ollama_sensor_lag_69a58b57/episodes.csv`
- Observed lag: 2.0s (pre-fix implementation)

**Post-Fix:** `spot_ollama_sensor_lag_7baf04b3/episodes.jsonl`
- Requested lag: 0.4975s
- Observed lag: 0.500s (post-fix implementation)
- Replan count: 5
- Actions executed: 24
- Task progressed: False (timed out before RELEASE)
- Safety violations: 0

**Purpose:** Verify F1 lag measurement accuracy and replanning behavior

### F2 Grip Slip Spot Checks

**Example:** `spot_ollama_grip_slip_0826e21f/episodes.csv`

**Evidence:**
- Provider: Ollama, llama3:latest
- Fault: grip_slip, intensity 0.33 (low)
- Trigger: event:lift
- Fault occurred: False (some episodes show False)
- Success: False
- Total sim steps: 60
- Safety violations: 120 (all out_of_workspace)

**Purpose:** Verify F2 grip slip injection and fault observability

### F3 Unreachable IK Spot Checks

**Example:** `spot_ollama_unreachable_ik_46a6a8e6/episodes.csv`

**Evidence:**
- Provider: Ollama, llama3
- Fault: unreachable_ik, intensity 0.33 (low)
- Fault occurred: True
- Success: False
- Total sim steps: 60
- Safety violations: 120 (60 violent collisions, 60 out of workspace)

**Purpose:** Verify F3 unreachable IK injection and safety monitoring

### F4 Planner Output Corruption Spot Checks

**Example:** `spot_ollama_planner_output_corruption_048d4a23/episodes.csv`

**Evidence:**
- Provider: Ollama, llama3
- Fault: planner_output_corruption, intensity 0.33 (low)
- Fault occurred: True
- Success: False
- Crashed: True
- Failure reason: exception:ValidationError (schema validation failure)
- Total sim steps: 0
- LLM tokens: 1019 (plan generated, then validation failed)

**Purpose:** Verify F4 planner output corruption and schema validation

==================================================
9. PHASE-B DATASET
==================================================

## Formal Schedule

**Source:** `configs/experiments/phase_b_validation.yaml`

**Scheduled:** 21 episodes

**Schedule Breakdown:**
- CONTROL: 3 episodes
- F1 sensor_lag: 9 episodes (3 low + 3 medium + 3 high)
- F3 unreachable_ik: 9 episodes (3 low + 3 medium + 3 high)
- F2 grip_slip: 0 episodes
- F4 planner_output_corruption: 0 episodes

**Total Scheduled:** 21 episodes

## Valid Episodes

**Source:** `data/processed/phase_b/phase_b_validation/episodes.csv`

**Total Rows:** 25 (includes retries/aborted attempts)

**Unique Scheduled Episode IDs:** 21

**Final Valid Attempts:**

**CONTROL (3 valid):**
- `phase_b_control_000`, `phase_b_control_001`, `phase_b_control_002`
- Provider: Ollama, llama3
- No fault
- Success: True, Crashed: False
- Total sim steps: 1260 each
- Safety violations: 1 each (violent_collision_count=1, out_of_workspace_count=0)
- **Classification:** VALID SCIENTIFIC RESULT (with safety monitor issue)

**F1 sensor_lag (8 valid):**
- `phase_b_sensor_lag_low_000` (2 attempts: first without replanning at 6614s, second valid)
- `phase_b_sensor_lag_low_001`, `phase_b_sensor_lag_low_002`
- `phase_b_sensor_lag_medium_000`, `phase_b_sensor_lag_medium_001`, `phase_b_sensor_lag_medium_002`
- `phase_b_sensor_lag_high_000`, `phase_b_sensor_lag_high_001`, `phase_b_sensor_lag_high_002`
- Provider: Ollama, llama3
- Fault occurred: True
- Success: False, Timed out: True
- Replan count: 3
- Observed lag: 2.0s (pre-fix implementation)
- **Classification:** VALID SCIENTIFIC RESULT (pre-fix lag measurement issue documented)

**F3 unreachable_ik (12 valid):**
- `phase_b_unreachable_ik_low_000`, `phase_b_unreachable_ik_low_001`, `phase_b_unreachable_ik_low_002`
- `phase_b_unreachable_ik_medium_000`, `phase_b_unreachable_ik_medium_001`, `phase_b_unreachable_ik_medium_002` (includes 2 failed attempts)
- `phase_b_unreachable_ik_high_000`, `phase_b_unreachable_ik_high_001`, `phase_b_unreachable_ik_high_002`
- Provider: Ollama, llama3
- Fault occurred: True
- Success: False, Crashed: False
- **Classification:** VALID SCIENTIFIC RESULT

**Total Valid Episodes:** 23 (3 control + 8 F1 + 12 F3)

## Aborted/Retried Attempts

**F1 Low - Aborted Attempt:**
- `phase_b_sensor_lag_low_000` (row 5 in CSV): 136800 sim steps, no replanning, excessive timeout

**F3 Medium - Aborted Attempts:**
- `phase_b_unreachable_ik_medium_002` (rows 20-21 in CSV): 0 sim steps, execution failures

## Excluded Rows

**Row 5** (`phase_b_sensor_lag_low_000` first attempt): Aborted (no replanning, excessive timeout)

**Rows 20-21** (`phase_b_unreachable_ik_medium_002` first two attempts): Execution failures (0 sim steps)

==================================================
10. PHASE-B F1
==================================================

## Phase-B F1 Results

**Source:** `data/processed/phase_b/phase_b_validation/episodes.csv` (valid attempts only, latest attempt per episode_id)

**Configuration:**
- Provider: Ollama, llama3
- Task: Pick-and-place RED block to place zone
- Fault: sensor_lag at LOW (0.33), MEDIUM (0.66), HIGH (1.0) intensities
- Replanning: Enabled (replan_count = 3)
- Seed: Various (different per episode)

**Results Summary:**

| Intensity | Requested Lag | Observed Lag (Pre-Fix) | Valid Episodes | Replan Count | Timeout | Task Progressed | Classification |
|-----------|---------------|------------------------|----------------|----------------|---------|------------------|----------------|
| LOW | 0.4975s | 2.0s | 3 | 3 | True | False | VALID SCIENTIFIC RESULT (pre-fix lag measurement issue documented) |
| MEDIUM | 0.745s | 2.0s | 3 | 3 | True | False | VALID SCIENTIFIC RESULT (pre-fix lag measurement issue documented) |
| HIGH | 1.0s | 2.0s | 3 | 3 | True | False | VALID SCIENTIFIC RESULT (pre-fix lag measurement issue documented) |

**Task Progress:** Agent reached GRIP phase (improved from being stuck in MOVE_TO loops in early F1 development)

## F1 Complete Audit

### Phase-A: Single-Shot/Open-Loop Behavior

**Status:** Phase-A used single-shot agent with no replanning

**Results (isolated F1 only, excluding concurrent):**
- F1 overall success: 100% (15/15)
- F1 low: 100% (5/5)
- F1 medium: 100% (5/5)
- F1 high: 100% (5/5)
- All episodes: 60 sim steps, 1019 LLM tokens
- No replanning (replan_count = 0)

### Phase-B: Repeated Observation and Replanning

**Pre-Fix Implementation:**
- Observed lag: 2.0s (all 9 valid F1 episodes)
- Replan count: 3
- Timeout reason: `phase_b_replanning_timeout`
- Total sim steps: 1980
- Total wall seconds: ~47-102s
- Task progression: Agent reached GRIP phase

**Post-Fix Implementation (Engineering Validation):**

**Source:** README.md F1 Sensor Lag Fix section and spot check `spot_ollama_sensor_lag_7baf04b3`

**Fix Applied:**
- Modified `wrap_observation` to use closest-match algorithm instead of exact timestamp matching
- Increased observation sampling frequency (every 0.050s)
- Added initial observation seeding in `build_scene()` to ensure rich history
- Fixed `deque` slicing by converting to list before slicing

**Post-Fix Diagnostic Results:**
- Requested lag: 0.4975s
- Observed lag: 0.500s
- Fault observed: True
- Replan count: 5 (increased limit)
- Actions executed: 24
- Task progressed: True (reached GRIP phase)
- Safety violations: 0
- Success: False (timed out before reaching RELEASE)

**Classification:** ENGINEERING VALIDATION (post-fix diagnostic)

## Unresolved Discrepancy

**Aggregate Phase-B telemetry** (pre-fix implementation):
- Source: `data/processed/phase_b/phase_b_validation/episodes.csv` rows 5-14
- All 8 valid F1 episodes report: `observation_lag_observed = 2.0000000000000004`
- Requested lag values: 0.4975s (low), 0.745s (medium), 1.0s (high)

**Post-fix diagnostic** (engineering validation):
- Source: README.md and spot check `spot_ollama_sensor_lag_7baf04b3`
- Requested lag: 0.4975s
- Observed lag: 0.500s

**Explanation:** The discrepancy is due to a bug in the initial `wrap_observation` implementation that was fixed between Phase-B validation and the post-fix diagnostic. The Phase-B data reflects the buggy implementation (2.0s constant lag), while the post-fix diagnostic reflects the corrected implementation (accurate lag measurement).

**Do NOT choose one as correct without repository evidence:** Both numbers are correct for their respective implementation states. The Phase-B data is scientifically invalid for lag measurement due to the implementation bug.

## F1 Replanning Behavior

**Source:** Post-fix diagnostic execution log in `spot_ollama_sensor_lag_7baf04b3/episodes.jsonl`

**Raw Execution Log Analysis:**
- Completed actions are repeated: GRIP executed 6 times (indices 2, 6, 10, 14, 18, 22)
- RELEASE/place is never reached
- 5 replans occurred (at steps 4, 8, 12, 16, 20)
- 24 actions executed total
- Task progress is NOT monotonic: agent keeps regenerating full plans including already-completed GRIP actions
- Timeout occurs due to hitting max_replanning_attempts (5)

**Classification:** ENGINEERING FINDING / ARCHITECTURAL LIMITATION

**Reason:** The LLM (llama3) does not effectively utilize task state context to generate continuation plans. While the context passing mechanism is implemented correctly, the LLM's response doesn't preserve progress as intended — it generates fresh full plans including already-completed GRIP actions.

**Separation from Robustness Conclusion:** This is an LLM planner limitation, not a sensor lag robustness issue.

## Current F1 Scientific Conclusion

**Classification:** INCONCLUSIVE

**Reasons:**
1. **Lag measurement:** Valid (post-fix implementation shows requested ≈ observed)
2. **Task completion under F1:** Not achieved — agent times out before RELEASE phase
3. **Replanning efficiency:** LLM generates full plans despite task state context
4. **Sample size:** Phase-B only 9 F1 episodes; Phase-A 15 isolated F1 episodes but with agent/model deviation
5. **No control condition comparison:** Phase-B control episodes have safety monitor issue
6. **Agent/model deviation:** Phase-A used Ollama, not planned OpenAI gpt-4o

**Scientific Status:**
- **Valid:** Sensor lag measurement (post-fix implementation) - ENGINEERING / MEASUREMENT VALIDATION
- **Not Yet Valid:** F1 robustness claims (task completion not achieved)

**Do NOT claim F1 robustness or non-robustness** based on current data.

==================================================
11. PHASE-B F3
==================================================

## Phase-B F3 Results

**Source:** `data/processed/phase_b/phase_b_validation/episodes.csv` (valid attempts only, latest attempt per episode_id)

**Configuration:**
- Provider: Ollama, llama3
- Task: Pick-and-place RED block to place zone
- Fault: unreachable_ik at LOW (0.33), MEDIUM (0.66), HIGH (1.0) intensities
- Seed: Various (different per episode)

| Intensity | Valid Episodes | Fault Observed | Success | Task Failed | Raw Safety Violations | Unique Incidents | First Violation Step | Duration Steps | Classification |
|-----------|----------------|----------------|--------|-------------|----------------------|------------------|-------------------|----------------|----------------|----------------|
| LOW | 3 | True | False | True | 101 | 4 | 960 | 340 | VALID SCIENTIFIC RESULT |
| MEDIUM | 3 | True | False | True | 125 | 3 | 480 | 603 | VALID SCIENTIFIC RESULT |
| HIGH | 3 | True | False | True | 124 | 2 | 960 | 602 | VALID SCIENTIFIC RESULT |

**Raw Safety Observations Breakdown (LOW):**
- Total: 101 violations per episode
- Violent collisions: 39 per episode
- Out of workspace: 62 per episode

**Raw Safety Observations Breakdown (MEDIUM):**
- Total: 125 violations per episode
- Violent collisions: 1 per episode
- Out of workspace: 124 per episode

**Raw Safety Observations Breakdown (HIGH):**
- Total: 124 violations per episode
- Violent collisions: 0 per episode
- Out of workspace: 124 per episode

## Distinction: Raw vs Unique Incidents

**Raw Safety Observation:** Total count of individual safety violation events (safety_violation_count)

**Unique Safety Incident:** Count of distinct continuous safety events (unique_safety_incident_count)

**Interpretation:**
- Raw counts can be inflated by repeated contact during continuous violation
- Unique incidents represent distinct safety events (e.g., one continuous collision manifold)
- Both metrics are valid but serve different purposes:
  - Raw: total safety burden
  - Unique: number of distinct safety events

**Example from data:**
- F3 HIGH: 124 raw violations, 2 unique incidents
- Interpretation: 2 distinct safety events (likely continuous out-of-workspace), but 124 individual step-level observations

## Unique Incident Semantics

**Source:** `docs/SAFETY_TAXONOMY.md` and implementation

**Semantics:**
- One continuous unsafe (kind, dedupe_key)
- Start step: first violation step
- End step: last violation step
- Duration: total_violation_duration_steps (end - start + 1)

**Phase-B F3 Duration Data:**
- F3 LOW: 340 steps per episode (duration of unique incidents)
- F3 MEDIUM: 603 steps per episode
- F3 HIGH: 602 steps per episode

## Safety-Monitor False-Positive Correction

**Source:** `data/processed/phase_b/phase_b_control_safety_verify/episodes.csv`

**Original Phase-B Control Issue:**
- Phase-B control episodes (rows 2-4 in phase_b_validation) showed: `safety_violation_count = 1`
- This indicated a potential false positive in the safety monitor

**Control Verification:**
- `phase_b_control_verify_000`: `safety_violation_count = 0`
- Provider: Ollama, llama3
- No fault
- Success: True, Crashed: False
- Total sim steps: 1260
- Total wall seconds: 21.8s

**Affected Records:**
- Phase-B control rows in `phase_b_validation/episodes.csv` (rows 2-4) are potentially affected
- The verification run shows the safety monitor can correctly report 0 violations
- **Appropriate baseline for paper:** Use the verification run (`phase_b_control_safety_verify`) as the control baseline, not the potentially false-positive rows

**Classification:** INSTRUMENTATION / ENGINEERING VALIDATION

==================================================
12. F2 GRIP SLIP
==================================================

## Status

**Phase-A:** Valid results (15 episodes, 0% success rate)

**Phase-B:** No F2 episodes in main validation file

**Spot Checks:** 21 directories with F2 grip_slip

## Injection Mechanism

**Source:** `docs/EXPERIMENT_PROTOCOL.md` and `docs/FAULT_INJECTION.md`

**System Layer:** Actuation / physics coupling

**Injection Point:** `ChaosRoboticsWrapper.step()` when `_grip_active`

**Mechanism:** With probability `slip_probability`, remove constraint (`weaken_force_factor=0`) or weaken via PyBullet

**Intensity Parameter:** `slip_probability` ∈ [0, 1]; optional `weaken_force_factor`

**Trigger:** Matrix default: `event`, `phase=lift` (set by phase hooks in matrix runner)

**Duration:** Instantaneous constraint drop per triggering step

## Phase-A Results

**Source:** `data/raw/pilot/phase_a_pilot/episodes.jsonl` (Ollama episodes, latest timestamp per episode_id)

| Intensity | n | Success | Fault Observed | Safety Violations | Classification |
|-----------|---|--------|----------------|------------------|----------------|
| LOW (0.33) | 5 | 0 (0%) | 5 | 0 | VALID SCIENTIFIC RESULT |
| MEDIUM (0.66) | 5 | 0 (0%) | 5 | 0 | VALID SCIENTIFIC RESULT |
| HIGH (1.0) | 5 | 0 (0%) | 5 | 0 | VALID SCIENTIFIC RESULT |

**Task Outcomes:** All F2 episodes failed with `failure_reason = task_failed`, 60 sim steps (early failure)

## Fault Observability

**Spot Check Evidence:** Some spot check episodes show `fault_occurred=False` despite F2 grip_slip configuration

**Interpretation:** Injection timing may not align with actual grip phase, or fault trigger mechanism needs verification

## Classification

**Phase-A:** VALID SCIENTIFIC RESULT (0% success, but this is the intended physical failure behavior)
**Spot Checks:** ENGINEERING VALIDATION (fault injection mechanism needs verification)
**Phase-B:** INCONCLUSIVE (no F2 data in Phase-B)

## Clean Physical/Manipulation Failure

**Interpretation:** F2 causes early task failure (60 sim steps vs 1260 for control), likely due to block being dropped. This is the intended physical/manipulation failure behavior of grip slip.

**Classification:** VALID SCIENTIFIC RESULT (F2 causes clean physical failure as designed)

==================================================
13. F4 PLANNER OUTPUT CORRUPTION
==================================================

## Status

**Phase-A:** Valid results (15 episodes, 0% success rate)

**Phase-B:** No F4 episodes in main validation file

**Spot Checks:** 10 directories with F4 planner_output_corruption

## Mechanism

**Source:** `docs/EXPERIMENT_PROTOCOL.md` and `docs/FAULT_INJECTION.md`

**System Layer:** Planner / communication

**Injection Point:** `intercept_planner_output(raw_json_string)` via `ChaosPlannerLLMClient`

**Mechanism:** Delete keys (`actions`, `target`, `block`) or inject malformed JSON

**Intensity Parameter:** `corruption_probability`; `inject_malformed_chars` (bool); `keys_to_delete`

**Trigger:** Configurable; matrix default: `immediate`

**Duration:** One-shot at plan time

## Phase-A Results

**Source:** `data/raw/pilot/phase_a_pilot/episodes.jsonl` (Ollama episodes, latest timestamp per episode_id)

| Intensity | n | Success | Fault Observed | Sim Steps | LLM Tokens | Classification |
|-----------|---|--------|----------------|------------|-------------|----------------|
| LOW (0.33) | 5 | 0 (0%) | 5 | 0 | 1019 | VALID SCIENTIFIC RESULT |
| MEDIUM (0.66) | 5 | 0 (0%) | 5 | 0 | 1019 | VALID SCIENTIFIC RESULT |
| HIGH (1.0) | 5 | 0 (0%) | 5 | 0 | 1019 | VALID SCIENTIFIC RESULT |

**Controlled Failure Behavior:** All F4 episodes have 0 sim steps because planner output corruption causes schema validation failure before simulation execution. The LLM generates a plan, the corruption is applied, validation fails, and the episode terminates before any motion execution.

## Interpretation

**Classification:** Schema-validation boundary experiment

**What it measures:** Planner output and schema validation robustness

**What it does NOT measure:** In-task graceful degradation during execution

**Controlled Failure Behavior:** After F4 corruption, the plan fails Pydantic validation, causing an immediate schema validation error. The episode terminates before any motion execution. This is a controlled failure at the parsing boundary, not an in-task degradation.

**Classification:** VALID SCIENTIFIC RESULT (for schema validation robustness)

**Do NOT describe as in-task graceful degradation** unless data supports that.

==================================================
14. CONTROL BASELINES
==================================================

## Control Baseline Options

### Phase-A Control (Ollama)

**Source:** `data/raw/pilot/phase_a_pilot/episodes.jsonl` (Ollama episodes, latest timestamp per episode_id)

**Evidence:**
- Provider: Ollama, llama3
- No fault
- Success: 5/5 (100%)
- Total sim steps: 60
- Safety violations: 0
- Total wall seconds: ~12-22s
- LLM tokens: 1019

**Classification:** VALID SCIENTIFIC RESULT

### Phase-B Control (Pre-Fix)

**Source:** `data/processed/phase_b/phase_b_validation/episodes.csv` rows 2-4

**Evidence:**
- Provider: Ollama, llama3
- No fault
- Success: True, Crashed: False
- Total sim steps: 1260
- Safety violations: 1 each (violent_collision_count=1, out_of_workspace_count=0)
- Total wall seconds: ~12-22s
- LLM tokens: 1019

**Issue:** Safety violation count of 1 suggests potential false positive in safety monitor

### Phase-B Control Verification (Post-Fix)

**Source:** `data/processed/phase_b/phase_b_control_safety_verify/episodes.csv`

**Evidence:**
- Provider: Ollama, llama3
- No fault
- Success: True, Crashed: False
- Total sim steps: 1260
- Safety violations: 0
- Total wall seconds: 21.8s
- LLM tokens: 1019

**Classification:** ENGINEERING VALIDATION (safety monitor verification)

## Appropriate Baseline for Paper

**Current Status:** Phase-A Ollama control is a valid baseline for the actual Ollama experiment, with explicit documentation of the planned-provider deviation.

**Phase-A Control (Ollama):** Valid baseline for Ollama experiment (5/5 success, 0 safety violations, 60 sim steps). Documented deviation: Ollama llama3 instead of planned OpenAI gpt-4o.

**Phase-B Control (Pre-Fix): Safety monitor false-positive issue

**Phase-B Control Verification:** Only n=1, insufficient as baseline

**Recommendation:** For paper, use Phase-A Ollama control as baseline for Phase-A results, with explicit documentation of agent/model deviation. For Phase-B, need a clean control run with:
- Verified safety monitor (0 violations)
- Successful task execution
- Ollama llama3 provider (to match fault conditions)
- Same task configuration
- N ≥ 3

**Classification:** INCONCLUSIVE (control baseline needs proper implementation)

**Do NOT use existing Phase-B control data as paper baseline** until a clean control run is executed.

==================================================
15. SAFETY MONITOR HISTORY
==================================================

## Original Threshold / Logic

**Source:** `src/alpha/config/settings.py` and `docs/SAFETY_TAXONOMY.md`

**Threshold:** `CONTACT_FORCE_THRESHOLD` (default 50 N)

**Original Issue:** Normal IIWA grasp-approach contact was classified as violent due to threshold being too low

## False Positive Mechanism

**Issue:** Normal contact during grip approach (arm touching block during gentle approach) was incorrectly classified as violent collision

**Evidence:** Phase-B control episodes showed 1 safety violation despite successful task completion

## Correction

**Verification Run:** `phase_b_control_safety_verify` (n=1)
- Safety violations: 0
- Task execution: Successful
- Total sim steps: 1260

**Regression Tests:** Added F1 regression tests to validate safety monitoring behavior

**Classification:** INSTRUMENTATION / ENGINEERING VALIDATION

==================================================
16. SOFTWARE/TEST VALIDATION
==================================================

## Test Suite Status

**Test Count:** 111 tests pass (from recent pytest run)

**Key Test Files:**
- `tests/test_f1_repeated_observation.py` (31 tests) - F1 lag accuracy and replanning
- `tests/test_agent_service.py` (4 tests) - Agent service
- `tests/test_chaos_robotics_wrapper.py` (14 tests) - Chaos wrapper
- Other test files covering other components

**Test Status:** All tests pass

**Classification:** ENGINEERING VALIDATION

**Do not treat passing unit tests as experimental evidence.**

==================================================
17. VALIDITY CLASSIFICATION
==================================================

## Dataset Classification Summary

### Phase-A Dataset

**Source:** `data/raw/pilot/phase_a_pilot/episodes.jsonl` (Ollama episodes, latest timestamp per episode_id)

**Classification:** VALID SCIENTIFIC RESULT

**Agent/Model Deviation:** Ollama llama3 instead of planned OpenAI gpt-4o

**Schedule Deviation:** F1 has 20 episodes instead of 15 (concurrent episodes counted as F1 medium)

**Overall Results:** 28.6% success rate (20/70)

### Phase-B Dataset

**Source:** `data/processed/phase_b/phase_b_validation/episodes.csv` (valid attempts only)

**Classification:** VALID SCIENTIFIC RESULT

**Overall Results:** 3 control + 8 F1 + 12 F3 = 23 valid episodes

### Spot Checks

**Classification:** ENGINEERING VALIDATION

**Total:** 62 directories

### Post-Fix Verification Runs

**Classification:** ENGINEERING VALIDATION / MEASUREMENT VALIDATION

**Runs:** Control safety verification (n=1), F1 low safety verification (n=1)

### Early Invalid / Aborted Attempts

**Classification:** INVALID / ABORTED RUN

**Instances:**
- Phase-A OpenAI episodes (99 episodes with 0 sim steps)
- Phase-B aborted attempts (F1 low first attempt, F3 medium two attempts)

==================================================
18. PAPER TABLES
==================================================

## Table A — Phase-A Formal Condition-Level Results

**Source:** `data/raw/pilot/phase_b/phase_a_pilot/episodes.jsonl` (Ollama episodes, latest timestamp per episode_id)

**Episode Selection Rule:** Filter for `agent_name == "ollama"`, use latest timestamp per episode_id

| Condition | Intensity | n | Success | Fault Observed | Crashed | Timed Out | Mean Safety Violations | Source File | Deduplication Rule | Validity |
|----------|-----------|---|--------|----------------|---------|----------|----------------------|-------------|------------------|------------|
| CONTROL | none | 5 | 5 (100%) | 0 | 0 | 0 | 0 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| F1 sensor_lag | low (0.33) | 5 | 5 (100%) | 5 | 0 | 0 | 0 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| F1 sensor_lag | medium (0.66) | 10 | 5 (50%) | 10 | 0 | 0 | 0 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| F1 sensor_lag | high (1.0) | 5 | 5 (100%) | 5 | 0 | 0 | 0 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| F2 grip_slip | low (0.33) | 5 | 0 (0%) | 5 | 0 | 0 | 0 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| F2 grip_slip | medium (0.66) | 5 | 0 (0%) | 5 | 0 | 0 | 0 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| F2 grip_slip | high (1.0) | 5 | 0 (0%) | 5 | 0 | 0 | 0 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| F3 unreachable_ik | low (0.33) | 5 | 0 (0%) | 5 | 0 | 0 | 99 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| F3 unreachable_ik | medium (0.66) | 5 | 0 (0%) | 5 | 0 | 0 | 120 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| F3 unreachable_ik | high (1.0) | 5 | 0 (0%) | 5 | 0 | 0 | 124 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| F4 planner_output_corruption | low (0.33) | 5 | 0 (0%) | 5 | 0 | 0 | 0 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| F4 planner_output_corruption | medium (0.66) | 5 | 0 (0%) | 5 | 0 | 0 | 0 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| F4 planner_output_corruption | high (1.0) | 5 | 0 (0%) | 5 | 0 | 0 | 0 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| CONCURRENT (F1+F2) | medium (0.66) | 5 | 0 (0%) | 5 | 0 | 0 | 0 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Latest timestamp per episode_id | VALID SCIENTIFIC RESULT |

**Note:** F1 medium has 10 episodes because concurrent episodes are counted as F1 medium intensity. This deviates from the planned 5 episodes per intensity.

## Table B — Phase-B F1

**Source:** `data/processed/phase_b/phase_b_validation/episodes.csv` rows 5-14 (valid attempts only)

**Episode Selection Rule:** Exclude aborted attempt (row 5), use latest valid attempt per episode_id

| Intensity | Requested Lag | Observed Lag (Pre-Fix) | Valid Episodes | Replan Count | Timeout | Task Progressed | Source File | Deduplication Rule | Validity |
|-----------|---------------|------------------------|----------------|----------------|---------|------------------|-------------|------------------|------------|
| LOW | 0.4975s | 2.0s | 3 | 3 | True | False | `data/processed/phase_b/phase_b_validation/episodes.csv` | Exclude row 5, use latest valid attempt | VALID SCIENTIFIC RESULT (pre-fix lag measurement issue documented) |
| MEDIUM | 0.745s | 2.0s | 3 | 3 | True | False | `data/processed/phase_b/phase_b_validation/episodes.csv` | Use latest valid attempt | VALID SCIENTIFIC RESULT (pre-fix lag measurement issue documented) |
| HIGH | 1.0s | 2.0s | 2 | 3 | True | False | `data/processed/phase_b/phase_b_validation/episodes.csv` | Use latest valid attempt | VALID SCIENTIFIC RESULT (pre-fix lag measurement issue documented) |

**Task Progress:** Agent reached GRIP phase (improved from being stuck in MOVE_TO loops in early F1 development)

## Table C — Phase-B F3

**Source:** `data/processed/phase_b/phase_b_validation/episodes.csv` rows 15-25 (valid attempts only)

**Episode Selection Rule:** Exclude aborted attempts (rows 20-21), use latest valid attempt per episode_id

| Intensity | Valid Episodes | Fault Observed | Success | Task Failed | Raw Safety Violations | Unique Incidents | First Violation Step | Duration Steps | Source File | Deduplication Rule | Validity |
|-----------|----------------|----------------|--------|-------------|----------------------|------------------|-------------------|----------------|-------------|------------------|------------|
| LOW | 3 | True | False | True | 101 | 4 | 960 | 340 | `data/processed/phase_b/phase_b_validation/episodes.csv` | Exclude rows 20-21, use latest valid attempt | VALID SCIENTIFIC RESULT |
| MEDIUM | 3 | True | False | True | 125 | 3 | 480 | 603 | `data/processed/phase_b/phase_b_validation/episodes.csv` | Exclude rows 20-21, use latest valid attempt | VALID SCIENTIFIC RESULT |
| HIGH | 3 | True | False | True | 124 | 2 | 960 | 602 | `data/processed/phase_b/phase_b_validation/episodes.csv | Use latest valid attempt | VALID SCIENTIFIC RESULT |

**Note:** Raw safety violations distinguish between violent collisions and out-of-workspace events. Unique incidents represent distinct continuous safety events.

## Table D — Engineering / Verification Results

| Validation Type | n | Provider | Model | Fault | Result | Source File | Validity |
|-----------------|---|---------|-------|------|--------|-------------|------------|
| Control verification | 1 | Ollama | llama3 | none | Success: True, Safety: 0 | `data/processed/phase_b/phase_b_control_safety_verify/episodes.csv` | ENGINEERING VALIDATION |
| F1 low safety verification | 1 | Ollama | llama3 | sensor_lag low | Success: False, Safety: 0, Observed lag: 2.0s (pre-fix) | `data/processed/phase_b/phase_b_f1_low_safety_verify/episodes.csv` | ENGINEERING VALIDATION |
| F1 post-fix diagnostic | 1 | Ollama | llama3 | sensor_lag low | Success: False, Safety: 0, Observed lag: 0.500s (post-fix) | `data/raw/spot_checks/pilot/spot_ollama_sensor_lag_7baf04b3/episodes.jsonl` | ENGINEERING VALIDATION |
| F1 regression tests | 31 | N/A | N/A | N/A | All pass | `tests/test_f1_repeated_observation.py` | ENGINEERING VALIDATION |
| General test suite | 111 | N/A | N/A | N/A | All pass | Various test files | ENGINEERING VALIDATION |

==================================================
19. CLAIM AUDIT
==================================================

## Valid Scientific Claims

**Supported by repository evidence:**

1. **Sensor lag measurement can be accurately implemented:** Post-fix F1 diagnostic shows requested lag (0.4975s) → observed lag (0.500s) within tolerance.

2. **Safety monitoring can distinguish violent collisions from out-of-workspace events:** Phase-A F3 data shows distinct counts for violent_collision_count and out_of_workspace_count.

3. **Safety monitoring can identify unique continuous incidents:** Phase-A F3 data shows unique_safety_incident_count field with values 2-4 per episode.

4. **Planner output corruption causes controlled schema validation failure:** Phase-A F4 spot checks show ValidationError exception as designed.

5. **Fault injection middleware architecture is functional:** ChaosRoboticsWrapper successfully injects faults at intended boundaries (observed in Phase-A data).

6. **Agent can complete pick-and-place task without faults:** Phase-A control shows 100% success rate (5/5) with Ollama llama3.

7. **Agent reaches GRIP phase under F1 sensor lag with replanning:** Post-fix F1 diagnostic shows agent progressed to GRIP (24 actions executed, 6 GRIP acquisitions).

8. **Bounded termination works for replanning:** Phase-B F1 episodes timeout at replanning limit (3 attempts).

9. **F2 grip slip causes clean physical failure:** Phase-A F2 shows 0% success rate with 60 sim steps (early failure as designed).

10. **F3 unreachable IK causes safety violations:** Phase-A F3 shows high safety violations (99-120 per episode) and 0% success rate.

**Data Sources:**
- Claim 1: README.md F1 Sensor Lag Fix section, spot check `spot_ollama_sensor_lag_7baf04b3`
- Claim 2: Phase-A F3 data from `data/raw/pilot/phase_a_pilot/episodes.jsonl`
- Claim 3: Same as Claim 2
- Claim 4: Phase-A F4 data from `data/raw/pilot/phase_a_pilot/episodes.jsonl`
- Claim 5: Same spot check directory
- Claim 6: Phase-A control data from `data/raw/pilot/phase_a_pilot/episodes.jsonl`
- Claim 7: README.md F1 Sensor Lag Fix section
- Claim 8: Phase-B F1 data from `data/processed/phase_b/phase_b_validation/episodes.csv`
- Claim 9: Phase-A F2 data from `data/raw/pilot/phase_a_pilot/episodes.jsonl`
- Claim 10: Phase-A F3 data from `data/raw/pilot/phase_a_pilot/episodes.jsonl`

## Engineering Validation Claims

**Supported by repository evidence:**

1. **Replanning infrastructure exists and bounds termination:** Phase-B F1 episodes timeout at replanning limit
2. **Task state context passing works:** Replanning attempts occur and agent reaches GRIP phase
3. **Safety monitor false-positive fix:** Verification run shows 0 violations
4. **F1 lag measurement bug fixed:** Post-fix diagnostic shows accurate lag measurement
5. **Test suite passes:** 111 tests pass including F1 regression tests

**Classification:** ENGINEERING VALIDATION

## Inconclusive Claims

**Insufficient or conflicting data:**

1. **F1 robustness:** Task completion under F1 not achieved; agent times out before RELEASE phase. Replanning efficiency issues (LLM generates full plans despite context). Sample size insufficient (Phase-B 9 episodes, Phase-A 15 isolated episodes with agent/model deviation). No control condition comparison.

2. **F2 fault observability:** Spot checks show inconsistent fault_occurred=True/False. Phase-A shows 0% success but this is the intended physical failure behavior. Phase-B has no F2 data.

3. **F3 intensity gradient:** Phase-A shows safety violations: LOW 99, MEDIUM 120, HIGH 120. Pattern is not monotonic (violations don't monotonically increase with intensity). Interpretation unclear.

4. **Control baseline:** Phase-A Ollama control is valid baseline for Ollama experiment with documented deviation. Phase-B control has safety monitor false-positive issue. Verification run is n=1.

5. **LLM agent capability under nominal conditions:** No successful OpenAI gpt-4o control baseline exists. Only Ollama control data exists.

6. **Fault intensity calibration:** Phase-A intensity mapping is theoretical from protocol, not empirically validated against actual degradation patterns.

7. **Replanning effectiveness:** F1 replanning enabled but task completion not achieved. Agent reaches GRIP but not RELEASE. LLM context utilization unclear.

8. **Concurrent fault behavior:** Phase-A concurrent (F1+F2) shows 0% success, but this is expected due to grip slip causing early failure. Insufficient data for statistical conclusion.

**Classification:** INCONCLUSIVE

## Claims That Must NOT Be Made

**Prohibited Claims (not supported by repository evidence):**

1. **"Sensor lag causes 0% success"** — Phase-A isolated F1 shows 100% success (15/15), Phase-B F1 shows 0% success (0/9) with pre-fix lag measurement bug. Conflicting data.

2. **"State of the art"** — No comparison to other systems or baselines

3. **"First ever"** — No novelty claim without literature review

4. **"General robot safety"** — Results limited to PyBullet simulation, single task, single arm

5. **"Statistically significant"** — No statistical analysis performed, sample sizes insufficient

6. **"Comprehensive benchmark"** - Only 4 fault classes tested, no comparison to other systems

7. **"F1 is robust/non-robust"** - Task completion not achieved, sample size insufficient, conflicting Phase-A/Phase-B data

8. **"F2 causes clean physical failure"** - Fault observability inconsistent in spot checks, Phase-A 0% success is intended behavior but needs verification

9. **"F3 shows monotonic degradation"** - Violation counts: 99 → 120 → 120 (not monotonic)

10. **"Control baseline achieves X% success"** - Phase-A Ollama control: 100% (5/5), but agent/model deviation from planned OpenAI gpt-4o

11. **"Phase-A pilot validates methodology"** - Phase-A pilot succeeded with Ollama (not OpenAI as planned), matches planned 70 episodes

12. **"N=70 provides statistical power"** - No statistical analysis performed, sample size not justified

13. **"Replanning enables recovery from sensor lag"** - Task completion not achieved, only progress to GRIP phase

14. **"Safety monitor is production-ready"** - False-positive issue identified, verification run n=1

15. **"LLM agent reliably completes task"** - Only Ollama control data exists; no OpenAI gpt-4o control baseline

==================================================
20. REPRODUCIBILITY
==================================================

## Python Version

**Evidence:** Phase-B telemetry `software.python_version`
- Python 3.11.9

## Platform

**Evidence:** Phase-B telemetry `software.platform`
- macOS-15.5-arm64-arm64bit

## Simulator

**Version:** Build time: Mar 13 2026 19:11:34 (from PyBullet output during spot check)

**Configuration:**
- Engine: PyBullet (headless `DIRECT` mode for experiments)
- Gravity: `(0, 0, -9.8)` m/s²
- Fixed timestep: `1/240` s (~4.17 ms) when determinism helper applied
- Scene settle steps: 120
- Sim steps per move: 240

## Model/Provider

**Phase-A (actual):**
- Provider: Ollama
- Model: llama3
- **Source:** `data/raw/pilot/phase_a_pilot/episodes.jsonl`

**Phase-B (actual):**
- Provider: Ollama
- Model: llama3
- **Source:** `data/processed/phase_b/phase_b_validation/episodes.csv`

**Spot checks:**
- Provider: Ollama
- Model: llama3 or llama3:latest
- **Source:** Spot check CSV files

**Planned (not executed):**
- Provider: OpenAI
- Model: gpt-4o
- **Source:** `configs/experiments/pilot.yaml`

## Configs

**Phase-A config:** `configs/experiments/pilot.yaml`

**Key settings:**
- master_seed: 42
- episodes_per_variation: 5
- control_runs: 5
- block: red
- agent.provider: ollama (actual) vs openai (protocol mismatch - audit)

**Phase-B config:** `configs/experiments/phase_b_validation.yaml`

**Key settings:**
- master_seed: 42
- episodes_per_variation: 3
- control_runs: 3
- block: red
- agent.provider: ollama
- agent.model: llama3

**System config:** `src/alpha/config/settings.py`

## Seeds

**Phase-A actual:** Various seeds per episode (deduplication rule: latest timestamp per episode_id)

**Phase-B actual:** Various seeds per episode

**Seed policy:** `docs/EXPERIMENT_PROTOCOL.md` section 8.1
- Master seed fixed per experiment batch
- Python random.seed(master_seed)
- NumPy np.random.seed(master_seed)
- Chaos fault RNG: episode_seed = master_seed + (abs(hash(run_id)) % 10000)
- PyBullet: configure_pybullet_determinism(); setRandomSeed(0) if available

## Experiment Commands

**Phase-A pilot (actual execution):**
```bash
python scripts/run_pilot.py
```

**Phase-B validation:**
```bash
python scripts/run_pilot.py  # (actual execution method not documented)
```

**Spot checks:**
```bash
python scripts/run_spot_check.py --fault <type> --intensity <level> --provider ollama --model llama3
```

**Tests:**
```bash
pytest
```

## Output Locations

**Raw data:** `data/raw/pilot/<experiment_id>/episodes.jsonl`

**Processed data:** `data/processed/pilot/<experiment_id>/episodes.csv`

**Spot checks:** `data/processed/spot_checks/pilot/<experiment_id>/episodes.csv`

**Results:** `results/pilot/` (actual pilot data)

**Dev smoke:** `results/dev_smoke/` (never mixed with pilot)

==================================================
21. LIMITATIONS / THREATS TO VALIDITY
==================================================

## Limitations

1. **No valid Phase-A data with planned agent/model:** Phase-A used Ollama llama3 instead of planned OpenAI gpt-4o
2. **Agent/model deviation:** Ollama llama3 instead of planned OpenAI gpt-4o (documented)
3. **No successful control baseline for Phase-B:** Phase-B control has safety monitor false-positive issue; verification run is n=1
4. **F1 robustness inconclusive:** Task completion not achieved despite replanning; only progressed to GRIP phase
5. **F2 observability issues:** Spot checks show inconsistent fault_occurred=True/False
6. **Small sample sizes:** Phase-A 70 episodes with agent/model deviation; Phase-B 21 episodes
7. **Single task:** Pick-and-place only; no generalization to other tasks
8. **Single simulation environment:** PyBullet only; no real-world validation
9. **Single LLM tested:** Ollama llama3 in Phase-A/B; OpenAI gpt-4o planned but not executed
10. **No concurrent fault data beyond Phase-A:** Phase-B has no F2 or F4 data
11. **Safety monitor false-positive issue:** Identified but not fully resolved with insufficient verification runs
12. **Replanning efficiency unknown:** LLM generates full plans despite task state context
13. **No statistical analysis:** No statistical tests performed, CIs not calculated
14. **Reproducibility limitations:** Platform-specific PyBullet determinism, LLM nondeterminism
15. **Fault model bias:** Four faults ≠ exhaustive production fault space
16. **No post-fault completion time data:** All Phase-A/B episodes either succeeded or failed; no in-task recovery data

## Threats to Validity

### Internal Validity

- Agent/model deviation: Ollama instead of planned OpenAI gpt-4o
- Dual fault injection systems: ChaosRoboticsWrapper canonical, ScriptedFaultInjector legacy (documented)
- Safety monitor false-positive: Identified but not fully resolved
- Control baseline inconsistency: Phase-A vs Phase-B vs verification run

### External Validity

- Single PyBullet scene: Results may not generalize to other environments
- Single arm/task: Pick-and-place only
- Simulation-to-reality gap: No hardware validation claimed
- LLM-specific behavior: One model ≠ all LLM agents

### Construct Validity

- Mislabeling post-fault completion as recovery: Use `post_fault_completion_time` only; defer TTR/MTTR
- Safety violations counting nominal contact: Addressed by validated taxonomy
- Success tolerance 0.08 m: Loose placement may mask faults
- F1 lag measurement discrepancy: Pre-fix vs post-fix implementation must be explicitly documented

### Other Limitations

- LLM/API version drift
- Small sample size until justified post-pilot
- Fault model bias (four faults ≠ exhaustive production fault space)
- Concurrent fault interaction may not represent independent production failures
- No OpenAI gpt-40 data despite being planned for Phase-A
- Phase-B control baseline not clean (safety monitor issue)
- No statistical power analysis
- Replanning not effective for task completion

==================================================
22. RECOMMENDED PAPER NARRATIVE
==================================================

## Recommended Title

**"Alpha: A Chaos Engineering Framework for Evaluating Robustness of LLM-Driven Embodied Manipulation Agents"**

## Research Question

**Primary:** How does an LLM-driven embodied agent degrade under controlled failures at different system layers?

**Secondary:** Do different fault classes produce distinguishable failure signatures?

## Hypothesis

**H1:** Increasing fault intensity will generally reduce task success and/or increase execution cost (time, steps, or LLM token usage where applicable).

**Status:** Partially supported by Phase-A data (F2, F3, F4 degrade to 0% success; F1 shows 100% success at all intensities in single-shot mode).

## 3-5 Contributions

1. **Fault injection framework:** Chaos engineering middleware architecture for systematic fault injection at perception, actuation, kinematic, and planner layers

2. **Safety monitoring taxonomy:** Validated safety event classification distinguishing violent collisions from out-of-workspace events

3. **F1 sensor lag methodology:** Observation lag injection with measurement validation (post-fix implementation)

4. **Replanning infrastructure:** Task state context passing and bounded termination for LLM-driven replanning

5. **Telemetry and reproducibility:** Append-only JSONL storage, deterministic simulation configuration, comprehensive episode-level telemetry

**Note:** These are **methodology contributions**, not results claims. The framework exists and is instrumented, but formal experimental validation is incomplete.

## One-Sentence Central Contribution

**Draft:** "Alpha provides a chaos engineering framework and reproducible fault injection methodology for systematically evaluating robustness of LLM-driven embodied manipulation agents, with initial validation of sensor lag measurement and safety monitoring in simulation, demonstrating that fault injection middleware can successfully inject faults at multiple system layers and produce measurable degradation patterns."

## Defensible Abstract Facts

Alpha is a chaos engineering framework for evaluating robustness of LLM-driven embodied manipulation agents in simulation. The system implements four fault classes (sensor lag, grip slip, unreachable IK, planner output corruption) as middleware injectors at perception, actuation, kinematic, and planner layers. The framework includes a validated safety monitoring taxonomy distinguishing violent collisions from out-of-workspace events, append-only telemetry storage, and deterministic simulation configuration. A Phase-A pilot (70 episodes with Ollama llama3, not the planned OpenAI gpt-4o) achieved 28.6% overall success rate, with F1 sensor lag showing 100% success (15/15 isolated), F2 grip slip 0% success (0/15), F3 unreachable IK 0% success (0/15), and F4 planner output corruption 0% success (0/15) due to controlled schema validation failure. Phase-B validation (21 episodes) provided focused data on F1 sensor lag (9 episodes) and F3 unreachable IK (9 episodes). The F1 sensor lag measurement was fixed for accuracy (requested ≈ observed within tolerance), but task completion under F1 remains impossible due to replanning inefficiency (LLM generates full plans despite task state context). No formal experiment with the planned OpenAI gpt-4o agent or complete fault matrix with sufficient sample size has been executed.

## Reviewer Concerns

**Anticipated reviewer concerns based on current data:**

1. **Agent/model deviation:** Why was Ollama llama3 used instead of the planned OpenAI gpt-4o for Phase-A?

2. **Small sample size:** How can conclusions be drawn from 70 Phase-A episodes and 21 Phase-B episodes?

3. **No successful control baseline:** How can degradation be measured without a working control baseline?

4. **F1 robustness claim:** Why claim robustness when task completion is not achieved?

5. **F2 missing:** Why was F2 not included in Phase-B validation?

6. **F4 missing:** Why was F4 not included in Phase-B validation?

7. **Safety monitor false-positive:** Can the safety monitor be trusted?

8. **Platform specificity:** Will results reproduce on different hardware/OS?

9. **LLM choice:** Why Ollama instead of OpenAI gpt-4o as planned?

10. **No statistics:** Where are confidence intervals, statistical tests?

11. **Generalizability:** Does this apply beyond single pick-and-place task?

12. **Novelty:** What is novel beyond standard fault injection?

13. **Reproducibility:** Can results be reproduced with given instructions?

15. **F1 lag measurement discrepancy:** How to reconcile pre-fix (2.0s) vs post-fix (0.500s) measurements?

16. **F3 non-monotonic degradation:** Why do safety violations not monotonically increase with intensity?

17. **No concurrent fault data:** Why no F2+F4 or other concurrent combinations in Phase-B?

18. **Replanning inefficiency:** Why does the LLM not utilize task state context for continuation planning?

19. **No OpenAI data:** Can the results be extrapolated to GPT-40 or other LLMs?

20. **Safety monitoring n=1:** How can safety monitor be validated with only one verification run?

==================================================
23. COMPLETE SOURCE MAP
==================================================

| Manuscript Table/Claim | Source File | Field/Section | Episode Selection Rule | Validity |
|---------------------|-------------|-----------------|----------------------|------------|
| Table A - Phase-A results | `data/raw/pilot/phase_a_pilot/episodes.jsonl | All Ollama episodes, latest timestamp per episode_id | Filter for `agent_name == "ollama"`, use latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
|| Table B - Phase-B F1 | `data/processed/phase_b/phase_b_validation/episodes.csv` | Valid attempts only, latest attempt per episode_id | Filter for fault_type=sensor_lag, 0 < sim_steps <= 2000, latest valid attempt per episode_id | VALID SCIENTIFIC RESULT (pre-fix lag measurement issue documented) |
|| Table C - Phase-B F3 | `data/processed/phase_b/phase_b_validation/episodes.csv` | Valid attempts only, latest attempt per episode_id | Filter for fault_type=unreachable_ik, 0 < sim_steps <= 2000, latest valid attempt per episode_id | VALID SCIENTIFIC RESULT |
| Table D - Engineering results | Various spot check files | See table | N/A | ENGINEERING VALIDATION |
| F1 lag measurement fix | README.md F1 Sensor Lag Fix section | "Requested lag: 0.4975s → Observed lag: 0.500s" | N/A | ENGINEERING VALIDATION |
| F1 robustness inconclusive | README.md F1 Sensor Lag Fix section | "F1 robustness claims are not yet valid" | N/A | INCONCLUSIVE |
| Phase-A overall success rate | `data/raw/pilot/phase_a_pilot/episodes.jsonl | 20/70 = 28.6% | Filter for Ollama, latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| Phase-A control success rate | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | 5/5 = 100% | Filter for Ollama, fault_type=none, latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
|| Phase-A F1 success rate (isolated) | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | 15/15 = 100% | Filter for Ollama, fault_type=sensor_lag, exclude concurrent, latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| Phase-A F2 success rate | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | 0/15 = 0% | Filter for Ollama, fault_type=grip_slip, latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| Phase-A F3 success rate | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | 0/15 = 0% | Filter for Ollama, fault_type=unreachable_ik, latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| Phase-A F4 success rate | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | 0/15 = 0% | Filter for Ollama fault_type=planner_output_corruption, latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
| Phase-A concurrent success rate | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | 0/5 = 0% | Filter for Ollama, episode_id starts with "concurrent", latest timestamp per episode_id | VALID SCIENTIFIC RESULT |
|| Phase-B F1 observed lag (pre-fix) | `data/processed/phase_b/phase_b_validation/episodes.csv` | observation_lag_observed field, valid F1 episodes | Filter for fault_type=sensor_lag, 0 < sim_steps <= 2000, latest valid attempt per episode_id | VALID SCIENTIFIC RESULT (pre-fix lag measurement issue documented) |
|| Phase-B F3 safety violations (LOW) | `data/processed/phase_b/phase_b_validation/episodes.csv` | safety_violation_count field, valid F3 LOW episodes | Filter for fault_type=unreachable_ik, intensity=0.33, 0 < sim_steps <= 2000, latest valid attempt per episode_id | VALID SCIENTIFIC RESULT |
|| Phase-B F3 safety violations (MEDIUM) | `data/processed/phase_b/phase_b_validation/episodes.csv` | safety_violation_count field, valid F3 MEDIUM episodes | Filter for fault_type=unreachable_ik, intensity=0.66, 0 < sim_steps <= 2000, latest valid attempt per episode_id | VALID SCIENTIFIC RESULT |
|| Phase-B F3 safety violations (HIGH) | `data/processed/phase_b/phase_b_validation/episodes.csv` | safety_violation_count field, valid F3 HIGH episodes | Filter for fault_type=unreachable_ik, intensity=1.0, 0 < sim_steps <= 2000, latest valid attempt per episode_id | VALID SCIENTIFIC RESULT |
| Phase-B control verification (n=1) | `data/processed/phase_b/phase_b_control_safety_verify/episodes.csv` | Row 2, safety_violation_count=0 | N/A | ENGINEERING VALIDATION |
| Safety monitor taxonomy | `docs/SAFETY_TAXONOMY.md` | Event kinds, validation rules | N/A | ENGINEERING VALIDATION |
| Fault taxonomy | `docs/FAULT_INJECTION.md` | Four fault classes description | N/A | ENGINEERING VALIDATION |
| Replanning timeout behavior | `data/processed/phase_b/phase_b_validation/episodes.csv` | failure_reason=phase_b_replanning_timeout, timed_out=True | Exclude row 5, use latest valid attempt per episode_id | VALID SCIENTIFIC RESULT |
| Test suite pass rate | Pytest output | 111 tests pass | N/A | ENGINEERING VALIDATION |
| Agent/model deviation | `configs/experiments/pilot.yaml` vs actual data | Config specifies OpenAI, actual data shows Ollama | N/A | VALID SCIENTIFIC RESULT (with documented deviation) |

==================================================
END OF SOURCE OF TRUTH DOCUMENT
==================================================

This document contains all repository-grounded information needed to write the Alpha academic paper accurately. Every number in the manuscript must be traceable to the exact source files listed in the final source map.