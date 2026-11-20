# T004: C7 metrics module, implementation and validation of the five director rulings

**Test ID:** T004 (run 1) | **Date:** 20 November 2026 | **Type:** unit tests on synthetic fixtures, mutation sanity check, regression re-run of T002 and T003 tests | **Status:** PASS (36 new tests, 54 earlier tests, full suite 326; 11 of 11 mutants detected), with new ambiguities in section 11

> T001, T002, T003 and all their raw outputs are preserved unchanged. Their recorded hashes refer to the module and test versions **before** T004. Those versions are kept byte-identical in `RAW_OUTPUTS/T004_run1/pre_T004_versions/` (hashes in `pre_T004_hashes.txt` match the values recorded in T002 and T003), so T002 and T003 remain reproducible.

## 1. Question and reason
The research director approved five rulings on the ambiguities found in T002 (with clarifications). Does `metrics_c7.py` now implement them exactly, and do the earlier tests still hold? The rulings change what counts as an audit error, which cases enter verified-retrieval metrics, and when "no matching candidate" may be claimed. Each is a denominator or numerator decision that a reviewer can challenge.

## 2. Expected behaviour (written before implementation)
1. **Audit label error is derived** from adjudicated records, with three reasons: impure benchmark group, false mapping, missed mapping. An impure group is automatically a contradiction; an unresolved group with a pure group is not. A case counts once in the numerator; reason counts are reported separately. A cannot-tell judgment is indeterminate, never an error.
2. **An automatic case that reviewers cannot verify** for the selected candidate stays in the Uncertain class.
3. **Ground-truth unresolved is distinct from HAMMER unresolved or abstention.** Only the former is excluded from verified-retrieval metrics; a HAMMER abstention (manual, unresolved, no score) never removes an otherwise adjudicable case.
4. **The R2 pool** is the primary pool for mapping and retrieval; R0 is descriptive and is not an input.
5. **"No matching candidate"** is claimed only when every candidate in the pool has a Stage B judgment and all are "different".

## 3. Environment
Python 3.12.5, pytest 8.4.2, macOS Darwin 25.5.0, git `6d31cbe`, working tree dirty (untracked files only added by this work; nothing staged or committed). SHA-256 after T004: `backend/hammer_pilot/metrics_c7.py` `08e15501a3b1c7dcb3a2592b97b05924b61b7b153affb9bad8074740791ed465` (587 lines); `backend/tests/test_metrics_c7.py` `7609afc9d8e87af6ffd392492569c93d43557fd38d818094a26797f5b72c4571` (405 lines); `backend/tests/test_metrics_c7_rulings.py` `563ed6d86e3504fe0c04fc5dd13cea8fa2d1254024887144199ee5db39b3bb42` (224 lines, new); `backend/tests/test_metrics_c7_smoke.py` unchanged `4067d7cabc1d98a1257199f491cb8186662ae7e142e6b909eff3c45ea2b2d8a6`; `backend/hammer_pilot/metrics.py` unchanged `a6433628b1d384f1082028c03060bf731e7a3f15db1fc8c5403c624373dfb657`.

## 4. Data
Synthetic only for the new tests. The earlier smoke test (T003) was re-run unchanged on the smoke capture, read-only. No provider request, no frozen artifact, no parameter changed.

## 5. What changed in the module
- **Case record:** the manual flag `label_contradicted` was removed (two sources of truth would have been ambiguous). A Stage A field `group_purity` (pure, impure, cannot_tell) was added; it belongs to a verified case.
- **Audit:** new `audit_reasons` and `audit_status`. Reasons: `impure_group` (group judged impure), `false_mapping` (a benchmark-mapped candidate judged different), `missed_mapping` (an unmapped candidate judged the same). A case with any reason is *contradicted*, even when its case label is uncertain or unverifiable (an impure group refutes the benchmark assertion that one person authored the group). Otherwise: *indeterminate* if the label is uncertain or unverifiable, the purity or a mapped candidate is cannot-tell, or a resolved case lacks a judgment for some pool candidate; else *consistent*. A definite audited case without a purity judgment raises an error. A ground-truth unresolved case with a pure group is *consistent* (not automatically a contradiction), counted separately as `unresolved_not_contradicted`. `label_errors` counts each case once; `reason_counts` may overlap and carry an explanatory note; the bracket treats indeterminate cases as all-right or all-wrong.
- **Verified retrieval:** `unresolved_no_unique_person` renamed `ground_truth_unresolved`; HAMMER abstentions are counted in `hammer_abstentions_included`, and `outcomes_of_cases_used` is reported; conditional Recall@k and conditional MRR were added (denominator: cases with a verified-same candidate; lower and upper bounds for cannot-tell candidates; cases with only cannot-tell candidates counted as `indefinite_mapped_cases`).
- **Scoring:** `resolved_no_matching_candidate` now requires a judgment for every pool candidate and all "different"; otherwise the reason is `resolved_different`. Both are incorrect and stay in the precision denominator.
- **Scope notes:** the report and verified-retrieval output state that the pool is the captured R2 pool and that R0 is descriptive only.

## 6. Procedure and commands
From `backend/`, with `PYTHONDONTWRITEBYTECODE=1 DATABASE_URL=sqlite+aiosqlite:///:memory:`:
```
.venv/bin/python -m pytest tests/test_metrics_c7_rulings.py -p no:cacheprovider -v --no-header
.venv/bin/python -m pytest tests/test_metrics_c7.py tests/test_metrics_c7_smoke.py -p no:cacheprovider -v --no-header
.venv/bin/python -m pytest tests -p no:cacheprovider -q --no-header -rfE
```
Mutation check: `RAW_OUTPUTS/T004_run1/scripts/mutate_t004.py` applies one defect at a time to the module, the two C7 synthetic test files are run, and the module is restored byte-identically (SHA-256 verified). The module patch and the test updates were scripted (`patch_t004.py`, `patch_old_tests_t004.py` in `scripts/`) and are preserved.

**Tests added (36, `test_metrics_c7_rulings.py`), by ruling.** *Ruling 1:* the removed flag; a 12-row table of derived audit statuses; impure versus unresolved group; Stage B reasons on an unresolved case; purity requirement and validation; once-per-case counting with separate, overlapping reason counts; indeterminate bracket; empty-pool case. *Ruling 2:* automatic cannot-verify case stays Uncertain, leaves the primary denominator, enters the bracket. *Ruling 3:* HAMMER abstentions stay in verified retrieval; only ground-truth unresolved cases are excluded and counted; a ground-truth unresolved automatic case is excluded from retrieval but scored incorrect; the two "unresolved" notions are separate counts; conditional verified retrieval on a hand-computed example. *Ruling 4:* the report states the R2 pool; the replay builder ignores an R0-only hit. *Ruling 5:* five judgment patterns for "no matching candidate"; both reasons stay in the denominator; verified miss requires complete judgments; an empty pool is a verified miss.

## 7. Results
| Check | Expected | Actual |
|---|---|---|
| Module patched, earlier tests re-run | tests relying on the removed flag or renamed key fail | 4 earlier tests failed (50 passed), all because of the deliberate API change (the flag, one key). Their fixtures were updated; the audit test was rewritten for the derived logic. No assertion about denominators was weakened |
| `test_metrics_c7_rulings.py` | all pass | **36 passed**, 0.26 s |
| `test_metrics_c7.py` + `test_metrics_c7_smoke.py` after T004 | all pass | **54 passed** (49 + 5), 2.06 s |
| Baseline excluding the three C7 test files | 236 | **236 passed** (unchanged) |
| Full backend suite | 236 + 49 + 5 + 36 | **326 passed**, 10.11 s |
| Mutants N1 to N11 | each detected | **all 11 detected** (failing tests: 5, 1, 1, 2, 5, 4, 3, 2, 2, 1, 2) |

Mutants: N1 impure group no longer a contradiction; N2 pure unresolved group counted as a contradiction; N3 numerator counts reasons instead of cases; N4 cannot-tell on a mapped candidate counted as an error; N5 HAMMER abstentions removed from verified retrieval; N6 ground-truth unresolved no longer excluded; N7 no-matching-candidate claimed without every candidate judged; N8 cannot-verify automatic case reported as Verified; N9 replay builder takes the R0 pool; N10 audit consistency claimed without every candidate judged; N11 verified miss claimed without every candidate judged. Module hash before and after: `08e15501…`.

**Note on the new tests passing first time.** All 36 new tests passed on their first run. This is why the mutation check was run: it shows that they can fail. A stray shell command (a `cat` waiting for input) stalled the first patching attempt; it wrote nothing, the module hash was confirmed unchanged, and the patch was then applied.

## 8. Interpretation
The module implements the five rulings as specified, and the earlier T002 and T003 checks still hold on the revised code. This is evidence of **implementation correctness against the written rulings**. It is not evidence that the rulings are statistically optimal or that the derived audit definition matches how reviewers will actually record judgments.

## 9. Limitations and sources of error
- The derivation is my operationalisation of the ruling. Reasons (b) and (c) use the benchmark-mapped set inside the pool: if the benchmark-mapped candidate is not in the pool, a wrong benchmark mapping cannot be detected from judgments alone.
- Fixtures are small and hand-built; no large-sample or property-based test; mutants are a fixed list chosen by the author.
- Synthetic Stage A and Stage B records do not exist as real data yet; no human-reviewed result is involved.

## 10. Artifacts
`RAW_OUTPUTS/T004_run1/`: `pytest_full_suite.txt`, `pytest_baseline_without_c7_files.txt`, `pytest_test_metrics_c7_rulings_verbose.txt`, `pytest_test_metrics_c7_and_smoke_after_T004_verbose.txt`, `mutation_check_t004.txt`, `c7_report_smoke_toolcheck_after_T004.json` (format check only), `pre_T004_versions/` with `pre_T004_hashes.txt`, `scripts/`. Hashes: `RAW_OUTPUTS/SHA256SUMS.txt`.

## 11. New ambiguities for the research director
1. **Ground-truth unresolved with a pure group** is recorded as *consistent* (not an error) and counted separately. It could instead be *indeterminate*. The rate changes only if such cases exist.
2. **Impure group with an uncertain or unverifiable case label** is counted as contradicted, because the benchmark's assertion of purity is refuted. Decision B says an impure group is labelled uncertain or unverifiable. Both statements hold in the module (the label class stays Uncertain or Unverifiable; the audit numerator counts it). Please confirm.
3. **End-to-end verified retrieval** also excludes ground-truth unresolved cases (as approved "keep as implemented"), whereas the C7 table says "cases verified with a definite label". Please confirm that the exclusion applies to end-to-end as well as conditional metrics.
4. **Conditional verified retrieval** was not in the earlier module. Its definition (denominator = cases with a verified-same candidate; cannot-tell-only cases shown separately) is mine.

## 12. What we learned and next step
The audit and retrieval definitions are now deterministic functions of adjudicated records. That also fixes the shape of the Stage A and Stage B records the reviewer tooling must capture: a purity judgment per case and a judgment for every candidate. The next engineering step is in the report that accompanies this record.
