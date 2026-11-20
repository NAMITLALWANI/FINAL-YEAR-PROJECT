# T017: capture stop-condition guard and the review driver (works capture, packet release)

**Test ID:** T017 (run 1) | **Date:** 20 November 2026 | **Type:** unit tests with mock transports; mutation sanity check; in-scratch dry run on the smoke data | **Status:** PASS (20 tests; 19 of 19 mutants detected after strengthening; full suite 585) | **No provider request.**

> T001 to T016 and all their raw outputs are preserved unchanged.

## 1. Question and reason
The ratification sheet required stop conditions that the capture did not have (a stop level on provider-reported cost; three consecutive server errors or timeouts), and runbook step 11 (candidate-works capture and the packet driver) had no tool. Can both be built so that a stop saves the offending response first, a leak aborts a release, and nothing reviewer-facing shows a case's origin?

## 2. Expected behaviour
The guard stops before the next request at 80% of the cost ceiling or after three consecutive 5xx or transport errors (success resets; 4xx does not count); the failing response is already saved and hashed. The works capture makes one hashed, budgeted request per distinct candidate, never stores the key or mailto, is resumable, and propagates provider and guard stops. The release builds Stage A and Stage B packets from allow-lists, scans them (zero findings or abort), shuffles by hash, writes reviewer files and a separate protected directory, and contains no ORCID, OpenAlex identifier or origin flag. Audit cases must be non-automatic primary cases of the primary condition and policy.

## 3. Environment
Python 3.12.5, pytest 8.4.2, git `6d31cbe`, dirty tree. SHA-256: `backend/hammer_pilot/guarded_transport.py` `7ddb764be9f46af89dcd035bb236b4879cf808b625bf09affee635814ecdc79d`; `backend/hammer_pilot/review_driver.py` `6d618d9d61ce1020c3e78d459721815f327a63848528b1fff3e574fa14c40ea6`; `backend/scripts/prepare_review_release.py` `e148d8c4594c6eea84acb585144a8845672170e82e349b1590b73c69cb2b7d01`; `backend/scripts/capture_hammer_pilot.py` `45d6f7b1fc62a9e374847592905e6564dc4b53f3f496362bdc6b4a6991454cd4`; `backend/tests/test_guarded_transport.py` `1be9bf57872d07780b32591e354700e40b0c23ea349f4c64a541b54ec7bee85a`; `backend/tests/test_review_driver.py` `8a22dffde7ab455018a94174dd18601db0607dac6c2dd90b0c4efdf0aa4d9c56`.

## 4. Data
Synthetic only for the tests. The dry run used the smoke capture, the smoke seeds, the real archive rows and the protected gold register **in a scratch directory outside the repository**; its manifest is a stand-in that treats the 50 smoke cases as primary and four manual cases as the audit draw. It defines no study case.

## 5. Results
| Check | Expected | Actual |
|---|---|---|
| `test_guarded_transport.py` | all pass | **7 passed** |
| `test_review_driver.py` | all pass | **13 passed** (3 were added after the first mutation pass) |
| Full backend suite | all pass | **585 passed** |
| Mutants Y1 to Y4, G1 to G4, R1 to R5, D1 to D6 | each detected | **19 of 19**; the first pass detected 16 (D4 pool de-duplication, D5 failed works response, D6 condition and policy filter survived); tests were added and the check repeated. The first-pass output is preserved |
| Dry run on the smoke data | release built, scanned, split | 8 cases (4 automatic, 4 audit), 16 packets (8 Stage A, 8 Stage B), queue of 16, **zero leak findings**; reviewer directory holds packets and scan reports only; protected directory holds `crosswalk.json` and `case_flags.json` |
| Capture without `--allow-network` | refused | refused |

## 6. Interpretation and limitations
The guard and the driver are implemented and behave as specified on mock transports. The works capture has **never contacted OpenAlex**: the live response shape (and its cost field) is assumed from the candidate capture. The dry run's Stage B packets contain no works because no works capture exists. The allow-list keeps only display names of authors of each work; whether those names suffice for reviewers is for the reviewer-time pilot to show.

## 7. Artifacts
`RAW_OUTPUTS/T017_run1/`: `pytest_full_suite.txt`, `mutation_check_t015_t017.txt`, `mutation_check_t015_t017_first_pass.txt`, `environment.txt`, `scripts/mutate.py`.
