# T010: end-to-end rehearsal on a synthetic world and simulation validation of the statistical methodology

**Test ID:** T010 (run 1) | **Date:** 20 November 2026 | **Type:** integration rehearsal with a known hidden truth; Monte Carlo validation of estimators, intervals and sizing | **Status:** PASS for the rehearsal (12 tests; full suite 526 passed); **two methodological findings** reported in section 7 | **Synthetic only: no archive, provider, real parameter or real label.**

> T001 to T009 and all their raw outputs are preserved unchanged.

## 1. Question and reason
T001 to T009 validated each component separately. Before the paper rests on the pipeline, (a) do the components wire together correctly, with every verified result matching an independently computed answer, and (b) do the statistical procedures of Decision C (E1/E2 estimators, per-stratum and pooled intervals, predictive sizing) behave as claimed under repeated sampling?

## 2. Expected behaviour
**Rehearsal.** Pilot draw, sizing, main draw, simulated resolver outputs, frozen predictions bound to the audit draw, blinded packets with a leak scan and a separate crosswalk, two simulated reviewers (one noisy) with an adjudicator, and the C7 report all run end to end. Reviewer-facing files hold no ORCID, provider id or case origin. Verified precision and the audit error rate equal an independent computation from the hidden truth; overall retrieval is identical with and without verification; the whole run is byte-reproducible.
**Simulation.** E1 is unbiased for the block-level truth and E2 for the person-level truth, while E1 weights are biased for the person-level truth (negative control). Per-stratum Clopper–Pearson intervals reach at least nominal coverage (conservative). The pooled stratified bootstrap is close to nominal. Predictive sizing reaches probability 1 − β when the true coverage is drawn from its prior, the plug-in rule *N* = ⌈*m′*/ĉ⌉ does not, and the lower-bound check is conservative.

## 3. Environment
Python 3.12.5, numpy 2.5.5, pytest 8.4.2, git `6d31cbe`, dirty tree (untracked files only). SHA-256: `backend/tests/test_rehearsal_end_to_end.py` `97c2a92b6ba4b79d06abaf0d78a551a90b221925259f80435fbeea2d43a6812e` (266 lines); `backend/scripts/validate_methodology_by_simulation.py` `b997363c9a5f0ec37fee4c22475f3d06d39f05d14b13abdfbc9082724c24b30a` (139 lines).

## 4. Data and parameters (all TEST values, none a proposal)
Rehearsal: a seeded 900-block synthetic catalogue; hidden truth per case (unique person or not, group pure or impure, true candidate); coverage by stratum 0.10, 0.18, 0.30, 0.40; pilot 30, 30, 15, 1 blocks; *m′* = 6, β = 0.20, γ = 0.10; audit size 25; reviewer noise 0.30.
Simulation: a seeded finite population with strata of 800, 600, 80 and 10 blocks (10 is a census), 1 to 6 case-eligible groups per block with the block rate rising with group count so that block-level and person-level truths differ (truth E1 = 0.2578, E2 = 0.3017); samples 40, 30, 20, 10 blocks. Sizing: frame 3000, 3000, 400, 20; pilots 40, 40, 30, 10; *m′* = 8, β = 0.10, γ = 0.10, *N*_max = 700.

## 5. Procedure and commands
`PYTHONDONTWRITEBYTECODE=1 DATABASE_URL=sqlite+aiosqlite:///:memory: .venv/bin/python -m pytest tests/test_rehearsal_end_to_end.py -p no:cacheprovider -v --no-header`; large runs: `scripts/validate_methodology_by_simulation.py --reps-estimators 600 --reps-sizing 300 --bootstrap 300 --seed 20261120` and `RAW_OUTPUTS/T010_run1/scripts/run_mismatch_sizing_1000.py`.

## 6. Results: rehearsal
12 tests passed (14 s). In the reference run (seed 4) the sizing gave *N* = 82 (uniform-prior sensitivity 72; the lower-bound check found no *N* within *N*_max = 300), 11 automatic assignments, 25 audited non-automatic cases and 36 reviewed cases, of which 30 were settled by agreement and 6 by adjudication. Checks: manifests verify and are bound to the SHA-256 of the frozen predictions; smoke, pilot and main blocks are disjoint; reviewer files are scan-clean with no provider id, rank field or case origin, and the crosswalk and flags are in a separate directory; noisy reviewers disagree (raw agreement below 1) and adjudication recovers the hidden truth for every reviewed case; **verified precision and selective risk equal the independent computation exactly**; the audit contradicted, consistent and indeterminate counts and the impure-group count equal the independent computation exactly; overall retrieval, label-free and benchmark-selective sections are byte-identical with and without verification; a corrupted verification set changes the counts visibly; two complete runs give identical manifest and packet hashes.

## 7. Results: simulation (raw: `RAW_OUTPUTS/T010_run1/`)
| Quantity | Result |
|---|---|
| E1 pooled, seed 20261120, 600 replications | mean 0.2617 against truth 0.2578: **+2.0 standard errors** |
| E2 pooled, same run | mean 0.3070 against truth 0.3017: **+2.25 standard errors** |
| Four further seeds (11 to 14, 600 replications each) | E1 bias 0.64, −0.55, −0.21, 0.25 standard errors; E2 0.85, −0.70, −0.07, 0.18; combined with the main seed, no systematic bias |
| Negative control: E1 weights against the person-level truth | −20 to −23 standard errors (the test can detect wrong weights) |
| Per-stratum Clopper–Pearson coverage (nominal 0.95) | S 0.970, M 0.972, L 0.962; XL (census) gets no interval |
| Pooled stratified bootstrap E1 interval, 600 intervals, 300 resamples | coverage **0.935** (nominal 0.95; Monte Carlo standard error 0.009) |
| Sizing, true coverage drawn from the Jeffreys prior (300 replications) | predictive success **0.899 ± 0.018** (target 0.90); lower-bound check 1.000; plug-in rule 0.677 |
| Sizing, true coverage Beta(3, 20), narrower than the prior (300 replications) | predictive 0.896 ± 0.018; lower bound 1.000 (no *N* found in 49 of 300); plug-in 0.549 |
| Same, 1,000 replications (seed 777) | predictive **0.881 ± 0.010**; lower bound 0.998 (no *N* found in 140 of 1,000); plug-in 0.566 |

**Disclosure.** The pre-declared seed showed both pooled estimators about 2 standard errors above truth (p ≈ 0.04). Because the unweighted-denominator argument says E1 is exactly unbiased, four further seeds were run to check; they show no bias. All five runs are reported. An earlier 500-replication sizing run (an earlier version of the script, same seed) gave 0.871 ± 0.015 under the mismatched generator; its output was not retained. The 1,000-replication run above supersedes it.

## 8. Interpretation and findings
1. **Weights and estimators:** E1 and E2 are implemented with the right weights; the person-level target needs the group-count weights, and ignoring them biases the estimate by about 20 standard errors in this population.
2. **Intervals:** per-stratum Clopper–Pearson is conservative (0.96 to 0.97); the pooled bootstrap is slightly below nominal (0.935). The C5 wording that the bootstrap is conservative when sampling fractions are small should not be read as a guarantee, since the percentile bootstrap with 20 to 40 blocks per stratum can undercover slightly.
3. **Finding A (sizing):** the predictive procedure achieves its target (0.899) when the model and prior are right, but with small pilots and a coverage distribution narrower than the prior it delivered **0.88 rather than 0.90** (about 2 percentage points short). The Bonferroni lower-bound check is very conservative (0.998) but returns no *N* within *N*_max in about 14% of runs. The plug-in rule delivers 0.55 to 0.68. This does not invalidate C9, but it means the guarantee is conditional on the model, and larger pilots or a smaller β (or reporting both *N* values, as C9 does) are the safeguards.
4. **Finding B (bootstrap):** see item 2; the lower-than-nominal coverage argues for reporting the exact per-stratum intervals alongside any pooled bootstrap interval, which C5 already requires.

## 9. Limitations
Simulations assume independent strata, simple random sampling of blocks and a Bernoulli outcome given the block; real coverage depends on name ambiguity and institution data in ways not simulated. The hidden-truth world is a model, not the benchmark. Monte Carlo errors are stated (0.01 to 0.02). The reviewer simulation does not model correlated reviewer errors. No claim about HAMMER's performance follows.

## 10. Artifacts
`RAW_OUTPUTS/T010_run1/`: `pytest_test_rehearsal_verbose.txt`, `pytest_full_suite.txt` (526 passed), `simulation_result_seed20261120.json`, `simulation_sizing_mismatch_1000_seed777.json`, `scripts/`. Hashes: `RAW_OUTPUTS/SHA256SUMS.txt`.

## 11. Next step
Resolve the director points in T006 to T010 and the open parameters, then obtain the archive. The remaining unscripted steps (real frame counts, coverage pilot, capture, reviewers) cannot be done offline.
