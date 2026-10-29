# Empirical Chaos Harness Pilot Gate Report (G1–G8)

| Gate | Name | Status | Metric | Threshold | Details |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **G1** | Plan Generation Schema Validity | **PASSED** | 1.00 | 1.00 | 10/10 plans generated with valid ActionPlan schema and actions |
| **G2** | Control Execution Baseline Reliability | **PASSED** | 1.00 | 0.90 | 10/10 control episodes completed successfully |
| **G3** | Fault Injection Delivery Verification | **PASSED** | 1.00 | 1.00 | 20/20 fault injections verified at designated hooks |
| **G4** | Safety Monitor Determinism | **PASSED** | 1.00 | 1.00 | Violation counts across 5 replays: [1, 1, 1, 1, 1] (identical=True) |
| **G5** | F1 Dynamic Sensor Lag Divergence | **PASSED** | 1.00 | 1.00 | 5/5 trials showed measurable Euclidean staleness divergence > 1mm |
| **G6** | F2 Grip Slip Graduation Monotonicity | **PASSED** | 1.00 | 1.00 | Calibrated probabilities: Low=0.3805, Med=0.661, High=0.95 (monotonic=True) |
| **G7** | F3 IK Offset Graduation Monotonicity | **PASSED** | 1.00 | 1.00 | Calibrated offsets: Low=0.1191m, Med=0.2082m, High=0.3m (monotonic=True) |
| **G8** | Continuation Planning Monotonic Progress | **PASSED** | 1.00 | 1.00 | 5/5 continuation plans omitted completed pick/grip steps |

**Overall Pilot Gate Status**: ALL GATES PASSED