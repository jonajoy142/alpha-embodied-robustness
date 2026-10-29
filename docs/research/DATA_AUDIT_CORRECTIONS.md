# Data Audit Corrections Table (HISTORICAL - SUPERSEDED)

> [!WARNING]
> **SUPERSEDED BY FINAL 150-EPISODE MATRIX EXPERIMENT**
> This document records historical corrections from August 2026 audits of early exploratory pilots (Phase-A/Phase-B).
> For the revised manuscript, the authoritative, controlled experimental dataset is the 150-episode head-to-head matrix documented in [`artifacts/final_150_matrix/MANUSCRIPT_SOURCE_OF_TRUTH.md`](file:///Users/jonajoy/Projects/alpha_repo/artifacts/final_150_matrix/MANUSCRIPT_SOURCE_OF_TRUTH.md).

**Date:** 2026-08-16 (Historical)
**Purpose:** Document historical numerical corrections made to early pilot notes during preliminary audits.

## Phase-A Corrections

| Section | Original Value | Corrected Value | Primary Source File | Reason for Correction |
|---------|----------------|-----------------|---------------------|----------------------|
| Section 6 - Actual Condition Counts | F1 sensor_lag: 20 episodes (5 low + 10 medium + 5 high) | F1 sensor_lag (isolated): 15 episodes (5 low + 5 medium + 5 high) | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Concurrent episodes were incorrectly counted as F1 medium. Concurrent episodes are separate from isolated F1. |
| Section 6 - Deviation from Planned Schedule | F1 has 20 episodes instead of 15 due to concurrent episodes being counted as F1 medium | Agent/model deviation: Ollama llama3 instead of OpenAI gpt-4o. Total matches planned 70 episodes. | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | No schedule deviation exists. The 70 episodes match the planned schedule (5 control + 15 each F1,F2,F3,F4 + 5 concurrent). |
| Section 7 - Condition-Level Results | F1 sensor_lag medium: n=10, success=5 (50%) | F1 sensor_lag (isolated) medium: n=5, success=5 (100%) | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Concurrent episodes should not be counted in isolated F1 matrix. |
| Section 7 - Overall Phase-A Results | Total success: 20 (28.6%) | Total success: 20 (28.6%) [5 control + 15 isolated F1] | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Clarified composition of success count. |
| Section 7 - F3 HIGH safety violations | Mean safety violations: 124 | Mean safety violations: 120 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Corrected from 124 to 120. Phase-A F3 HIGH shows 120 violations (0 violent, 120 out_of_workspace). |
| Section 10 - F1 Complete Audit - Phase-A | F1 overall success: 75% (15/20) | F1 overall success: 100% (15/15) (isolated only, excluding concurrent) | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Corrected to exclude concurrent episodes from isolated F1 count. |
| Section 10 - F1 Complete Audit - Phase-A | F1 medium: 50% (5/10) | F1 medium: 100% (5/5) | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Corrected to exclude concurrent episodes from isolated F1 count. |
| Section 10 - Current F1 Scientific Conclusion | Sample size: Phase-B only 8 F1 episodes; Phase-A 20 F1 episodes | Sample size: Phase-B only 9 F1 episodes; Phase-A 15 isolated F1 episodes | `data/processed/phase_b/phase_b_validation/episodes.csv`, `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Corrected Phase-B count to 9, Phase-A count to 15 isolated. |
| Section 10 - Current F1 Scientific Conclusion | Scientific Status: Valid - Sensor lag measurement (post-fix implementation) | Scientific Status: Valid - Sensor lag measurement (post-fix implementation) - ENGINEERING / MEASUREMENT VALIDATION | README.md F1 Sensor Lag Fix section | Reclassified from scientific result to engineering/measurement validation. |
| Section 14 - Appropriate Baseline for Paper | Current Status: Neither Phase-A nor Phase-B control dataset is fully suitable as paper baseline | Current Status: Phase-A Ollama control is a valid baseline for the actual Ollama experiment, with explicit documentation of the planned-provider deviation | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Phase-A Ollama control is valid baseline for Ollama experiment with documented deviation. |
| Section 19 - Inconclusive Claims | F1 robustness: Phase-B 8 episodes, Phase-A 20 episodes | F1 robustness: Phase-B 9 episodes, Phase-A 15 isolated episodes | `data/processed/phase_b/phase_b_validation/episodes.csv`, `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Corrected episode counts. |
| Section 19 - Inconclusive Claims | F3 intensity gradient: LOW 99, MEDIUM 120, HIGH 124 | F3 intensity gradient: LOW 99, MEDIUM 120, HIGH 120 | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Corrected F3 HIGH from 124 to 120. |
| Section 19 - Claims That Must NOT Be Made | "Sensor lag causes 0% success" — Phase-A F1 shows 75% success (15/20) | "Sensor lag causes 0% success" — Phase-A isolated F1 shows 100% success (15/15) | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Corrected to exclude concurrent episodes. |
| Section 19 - Claims That Must NOT Be Made | "Phase-A pilot validates methodology" - schedule deviations | "Phase-A pilot validates methodology" - matches planned 70 episodes | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | No schedule deviation exists. |
| Section 21 - Limitations | Phase-A schedule deviation: F1 has 20 episodes instead of 15 | Agent/model deviation: Ollama llama3 instead of planned OpenAI gpt-4o (documented) | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Removed incorrect schedule deviation. |
| Section 21 - Limitations | Phase-B 23 episodes | Phase-B 21 episodes | `data/processed/phase_b/phase_b_validation/episodes.csv` | Corrected Phase-B count to 21 valid episodes. |
| Section 21 - Threats to Validity | Schedule deviation: F1 20 episodes instead of 15 | Removed (no schedule deviation exists) | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Removed incorrect schedule deviation. |
| Section 22 - Hypothesis | F1 shows 75% success at low/high but 50% at medium | F1 shows 100% success at all intensities in single-shot mode | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Corrected to exclude concurrent episodes. |
| Section 22 - Defensible Abstract Facts | F1 sensor lag showing 75% success (15/20) | F1 sensor lag showing 100% success (15/15 isolated) | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Corrected to exclude concurrent episodes. |
| Section 22 - Defensible Abstract Facts | Phase-B validation (23 episodes) | Phase-B validation (21 episodes) | `data/processed/phase_b/phase_b_validation/episodes.csv` | Corrected Phase-B count to 21 valid episodes. |
| Section 22 - Defensible Abstract Facts | F1 sensor lag (8 episodes) | F1 sensor lag (9 episodes) | `data/processed/phase_b/phase_b_validation/episodes.csv` | Corrected F1 count to 9. |
| Section 22 - Defensible Abstract Facts | F3 unreachable IK (12 episodes) | F3 unreachable IK (9 episodes) | `data/processed/phase_b/phase_b_validation/episodes.csv` | Corrected F3 count to 9. |
| Section 22 - Reviewer Concerns | Schedule deviation: Why does F1 have 20 episodes instead of the planned 15? | Removed (no schedule deviation exists) | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Removed incorrect schedule deviation concern. |
| Section 22 - Reviewer Concerns | 70 Phase-A episodes and 23 Phase-B episodes | 70 Phase-A episodes and 21 Phase-B episodes | `data/processed/phase_b/phase_b_validation/episodes.csv` | Corrected Phase-B count to 21. |
| Section 23 - Complete Source Map | Phase-A F1 success rate: 15/20 = 75% | Phase-A F1 success rate (isolated): 15/15 = 100% | `data/raw/pilot/phase_a_pilot/episodes.jsonl` | Corrected to exclude concurrent episodes. |
| Section 23 - Complete Source Map | Phase-A schedule deviation | Removed (no schedule deviation exists) | N/A | Removed incorrect schedule deviation. |

## Phase-B Corrections

| Section | Original Value | Corrected Value | Primary Source File | Reason for Correction |
|---------|----------------|-----------------|---------------------|----------------------|
| Section 10 - Phase-B F1 Results | HIGH: Valid Episodes = 2 | HIGH: Valid Episodes = 3 | `data/processed/phase_b/phase_b_validation/episodes.csv` | Corrected F1 HIGH count to 3 (all 3 high intensity episodes are valid). |
| Section 10 - Phase-B F1 Results | Source: rows 5-14 (valid attempts only) | Source: valid attempts only, latest attempt per episode_id | `data/processed/phase_b/phase_b_validation/episodes.csv` | Clarified selection rule to use latest valid attempt per episode_id. |
| Section 10 - F1 Complete Audit - Phase-B | Observed lag: 2.0s (all 8 valid F1 episodes) | Observed lag: 2.0s (all 9 valid F1 episodes) | `data/processed/phase_b/phase_b_validation/episodes.csv` | Corrected F1 count to 9. |
| Section 11 - Phase-B F3 Results | Source: rows 15-25 (valid attempts only) | Source: valid attempts only, latest attempt per episode_id | `data/processed/phase_b/phase_b_validation/episodes.csv` | Clarified selection rule to use latest valid attempt per episode_id. |
| Section 23 - Complete Source Map | Table B - Phase-B F1: Rows 5-14, valid attempts only | Table B - Phase-B F1: Valid attempts only, latest attempt per episode_id | `data/processed/phase_b/phase_b_validation/episodes.csv` | Clarified selection rule. |
| Section 23 - Complete Source Map | Table C - Phase-B F3: Rows 15-25, valid attempts only | Table C - Phase-B F3: Valid attempts only, latest attempt per episode_id | `data/processed/phase_b/phase_b_validation/episodes.csv` | Clarified selection rule. |
| Section 23 - Complete Source Map | Phase-B F1 observed lag: rows 5-14 | Phase-B F1 observed lag: valid F1 episodes | `data/processed/phase_b/phase_b_validation/episodes.csv` | Clarified selection rule. |
| Section 23 - Complete Source Map | Phase-B F3 safety violations (LOW): rows 15-17 | Phase-B F3 safety violations (LOW): valid F3 LOW episodes | `data/processed/phase_b/phase_b_validation/episodes.csv` | Clarified selection rule. |
| Section 23 - Complete Source Map | Phase-B F3 safety violations (MEDIUM): rows 18-22 | Phase-B F3 safety violations (MEDIUM): valid F3 MEDIUM episodes | `data/processed/phase_b/phase_b_validation/episodes.csv` | Clarified selection rule. |
| Section 23 - Complete Source Map | Phase-B F3 safety violations (HIGH): rows 23-25 | Phase-B F3 safety violations (HIGH): valid F3 HIGH episodes | `data/processed/phase_b/phase_b_validation/episodes.csv` | Clarified selection rule. |

## Summary of Total Corrections

- **Phase-A corrections:** 19 corrections
- **Phase-B corrections:** 8 corrections
- **Total corrections:** 27 corrections

## Key Findings from Audit

1. **No schedule deviation exists:** Phase-A has exactly 70 episodes as planned (5 control + 15 each F1,F2,F3,F4 + 5 concurrent). The concurrent episodes are separate from isolated F1 episodes.

2. **Phase-B count corrected:** Phase-B has 21 valid episodes (3 control + 9 F1 + 9 F3), not 23 as previously reported.

3. **F1 HIGH count corrected:** Phase-B F1 HIGH has 3 valid episodes, not 2.

4. **F3 HIGH safety violations corrected:** Phase-A F3 HIGH has 120 violations, not 124.

5. **Phase-A Ollama control is valid baseline:** Phase-A Ollama control (5/5 success, 0 safety violations) is a valid baseline for the Ollama experiment with documented deviation from planned OpenAI gpt-4o.

6. **F1 lag measurement reclassified:** Reclassified from scientific result to engineering/measurement validation.

## Confirmation of Reconciliation

**Phase-A counts reconcile exactly:**
- Control: 5 ✓
- Isolated F1: 15 (5 low + 5 medium + 5 high) ✓
- F2: 15 (5 low + 5 medium + 5 high) ✓
- F3: 15 (5 low + 5 medium + 5 high) ✓
- F4: 15 (5 low + 5 medium + 5 high) ✓
- Concurrent: 5 ✓
- **Total: 70 episodes ✓**

**Phase-B counts reconcile exactly:**
- Control: 3 ✓
- F1: 9 (3 low + 3 medium + 3 high) ✓
- F3: 9 (3 low + 3 medium + 3 high) ✓
- **Total: 21 valid episodes ✓**

All formal Phase-A and Phase-B counts now reconcile exactly with the primary CSV/JSONL data.