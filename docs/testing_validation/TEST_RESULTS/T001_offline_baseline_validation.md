# T001: Offline baseline validation (historical record)

**Test ID:** T001 (run 1 original, run 2 evidence re-capture) | **Date:** 20 November 2026 | **Type:** existing automated suites, replay, reproducibility, leakage and safeguard checks, metrics-gap probe | **Status:** PASS for items 1 to 8; one documented gap (item 9)

> **Historical baseline.** This record describes the repository **before** the C7 metrics module existed. None of these results come from `metrics_c7.py` (see T002 and T003). Run 1 results were observed in the working session; only the full pytest output was saved at the time. Run 2 re-executed the same commands afterwards to preserve raw output. It is a new run record, and run 1 is not overwritten. Times of day were not recorded.

## 1. Question and reason
Can the existing HAMMER implementation be validated offline, using only saved captures, before any new provider request or evaluation step? The test establishes a trustworthy starting state: what passes, what reproduces, and where the existing tooling differs from the accepted protocol (Decisions A, B, C and integrated protocol v0.2).

## 2. Expected behaviour
- All existing automated tests pass.
- Replaying the saved 50-case smoke capture completes without error, with consistent row counts, and is byte-reproducible.
- All saved provider responses match their recorded hashes.
- The six outcome categories stay distinguishable in code.
- Automatic assignments respect the weak-evidence safeguards.
- No benchmark ORCID appears in prediction, evidence or reviewer-facing artifacts.

## 3. Environment
macOS (Darwin 25.5.0); Python 3.12.5 (backend venv); pytest 8.4.2. Git `main` at `6d31cbe`; working tree dirty (untracked `docs/` and `paper/` files, tracked `backend/academic_search.db` modified; not touched by these tests). Database SHA-256 before and after: `3659ab2867e43b4726d8a501c10389c1a889d6c2e50d5d6b26dbef2e0e7c56c8`. Run 2 was executed after `metrics_c7.py` and its tests had been added as untracked files. Run 2's pytest command therefore excluded the two new test files, so that it reproduces the baseline count. No environment variables overrode resolver weights or thresholds (`.env` holds only `ENABLE_OPENALEX`, `DATABASE_URL`, `OPENALEX_MAILTO`).

## 4. Data
Synthetic fixtures inside the existing test suite; the 50-case, 23-block LAGOS-AND smoke capture in `research_data/lagos_and_v2/smoke_v1/` (92 successful provider responses, 42 author and 50 works requests; plus a preserved failed attempt of 40 requests); benchmark gold register for the leakage scan (read in memory, never printed). **The smoke sample is not a probability sample**, and cases within a block are not independent.

## 5. Procedure, commands and results
All commands ran from `backend/` with `PYTHONDONTWRITEBYTECODE=1`; tests also set `DATABASE_URL=sqlite+aiosqlite:///:memory:`.

| # | Check | Command or method | Expected | Actual |
|---|---|---|---|---|
| 1 | Full backend suite | `.venv/bin/python -m pytest tests -p no:cacheprovider -q --no-header -rfE` | all pass | **236 passed**, 2 warnings (a Starlette `anyio` deprecation, a `datetime.utcnow()` deprecation in a test); 10.50 s in run 1, 8.52 s in run 2 |
| 1a | Pilot, replay, capture, metrics and LAGOS-prep tests (5 files) | same, five files | all pass | 83 passed |
| 1b | Resolver, scoring, policy, candidates, enrichment tests (8 files) | same, eight files | all pass | 97 passed |
| 2 | Replay | `.venv/bin/python -I scripts/replay_hammer_pilot.py --pilot-dir ../research_data/lagos_and_v2/smoke_v1 --out-dir <new dir>` | 50 cases × 3 conditions × 3 policies = 450 predictions; 50 × 2 arms = 100 retrieval rows; 50 × 3 conditions = 150 snapshots | 450 / 100 / 150 |
| 3 | Reproducibility | `.venv/bin/python -I scripts/verify_hammer_pilot_reproducibility.py --pilot-dir <smoke_v1> --work-dir <new dir>` | replay twice, byte-identical | `identical: True`; **1,897,516 bytes compared (run 1)**, 1,897,618 (run 2; see below) |
| 4 | Replay against committed outputs | `cmp` of each output file against `smoke_v1/replay/` | identical | `evidence_snapshot.jsonl`, `predictions.csv`, `retrieval.csv` byte-identical (hashes below). `run_manifest.json` differs only in `git_sha` and `git_status_sha256` in run 1 |
| 5 | Capture integrity | `load_index` and `verify_capture_hashes` on `captures/` | every body matches its recorded SHA-256 | 92 of 92 match, all HTTP 200. The preserved failed attempt: 40 entries, **all HTTP 401** |
| 6 | Outcome vocabulary | read `hammer_pilot/replay.py` (`evaluate_policies`) and the tests | `provider_failed`, `empty_pool`, `no_score`, `manual`, `unresolved`, `auto` distinct | distinct in code; covered by passing unit tests (`test_provider_failure_versus_successful_empty`, `test_p0_null_top_score_is_no_score_in_every_policy`, and others). **In the smoke data only `auto` (4 for C1 with the selective policy) and `manual` (46) occur**, so the other four categories are exercised only by unit tests |
| 7 | Safeguards | `scripts/offline_checks.py` and `safeguard_snapshot_check.py` (copies in `RAW_OUTPUTS/T001_run2/scripts/`) | automatic rows satisfy score ≥ 0.75, margin, ≥ 2 observed signals, a non-zero corroborating signal, no unscored competitor, no mismatched signal sets | 11 `selective_policy_v2` automatic rows checked; **0 violations**. C0 under the selective policy: 0 automatic. All 4 C1 automatic assignments came from single-candidate pools, so margin and dominance were waived (rule P3) |
| 8 | Leakage | exact-string search for the 50 gold ORCID values and for any ORCID pattern | none in predictions, retrieval, snapshots, manifest, seeds, DOI register, case summaries, diagnostics | **0 gold hits and 0 ORCID-pattern hits** in each of those. The raw provider bodies hold 307 gold hits and 863 pattern hits (provider payload, expected, not reviewer-facing). The resolver source never references ORCID |
| 9 | C7 gap probe | synthetic calls to `hammer_pilot/metrics.py` | produce the C7 denominators | see section 7 |

**Run 2 byte count.** The reproducibility check compared 1,897,618 bytes, 102 more than run 1. The cause is verified: `run_manifest.json` lists a SHA-256 for every file of the package, and run 2 ran after `metrics_c7.py` existed, so the manifest gained that one line (plus a changed `git_status_sha256`). The three data outputs are unchanged. This shows that the manifest covers the whole package.

**Hashes (SHA-256, replay outputs identical to the committed files).**
`evidence_snapshot.jsonl` `a007ccb0fed124022c5127696d208161aa10efc9505c81afb0ae286ab186e1e8`; `predictions.csv` `a65f8b1da2f5bc7d18fdd45aba905895adf9af3edcffaf74517c304b982e51ee`; `retrieval.csv` `5dbd88a5424f83bb6f526c236b8b7fa7c07b7a351588a3e0c2259bf7fcf93358`.

## 6. Interpretation
The implementation reproduces its recorded smoke outputs exactly, the saved provider responses are intact, no benchmark label reaches the prediction or evidence artifacts, and the observed automatic assignments obey the safeguards. This is evidence of **software correctness and reproducibility**. It is not evidence of resolution accuracy.

## 7. Documented gap: existing `metrics.py` versus Decision C7
Confirmed by reading the code and by a synthetic probe (details of the probe were observed on the console and are not preserved as a raw file):
1. Automatic coverage drops uncertain cases from its denominator (3 drawn cases, 1 uncertain, denominator 2). C7 requires all `N`.
2. There is no end-to-end success@k and no end-to-end MRR; only conditional recall and conditional MRR exist.
3. The mapping rate is still named `catalog_coverage` and is computed on the union of the R0 and R2 pools.
4. There is no all-wrong or all-right bracket, no unverifiable state, no reporting classes, no strata, no E1/E2 weights, no bootstrap and no sparse-count handling.
This is a mismatch with the later-accepted protocol, not a defect in the code against its original specification. It motivated T002.

## 8. Limitations and sources of error
- Replay re-runs scoring on saved responses; it does not test live provider behaviour, rate limits or schema drift.
- The smoke sample is 50 cases in 23 blocks and is not independent. Nothing here estimates performance.
- The leak scan finds exact gold strings and ORCID-shaped strings. It does not detect indirect leakage (for example through names or affiliations).
- The safeguard check examined 11 automatic rows only.
- Run 1 subset counts (83 and 97) were observed in the console and later re-captured in run 2; the run 1 console output itself was not saved.

## 9. Artifacts
`RAW_OUTPUTS/T001_run1/pytest_full.txt` (original full-suite output, saved at the time). `RAW_OUTPUTS/T001_run2/`: `environment.txt`, `pytest_baseline_236.txt`, `pytest_subset_pilot_lagos.txt`, `pytest_subset_resolver.txt`, `replay_stdout.txt`, `replay_hashes.txt`, `reproducibility_check.txt`, `capture_hash_check.txt`, `offline_checks_output.txt`, `safeguard_snapshot_check_output.txt`, `scripts/`. Integrity hashes: `RAW_OUTPUTS/SHA256SUMS.txt`.

## 10. What we learned and next steps
The baseline is sound. The metrics tooling needed to be aligned with Decision C7 (T002), and the C7 module needed a cross-check against independent artifacts (T003). Not yet tested: live provider behaviour, any outcome category other than `auto` and `manual` on real data, and every evaluation step in integrated protocol section 7 beyond offline replay.
