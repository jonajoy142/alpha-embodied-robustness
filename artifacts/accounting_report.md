# Episode Attempt Accounting Report

## 1. Overview
- **Total Raw Attempts Ingested**: 169
- **Accepted Episodes**: 70 (41.4%)
- **Rejected Attempts**: 99 (58.6%)

## 2. All-Attempts vs. Accepted Reliability

| Metric | All Attempts (N=169) | Accepted Episodes (N=70) | Impact / Bias |
| :--- | :--- | :--- | :--- |
| **Crash Rate** | **58.6%** (99/169) | **0.0%** (0/70) | Discarding OpenAI runs masked a 57%+ abort/crash rate |
| **Success Rate** | **11.8%** (19/169) | **28.6%** (19/70) | Paper reported 28.6% by omitting failed client invocations |

## 3. Discarded Records Breakdown (N=99)

| Rejection Reason | Count | Root Cause | Defined Timing |
| :--- | :--- | :--- | :--- |
| `openai_runtime_error` | 70 | OpenAI client initialization exception / missing key runtime failure | Post-hoc filtering after failed API execution |
| `openai_quota_exceeded_429` | 26 | OpenAI HTTP 429 quota exhaustion (`insufficient_quota`) | Post-hoc filtering after failed API execution |
| `openai_zero_step_abort` | 3 | Zero-step early invocation termination before simulation started | Post-hoc filtering after failed API execution |

## 4. Per-Agent Breakdown

| Agent / Runtime | Model | Attempts | Crashes / Aborts | Successes | Crash Rate | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `openai` | `gpt-4o` | 99 | 99 | 0 | 100.0% | 0.0% |
| `ollama` | `llama3` | 70 | 0 | 20 | 0.0% | 28.6% |

## 5. Accepted Episodes by Fault Condition (Ollama / llama3)

| Fault Type | Episodes | Successes | Success Rate |
| :--- | :--- | :--- | :--- |
| `none` | 5 | 5 | 100.0% |
| `sensor_lag` | 20 | 15 | 75.0% |
| `grip_slip` | 15 | 0 | 0.0% |
| `unreachable_ik` | 15 | 0 | 0.0% |
| `planner_output_corruption` | 15 | 0 | 0.0% |

## 6. Discard Rule Evaluation & Scientific Integrity Assessment
- **Rule Definition Timing**: Post-hoc. The 99 runs were attempted with OpenAI; when quota/connection failed, the author switched to Ollama and silently omitted the OpenAI logs.
- **Bias Impact**: Severe if reporting 'agent reliability' or 'system stability', because claiming 0% crash rate is demonstrably false when external API infrastructure fails 100% of the time.
- **Defensible Revision**: In the revised paper, both all-attempt (infrastructure reliability) and accepted-cohort (planner execution given complete environment connection) must be reported side-by-side with full transparency.