# T006: stratified predictive sizing script (Decision C9, revision 3)

**Test ID:** T006 (run 1) | **Date:** 20 November 2026 | **Type:** unit and numerical-method validation on synthetic fixtures (exact rational arithmetic, independent simulation, regression to published planning values, mutation sanity check) | **Status:** PASS (86 new tests; full suite 428; 14 of 15 mutants detected cleanly, the 15th detected by a targeted rerun) | **No parameter was chosen or frozen.**

> T001 to T005 and all their raw outputs are preserved unchanged. This record covers new files only: `backend/hammer_pilot/sizing_c9.py`, `backend/scripts/size_hammer_main_sample.py` and `backend/tests/test_sizing_c9.py`.

## 1. Question and reason
Does the sizing script implement the stratified predictive procedure of Decision C9 (revision 3) correctly, including the guarded smallest-*N* search and the lower-bound sensitivity, and can it be trusted to size a study whose cost and claims depend on it? An error here (for example a wrong tail, a mis-rounded allocation, or a search that returns an *N* from a non-monotone dip) would silently under- or over-size the main evaluation.

## 2. Mathematical method
**Inputs (all supplied by the caller; none has a default):** post-exclusion stratum sizes *N_h*; allocation floors *f_h*; pilot counts (*a_h* automatic among *n_p,h* cases) per stratum; target *m′*; β; γ; *N*_max.

1. **Posterior coverage per stratum.** With prior Beta(*α₀*, *β₀*) (Jeffreys (½, ½) primary, uniform (1, 1) sensitivity), *c_h* ~ Beta(*α₀* + *a_h*, *β₀* + *n_p,h* − *a_h*), independent across strata. A stratum with no pilot observations keeps the prior.
2. **C3 allocation** *n_h*(*N*): effective floor *f′_h* = min(*f_h*, *N_h*); proportional shares *N*·*N_h*/Σ*N_h*; per round, unbound strata whose share exceeds *N_h* are bound at *N_h* (census) and those below *f′_h* are bound at *f′_h*; the remainder is allocated across unbound strata proportionally to *N_h*; repeat until nothing new binds; largest-remainder rounding (exact Fractions; ties go to the larger frame size, then the earlier stratum). The plan is rejected (`AllocationInfeasible`) if Σ*f′_h* > *N*, if *N* exceeds the frame, or if binding cannot sum to *N*.
3. **Predictive count per stratum.** *A_h* | *n_h* ~ BetaBinomial(*n_h*, *α_h*, *β_h*) with pmf P(*k*) = C(*n*, *k*) B(*k* + *α*, *n* − *k* + *β*)/B(*α*, *β*), built from P(0) = Π_{i<n}(*β*+*i*)/(*α*+*β*+*i*) and the ratio recurrence P(*k*+1)/P(*k*) = (*n*−*k*)(*k*+*α*)/((*k*+1)(*n*−*k*−1+*β*)), evaluated in log space.
4. **Total.** *A* = Σ*A_h* has the **exact convolution** of the stratum pmfs (floating-point exact; normalisation to 1e-9 is checked on every pmf). P(*A* ≥ *m′*) is the upper tail.
5. **Search.** Over *N* from max(*m′*, Σ*f′_h*, 1) to *N*_max, the answer is the smallest *N* with P(*A* ≥ *m′*) ≥ 1 − β **such that the condition also holds for every *N′* in [*N*, *N*_max]** (the whole suffix). An *N′* with no feasible allocation fails the condition and is reported. The first *N* meeting the condition, any failing *N′* after it, and a borderline flag (probability within 1e-9 of the threshold) are reported, never adjusted.
6. **Lower-bound sensitivity.** *c_L,h* is the exact one-sided Clopper–Pearson lower limit at level 1 − γ/*H*, with *H* = the number of strata in the frame (Bonferroni), and 0 where there is no pilot data. P(Σ Binomial(*n_h*, *c_L,h*) ≥ *m′*) ≥ 1 − β with the same guarded search.
7. **Failure reporting.** `not_found_within_N_max` with a reason (the smallest *N* that could reach *m′* already exceeds *N*_max; the condition fails at *N*_max; no *N* has an all-satisfying suffix), the probability at *N*_max, and the maximum probability in the range. Invalid inputs raise `SizingError`.

## 3. Assumptions and implementation choices (for the director)
Independent strata; the pilot is representative of its stratum in the main frame; coverage is stable under frozen code; the beta-binomial treats strata as infinite populations (expected conservative in the lower tail, to be checked, not assumed). Choices that the C9 text does not fix:
1. **Simultaneous binding.** The "repeat until no further stratum becomes bound" rule is implemented literally, with all violating strata bound in the same round. Because *N* ≤ Σ*N_h* implies every share is at most *N_h*, a stratum is in practice bound only by a floor (a floor at or above the frame size gives a census). The cap rule never fires on its own. If simultaneous binding cannot sum to *N*, that *N* is infeasible and is reported.
2. **Largest-remainder rounding is not monotone in *N*** (the Alabama paradox). T006 contains a fixture where stratum M receives 3 at *N* = 32 and 2 at *N* = 33, which makes P(*A* ≥ *m′*) fall from 0.7276 to 0.6458. This is the case that the guard in C9 step 5 exists for.
3. **The same guarded search is applied to the lower-bound check.** C9 states the guard in step 5 only.
4. **Bonferroni *H*** counts all strata of the frame, including strata without pilot data (which contribute a limit of 0).
5. ***N*_max must not exceed the frame size** (a sample cannot exceed the frame); the script raises an error otherwise.
6. The target *m′* is an input. The script does not implement the allowance that inflates *m* to *m′*, which C9 leaves as a declared quantity.
7. numpy is used for the convolution. It is installed in the backend environment (as a dependency of other packages) but is not listed in `requirements.txt`.

## 4. Environment
Python 3.12.5, numpy 2.5.5, pytest 8.4.2, macOS Darwin 25.5.0, git `6d31cbe`, dirty working tree (untracked files only added by this work; nothing staged or committed). SHA-256: `backend/hammer_pilot/sizing_c9.py` `b9a2abc1a28b289193b383a289f0ad4247e04720c7a13833d7a3d694eb547ba6` (335 lines); `backend/scripts/size_hammer_main_sample.py` `87c9bcd5d7f71c9d5e7adffbbe4adbcda5655672a04627db805b0eaa5f421de4` (43 lines); `backend/tests/test_sizing_c9.py` `149d78c3fec63b0cdcb7d4e3752b5a358342dd5d69df7f8433a68f9a6b19b530` (447 lines). `metrics.py` and `metrics_c7.py` are unchanged (`a6433628…`, `776e02e8…`).

## 5. Data and input parameters
**Synthetic only.** No frame counts, pilot data, test-frame computation, sample or provider request was used. Fixtures are small hand-built frames, a seeded random generator for allocation properties, and one four-stratum fixture (`ALABAMA`: frames 40, 12, 40, 60; floor 1 on L; pilot 2/13, 4/4, 4/14, 0/13; *m′* = 6; *N*_max = 80). Values such as β = 0.30 in that fixture were chosen to make the dip decisive and are **test values, not proposals**. The CLI example in the raw outputs uses the same synthetic fixture and is not a planning result. *m*, *m′*, β, γ, *N*_max, floors, pilot sizes and priors for the real study remain open.

## 6. Procedure and commands
From `backend/`, with `PYTHONDONTWRITEBYTECODE=1 DATABASE_URL=sqlite+aiosqlite:///:memory:`:
```
.venv/bin/python -m pytest tests/test_sizing_c9.py -p no:cacheprovider -v --no-header
.venv/bin/python -m pytest tests -p no:cacheprovider -q --no-header -rfE
.venv/bin/python -I scripts/size_hammer_main_sample.py --inputs <inputs.json> --out <new file>
.venv/bin/python -I ../docs/testing_validation/RAW_OUTPUTS/T006_run1/scripts/emit_c9_validation_table.py
```
Mutation check: `RAW_OUTPUTS/T006_run1/scripts/mutate_t006.py` (15 defects, one at a time, module restored byte-identically).

**Test groups (86 test items).** Input validation (frames, explicit floors, pilot data, planning parameters; no defaults for open parameters; inputs not mutated). C3 allocation (largest remainder and ties, floor binding with redistribution, census, infeasible cases, 400 random property checks, the non-monotone fixture). Distributions (beta-binomial pmf against exact rational arithmetic for 7 parameter sets; moments; binomial pmf and edges; invalid parameters; exact convolution against rational convolution; tail edges; numerical stability for large and extreme parameters). Priors, posteriors and limits (Jeffreys and uniform posteriors, zero-pilot strata, Bonferroni limits). Search and guard (suffix rule, failure reporting, infeasible *N′*, borderline flag, the non-monotone fixture with an independent re-check over the whole range). Validation against C9 (10 illustrative values; exact rational confirmation of 390 and 413; the *m*/*c* rule; stratified versus pooled; large-pilot limit). Zero-pilot, census, floors and infeasibility. Exact convolution against a seeded simulation and against rational arithmetic. Full procedure, determinism and the command-line script.

## 7. Expected and actual results
| Check | Expected | Actual |
|---|---|---|
| `test_sizing_c9.py` | all pass | **86 passed**, 4.09 s |
| Full backend suite | 342 earlier + 86 | **428 passed**, 14.99 s |
| Suite without the sizing tests | 342 | 342 passed (unchanged) |
| C7 test files (106 tests) | unchanged | 106 passed |
| Illustrative C9 values by the known-coverage helper | *N* = 210, 227, 390, 413, 193, 204, 1123, 1161, 370, 381 | **all ten equal**; each confirmed by exact rational binomial tails: P(*N*−1) < 1 − β ≤ P(*N*) |
| Required check *m* = 32, *c* = 0.10 | *N* = 390 (β = 0.10), 413 (β = 0.05) | **390 and 413** (P = 0.9000 and 0.9503) |
| The *m*/*c* rule (*N* = ⌈*m*/*c*⌉) | about one half | 0.5154 to 0.5385 across the ten rows |
| Beta-binomial pmf versus exact rational arithmetic | agree | maximum difference below 1e-12 for all 7 parameter sets |
| Convolution and tails versus exact rational convolution | agree | below 1e-13 |
| Moments | closed forms | mean and variance agree to 1e-10 and 1e-9 relative |
| Exact total versus seeded simulation (3 strata, *N* = 120, *m′* = 16, 400,000 draws, seed 20261120) | within 5 binomial standard errors | within |
| Non-monotone fixture, guard | first meeting *N* = 31; fails at 33; answer 34 | **31, [33], 34**; independent re-check holds at every *N′* from 34 to 80 |
| Dip at the end of the range (*N*_max = 33) | reported as not found with the first-meeting *N* | as expected |
| Stratified predictive versus pooled binomial | finite pilot raises *N* above 390 | *N* > 390; with a 2,000,000-case pilot, *N* differs from 390 by at most 1 |
| Mutants Q1 to Q15 | each detected | 14 detected by clean failing runs (counts below); Q9 detected by a targeted rerun (below) |

Failing-test counts by mutant (from `mutation_check_t006.txt`): Q1 6, Q2 3, Q3 1, Q4 3, Q5 1, Q6 8, Q7 20, Q8 18, Q10 1, Q11 5, Q12 3, Q13 11, Q14 3, Q15 1.

**Mutant Q9** (the check that *N*_max does not exceed the frame, removed) did not finish the full run cleanly: without the guard, one validation test searched a 100,000-block frame and exhausted resources, so the run produced no summary. A targeted rerun of the test that exercises the guard, with the mutant applied, fails cleanly (`mutation_check_t006_Q9_targeted.txt`). Module hash before and after both runs: `b9a2abc1…`. No stray process was left running.

Illustrative-value table and synthetic CLI example: `c9_illustrative_validation.txt`, `example_inputs_synthetic.json`, `example_output_synthetic.json`, `example_cli_stdout.txt`.

## 8. Interpretation
The distributions and convolution agree with exact rational arithmetic and with an independent simulation. The search reproduces the illustrative planning values of C9 for known coverage, confirmed exactly. The stratified procedure is shown to differ from the pooled binomial in the expected direction. The guard returns a later *N* when allocation is non-monotone, as C9 intends. This is evidence of **correct implementation of the written procedure**. It is not a planning result, and it does not show that the assumptions of C9 hold for HAMMER's real coverage.

## 9. Development history and defects found
- **First run: 82 passed, 3 failed.** (a) A test fixture error: a tie test used frames of size 1 with *N* = 10. (b) and (c) A **real defect in my first implementation**: the pmf start was computed as a difference of log-gamma values, which for a very large pilot (parameters near 2×10⁵ and 1.8×10⁶) lost about 4×10⁻⁹ of normalisation. The built-in normalisation check raised an error, as designed. It was fixed by computing log P(0) as a sum of *n* small log terms, which keeps normalisation near 10⁻¹⁵. A regression test and a mutant (Q12) now cover it.
- Second run: 86 passed after the fixture fix and the added regression test. No expected value was changed to make a test pass.
- The unrealistic situation in which the Q9 mutant exhausted resources is recorded above.

## 10. Limitations and sources of error
- Floating-point arithmetic: probabilities are accurate to about 1e-13 in the tested cases; the borderline flag (1e-9) warns when a decision rests on rounding.
- The reference implementations in the tests are mine, but they use different arithmetic (exact rationals, a simulation); they share the C9 specification.
- The simulation check is statistical (5-sigma), seeded, and covers one fixture.
- Performance: a realistic four-stratum search up to *N*_max = 1,500 ran in under a second; much larger ranges (tens of thousands) were not tested and are not expected to be needed.
- The script plans from inputs that do not yet exist; its output is only as valid as C9's assumptions and the supplied pilot.

## 11. Points for the research director
1. The simultaneous-binding rule and the observation that the cap never fires on its own (section 3, items 1 and 2).
2. Whether the guard should apply to the lower-bound check (item 3), and whether *H* should count only strata with pilot data (item 4).
3. Whether to list numpy in `requirements.txt` (item 7).

## 12. Artifacts
`RAW_OUTPUTS/T006_run1/`: `pytest_full_suite.txt`, `pytest_suite_without_sizing_tests.txt`, `pytest_test_sizing_c9_verbose.txt`, `mutation_check_t006.txt`, `mutation_check_t006_Q9_targeted.txt`, `c9_illustrative_validation.txt`, `example_inputs_synthetic.json`, `example_output_synthetic.json`, `example_cli_stdout.txt`, `scripts/`. Hashes: `RAW_OUTPUTS/SHA256SUMS.txt`.

## 13. What we learned
The non-monotone allocation is not hypothetical, so the guard matters; a naive "first *N* that works" would have returned 31 where 34 is correct in the fixture. Very large pilots need a numerically careful pmf. The pooled-binomial values in C9 are a correct limiting case, but the stratified procedure, with pilot uncertainty, asks for more.

## 14. Next step
Recorded in the report that accompanies this test. The script is ready to be used once the open parameters are chosen by the director; it must not be run on real inputs before they are approved and the pilot exists.
