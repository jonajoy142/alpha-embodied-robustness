# Experiment Matrix Summary

| Fault Type | Intensity | Success Rate | Fault Observed Rate | Crash Rate | Episode Safety Violation Rate | Mean Post-Fault Completion Time (sim steps) | Mean Raw Safety Observations | Mean Unique Safety Incidents | Mean First Violation Step | Mean Violation Duration (steps) | Mean Requested F1 Lag | Mean Observed F1 Lag |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| grip_slip | high | 20.0% | 80.0% | 0.0% | 0.0% | N/A | 0.00 | 0.00 | N/A | 0.00 | N/A | N/A |
| grip_slip | low | 60.0% | 40.0% | 0.0% | 0.0% | N/A | 0.00 | 0.00 | N/A | 0.00 | N/A | N/A |
| grip_slip | medium | 40.0% | 60.0% | 0.0% | 0.0% | N/A | 0.00 | 0.00 | N/A | 0.00 | N/A | N/A |
| none | none | 100.0% | 0.0% | 0.0% | 0.0% | N/A | 0.00 | 0.00 | N/A | 0.00 | N/A | N/A |
| planner_output_corruption | high | 0.0% | 100.0% | 0.0% | 0.0% | N/A | 0.00 | 0.00 | N/A | 0.00 | N/A | N/A |
| planner_output_corruption | low | 0.0% | 100.0% | 0.0% | 0.0% | N/A | 0.00 | 0.00 | N/A | 0.00 | N/A | N/A |
| planner_output_corruption | medium | 0.0% | 100.0% | 0.0% | 0.0% | N/A | 0.00 | 0.00 | N/A | 0.00 | N/A | N/A |
| sensor_lag | high | 100.0% | 100.0% | 0.0% | 0.0% | 1140.0 | 0.00 | 0.00 | N/A | 0.00 | 1.5 | 0.5 |
| sensor_lag | low | 100.0% | 100.0% | 0.0% | 0.0% | 1140.0 | 0.00 | 0.00 | N/A | 0.00 | 0.6 | 0.5 |
| sensor_lag | medium | 100.0% | 100.0% | 0.0% | 0.0% | 1140.0 | 0.00 | 0.00 | N/A | 0.00 | 1.0 | 0.5 |
| sensor_lag+grip_slip | medium | 40.0% | 100.0% | 0.0% | 0.0% | 1140.0 | 0.00 | 0.00 | N/A | 0.00 | 1.0 | 0.5 |
| unreachable_ik | high | 0.0% | 100.0% | 0.0% | 100.0% | N/A | 124.00 | 2.00 | 960.0 | 602.00 | N/A | N/A |
| unreachable_ik | low | 0.0% | 100.0% | 0.0% | 100.0% | N/A | 62.00 | 1.00 | 960.0 | 301.00 | N/A | N/A |
| unreachable_ik | medium | 0.0% | 100.0% | 0.0% | 100.0% | N/A | 62.00 | 1.00 | 960.0 | 301.00 | N/A | N/A |
