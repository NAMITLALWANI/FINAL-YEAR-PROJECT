# T009: two-stage review records, agreement statistics and conversion to C7 (Decision B5 to B7)

**Test ID:** T009 (run 1) | **Date:** 20 November 2026 | **Type:** unit tests on synthetic records; mutation sanity check | **Status:** PASS (31 tests; 11 of 11 mutants detected) | **No reviewer was recruited or assumed, and no real label exists.**

> T001 to T008 and all their raw outputs are preserved unchanged.

## 1. Question and reason
Decision B5 requires a two-stage record schema (one Stage A row per reviewer per case; one Stage B row per reviewer per case per candidate), independent reviewers, a third-person adjudicator, agreement reported with counts, and the original reviewer rows kept. C7 needs, for each audited or verified case, a label state, a group-purity judgment and a judgment for every pool candidate under the real candidate identifier. Does the record layer enforce the independence and completeness rules, compute agreement correctly, and convert adjudicated labels to exactly what the C7 module consumes?

## 2. Expected behaviour
Rows are validated (vocabularies equal to C7's, confidence 1 to 5, boolean ORCID-encounter flag, non-negative minutes). A case needs exactly two distinct reviewers, each judging every candidate in the packet; the packet builder may not be a reviewer; a disagreement on status, purity or any candidate requires an adjudication row from a third person who is neither reviewer nor builder; a resolved adjudication judges every candidate; reviewer rows are never overwritten. Agreement is reported as raw agreement, Cohen's kappa and counts, with kappa undefined when chance agreement is 1. The reviewer-time helper takes the available hours explicitly and applies *N* = ⌊60*H*/(*t_A* + *k t_B*)⌋. The conversion applies the crosswalk, so reviewer-facing opaque ids never reach C7.

## 3. Environment
Python 3.12.5, pytest 8.4.2, git `6d31cbe`, dirty tree (untracked files only). SHA-256: `backend/hammer_pilot/review_records.py` `45cedaedcdf35f029177d2aff2d6a28fd5d9e7dc57ed15be3bd554d649a6b005` (215 lines); `backend/tests/test_review_records.py` `83a49633d404a13941edebbc29221139189990a1dcccf1c17414b77ad1123ab7` (227 lines).

## 4. Data
Synthetic records only (invented reviewer names, candidates and judgments). Hand-computed kappa examples: 50 pairs with raw agreement 0.7, chance agreement 0.5 and kappa 0.4; a 14-pair three-category example.

## 5. Procedure and commands
`PYTHONDONTWRITEBYTECODE=1 DATABASE_URL=sqlite+aiosqlite:///:memory: .venv/bin/python -m pytest tests/test_review_records.py -p no:cacheprovider -v --no-header` (from `backend/`); mutation check `RAW_OUTPUTS/T009_run1/scripts/mutate_t009.py`.

## 6. Results
| Check | Expected | Actual |
|---|---|---|
| `test_review_records.py` | all pass | **31 passed**, 0.08 s |
| Row validation | bad vocabulary, range, boolean or missing id rejected | 13 rejected cases |
| Independence and completeness | two distinct reviewers; every candidate judged; builder not a reviewer; adjudicator is a third person | enforced (separate tests for each) |
| Disagreement handling | status, purity or candidate disagreement requires adjudication; raw rows untouched | enforced |
| Kappa | 0.4 for the 50-pair example; 1, −1 and undefined edge cases | exact |
| Conversion | crosswalk applied; C7 audit and scoring results as expected | `consistent` when reviewers agree with the benchmark mapping; `contradicted` with false and missed mapping when they do not; automatic cases scored `correct` and `incorrect` as expected |
| Time helper | ⌊60 × 10/(15 + 3 × 3)⌋ = 25 | 25; hours required explicitly |
| Templates and CSV | exact headers, no data rows, no overwrite | as expected |
| Mutants U1 to U11 | each detected | **11 of 11** (the first pass detected 10; see below) |

## 7. Interpretation
The record layer enforces the independence and completeness rules of Decision B and produces the exact inputs the C7 audit and verified-precision functions need, so a future review can move from CSV files to a C7 report without hand conversion. This is evidence of **correct implementation**, not of reviewer quality.

## 8. Development history
First mutation pass: 10 of 11 detected. Mutant U9 (ORCID encounters recorded in Stage B ignored) survived because tests set the flag only in Stage A rows. A Stage B-only test was added; the second pass detected all 11. The first pass's raw output was overwritten.

## 9. Limitations and points for the director
- Reviewer names, independence attestations, availability and hours are deferred (personnel); the code assumes none.
- Adjudication is required only for disagreement (v0.2 section 5.4 reading); Decision B5 can also be read as requiring an adjudicator's final label for every case. Please confirm.
- Group purity "unresolved" and the label state "unresolved" are different fields, as in T005.
- Kappa is unstable at small *n*; the report always carries the counts.

## 10. Artifacts
`RAW_OUTPUTS/T009_run1/`: `pytest_test_review_records_verbose.txt`, `mutation_check_t009.txt`, `scripts/mutate_t009.py`. Hashes: `RAW_OUTPUTS/SHA256SUMS.txt`.
