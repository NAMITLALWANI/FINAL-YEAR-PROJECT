# T019: free-tier exploratory capture, two integration defects, and the benchmark-derived exploratory evaluation

**Test ID:** T019 (run 1) | **Date:** 20 November 2026 | **Type:** real provider capture (free keyless tier, stop-guarded), offline replay, benchmark-derived analysis, regression tests | **Status:** PARTIAL: 18 of 50 drawn cases captured before the free daily quota ended; analysis complete for what exists; **no independently verified result** | **No money was spent and no credential was used.**

> T001 to T018 and all their raw outputs are preserved unchanged.

## 1. Question and reason
Without a credential, spending or reviewers, how much of the evaluation can still be run on real data, and what does it show? The user ruled out any payment or key.

## 2. What was done
1. One keyless probe request showed that OpenAlex serves a small free daily budget (USD 0.10, shared per network address) without a key.
2. **Defect 1 (negative result).** The first capture attempt (freeze F2, exploratory sample) was refused locally by `capture.verify_seed_freeze`: `seeds_from_manifest.py` wrote a `seed_freeze.json` without `frozen_at`, `seeds_sha256` and `doi_register_sha256`. No request was made. Fixed in the writer; regression test `test_seed_freeze_is_accepted_by_the_capture_step`. F2 superseded by F3.
3. **Defect 2 (negative result).** The second attempt (F3) sent 70 requests and **all 70 were recorded as DecodingError**: the new stop guard rebuilt an already decoded body with the wire response's `content-encoding: gzip` header. Mock-transport tests had no compression and could not show it. No usable data; the run is preserved (`RAW_OUTPUTS/T019_run1/capture_run1_output.txt`; the capture directory under `eval_F3/`, marked SUPERSEDED). It consumed part of the free quota. Fixed; regression test `test_compressed_responses_survive_the_guard`, with a negative control showing that the test fails on the old code. F3 superseded by F4.
4. Freeze **F4** (manifest SHA-256 `f5ab53be60549d4e5eb9be916630b83d4ecf8c3a02d88e7a61b51fad6164838b`) was written and verified; the pilot (250 blocks) and an **exploratory sample of 50 blocks** (23 S, 24 M, 3 L; one primary case per block; main frame minus the smoke and pilot blocks; derived main seed 2736699991) were drawn offline.
5. Guarded keyless capture: 39 requests, 38 HTTP 200 and one HTTP 429 (the shared free quota ended), provider-reported cost USD 0.0218; **18 cases completed** (9 S, 9 M). The cases are processed in opaque-identifier order, unrelated to the strata, so they are a random subset of the drawn 50.
6. Offline replay of the 18 completed cases (a copied, restricted capture directory; nothing edited in place): 162 prediction rows. Replay reproducibility check: **identical** (937,204 bytes compared, 0 differing files). All 39 response hashes verify. No benchmark ORCID (0 of 97) in the seeds, register, freeze, predictions, retrieval or results; no key or mailto in the capture index.
7. `scripts/analyze_free_evaluation.py`: a benchmark-derived analysis of the smoke sample (50 cases, 23 blocks) and the exploratory 18, with Clopper-Pearson intervals, a one-case-per-block view of the smoke sample, safeguards and gate-failure counts, and a planning table from the sizing tool under assumed pilot outcomes. Results: `RAW_OUTPUTS/T019_run1/results_free_evaluation.json`; tables: `paper/HAMMER_IEEE_PAPER/tables_generated/exp_*.tex`.

## 3. Environment
Python 3.12.5, pytest 8.4.2, git `6d31cbe`, dirty tree. SHA-256: `backend/hammer_pilot/guarded_transport.py` `634310f803608e22710b0926337df63bbc569a8a55da25ec5ed9139d42410259`; `backend/hammer_pilot/seeds_from_manifest.py` `c7b47070759ee5718318c7f4d1c8cccf387378b2c55fcebdcdb2f91138f1f506`; `backend/scripts/analyze_free_evaluation.py` `64ecf3916777c76d39e479afd749c99390d55e4f72162c3f2b50394eaf78aa9d`; `backend/tests/test_free_evaluation.py` `dfba703c16081eb9d663e448ad9ddba1a186336222a385b1409f8d0f551d6550`; results `3b33d6c1f8de1a14ae68f2bc4085d6a5946b2fa2440c800f432dd356be979627`.

## 4. Results (benchmark-derived; provisional ORCID agreement; exploratory)
| Quantity | Smoke (50 cases, 23 blocks) | Exploratory (18 cases) |
|---|---|---|
| Expected ORCID in R2 pool | 38 (76%) | 13 (72%) |
| Provider's first candidate agrees | 22 (44%) | 7 (39%) |
| HAMMER top-1 (forced, C1) agrees | 17 (34%) | 6 (33%) |
| C1, full policy: automatic | 4 (8%); 3 agree | 0 |
| C1, gates without safeguards: automatic | 4 | 0 |
| C1x, full policy / without safeguards | 7 / 26 | 3 / 8 |
| Top-score median; cases below 0.75 | 0.88; 0 | 0.88; 1 |
| Margin < 0.15 / dominance < 1.35 / fewer than 2 signals | 37 / 44 / 14 | 14 / 17 / 3 |
The smoke figures equal the independent T003 values exactly (checked by test). Full tables and intervals are in the manuscript (Section 6).

## 5. Tests
`test_free_evaluation.py` 4 passed; two regression tests added (seed freeze, compressed responses). Full suite **591 passed**.

## 6. Interpretation
At small scale the main constraint on automatic assignment was competition among similarly named candidates, not low scores; HAMMER's own ordering of a pool did not agree with the benchmark more often than the provider's order; roughly a quarter of expected profiles were absent from the pool. These are hypotheses for the planned evaluation, and not accuracy.

## 7. Limitations
18 cases is too few for inference; the smoke sample is clustered and not a probability sample; no L or XL case in the exploratory sample; the label is provisional and nothing is verified; one provider, one date, a shared free quota; the exploratory draw consumed the F4 derived main seed, so a confirmatory sample needs a new freeze and must exclude these blocks; the analysis script has no mutation check (its smoke figures are cross-checked against T003 instead).

## 8. Artifacts
`RAW_OUTPUTS/T019_run1/`: capture outputs for both attempts, freeze and draw outputs (F3, F4), `results_free_evaluation.json`, reproducibility and integrity outputs, `pytest_full_suite.txt`, `scripts/`. Data: `research_data/lagos_and_v2/eval_F4/exploratory/` (capture, replay_input, replay) and `eval_F4/free_evaluation/`. Protected files stay in `LAGOS_SOURCE/protected/`.
