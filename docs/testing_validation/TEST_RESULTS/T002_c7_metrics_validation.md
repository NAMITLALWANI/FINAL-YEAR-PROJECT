# T002: C7 metrics module, synthetic-fixture validation

**Test ID:** T002 (run 1) | **Date:** 20 November 2026 | **Type:** unit tests on synthetic fixtures plus a mutation sanity check | **Status:** PASS (49 of 49), with open methodological ambiguities listed in section 11

## 1. Question and reason
Does `backend/hammer_pilot/metrics_c7.py` compute the quantities, denominators and scoring rules of Decision C7 correctly? C7 was approved after the existing `metrics.py` was written, and T001 showed they disagree. A viva or reviewer will ask whether the headline denominators (for example "unresolved cases stay in the precision denominator") are enforced by tests and not only described in prose.

## 2. Expected behaviour (hypotheses, written before the first run)
- Label-free rates use all `N` primary cases, and the six outcome categories partition them.
- End-to-end retrieval uses all `N`; conditional retrieval uses only cases with a mapped profile in the R2 pool.
- An automatic assignment is **incorrect and stays in the verified-precision denominator** if the selected candidate is a different person, if no candidate is the person, or if the case is unresolved. Only uncertain and unverifiable cases leave it, and they appear in all-wrong and all-right brackets.
- E1 weights are `N_h/n_h`; E2 weights are `(N_h/n_h)·g_i`. Census strata get no sampling interval. A bootstrap interval is withheld when sparse, when the minimum stratum size is unspecified, when a stratum is too small, and always for zero errors.
- The module fails loudly (raises) on inconsistent input instead of dropping cases.

## 3. Environment
Python 3.12.5, pytest 8.4.2, macOS Darwin 25.5.0, git `6d31cbe` (working tree dirty; `metrics_c7.py` and the two test files are untracked). SHA-256: `backend/hammer_pilot/metrics_c7.py` `0d3c2afad99d03fc069b8a230e52ad26f1fa4e66f3d5e8a4a4ebdbb4f05872ed` (517 lines); `backend/tests/test_metrics_c7.py` `a27067af41bb3744cdaaab3509a24a2c8791b3aa372db72bbe0f67678eb534b2` (404 lines). `metrics.py` is unmodified (`git diff` against HEAD is empty; SHA-256 `a6433628b1d384f1082028c03060bf731e7a3f15db1fc8c5403c624373dfb657`). The module reuses only the Clopper–Pearson and zero-event helpers of `metrics.py`.

## 4. Data
**Synthetic only.** Small hand-built case sets whose expected values were computed by hand in the test source. No benchmark data, no captures, no network, no ORCID.

## 5. Procedure and commands
```
cd backend
PYTHONDONTWRITEBYTECODE=1 DATABASE_URL=sqlite+aiosqlite:///:memory: \
  .venv/bin/python -m pytest tests/test_metrics_c7.py -p no:cacheprovider -v --no-header
```
Test groups (49 test items): input validation (13 parametrised and individual checks); sample validation and secondary-case exclusion; label-free rates over all `N` and the six-category partition; end-to-end versus conditional retrieval with a hand-computed example; R2-pool-only mapping; the verified scoring table (8 rows plus error cases); the precision denominator with unresolved and no-match cases; all-wrong and all-right brackets; unverified automatic assignments; benchmark precision; reporting classes; E1 and E2 weights on a three-stratum example; census handling; per-stratum Clopper–Pearson; unsampled and negligible-weight strata; bootstrap reproducibility, withholding rules and census-fixed resampling; zero-error and sparse regimes; provisional parameter labelling; verified retrieval with cannot-tell bounds; audit label-error and bracket; a full-report determinism test; the replay-row builder; and a static check that the module imports no network library and reads no ORCID field.

**Mutation sanity check.** Six deliberate defects were introduced one at a time into a copy of the module (script `RAW_OUTPUTS/T002_run1/scripts/mutate.py`), the test file run, and the module restored byte-identically (SHA-256 confirmed before and after).

## 6. Results
| Check | Expected | Actual |
|---|---|---|
| `test_metrics_c7.py` | all pass | **49 passed**, 1.24 s |
| Full backend suite with the new tests | 236 existing + 49 + 5 smoke (T003) | **290 passed**, 9.39 s |
| Mutant M1: unresolved dropped from the precision denominator | detected | 3 tests fail |
| M2: resolved-without-matching-candidate dropped | detected | 3 tests fail |
| M3: E1 weight wrongly multiplied by `g` | detected | 1 test fails |
| M4: label-free denominator excludes provider failures | detected | 1 test fails |
| M5: end-to-end denominator restricted to mapped cases | detected | 1 test fails |
| M6: sparse regime disabled, so a bootstrap runs on zero errors | detected | 2 tests fail |

**Mutation attempt note.** The first M5 attempt did not apply (a search string mismatched) and the console printed the previous mutant's result. This was noticed, the pattern was corrected, and M5 was rerun. The table above records the valid rerun. The raw file `mutation_check.txt` is from a complete second pass of all six mutants.

## 7. Verified denominators (worked example from the tests)
Seven automatic assignments: two correct, one resolved-but-different, one resolved with no matching candidate, one unresolved, one uncertain, one unverifiable. Primary precision: 2 of 5 (the different, the no-match and the unresolved cases stay in). Risk: 3 of 5. All-wrong bracket: 2 of 7. All-right bracket: 4 of 7.

## 8. Interpretation
The tests demonstrate that the implementation matches the C7 table on hand-computed fixtures and that the mutation sanity check would catch six realistic denominator, weighting and inference mistakes. This demonstrates **code correctness against the specification as I read it**. It does not demonstrate that the specification is statistically optimal, or that the estimators perform well on real data.

## 9. Development history (kept for traceability)
- Before the first test run, one edit was made to the module: per-stratum counts for proportion quantities are cast to integers.
- First run: 30 passed, 1 failed (stopped on first failure). Cause: a test fixture for the reporting-class test omitted `label_contradicted` for an audited case with a definite label. The module correctly raised an error. The fixture was fixed.
- Second run: 47 passed, 2 failed. Causes: the same missing field in the verified-retrieval fixture, and a source-text check that was too fragile because prose mentions "ORCID". Both are test-side. The check was replaced by a regular expression that detects quoted field names or attribute access.
- Third run: 49 passed. **No change was made to the module's behaviour to make a test pass.**

## 10. Limitations and sources of error
- The tests encode my reading of C7. A misreading would be encoded identically in code and tests (the mutation check does not protect against this).
- Hand-computed expectations cover small cases. There is no property-based or large-sample test of the bootstrap (it is checked for reproducibility, plausibility and withholding rules, not for nominal coverage).
- The bootstrap uses the standard-library generator seeded with a text key (`seed|quantity|estimand`). This is a design choice not stated in the protocol.
- The default values in `InferenceSettings` are the provisional thresholds of Decision C5 and are labelled as such in the output. They are not frozen parameters.

## 11. Methodological ambiguities found (for the research director)
1. **Audit label-error definition.** C7 says "verified label contradicts the benchmark label" without defining the contradiction. The module takes it as an adjudicated flag supplied with the record, and does not infer it.
2. **Reporting class when reviewers cannot tell for the selected candidate.** The module places such an automatic case in the *Uncertain* class (so the class counts match the bracket counts). C7 does not say so explicitly.
3. **Verified retrieval for an unresolved case, and for cannot-tell candidates.** Unresolved cases are excluded from verified retrieval denominators and counted; cannot-tell candidates produce lower and upper bounds. C7 says only "verified cases with a definite label".
4. **Which pool.** Mapping and retrieval use the R2 (name-only) pool, per the instruction; C7's table says "the pool".
5. **Case with no full Stage B judgments.** A resolved automatic case judged "different" without full pool judgments is reason `resolved_different`, because "no matching candidate" cannot be established without every candidate judged.

## 12. Artifacts
`RAW_OUTPUTS/T002_run1/`: `pytest_test_metrics_c7_verbose.txt`, `pytest_full_suite_with_c7.txt`, `mutation_check.txt`, `scripts/mutate.py`. Hashes: `RAW_OUTPUTS/SHA256SUMS.txt`.

## 13. What we learned and next step
The C7 definitions are implementable and testable. T003 cross-checks the module on real captures against independent artifacts. The next engineering step toward the main experiment is to resolve the ambiguities above (director), then build the remaining protocol tooling (one-case-per-block selector, sizing script, packet builder), each after its own authorisation.
