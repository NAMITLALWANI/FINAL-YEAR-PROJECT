# Decision C: statistical design of the main evaluation (revision 3, for final review)

**Date:** 20 November 2026. **Status:** revision 3, incorporating the research director's review of revision 2: two required C9 corrections, provisional status for the numerical thresholds, and one C7 clarification. **LOCKED by the research director on 20 November 2026 as written in revision 3 (see section 6); the items listed as open in section 4 remain open and are not locked.** **No sample size is proposed or approved.** **Read-only:** no manuscript, code, seed, dataset, capture or evaluation artifact was changed, no provider request was made, and the LAGOS archive was not opened. Facts marked *verified* come from `research_data/lagos_and_v2/seed_v1/dataset_quality_report.json`, `sampling_manifest.json`, `backend/hammer_lagos/prep.py` and the Section 5 source. Decisions A and B are approved (`DECISION_A_LABEL_STRATEGY_RECORD.md`, `DECISION_B_DOSSIER_DESIGN_PROPOSAL.md`). The evaluation is unfrozen.

**Personnel deferral (director, 20 November 2026).** Every requirement involving people outside the project is postponed to the end and handled together. This design assumes no reviewer count and no reviewer hours. Reviewer capacity appears only as a named unknown.

## 0. Director's rulings
| Item | Ruling | Where it stands |
|---|---|---|
| C1 One primary case per block, secondary cases kept | Approved | unchanged |
| C2 E1 primary, E2 secondary, corrected weights | Approved | unchanged |
| C3 Proportional allocation, floors, census caps | Approved | unchanged |
| C4 Test split only, smoke blocks excluded | Approved | pilot blocks now also excluded (C9) |
| C5 Inference | Approved in principle | numerical thresholds are provisional diagnostics, not locked (section 2, C5) |
| C6 Verified and benchmark-derived results separated | Approved | unchanged |
| C7 Metric-specific denominators | Approved, with one clarification | scoring of automatic assignments against a verified label is now defined explicitly |
| C8 Exploratory block-clustered analysis | Approved | the 20-block figure is a warning only |
| C9 Sizing and pilot | **Two corrections required** | stratified predictive sizing; pilot drawn from reserved disjoint test blocks |

Still not approved: sample size, *m*, β, pilot size, reviewer capacity, provider budget, pilot execution, seeds, selector implementation and evaluation freeze.

## 1. What the artifacts show (verified)
| Finding | Consequence |
|---|---|
| 80,294 blocks, 70,351 eligible. Exclusions: 2,391 with more than 8 ORCID groups; 7,552 with no group holding two unique DOIs. No block has mixed splits | The frame is fixed by existing code |
| Every eligible block has at least two ORCID groups; blocks above 8 groups are excluded | The study concerns a restricted, benchmark-defined set of ambiguous author blocks (section 3, condition 1) |
| Eligible blocks by size band (unique DOIs: S 0 to 9, M 10 to 49, L 50 to 199, XL 200 or more) over **all splits**: S 32,188; M 33,698; L 4,423; XL 42 | Per 1,000 blocks drawn at random: about 457 S, 479 M, 63 L, 0.6 XL. **The test-only counts are smaller and not yet computed**, notably for XL |
| Distinct ORCIDs equal the (block, ORCID) pairs, 244,564 each | Each ORCID is in exactly one block, so one case per block is also one case per person |
| Eligible blocks hold at most 8 ORCID groups | The number of case-eligible groups *g* in a block is at most 8 |
| Smoke sample: complete blocks, round-robin across bands, 50 cases in 23 blocks | Not representative; never confirmatory |
| Test blocks over all 80,294 blocks: 20,081 (train 40,253, validation 19,960) | Eligible test counts per band must be computed before freeze |
| `prep.py` selects complete blocks | The one-case-per-block selector does not exist and is not to be written yet |

## 2. Decisions

### C1. Sample design (approved)
One hash-selected primary case per block: the case-eligible group with the smallest `sha256(seed|block|orcid)`. Other case-eligible groups of the sampled block are recorded as *secondary* in the frozen manifest before capture. Secondary cases never enter a primary estimate, are benchmark-derived only, and are exploratory (C8).

### C2. Estimand (approved)
Notation: strata *h* (S, M, L, XL); *N_h* the frame size of stratum *h*; *n_h* the number of sampled blocks; *g_i* the number of case-eligible groups in the block of case *i*. The selection probability of person *i* is (*n_h*/*N_h*) · (1/*g_i*), so the inverse-probability weight is *w_hi* = (*N_h*/*n_h*) · *g_i*.

| | E1, block level (primary) | E2, person level (secondary) |
|---|---|---|
| Question | a random eligible block, then a random eligible person in it | a random eligible person in the frame |
| Case weight | *w_hi* = *N_h*/*n_h*, no factor *g_i* | *w_hi* = (*N_h*/*n_h*) · *g_i* |
| Pooled estimate | Σ_h (*N_h*/*N*) p̂_h, equal to the weighted ratio with these weights | Hájek ratio Σ *w_hi* y_hi / Σ *w_hi* |
| Population size estimated | number of blocks | number of (block, person) pairs, computed at frame freeze |

Within a stratum E1 is the unweighted sample proportion. The paper keeps the two questions explicitly distinct.

### C3. Strata and allocation (approved)
Fixed S/M/L/XL bands from `prep.py`; per stratum before pooled; frame-weighted pooling; XL descriptive. Allocation algorithm, fixed before the draw and recorded in the manifest:
1. Fix total *N* and floors *f_h* (values come later; the C9 procedure supplies *N*).
2. Start from proportional counts *N*·*N_h*/Σ*N_h*.
3. Where a floor binds, set *n_h* = *f_h*. Where a floor or the proportional count exceeds the stratum's available population, set *n_h* = *N_h* (a census of that stratum).
4. Fix every bound stratum at its value and allocate the remaining total across the unbound strata proportionally to *N_h*. Repeat until no further stratum becomes bound.
5. Round by largest remainder so that Σ*n_h* = *N*. If Σ min(*f_h*, *N_h*) exceeds *N*, the plan is rejected.
A census stratum has weight 1 and no sampling variability with respect to the frame. Report it as a count, not as an interval.

### C4. Frame (approved)
Main frame = eligible test blocks excluding the 23 smoke blocks **and the pilot blocks reserved under C9**. New main seed declared at freeze; the smoke seed 20261119 is not reused. No replacement after the manifest is frozen. Before freeze, compute the exact eligible test-frame size per band, the number of pilot blocks per band, and the resulting *N_h*, with each stratum's sampling fraction *f_h* = *n_h*/*N_h*. These counts are **not computed in this revision**.

### C5. Inference (approved in principle)
Strata are finite populations sampled without replacement, so a binomial interval is a model, not the design. The protocol distinguishes three regimes and never calls an interval design-exact.

| Regime | What is reported | Basis and limits |
|---|---|---|
| **R1. Per stratum** | Clopper–Pearson interval on the stratum count | Under two-stage selection the binomial variance is an upper bound for the without-replacement variance (up to a factor *N_h*/(*N_h*−1)), so the interval is a **conservative superpopulation approximation**, and is labelled so. *f_h* is reported for every stratum and serves as a **diagnostic trigger**: a large *f_h* flags that the interval may be materially too wide. It is not a statistical boundary. A census stratum gets no interval |
| **R2. Pooled, frame-weighted** | E1 or E2 point estimate with a stratified percentile bootstrap interval | 10,000 resamples with a recorded seed, cases resampled within strata, census strata held fixed. The bootstrap ignores the finite-population correction and is conservative when *f_h* is small |
| **R3. Sparse automatic precision** | Counts per stratum and exact intervals; pooled raw counts labelled "unweighted, descriptive"; zero-event bound when there are no errors | Chosen when a sparse-count warning below is triggered. A bootstrap on zero errors would return a degenerate interval and is **never reported** |

**Provisional numerical thresholds.** None is locked. Each is a warning or diagnostic, and the final protocol must either fix it or state how it is judged.
| Quantity | Provisional role |
|---|---|
| Sampling fraction about 0.10 | diagnostic trigger for R1, not a boundary |
| About 30 automatic assignments | provisional sparse-count warning |
| About 5 errors | provisional sparse-count warning |
| Minimum stratum size for bootstrap | **no provisional value; must be specified before freeze** |
| About 20 contributing blocks (C8) | provisional warning, not a guarantee of reliable inference |

**A stratum too small to resample.** Reporting an estimate without an interval is preferable to a misleading interval. For a non-census stratum below the (to be specified) minimum size: report its estimate and its counts; give an exact R1 interval where the estimator is a simple proportion; give **no interval** for bootstrap-dependent quantities such as MRR and weighted ratios. For the pooled analysis, the pooled interval is withheld by default. The director may predeclare, before freeze, a negligible frame weight below which a stratum is dropped from the pooled estimand, which is then relabelled with the strata it covers (for example "pooled over S, M and L") while the dropped stratum is reported separately. The pooled estimand is never silently changed.

Further rules:
- Conditional rates (automatic precision given automatic) are conditional binomial given the count of automatic assignments within a stratum. This assumes exchangeability of cases within the stratum and is stated as such.
- Pooled unweighted counts are not frame-representative under P3.
- MRR uses the R2 bootstrap. Paired differences (C0 vs C1, other policy vs primary pair, R0 vs R2) use a paired stratified bootstrap and, where inclusion probabilities are equal, exact McNemar on the discordant pairs. All are descriptive and benchmark-derived.
- Independence across blocks is an assumption. After capture, report the number of OpenAlex candidate profiles that appear in more than one case pool, as a diagnostic.
- Uncertain and unverifiable handling follows Decision A, with the all-wrong and all-right bracket on every verified rate.

### C6. Endpoints and the audit limitation (approved)
The Decision A audit samples only the non-automatic frame of C1 with `selective_policy_v2`. Its label-error rate describes that frame and nothing else, and the audit estimate accompanies no overall retrieval result.

| Claim | Label basis | Denominator | Population described |
|---|---|---|---|
| Automatic coverage, manual, unresolved, empty-retrieval, provider-failure, no-defined-score rates | label-free (HAMMER outputs and provider status) | all *N* primary cases | primary sample |
| **Overall RQ2a retrieval**: pool mapping rate, end-to-end success@*k*, conditional Recall@*k*, MRR | **benchmark-derived** ORCID agreement | as in the C7 table | primary sample |
| **Verified retrieval** | verified by the dossiers | only the cases actually verified, with a definite label | reported **separately** for (i) the automatic assignments and (ii) the random non-automatic audit sample; never pooled with each other or with the overall figures |
| Verified automatic precision, selective risk (primary pair) | verified | automatic assignments scored under the C7 table | primary sample |
| Audit label-error rate | verified against benchmark | audited non-automatic cases with a definite label | the non-automatic frame of the primary pair only |
| Other conditions and policies, C1x, R0 vs R2 | benchmark-derived | as in the C7 table | primary sample |

The audit error rate is not a correction factor, does not adjust overall retrieval, and does not describe automatic assignments or other conditions and policies. A combined estimator that weights the audit up to the whole sample would use the audit to correct benchmark results, which Decision A forbids, so it is not adopted. Primary endpoints are automatic coverage and verified precision (RQ2b), and overall benchmark-derived end-to-end success@1, @10 and mapping rate (RQ2a). The evaluation is estimation with intervals, not pass or fail; no hypothesis test is run and no multiplicity correction applies. Everything else is exploratory.

### C7. Fixed design, denominators and scoring against a verified label (approved with clarification)
No optional stopping, no replacement and no extension after results are seen. Every drawn primary case stays in the **case accounting**: each appears in exactly one of the six outcome categories (automatic, manual, unresolved, empty retrieval, provider failure, no defined score) and one reporting class (Decision A). A case need not be in every metric's denominator. Each denominator is fixed in advance:

| Metric | Label basis | Numerator | Denominator | Stays visible |
|---|---|---|---|---|
| Automatic coverage; manual and unresolved rates; empty, failure and no-score rates | label-free | cases in the category | all *N* primary cases | all categories reported together |
| Pool mapping rate | benchmark | cases with a mapped profile in the pool | all *N* (all benchmark labels are resolved) | unmapped cases, including empty and failed retrievals |
| End-to-end success@*k*, end-to-end MRR | benchmark | mapped within the first *k* (reciprocal rank; unmapped counts as 0) | all *N* | failures and empties count as misses |
| Conditional Recall@*k*, conditional MRR | benchmark | first mapped profile within *k* (reciprocal rank) | cases with a mapped profile | always shown beside the end-to-end values and the mapping rate |
| Automatic precision, selective risk | verified | automatic assignments scored **correct** | automatic assignments scored **correct or incorrect** under the table below | automatic assignments labelled uncertain or unverifiable are counted separately, with a bracket in which they are all wrong or all right |
| Audit label-error rate | verified | audited cases whose verified label contradicts the benchmark label | audited non-automatic cases with a definite label | uncertain and unverifiable counts and the bracket |
| Verified retrieval | verified | as for overall retrieval, on verified cases | cases verified with a definite label, by subset | uncertain and unverifiable counts |
| Cases with no pool (provider failure, empty retrieval) | | | | they cannot be automatic, remain in the audit frame, and receive Stage A only because no pool exists for Stage B |

**Scoring one automatic assignment against its verified label.** *Resolved* means the reviewers identified a definite intended person. *Unresolved* means they determined that no unique intended person exists. *Uncertain* and *unverifiable* follow Decision A.
| Verified status of the case | Selected candidate | Scored as | In the precision denominator |
|---|---|---|---|
| Resolved | judged the same person | correct automatic assignment | yes |
| Resolved | judged a different person | incorrect (false automatic assignment) | yes |
| Resolved, and no candidate in the pool is the person (a definite identity with no matching candidate) | any candidate | incorrect (false automatic assignment) | **yes** |
| Unresolved (no unique intended person) | any candidate | incorrect (false automatic assignment) | **yes** |
| Uncertain or unverifiable at case level, or reviewers cannot tell for the selected candidate | | not scored; counted and reported | no, but visible with the bracket |
Only the uncertain and unverifiable cases leave the denominator. A definite identity without a matching candidate, and a case with no unique intended person, never disappear from it. The paper must define all four rows in these terms. The current Section 5 text, which defines *R* as "the audited cases" and lists the unresolved-control measure, needs a later edit to match. That edit is not applied.

### C8. Clustered secondary analysis (approved)
Block-level cluster bootstrap on secondary cases only, recomputing precision as summed correct automatic over summed automatic, with a leave-one-block-out check. Report the number of blocks and the number contributing at least one automatic decision. **About 20 contributing blocks is a warning, not a validity threshold.** Always report the actual distribution of automatic assignments across blocks (blocks with zero, one and two or more, the largest share from a single block, and the leave-one-block-out range), and judge reliability from that. Report an intra-block correlation only if estimable. Exploratory and benchmark-derived, never merged with the primary estimates.

### C9. Coverage pilot and stratified predictive sizing (revised, two corrections applied)
**Pilot source: reserved disjoint test blocks.** The label-free coverage pilot is drawn from eligible test blocks excluding the smoke blocks, and its blocks (whole blocks, all groups) are then removed from the main frame. This gives a pilot from the same source population, no overlap with the main sample, and no train-to-test coverage assumption. Order of operations:
1. Freeze code, thresholds, weights, policy and the pilot rules.
2. Draw the pilot by the same one-case-per-block hash rule with a separate pilot seed declared before the draw, stratified by the four bands, with per-stratum pilot sizes *n_p,h* (undecided).
3. Run the pilot. It scores no correctness and uses no labels, only each case's decision category. **Execution is not authorised**: it needs its own request budget and cost ceiling and none is requested.
4. Compute the sizing below.
5. Define the main frame as eligible test blocks minus smoke blocks minus pilot blocks, recompute *N_h*, and draw the main sample with the main seed.
The pilot draw is a hash-random removal, so the remaining frame is a random subset of the eligible test blocks. State in the paper that *N_h* refers to the post-exclusion frame.

**Feasibility and fallback.** Reserving pilot blocks must leave the main allocation feasible: *n_p,h* + *n_h* ≤ the eligible test count of the stratum. This is most likely to bind in XL, where the test count is small. For a stratum where it fails, the two options are (a) draw that stratum's pilot from train or validation blocks of the same band, with the **train-to-test transfer assumption reported explicitly** for that stratum, or (b) run no pilot for it and let its predictive distribution rest on the prior alone, which is very wide. A pilot from a different split is a fallback only.

**Why *N* = ⌈*m*/*c*⌉ is not enough.** It makes *m* the expected number of automatic assignments, not a guarantee. With coverage known exactly, that *N* reaches *m* with probability of about 0.5. Pooled binomial illustration (assumed coverage values, not forecasts or plans; the stratified procedure below replaces it):
| Target *m* | *c* | *N* = ⌈*m*/*c*⌉ | P(automatic ≥ *m*) at that *N* | Smallest *N* for P ≥ 0.90 | for P ≥ 0.95 |
|---:|---:|---:|---:|---:|---:|
| 16 | 0.10 | 160 | 0.54 | 210 | 227 |
| 32 | 0.10 | 320 | 0.53 | 390 | 413 |
| 32 | 0.20 | 160 | 0.53 | 193 | 204 |
| 100 | 0.10 | 1,000 | 0.52 | 1,123 | 1,161 |
| 100 | 0.30 | 334 | 0.53 | 370 | 381 |

**Stratified predictive sizing (procedure to adopt; no value chosen).**
1. Choose the target *m* of automatic assignments once reviewer capacity and the desired precision bound are known (both deferred). *m* may be inflated to *m′* by a declared allowance for automatic assignments that end up uncertain or unverifiable, since those leave the precision denominator.
2. From the pilot, for each stratum *h* with *a_h* automatic assignments among *n_p,h* cases, model unknown coverage *c_h* with Beta(*a_h*+½, *n_p,h*−*a_h*+½), independently across strata (Jeffreys prior; a stratum with no pilot data keeps Beta(½, ½)). Report a sensitivity run with a uniform Beta(1, 1) prior.
3. For a candidate total *N*, apply the C3 algorithm to obtain *n_h*(*N*) (with floors, census caps and the post-exclusion *N_h*).
4. The automatic count in stratum *h* is *A_h* | *n_h* ~ BetaBinomial(*n_h*, *a_h*+½, *n_p,h*−*a_h*+½). The total is *A* = Σ_h *A_h*, whose distribution is obtained by exact convolution (or a seeded simulation with a recorded draw count).
5. Select the smallest *N* with P(*A* ≥ *m′*) ≥ 1−β that also holds for every *N′* in a declared search range up to *N*_max. This guards against non-monotone behaviour from rounding and floors.
6. **Sensitivity check, reported alongside:** replace each *c_h* by its exact one-sided lower confidence limit *c_L,h* at level 1−γ/*H* (Bonferroni across the *H* strata, γ declared), with *c_L,h* = 0 where there is no pilot data, and find the smallest *N* with P(Σ_h Binomial(*n_h*, *c_L,h*) ≥ *m′*) ≥ 1−β. Both *N* values are reported.
7. Freeze *N*, *m*, *m′*, β, γ, the pilot size and allocation, floors, priors, *N*_max and the calculation script in the manifest before the main capture.

**Assumptions to state.** Independent strata; the pilot is representative of its stratum in the main frame (justified by the random draw from the same test frame); coverage is stable under frozen code; the beta-binomial treats strata as infinite populations, which is expected to be conservative for the lower tail when *m′* is below the predictive mean and is to be checked. **A pilot result never changes thresholds, weights, code or policy.** If coverage is too low to reach the target at a feasible *N*, that is reported to the director, and any change after seeing pilot output requires a new freeze and a new pilot on fresh blocks. Pilot blocks never enter the main sample. The pilot size, *m*, β, γ and *N* are all undecided, and the pilot size controls the predictive uncertainty.

## 3. Conditions recorded before locking
1. **Benchmark scope.** The eligible frame contains blocks with at least two ORCID groups and excludes blocks with more than eight, so the study concerns a restricted, benchmark-defined population of ambiguous author blocks. It does not establish performance over all author names or over the hardest homonym cases. Proposed wording for Section 8 or Section 5 (not applied):
   > The evaluation frame consists of benchmark-defined blocks with at least two ORCID-labelled authors and at most eight. Results therefore describe this restricted population of ambiguous blocks. They do not establish performance across all author names, nor on the most ambiguous names, which the cap excludes.
2. **Coverage pilot approval.** Approved as a design requirement, with its source now the reserved test blocks. Execution needs a separate request budget and cost ceiling. No provider call is authorised.
3. **Retrieval-label dependency (Decision A).** Verified retrieval and benchmark-derived retrieval stay distinguishable in every table. The audit error rate applies only to its defined frame and is never a correction factor. This is built into C6 and C7.

## 4. Decision checklist for final review
| # | Decision | Status in this revision |
|---|---|---|
| C1 | One hash-chosen primary case per block; secondary cases only for C8 | Approved |
| C2 | E1 primary, E2 secondary; corrected weights | Approved |
| C3 | P3 with capped census strata and redistribution algorithm | Approved |
| C4 | Eligible test blocks minus smoke and pilot blocks; new seed at freeze; no replacement | Approved, pilot exclusion added |
| C5 | Three inference regimes; thresholds provisional; too-small-stratum rule added | Approved in principle |
| C6 | Claims tagged by label basis; verified and benchmark-derived kept apart | Approved |
| C7 | Case accounting, denominators, explicit scoring table for verified labels | Approved, clarification applied |
| C8 | Cluster bootstrap, exploratory; 20 blocks is a warning | Approved |
| C9 | Pilot from reserved disjoint test blocks (train or validation as per-stratum fallback only); stratified beta-binomial sizing with a lower-bound sensitivity check | Both corrections applied, for confirmation |

**Open before freeze:** the minimum stratum size for the bootstrap; whether a negligible-weight rule for the pooled estimand is predeclared; the final form of each provisional threshold; *N*, *m*, *m′*, β, γ, pilot size, floors, priors, *N*_max.

## 6. Lock record (20 November 2026)
The research director locked Decision C as written in revision 3: C1 to C9, including the stratified predictive sizing procedure, the reserved test-block coverage pilot, the C7 scoring table for verified labels, and the provisional status of every numerical threshold.

Locking fixes the design, not these items, which stay open and must be settled before the evaluation is frozen: the minimum stratum size for the bootstrap; whether a negligible-weight rule for the pooled estimand is predeclared; the final form of each provisional threshold (sampling fraction, sparse-count warnings, contributing-block warning); *N*, *m*, *m′*, β, γ, the pilot size and allocation, floors, priors and *N*_max; reviewer capacity (deferred with all personnel items); the provider-request budget and cost ceiling for the pilot and any candidate-works capture; seeds.

Decisions A, B and C are now each approved or locked as designs. Not authorised by this lock: implementing the selector, computing test-frame counts, running the pilot, making provider requests, generating dossiers, editing the manuscript, or freezing the evaluation.

## 5. What has not been done
No frame or test-split count was computed, no selector was written, no pilot or capture was run, no budget was requested, no seed was fixed, and the manuscript was not edited. Section 5 will need edits for Decisions A, B and C once the protocol is frozen: the metric definitions, the four-row scoring definition above, the unresolved-control measure, the label-strategy and sampling-design subsections, and the scope statement. Nothing is frozen. The next milestone is one coherent protocol across Decisions A, B and C.

## 7. Clarification addendum (20 November 2026)
Recorded after the lock, from the consistency review of the integrated protocol draft. **The locked text above is unchanged.** These two clarifications fix an ordering ambiguity in C9 and do not alter the design. **Both clarifications were confirmed by the research director on 20 November 2026.**

**X-02, order of operations in C9.** The post-exclusion stratum sizes *N_h* (eligible test blocks minus smoke blocks minus pilot blocks) depend only on which blocks were reserved, not on any outcome. They are therefore computed immediately after the pilot is drawn and **before** the sizing calculation, which uses them in the C3 allocation step. Only the draw of the main sample waits for *N*. This replaces the reading in the C9 order of operations in which "compute the sizing" (step 4) precedes "define the main frame, recompute *N_h*" (step 5).

**X-03, feasibility of the pilot reservation.** *N* is unknown when the pilot is drawn, so the feasibility condition *n_p,h* + *n_h* ≤ the eligible test count of stratum *h* is evaluated against *N*_max, the upper end of the sizing search. Where a stratum fails it, the two C9 options apply (train or validation blocks for that stratum with the transfer assumption stated, or no pilot data for it). Where the reservation only shrinks a stratum that the C3 census cap would take whole, the main allocation uses the post-exclusion *N_h* and the smaller census is reported. Which of these cases applies is checked at the freeze, with counts not yet computed.

### C7 rulings recorded 20 November 2026 (approved by the research director)
The locked C7 text above is unchanged. These rulings settle ambiguities found while implementing C7 (`backend/hammer_pilot/metrics_c7.py`, test records T002 to T004) and add no parameter and no freeze.
1. **Audit label error is derived from adjudicated records**, never supplied as a flag. Three reasons: an impure benchmark group (automatically a contradiction; an unresolved group is not), a false mapping (a benchmark-mapped candidate judged a different person) and a missed mapping (an unmapped candidate judged the same person). A case counts once in the overall numerator; reason-specific counts are reported separately. A "cannot tell" judgment is uncertain, not an error.
2. **An automatic case whose selected candidate reviewers cannot verify** stays in the Uncertain class.
3. **Ground-truth unresolved is distinct from a HAMMER unresolved or abstention outcome.** Only ground-truth unresolved cases are excluded from conditional verified-retrieval metrics. A HAMMER abstention never removes an otherwise adjudicable case from retrieval evaluation.
4. **The R2 candidate pool** is the primary pool for C7 mapping and retrieval metrics. R0 remains descriptive.
5. **"No matching candidate"** requires a Stage B judgment for every candidate in the pool (and all judged different) before a pool is classified that way.
Open points the implementation raised (T004 section 11): classification of an unresolved case with a pure group (recorded as consistent); an impure group with an uncertain case label (recorded as contradicted in the audit, class unchanged); whether end-to-end verified retrieval also excludes ground-truth unresolved cases (currently yes); and the definition of conditional verified retrieval.

### C7 clarifications recorded 20 November 2026 (approved by the research director; test record T005)
The locked C7 text is unchanged and no parameter is added or frozen. These clarifications refine the four open points raised in the previous entry.
1. **Group-purity states** are pure, impure and unresolved. A **pure group whose case label is unresolved** is indeterminate, not consistent.
2. **Benchmark-group validity is separate from case-level candidate verification.** A confirmed impure group is a benchmark contradiction, but an uncertain or unverifiable case stays outside the definite-label audit error-rate denominator. Group impurity is reported separately, and the uncertainty bracket is preserved.
3. **Overall benchmark-derived retrieval** keeps all *N* primary cases (end-to-end success@*k* as specified by C7). **Verified retrieval** uses only cases with a definite verified label, and excluded categories are reported separately. The audit never adjusts overall benchmark-derived retrieval.
4. **Conditional verified retrieval** keeps its definition: its denominator is the cases with a verified-same candidate in the R2 pool. All other judgment categories are reported separately.
