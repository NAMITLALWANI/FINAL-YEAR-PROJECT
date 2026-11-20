<!-- Draft v0.1 saved verbatim as received on 20 November 2026. Not edited. Findings and proposed changes are in INTEGRATED_PROTOCOL_CONSISTENCY_REVIEW.md. -->

# HAMMER — Integrated Evaluation Protocol and Open-Items Register

**Document type:** Internal research protocol  
**Status:** Draft for cross-decision consistency review  
**Scope:** Integration of Decisions A, B and C  
**Authority:** The three approved decision records. This document consolidates them; it does not supersede or amend them.

---

## 1. Purpose and governing principles

This document integrates the approved design decisions for the HAMMER evaluation into one coherent protocol. It establishes the sequence of evaluation activities, the relationship between independent labels and benchmark-derived labels, the blinded review process, the sampling and statistical design, and the outstanding operational decisions.

The protocol must preserve these principles:

1. Work-level publication matching and person-level author identity resolution remain separate tasks.
2. Retrieval quality and selective-resolution quality are evaluated separately.
3. Benchmark-derived ORCID agreement is not represented as independent ground truth.
4. Verified results and benchmark-derived results are reported separately.
5. Candidate retrieval, resolver decisions, reviewer judgments and adjudicated labels retain separate provenance.
6. Automatic assignment, manual review, unresolved outcomes, empty retrieval, provider failure and no-defined-score outcomes remain distinguishable.
7. All parameters that remain provisional must be selected and documented before the relevant evaluation freeze.
8. No test-informed changes are made after the sealed evaluation is inspected. A changed protocol requires a new version and an appropriately independent evaluation.

## 2. Decision authority and status

| Decision | Subject | Status | Governing rule |
|---|---|---|---|
| A | Label strategy and audit population | Locked | Use the approved label strategy and its defined audit population. |
| B | Evidence dossiers, blinding and independent review | Approved | Use the approved two-stage blinded dossier design and leakage controls. |
| C | Sampling, estimands, inference and coverage-based sizing | Locked as revision 3 | Apply C1–C9 as written. Numerical thresholds and operational parameters remain provisional. |

This protocol does not reopen the substance of A, B or C. If integration reveals an apparent conflict, it must be entered in the open-items register and resolved through an explicit clarification or amendment to the relevant decision record.

## 3. Evaluation populations and label basis

### 3.1 Primary evaluation pair

The primary evaluation pair is:

- **Condition:** C1
- **Policy:** `selective_policy_v2`

Only automatic assignments produced by this primary pair define the primary automatic-assignment population for verified precision.

Other conditions and policies remain secondary or exploratory according to the locked decisions. Their results must not be substituted for the primary pair.

### 3.2 Label categories

The evaluation distinguishes:

- **Verified labels:** identities established through the approved independent review and adjudication process.
- **Benchmark-derived labels:** provisional ORCID-based identity mappings supplied by LAGOS-AND.
- **Uncertain labels:** cases for which the review process cannot establish a sufficiently definite identity.
- **Unverifiable cases:** cases for which the required independent evidence cannot be accessed or established.

Uncertain and unverifiable cases must remain visible in case accounting. Their exclusion from a primary verified metric must not make them disappear from reporting. Apply the approved all-wrong/all-right sensitivity bracket to verified rates.

Benchmark-derived ORCID agreement must never be described as independently verified identity accuracy.

### 3.3 Benchmark scope

The evaluation frame is restricted to eligible LAGOS-AND blocks. It excludes blocks with more than eight ORCID groups and blocks that fail the eligibility criteria.

Consequently, the study concerns a restricted benchmark-defined population of ambiguous author blocks. It does not establish performance across all author names or across the most ambiguous homonym cases excluded by the block-size restriction.

### 3.4 Retrieval and identity resolution

The following are distinct evaluation questions:

- **Retrieval:** Did the candidate pool contain a profile that could be mapped to the intended person?
- **Resolution:** Did HAMMER select that person automatically, send the case for manual review, or leave it unresolved?

A retrieval failure must not be reclassified as a resolver abstention. Successful empty retrieval and provider failure remain separate outcomes.

## 4. Decision A — label strategy and audit population

### 4.1 Primary label strategy

Decision A governs the construction and use of the independent-label evidence.

The primary verified precision analysis is restricted to automatic assignments from C1 with `selective_policy_v2`.

The audit is associated with the non-automatic population of that same primary pair. Its error estimate must not be transferred to:

- automatic assignments;
- other context conditions;
- other decision policies;
- the overall retrieval estimate;
- the full benchmark population.

The audit error rate is not a general correction factor for benchmark-derived retrieval results.

### 4.2 Reporting classes

Every case must receive exactly one reporting class under Decision A. The final protocol implementation must preserve the approved class definitions and the predeclared stratum-merging rule.

Where allocation or rounding is required, use the approved largest-remainder procedure and the prescribed hash ordering within strata. Do not change strata after observing outcomes.

### 4.3 Audit interpretation

The verified non-automatic audit describes only the population from which it is drawn. It does not validate automatic assignments and cannot be used to correct the benchmark-derived overall retrieval result.

**Integration clarification required:** Decision A is recorded as requiring an audit of the entire non-automatic frame, whereas Decision C describes a random non-automatic audit sample. The final operational protocol must state whether A means a census of all non-automatic cases or defines the frame from which a random audit sample is drawn. Until clarified, neither interpretation is assumed here.

## 5. Decision B — blinded evidence dossiers and review

### 5.1 Review design

Use the approved two-stage blinded process.

**Stage A — identity establishment**

Reviewers establish the intended identity from the benchmark group's publication evidence and independent external evidence, before being shown candidate profiles.

The review must test group purity rather than assume that all publications assigned to a benchmark group belong to one person.

**Stage B — candidate mapping**

Reviewers assess the shuffled, redacted candidate profiles against the identity established in Stage A.

The task is to determine whether each candidate is the same person, a different person, or cannot be determined from available evidence.

### 5.2 Dossier construction and leakage controls

The dossier process must preserve the approved safeguards:

- Do not include the expected benchmark ORCID.
- Remove ORCID strings and ORCID URLs from candidate material, including raw payload-derived material and works authorship data.
- Remove HAMMER scores, ranks, signal sets, selected-candidate indicators and decision outcomes.
- Shuffle candidate profiles and assign opaque candidate identifiers.
- Remove dataset group identifiers, block identifiers, split membership and provider ordering.
- Keep the opaque-ID crosswalk separate from reviewer-facing materials.
- Generate packets through a reproducible script; do not manually edit individual packets.
- Record residual leakage risks, including ORCID information reviewers may independently encounter during external searches.

### 5.3 External research and evidence logging

Use the approved fixed dossier as the starting material. Limited external research is permitted under the approved design and must be logged.

Reviewers must record evidence references, searches performed, confidence, rationale and whether they encountered an ORCID. Reviewer time should be recorded as specified in the approved design.

### 5.4 Independent judgments and adjudication

Reviewers work independently. Their initial judgments must be retained separately.

A third adjudicator reviews disagreements and records the final adjudication and rationale. The final label must not overwrite the original reviewer judgments.

Report reviewer agreement and adjudication outcomes. Interpret agreement statistics cautiously where the number of reviewed cases is small.

### 5.5 Reviewer independence

Reviewers should not be HAMMER developers or people who have already seen HAMMER outputs. The preferred reviewer pool is outside peers, not project members.

Names, availability, reviewer capacity and other personnel requirements remain deferred until the end, as agreed. This protocol does not assume that reviewers have been recruited.

## 6. Decision C — sampling and statistical design

### 6.1 Primary sampling unit

The confirmatory sample uses one hash-selected primary case per eligible block. Other eligible groups from the same block are retained only for the approved secondary analysis.

The primary case is selected using the locked hash-based rule. The sampling unit and its inclusion probability must be preserved in the sampling manifest.

### 6.2 Estimands and weights

- **E1** is the primary estimand, with block-level sampling weights \(N_h/n_h\).
- **E2** is the secondary estimand, with weights \((N_h/n_h)g_i\).

The primary and secondary estimands must not be conflated. The report must identify which estimand each estimate represents.

### 6.3 Strata and allocation

Use the locked S, M, L and XL strata based on unique DOI counts.

Apply the approved proportional allocation procedure, including floors, census caps, largest-remainder allocation and iterative redistribution. Census strata are treated according to the locked rule.

No stratum boundary or allocation rule may be changed after outcomes are observed.

### 6.4 Evaluation frame

The main evaluation frame is the eligible test split after excluding:

- blocks used in the earlier smoke capture;
- blocks reserved for the coverage pilot.

The main sample uses a new seed at the appropriate freeze point and sampling without replacement. The exact frame counts and selected cases have not yet been computed.

### 6.5 Inference

Apply the three inference regimes defined in Decision C:

- **R1:** stratum-level exact binomial intervals as conservative superpopulation approximations under their stated assumptions.
- **R2:** the approved pooled, frame-weighted stratified bootstrap for quantities that support it.
- **R3:** sparse automatic-precision reporting using counts and exact intervals, without a bootstrap that would produce misleading degenerate intervals.

The numerical diagnostics and minimum thresholds remain provisional. The final protocol must state the chosen values before freeze.

The beta-binomial predictive distribution used for sizing is a superpopulation approximation. Its lower-tail conservatism is not guaranteed. The lower-confidence-bound sensitivity calculation is a separate planning check under its stated assumptions.

### 6.6 Endpoints and metric-specific denominators

Every case remains in overall case accounting and receives exactly one outcome category:

1. automatic;
2. manual;
3. unresolved;
4. empty retrieval;
5. provider failure;
6. no defined score.

Not every case belongs in every metric denominator. Apply the metric-specific denominators in Decision C7.

Primary endpoints include:

- automatic coverage;
- verified automatic precision and selective risk;
- benchmark-derived overall retrieval measures, including candidate-pool mapping rate and end-to-end retrieval measures.

Conditional retrieval metrics and end-to-end retrieval metrics must remain separate. A metric calculated only among cases with a mapped profile must not be presented as if it used all resolved cases.

Verified retrieval results must be reported separately for automatic assignments and the random non-automatic audit sample. Do not pool these groups or use the audit error rate as a correction factor.

### 6.7 Secondary block-level analysis

Retain secondary cases only for the exploratory C8 analysis. Apply the approved block-level cluster bootstrap and associated diagnostics.

Do not treat multiple cases from the same block as independent observations.

### 6.8 Coverage pilot and predictive sizing

The coverage pilot is drawn from reserved test blocks, disjoint from the main evaluation sample.

Its purpose is to estimate automatic coverage under the exact primary pair: C1 with `selective_policy_v2`.

The approved stratified predictive sizing procedure must be followed. It carries pilot uncertainty into the predicted automatic count in the main sample and includes the separate lower-confidence-bound sensitivity calculation.

The pilot is not authorised for execution by this protocol draft. Its size, allocation, parameters, budget and seed remain open.

## 7. Integrated order of operations

The following sequence combines the locked designs without authorising their execution.

| Stage | Activity | Required output or condition |
|---|---|---|
| 1 | Confirm the integrated protocol and resolve cross-decision contradictions | One internally consistent protocol; locked decisions remain unchanged unless explicitly amended |
| 2 | Resolve non-personnel operational parameters | Final thresholds, allocation parameters, inference rules, sizing inputs and cost ceiling |
| 3 | Resolve personnel requirements at the end | Reviewer/adjudicator availability, capacity and agreed workload |
| 4 | Freeze the relevant software, policy, weights, configuration and protocol versions | Versioned implementation and configuration manifest |
| 5 | Define and draw the coverage pilot from reserved test blocks | Pilot sampling manifest; no overlap with smoke or main sample |
| 6 | Execute the separately authorised label-free coverage pilot | Captured outcomes and reproducible pilot artifacts |
| 7 | Calculate the main sample size using the locked predictive procedure | Sizing calculation, assumptions, sensitivity result and selected sample size |
| 8 | Define the main test frame excluding smoke and pilot blocks | Frame manifest and eligibility counts |
| 9 | Draw the main sample and preserve the sampling manifest | Frozen primary cases, strata, weights and seed |
| 10 | Prepare and review Stage A identity dossiers | Independent identity judgments and adjudicated labels |
| 11 | Capture candidate retrieval responses under the approved budget | Raw provider responses, timestamps, hashes and ordered candidate pools |
| 12 | Prepare and review Stage B candidate dossiers | Blinded candidate mappings and adjudications |
| 13 | Freeze predictions, evidence snapshots and analysis inputs | Reproducible run and analysis manifests |
| 14 | Unseal and analyse according to the predeclared plan | Metric tables, intervals, exclusions and sensitivity analyses |
| 15 | Update the manuscript from verified artifacts | Claims traceable to frozen outputs and approved denominators |

This sequence is a dependency plan, not permission to perform any stage.

## 8. Open-items register

### 8.1 Cross-decision clarification

| ID | Item | Current status | Required resolution |
|---|---|---|---|
| X-01 | Decision A audit of the entire non-automatic frame versus Decision C random audit sample | **Clarification required** | Confirm whether the audit is a census or a sample from the non-automatic frame. Record the interpretation in the relevant decision record without silently changing its scope. |

### 8.2 Statistical and sampling parameters

| ID | Item | Status |
|---|---|---|
| C-O1 | Minimum stratum size for bootstrap resampling | Open |
| C-O2 | Negligible-weight rule for a pooled estimand | Open; if adopted, must be predeclared and the resulting estimand relabelled |
| C-O3 | Final sampling-fraction diagnostic threshold | Provisional |
| C-O4 | Final sparse automatic-count warning | Provisional |
| C-O5 | Final sparse error-count warning | Provisional |
| C-O6 | Final C8 contributing-block warning | Provisional |
| C-O7 | Pilot size and allocation by stratum | Open |
| C-O8 | Main sample size \(N\) | Open |
| C-O9 | Target automatic count \(m\) and adjusted target \(m'\) | Open |
| C-O10 | Predictive sizing probability parameter \(\beta\) | Open |
| C-O11 | Lower-bound sensitivity parameter \(\gamma\) | Open |
| C-O12 | Allocation floors and census handling inputs | Open where not fixed by the locked C3 algorithm |
| C-O13 | Predictive prior specification and sensitivity prior | Open |
| C-O14 | Maximum search value \(N_{\max}\) | Open |
| C-O15 | New pilot and main-study seeds | Open; must be recorded at the appropriate freeze point |
| C-O16 | Exact eligible test-frame counts and resulting allocation | Not computed; computation is not authorised by the decision lock |

### 8.3 Dossier and review operations

| ID | Item | Status |
|---|---|---|
| B-O1 | Reviewer and adjudicator names | Deferred to end |
| B-O2 | Reviewer independence confirmations | Deferred to end |
| B-O3 | Reviewer availability and capacity | Deferred to end |
| B-O4 | Reviewer time and total workload feasibility | Deferred to end |
| B-O5 | Pilot review cases and workflow feasibility | Open; no cases selected |
| B-O6 | Candidate dossier builder and automated leakage scan | Not implemented or run |
| B-O7 | Final dossier schema and validation | To be checked before packet creation |

### 8.4 Provider and execution budget

| ID | Item | Status |
|---|---|---|
| P-O1 | Provider-request budget | Open |
| P-O2 | Monetary cost ceiling | Open |
| P-O3 | Request-count ceiling and per-case request assumptions | Open |
| P-O4 | Candidate works/enrichment capture scope and page limits | Open |
| P-O5 | Stop conditions for provider errors, rate limits and unexpected cost | Must be specified before authorised capture |

### 8.5 Manuscript integration

| ID | Item | Status |
|---|---|---|
| M-O1 | Integrate the final A/B/C protocol into the manuscript methodology and experimental design | Not started |
| M-O2 | Align metric definitions and denominators with C7 | Not started |
| M-O3 | State the benchmark scope and label circularity limitations | Not started |
| M-O4 | Document the audit population and its limited interpretation | Blocked by X-01 clarification |
| M-O5 | Report all thresholds and parameters actually frozen | Blocked until operational values are selected |
| M-O6 | Write results, discussion and claims only from verified evaluation artifacts | Not started |

## 9. Freeze requirements

The evaluation must not be described as frozen until the relevant prerequisites have been completed and recorded.

At minimum, the freeze package must identify:

- protocol and decision-record versions;
- eligible frame and exclusions;
- sampling strata, allocation, inclusion probabilities and weights;
- seeds and selected cases;
- pilot and main sample separation;
- reviewer and adjudicator arrangements;
- label rubric and adjudication procedure;
- dossier generation and leakage checks;
- software revision, dirty state, dependencies and effective configuration;
- resolver thresholds, weights and policy;
- provider-request and cost limits;
- raw response and evidence snapshot hashes;
- metric definitions, denominators and interval procedures;
- predictive sizing calculation and sensitivity result.

A freeze does not retroactively authorise earlier work. Every action must have its own approval where required.

## 10. Explicitly not authorised by this document

This integrated draft does not authorise:

- writing or running the sample selector;
- computing test-frame counts;
- drawing pilot or main samples;
- making provider requests;
- generating candidate or identity dossiers;
- recruiting or assigning reviewers;
- changing code, thresholds, weights or resolver policy;
- changing the benchmark or labels;
- editing the manuscript;
- starting the main evaluation;
- declaring the evaluation frozen.

The decisions define the approved research design. The operational work remains subject to the open-items register and the required authorisations.

## 11. Change control

This document is a consolidation layer, not a replacement for Decisions A, B or C.

If an open item is resolved, record the selected value, rationale, date and approving authority. If the resolution changes a locked design, update the relevant decision record through an explicit amendment and preserve its previous version.

Do not silently edit a locked decision by changing only this integrated document.

---

**Current status:** Decisions A, B and C are recorded as settled designs. Decision C is locked as revision 3. Operational parameters remain open. No selector, pilot, provider capture, dossier generation, manuscript integration or evaluation freeze has been authorised or performed by this draft.
