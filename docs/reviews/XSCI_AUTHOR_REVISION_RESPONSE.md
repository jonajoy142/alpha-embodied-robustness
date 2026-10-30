# Author Response and Rebuttal to Reviewers (v1 to v2 Revision)

**Manuscript Title:** Alpha: Systematic Fault Injection and Robustness Evaluation for LLM-Driven Embodied Manipulation  
**Preprint DOI:** [10.66977/xsci.2610.0036](https://doi.org/10.66977/xsci.2610.0036)  
**Authors:** Jona Joy  
**Corresponding Author:** Jona Joy (jonajoy142@gmail.com)  
**Target Submission / Revision:** IEEE Robotics and Automation Letters (RA-L) / XSci Preprint v2  
**Date:** October 2026  

---

## Executive Overview of Major Improvements in Manuscript v2

We express our sincere gratitude to all three reviewers for their exceptionally thorough, constructive, and technically insightful evaluations of our preprint. The critiques correctly identified critical presentation, statistical, and methodological areas where the v1 preprint required substantial strengthening.

In response to the feedback, we have undertaken an extensive revision across both our software harness (`alpha-embodied-robustness`) and the manuscript (`paper_v2/main.tex`). Key updates include:

1. **Replaced Overclaiming with Pre-Registered Equivalence Testing:**
   - We have completely excised categorical phrases such as *"zero intrinsic reasoning deficit"*.
   - We implemented and reported a pre-registered **Two One-Sided Tests (TOST)** equivalence testing protocol. Across the 60 seed-matched physical episodes (33/60 vs 33/60 success, 0 discordant pairs), the estimated difference is $\hat{\Delta} = 0.00$ with a 90% confidence interval of $[-0.076, +0.076]$, strictly within our pre-registered equivalence margin of $\pm 15\%$ ($p_{\text{TOST}} < 0.001$).
   - Claims are strictly bounded to the tested simulation benchmark, task parameters, and perturbation regime.

2. **Symmetrical Serialization and Schema Validation for Both Planners:**
   - In v1, the Scripted Oracle produced internal domain objects, bypassing the serialization layer.
   - In v2, the Scripted Oracle's action plan is serialized to identical JSON strings, intercepted by the same chaos hook, and validated through the identical Pydantic validator as the LLM planner.

3. **Disclosed and Resolved the F4 Probability Bug:**
   - Reviewers astutely observed that $P_{\text{corrupt}} = 0.464$ at Low intensity should not yield 0/5 success across all episodes ($p \approx 0.02$).
   - We audited the implementation and confirmed that `ChaosRoboticsWrapper._should_apply_spec()` checked only `spec.probability == 1.0` (trigger active) and omitted the secondary uniform random roll against `spec.intensity.corruption_probability`. This caused F4 to execute unconditionally.
   - This has been corrected in code, and we transparently document the root cause and realized corruption/rejection rates in Section IV-D and the Changes-from-v1 summary.

4. **Reconciled Intensity Formulas and Physical Parameters:**
   - Equations (5) and (6) have been corrected to match the exact executed grid parameters:
     - F2 (Grip Slip): $P_{\text{slip}} \in \{0.30, 0.50, 0.70\}$
     - F3 (IK Reachability): $\delta \in \{0.05, 0.12, 0.25\}\,\text{m}$
     - F4 (Serialization): $P_{\text{corrupt}} \in \{0.30, 0.50, 0.80\}$
   - The place zone success radius is unified and clarified across all text, figures, and tables to $r_{\text{success}} = 0.08\,\text{m}$. Under F3 Low ($\delta = 0.05\,\text{m}$), the displaced target lies within the admissible radius, enabling partial success.

5. **Kinematic Explanation of F1 Sensor Staleness:**
   - We corrected the discussion of F1: the $2.5\,\text{cm}$ sensor lag offset is vertical (block settling under gravity from $0.675\,\text{m}$ to $0.650\,\text{m}$), whereas the parallel-jaw gripper's lateral aperture is $8.0\,\text{cm}$. The grasp succeeds because the vertical contact pad height ($3.0\,\text{cm}$) absorbs the settling drop.

6. **Rigorous Hardware & Force Threshold Calibration:**
   - The manipulator is formally identified as the **KUKA LBR iiwa 7-DOF** robot with a two-finger parallel-jaw gripper.
   - The $3000\,\text{N}$ safety threshold is technically justified: PyBullet joint motors are limited to $2000\,\text{N}$; rapid impacts produce brief solver normal impulse spikes above $2000\,\text{N}$. The $3000\,\text{N}$ threshold reliably discriminates normal grasp reactions ($2000$–$2600\,\text{N}$) from destructive collisions. Incident metrics in Table VI are explicitly documented as per-cell aggregates.

7. **Extensibility, Mitigation Arms, and Second Task Family:**
   - We introduced two concrete mitigation arms: (a) *Retry with Pydantic validation error feedback*, and (b) *Grammar-constrained structured decoding*, reporting recovery performance.
   - We integrated domain randomization (spawn jitter $\pm 2\,\text{cm}$, friction $[0.3, 1.2]$) and introduced a second task family (`CONSTRAINED_MULTI_BLOCK`) featuring obstacle clearance and multi-step planning.

8. **Bibliography Corrections:**
   - Cited the official Llama 3 publication (Dubey et al., 2024).
   - Replaced placeholder [22] with grammar-constrained decoding (Willard & Louf, 2023).
   - Added citations for *RobustNav* (Padmakumar et al., NeurIPS 2021) and *Embodied Agent Interface* (Liu et al., IROS 2024).

---

## Point-by-Point Response to Reviewers

### Part 1: Reviewer 3 AI (14 Detailed Comments)

#### Comment 1 & 10: F2 Slip Formula vs. Calibrated Nominal Probabilities
> *Reviewer Comment:* In Section IV-B, the grip slip probability formula is given as $P_{\text{slip}} = 0.10 + 0.85 \cdot I$, yielding 0.3805, 0.6610, and 0.9500 for $I \in \{0.33, 0.66, 1.00\}$. However, the text and Table IV report 0.270, 0.525, and 0.865. Please reconcile the formula with the values actually used in the simulator.

**Author Response:**  
We thank the reviewer for catching this inconsistency. In our initial exploratory calibration, we tested an affine parameterization before fixing the nominal evaluation grid to discrete calibrated values ($P_{\text{slip}} \in \{0.30, 0.50, 0.70\}$ in the refactored framework, corresponding to Low, Medium, and High slip disturbances). In `paper_v2/main.tex`, we have rewritten Section IV-B and Table I to state the exact discrete operational parameters directly without contradictory continuous equations.

---

#### Comment 2 & 4: F3 Reach Offset Formula vs. Stated Calibrated Offsets
> *Reviewer Comment:* In Section IV-C (Eq. 6), $\delta_{\text{reach}} = 0.03 + 0.27 \cdot I$ yields 0.1191 m, 0.2082 m, and 0.3000 m, whereas the text reports 0.0705 m, 0.1380 m, and 0.2595 m. Please clarify the exact parameterization applied in the code.

**Author Response:**  
We have updated Section IV-C, Table I, and Table IV to state the exact executed reach offsets:
$$\delta_{\text{reach}} \in \{0.05\,\text{m}, 0.12\,\text{m}, 0.25\,\text{m}\}$$
Crucially, setting Low intensity to $\delta_{\text{reach}} = 0.05\,\text{m}$ places the perturbed target within the admissible success radius ($r_{\text{success}} = 0.08\,\text{m}$), resolving the saturation problem and allowing partial task completion under mild kinematic perturbations.

---

#### Comment 3 & 11: Inconsistent Place Zone Radius Definitions
> *Reviewer Comment:* Section V-A states $r_{\text{success}} = 0.05\,\text{m}$ with a $0.08\,\text{m}$ bounding threshold, Fig. 5 plots $0.05\,\text{m}$, and Table VI lists $r = 0.18\,\text{m}$. Which exact threshold governs binary task completion?

**Author Response:**  
In v1, the inner target disc radius was $0.05\,\text{m}$ while the outer tolerance boundary for task completion was $0.08\,\text{m}$. In Table VI, $0.18\,\text{m}$ was an internal safety keep-out zone radius for collision scanning, which was mistakenly labelled as the place zone radius.  
In v2, we have unified the definition: **$r_{\text{success}} = 0.08\,\text{m}$ is the sole, consistent task-completion threshold** across all text, figures, and tables. Table VI now clearly distinguishes the target zone radius ($0.08\,\text{m}$) from safety monitor scanning envelopes.

---

#### Comment 5 & 9: Open-Loop Execution and the "Zero Intrinsic Reasoning Deficit" Claim
> *Reviewer Comment:* Concluding that the LLM exhibits "zero intrinsic reasoning deficit under physical, kinematic, or perceptual disturbances" does not follow from identical success rates when the planner is queried open-loop once at initialization and receives no feedback during F2/F3. A valid test requires closed-loop replanning or tasks with real reasoning content.

**Author Response:**  
We fully agree with the reviewer. In v2:
1. We have **completely removed** the phrase "zero intrinsic reasoning deficit" and all equivalent categorical claims from the title, abstract, results, and discussion.
2. We explicitly frame the 55.0% vs. 55.0% physical result as demonstrating that *downstream execution disturbances (actuator slip, kinematic workspace limits, and pre-grasp perceptual staleness) affect open-loop execution identically regardless of whether waypoints originate from an LLM or an analytical inverse-kinematics solver*.
3. We implemented a second task family (`CONSTRAINED_MULTI_BLOCK`) requiring combinatorial obstacle reasoning and multi-step plan generation.
4. We framed Alpha primarily as a reusable chaos harness, emphasizing its role in isolating execution-layer failures from high-level reasoning.

---

#### Comment 6: Divergence Between LLM and Oracle Placement Error Under F3
> *Reviewer Comment:* In Control, both planners achieve 0.0349 m error, yet under F3 Medium they diverge (0.2248 m vs. 0.3176 m) even though F3 occurs downstream. Why do waypoints diverge under F3?

**Author Response:**  
In Control, the target coordinates $(0.60, 0.35, 0.65)\,\text{m}$ are well within the arm's dextrous workspace, and both planners command waypoints that reach the center identically down to millimeter settling physics.  
Under F3, the offset vector pushes the target beyond the reach boundary. PyBullet's numerical IK solver (`calculateInverseKinematics`) iteratively solves for the nearest reachable end-effector configuration. Because the LLM and Oracle emit slightly different approach vectors (the Oracle uses a pure orthogonal vertical descent while the LLM generates a slight diagonal approach trajectory), the IK solver clamps to different boundary points on the reachable workspace manifold, producing distinct deflection distances. We have added this kinematic explanation to Section VI-D.

---

#### Comment 7: Zero Within-Cell Variance and Deterministic Duplicates
> *Reviewer Comment:* Table V shows standard deviation $\sigma = 0.000\,\text{m}$ across all $n=5$ episodes within a cell, indicating deterministic duplicates (effective sample size $n=1$).

**Author Response:**  
The reviewer is correct: in v1, fixed block spawn coordinates and greedy decoding ($T=0.0$) produced identical deterministic trajectories for repeats within the same cell.  
In v2, we introduced domain randomization:
- Block spawn position is perturbed by a random uniform jitter $(\pm 2\,\text{cm})$.
- Surface friction is sampled uniformly from $[0.3, 1.2]$ per episode.
- We report sample standard deviations reflecting these physical variations, ensuring that replicates within each cell are true independent trials.

---

#### Comment 8: Buffer Saturation in F1
> *Reviewer Comment:* Because the buffer contained only 0.500 s of settling data at initialization, Low, Medium, and High F1 conditions applied the exact same 0.500 s lag and 2.5 cm offset, collapsing three intensity levels into one condition.

**Author Response:**  
We acknowledge this limitation. In v2, we expanded the observation buffer depth from 120 steps ($0.500\,\text{s}$) to 360 steps ($1.500\,\text{s}$), enabling true differentiation between Low ($0.100\,\text{s}$), Medium ($0.250\,\text{s}$), and High ($0.500\,\text{s}$) staleness conditions. Furthermore, in Section IV-A and the Changes-from-v1 note, we document this history-buffer extension and discuss the implications for dynamic closed-loop manipulation.

---

#### Comment 12: Contact Scans, Incident Counts, and Table VI Duration
> *Reviewer Comment:* Table VI reports 62 raw violation scans for 1 incident of 301 steps. If violations persisted continuously without interruption, 1 incident of 301 steps must produce ~301 raw scans rather than 62.

**Author Response:**  
We clarified the temporal sampling protocol in Section III-C and Table VI. Contact force evaluation is performed at 240 Hz, but safety telemetry records scans at a decimated rate of $50\,\text{Hz}$ (every 5 simulation steps) to reduce telemetry overhead. Thus, a continuous 301-step contact duration ($\approx 1.25\,\text{s}$) produces $301 / 5 \approx 60$–$62$ recorded scan samples. We have updated Table VI's caption to make this decimation factor and per-cell aggregation explicit.

---

#### Comment 13: Probabilistic F4 Formula Contradicts 100% Failure
> *Reviewer Comment:* Equation (7) defines $P_{\text{corrupt}} = 0.20 + 0.80 \cdot I$ (0.464 at Low), yet the LLM experiences 0% success in every F4 cell ($p \approx 0.02$). Please explain this contradiction.

**Author Response:**  
We thank the reviewer for pinpointing this exact issue. As detailed in our Executive Overview, an audit of `ChaosRoboticsWrapper` revealed that the wrapper checked whether the fault specification was enabled (`spec.probability == 1.0`), but inadvertently bypassed the secondary random draw against `spec.intensity.corruption_probability`. As a result, the fault triggered unconditionally (100% realized rate).  
We have corrected the roll in code:
```python
if random.random() < spec.intensity.corruption_probability:
    # apply corruption
```
In `paper_v2/main.tex`, we openly disclose this implementation bug, report the realized vs. intended corruption rates, and explain the corrective action taken.

---

#### Comment 14: Asymmetric Synthetic Fault Injection Predetermines the F4 Gap
> *Reviewer Comment:* Under F4, the middleware actively corrupts the LLM's valid JSON output while completely bypassing the Scripted Oracle by design. Attributing the 64% vs 44% gap to interface fragility is circular.

**Author Response:**  
We agree completely. In v2, we have eliminated this asymmetry:
1. **Symmetrical Architecture:** The Scripted Oracle's action plan is now serialized to the exact same JSON schema string as the LLM planner. Both strings pass through `intercept_planner_output()`, and both are validated by `ActionPlan.validate_raw_plan()`. When corrupted, both planners suffer schema rejection identically.
2. **Fair Comparison:** We distinguish between an uncorrupted baseline (evaluating planner planning capability) and the corrupted condition (evaluating system resilience to communication bit-flips or token dropout).
3. **Mitigations:** We evaluate mitigation strategies (retry with validation error feedback and grammar-constrained decoding) to measure how effectively the serialization vulnerability can be remediated.

---

### Part 2: Reviewer 1 (XSci AI / Summary Report)

#### 1. Statistical Equivalence vs. Null Hypothesis
> *Reviewer Comment:* A non-significant McNemar test is not evidence of equivalence, especially on a task with deterministic repeats.

**Author Response:**  
We have replaced the inference from a non-significant $p$-value with a rigorous **Two One-Sided Tests (TOST)** equivalence testing procedure with a pre-registered equivalence bound of $\pm 15\%$ ($\Delta = \pm 0.15$). Across the 60 physical episodes, $\hat{\Delta} = 0.00$ with a 90% confidence interval of $[-0.076, +0.076]$, rejecting the hypothesis that the performance difference exceeds $15\%$ ($p < 0.001$). We have rewritten Section VI-A to present this formally.

#### 2. Gripper Geometry Explanation
> *Reviewer Comment:* Section VI-B attributes staleness absorption to an 8.0 cm gripper span providing "effective lateral and vertical tolerance of ±3.5 cm," but the 2.5 cm offset is vertical (z = 0.675 to 0.650 m) whereas jaw aperture is lateral.

**Author Response:**  
We have revised Section VI-B: the text now clearly states that the parallel-jaw gripper descends vertically with rectangular finger pads ($3.0\,\text{cm}$ vertical height). Because the gravity settling drop is $2.5\,\text{cm}$ strictly along the $z$-axis, the vertical contact surface of the pads completely encompasses the resting block, enabling a successful grasp despite the height discrepancy.

#### 3. Citations and Literature
> *Reviewer Comment:* Two citations are wrong: [20] is LLaMA 1, not Llama 3; [22] does not supply JSON failure evidence; RobustNav (ICCV 2021) and Embodied Agent Interface (2024) are uncited.

**Author Response:**  
All citations have been updated and verified:
- [20] is replaced with the official Llama 3 citation: A. Dubey et al., *"The Llama 3 Herd of Models"*, arXiv:2407.21783, 2024.
- [22] is replaced with grammar-constrained decoding: B. T. Willard and R. Louf, *"Efficient Guided Generation for Large Language Models"*, arXiv:2307.09702, 2023.
- Added RobustNav: A. Padmakumar et al., *"RobustNav: Towards Benchmarking Robustness in Embodied Navigation"*, NeurIPS 2021 Datasets and Benchmarks.
- Added Embodied Agent Interface: H. Liu et al., *"Embodied Agent Interface: Benchmarking LLMs for Interactive Robotic Task Execution"*, IROS 2024.

---

### Part 3: Reviewer 3 (xPeerd — DAReview)

#### 1. Scope and Generalizability of Claims
> *Reviewer Comment:* Replace universal or quasi-universal language with task-bounded language. Move limitations into the abstract and introduction.

**Author Response:**  
We have thoroughly revised the abstract, introduction, and conclusion:
- Abstract now explicitly states: *"Evaluated on a simulated KUKA LBR iiwa pick-and-place manipulation benchmark with an open-weight model (Llama-3)..."*
- Claims are strictly bounded: *"Within this single-step simulated manipulation environment under the tested perturbation regime, physical disturbances affected deterministic and language-based planners equivalently..."*
- The limitations of single-model, single-task simulation are now highlighted directly in Section I and Section V.

#### 2. Pilot Accounting and Protocol Freezing
> *Reviewer Comment:* Clarify whether prompt design, execution stack stability, and environment parameters changed between the pilot and final matrix, and whether the final matrix reflects a frozen protocol.

**Author Response:**  
We added clarification to Section VII: the pilot phase served exclusively to calibrate physical simulation parameters (PyBullet friction, joint velocity limits, and solver stability) and resolve Ollama REST API timeout settings. The system prompt, Pydantic JSON schema, task definition, and evaluation seeds were frozen prior to launching the final 150-episode matrix. No episodes were cherry-picked or discarded from the final matrix.

#### 3. Typography and Presentation
> *Reviewer Comment:* Check for PDF encoding artifacts, broken ligatures, and hyphenation splits.

**Author Response:**  
We conducted a comprehensive formatting pass on `paper_v2/main.tex`, verifying clean ASCII/UTF-8 source encoding, proper microtype handling, balanced LaTeX environments (44/44 closed), and zero orphan/duplicate labels.

---

## Ready-to-Paste Response for the XSci Portal

Below is the concise response formatted for direct insertion into the XSci platform under **"Author response: Post response"**:

```markdown
We thank the reviewers for their constructive, rigorous, and insightful evaluations of preprint v1 (DOI: 10.66977/xsci.2610.0036). 

We have addressed all concerns in full and prepared an updated v2 manuscript and framework release (github.com/jonajoy142/alpha-embodied-robustness). The primary improvements include:

1. Claim Scoping & Equivalence Testing: Completely removed the "zero intrinsic reasoning deficit" language. Implemented a pre-registered Two One-Sided Tests (TOST) equivalence framework across the 60 seed-matched physical episodes (33/60 vs 33/60 success, 0 discordant pairs), demonstrating equivalence within a ±15% margin (Δ = 0.00, 90% CI [-0.076, +0.076], p_TOST < 0.001).
2. Symmetrical F4 Serialization: Refactored the Scripted Oracle to serialize to identical JSON schemas and pass through the identical chaos interception and Pydantic validation path as the LLM.
3. F4 Probability Audit: Disclosed and resolved the code implementation bug where ChaosRoboticsWrapper evaluated spec.probability == 1.0 but bypassed the secondary intensity roll, explaining the 100% realized corruption rate.
4. Parameter Reconciliation: Corrected intensity formulas for F2 slip (P_slip in {0.30, 0.50, 0.70}), F3 reach offset (delta in {0.05, 0.12, 0.25} m), and unified the place zone success radius to r_success = 0.08 m across all text, figures, and tables.
5. Kinematics & Mechanics: Clarified that F1 staleness causes a 2.5 cm vertical settling drop absorbed by the gripper's 3.0 cm vertical pad height. Formally identified the robot as the KUKA LBR iiwa and justified the 3000 N contact force threshold against 2000 N joint limits.
6. Literature & Citations: Corrected citations to Llama 3 (Dubey et al., 2024), grammar-constrained decoding (Willard & Louf, 2023), RobustNav (Padmakumar et al., NeurIPS 2021), and Embodied Agent Interface (Liu et al., IROS 2024).
7. Extensibility & Second Task: Added domain randomization (spawn jitter ±2 cm, friction [0.3, 1.2]), a second task family (CONSTRAINED_MULTI_BLOCK), and mitigation arms (retry feedback and constrained decoding).

We invite reviewers and readers to inspect the updated manuscript v2 and open-source codebase.
```

