# T016: C7 report assembly from a frozen selection, capture, replay and verified labels

**Test ID:** T016 (run 1) | **Date:** 20 November 2026 | **Type:** unit tests; mutation sanity check; read-only regression on the smoke capture | **Status:** PASS (7 tests; 5 of 5 mutants detected) | **No provider request.**

> T001 to T015 and all their raw outputs are preserved unchanged.

## 1. Question and reason
Runbook step 14 had no tool: nothing assembled `metrics_c7.Case` records from the manifest, seeds, replay output, benchmark mapping and verified labels. Can the real report be produced by a tested script?

## 2. Expected behaviour
Benchmark mapping reproduces the independent smoke diagnostic; secondary cases are never primary and never receive verified labels; a missing primary prediction, an unknown predicted case, a stratum disagreement between seeds and manifest, or an unexpected verified field is refused; without verified labels the report says verification is pending and every case is benchmark-derived; a partial set of labels for automatic cases is reported as incomplete.

## 3. Environment
Python 3.12.5, pytest 8.4.2, git `6d31cbe`, dirty tree. SHA-256: `backend/hammer_pilot/report_assembly.py` `939a334da6eb528db1fd1f3ca0590d6b2061b323dbbbfcb98172232e6384cb75`; `backend/scripts/assemble_c7_report.py` `5900dfeef91387392bce790132a448b05fafe58ee2237bca3ba905cd9f8c77a2`; `backend/tests/test_report_assembly.py` `972140cfd5a360c9c8b8806590885727073124d0a8087c3d1b6fbf44d94ec8f8`.

## 4. Data
Hand-made synthetic cases; the 50-case smoke capture and the protected gold register (in memory only).

## 5. Results
| Check | Expected | Actual |
|---|---|---|
| `test_report_assembly.py` | all pass | **7 passed** |
| Smoke benchmark mapping | expected ORCID in the R2 pool for 38 of 50 (T003) | 38 of 50; no gold ORCID in the mapping output |
| Report without labels | verification pending; 6 of 6 primary cases benchmark-derived | as expected |
| Mutants R1 to R5 (mapping comparison, stratum check, primary flag, completeness rule, secondary-label check) | each detected | **5 of 5** |

## 6. Interpretation and limitations
The step from replay to report is implemented and tested. It has not run on real study data (none exists). The script reads inference settings from the freeze parameters and the bootstrap seed from the freeze's main seed.

## 7. Artifacts
`RAW_OUTPUTS/T017_run1/mutation_check_t015_t017.txt` (R1 to R5), pytest output in `RAW_OUTPUTS/T017_run1/pytest_full_suite.txt`.
