# T005: C7 metrics module, validation of the four director clarifications (group validity and verified retrieval)

**Test ID:** T005 (run 1) | **Date:** 20 November 2026 | **Type:** unit tests on synthetic fixtures, mutation sanity check, regression re-run | **Status:** PASS (16 new tests; 90 earlier C7 tests; full suite 342; 10 of 10 mutants detected)

> T001 to T004 and all their raw outputs are preserved unchanged. T004's report is not edited. Two of T004's audit definitions are **superseded** by this record (section 5). The module and test versions that T004 describes are preserved byte-identically in `RAW_OUTPUTS/T005_run1/pre_T005_versions/` (hashes in `pre_T005_hashes.txt` equal the values in T004), so T004 stays reproducible.

## 1. Question and reason
The director approved the four C7 points raised in T004 with clarifications. Does `metrics_c7.py` now keep benchmark-group validity apart from case-level candidate verification, treat a pure unresolved group as indeterminate, keep overall benchmark-derived retrieval untouched by any audit, and keep the approved conditional verified-retrieval definition with every other judgment category reported separately? These decisions change the audit error-rate denominator and the retrieval denominators.

## 2. Expected behaviour (written before implementation)
1. Group-purity states are **pure, impure, unresolved**. A pure group whose case label is unresolved is **indeterminate**, not consistent. Neither counts in the error numerator or the definite-label denominator; both stay in the bracket.
2. A confirmed impure group is a benchmark contradiction **when the case label is definite**. An uncertain or unverifiable case stays **outside** the definite-label error-rate denominator even if its group is impure. Group impurity is reported separately (`group_validity`), and the uncertainty bracket is preserved.
3. Overall end-to-end retrieval keeps **all N** primary cases and is byte-identical with or without verified labels. Verified retrieval uses only cases with a definite verified label, and excluded categories are reported separately. No audit result adjusts overall retrieval.
4. Conditional verified retrieval keeps its denominator: cases with a verified-same candidate in the R2 pool. Every other judgment category is reported separately.

## 3. Environment
Python 3.12.5, pytest 8.4.2, macOS Darwin 25.5.0, git `6d31cbe`, dirty working tree (untracked files only added by this work; nothing staged or committed). SHA-256 after T005: `backend/hammer_pilot/metrics_c7.py` `776e02e8e7d040a325f533f0868cbe19a539de76a485fbd46612e14f27c41d8c` (620 lines); `backend/tests/test_metrics_c7.py` unchanged `7609afc9d8e87af6ffd392492569c93d43557fd38d818094a26797f5b72c4571`; `backend/tests/test_metrics_c7_rulings.py` `29b85b9759a028dd27e10a65f9ec64fda49e1aed0e052904c37c734822451403` (3 tests updated); `backend/tests/test_metrics_c7_t005.py` `27e75226e8bb64f38663246d058e27c4bad95bca312b286444e2ff894e28703b` (188 lines, new); `backend/tests/test_metrics_c7_smoke.py` unchanged `4067d7cabc1d98a1257199f491cb8186662ae7e142e6b909eff3c45ea2b2d8a6`; `backend/hammer_pilot/metrics.py` unchanged `a6433628b1d384f1082028c03060bf731e7a3f15db1fc8c5403c624373dfb657`.

## 4. Data
Synthetic only for the new tests. The T003 smoke test was re-run unchanged on the smoke capture (read-only). No provider request, no frozen artifact, no parameter changed, and no sizing script written.

## 5. What changed
**Module** (scripted patch preserved: `scripts/patch_t005.py`):
- Group-purity states are now `pure`, `impure`, `unresolved` (the earlier `cannot_tell` purity value is no longer accepted; judgments of individual candidates keep `cannot_tell`).
- `audit_status` reordered: an uncertain or unverifiable case label is indeterminate first, whatever its purity or Stage B evidence. For a definite case: any reason (impure group, false mapping, missed mapping) gives *contradicted*; otherwise an unresolved purity, or a pure group with an unresolved case label, gives *indeterminate*; then a cannot-tell mapped candidate or incomplete Stage B judgments give *indeterminate*; else *consistent*.
- `audit_label_error` gained `group_validity`: purity counts for the three states plus `not_recorded`, an impure-group rate over cases with determinate purity (pure plus impure), impure counts by case label state, and the count of impure groups outside the definite-label denominator. `unresolved_not_contradicted` was removed because that case is now indeterminate.
- `verified_retrieval` gained `judgment_categories` (verified-same in pool, cannot-tell only, verified no match, empty pool, and the subset of verified-same cases that also have cannot-tell candidates) with a note that the conditional denominator is `verified_same_in_pool`.
- Report notes now state that overall benchmark-derived retrieval keeps all N and is never adjusted by any audit, and that group impurity is reported separately.

**Superseded T004 definitions.** (a) T004 recorded a pure unresolved group as *consistent*; it is now *indeterminate*. (b) T004 counted an uncertain case with an impure group as *contradicted* (in numerator and denominator); it is now *indeterminate* and its impurity appears in `group_validity`. Three T004 tests that encoded these definitions were updated (the `cannot_tell` purity row, the impure-and-uncertain row, and the impure-versus-unresolved test). No other earlier test needed a change. The edit script is preserved (`scripts/patch_t004_tests_for_t005.py`).

## 6. Procedure and commands
From `backend/`, with `PYTHONDONTWRITEBYTECODE=1 DATABASE_URL=sqlite+aiosqlite:///:memory:`:
```
.venv/bin/python -m pytest tests/test_metrics_c7_t005.py -p no:cacheprovider -v --no-header
.venv/bin/python -m pytest tests/test_metrics_c7.py tests/test_metrics_c7_rulings.py tests/test_metrics_c7_smoke.py -p no:cacheprovider -v --no-header
.venv/bin/python -m pytest tests -p no:cacheprovider -q --no-header -rfE
```
Mutation check: `scripts/mutate_t005.py` (ten defects, one at a time; the module is restored byte-identically afterwards).

**New tests (16), by clarification.** *1:* the three purity states and rejection of `cannot_tell`; pure group with unresolved label indeterminate, outside the definite denominator, kept in the bracket; unresolved purity as its own state; Stage B contradictions still count under unresolved purity or label. *2:* uncertain and unverifiable cases with an impure group stay outside the definite denominator (two parametrised cases); a resolved impure case is a contradiction; Stage B evidence does not pull an uncertain case in; impure-group rate uses determinate purity only; cases without a purity record are counted. *3:* overall retrieval, label-free and benchmark selective sections are JSON-identical with and without verified labels and keep all N; verified retrieval uses only definite cases with excluded categories counted separately; the report states that overall retrieval is never adjusted. *4:* the conditional denominator is the verified-same cases only, with all other categories reported; lower and upper bounds with cannot-tell candidates; the definition is unchanged without cannot-tell candidates.

## 7. Results
| Check | Expected | Actual |
|---|---|---|
| Patch applied, earlier tests re-run | only tests encoding the superseded definitions fail | 3 failed, 87 passed; exactly the three T004 tests encoding the superseded definitions |
| After updating those three tests | all earlier C7 tests pass | 90 passed |
| `test_metrics_c7_t005.py` | all pass | 16 passed (one fixture error in the test file was found and fixed on the first run: judgments were keyed to candidates absent from the pool, and the module correctly rejected them) |
| Baseline excluding all four C7 test files | 236 | **236 passed** |
| Full backend suite | 236 + 49 + 36 + 16 + 5 | **342 passed**, 10.64 s |
| Mutants P1 to P10 | each detected | **all 10 detected** (failing tests: 2, 2, 14, 2, 1, 3, 1, 1, 2, 2) |

Mutants: P1 pure unresolved treated as consistent again; P2 unresolved purity treated as consistent; P3 uncertain impure case pulled into the definite denominator; P4 impure groups outside the definite denominator not reported; P5 impure-group rate denominator includes unresolved purity; P6 conditional denominator includes cannot-tell-only cases; P7 judgment categories swapped; P8 overall retrieval adjusted by verified label; P9 `cannot_tell` accepted again as a purity state; P10 uncertainty bracket loses indeterminate cases. Module hash before and after: `776e02e8…`. P3 produced 14 failures partly because removing the early return also exposes uncertain cases to the purity-required error path. It is still a valid detection.

## 8. Interpretation
The module separates benchmark-group validity from case-level verification as specified, and overall benchmark-derived retrieval is demonstrably independent of verification (identical output with and without labels). This is evidence of implementation correctness against the written clarifications. It does not show that real reviewer records will fit these states, and no human-reviewed data exists.

## 9. Limitations and sources of error
- Hand-built fixtures; a fixed list of author-chosen mutants.
- The impure-group rate is an unweighted count over the audited sample, with an exact interval conditional on determinate purity; it describes only the audited non-automatic frame.
- Verified retrieval still selects cases by label state (resolved), so a resolved case with an impure group stays in verified retrieval. The clarification did not address this.

## 10. Artifacts
`RAW_OUTPUTS/T005_run1/`: `pytest_full_suite.txt`, `pytest_baseline_without_c7_files.txt`, `pytest_test_metrics_c7_t005_verbose.txt`, `pytest_test_metrics_c7_earlier_files_after_T005_verbose.txt`, `mutation_check_t005.txt`, `c7_report_smoke_toolcheck_after_T005.json` (format check only), `pre_T005_versions/`, `scripts/`. Hashes: `RAW_OUTPUTS/SHA256SUMS.txt`.

## 11. Remaining points for the research director
1. **Purity vocabulary.** I read "keep pure, impure and unresolved as separate group-purity states" as replacing the earlier third value `cannot_tell` with `unresolved`. Please confirm that the two are the same state. A pure group with an unresolved case label is handled separately (also indeterminate).
2. **Impure group with an uncertain case.** It is outside the definite-label error rate, appears in `group_validity`, and enters only the all-wrong end of the bracket. Please confirm that the all-right end should not count it.
3. **Impure group with a resolved case label in verified retrieval.** It stays in because the cases are selected by label state. Please confirm or ask for its exclusion.

## 12. What we learned and next step
Group validity and candidate verification are now two reported quantities, which fixes what the Stage A record must capture (a three-state purity judgment) and keeps the audit estimate from leaking into overall retrieval. The next engineering step is in the accompanying report.
