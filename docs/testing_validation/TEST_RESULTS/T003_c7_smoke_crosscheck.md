# T003: C7 metrics module, cross-check on the smoke capture

**Test ID:** T003 (run 1) | **Date:** 20 November 2026 | **Type:** smoke-data tooling cross-check (offline, read-only) | **Status:** PASS (5 of 5) | **This is a tooling validation, not a performance result.**

## 1. Question and reason
Do the C7 module's arithmetic and case handling agree with **independently produced** artifacts on real captured data? Synthetic fixtures (T002) can share a misreading with the code. Agreement with artifacts made by different code (the ORCID diagnostics script and the existing `metrics.py`) is stronger evidence against implementation mistakes.

## 2. Expected behaviour
- The module's outcome counts for C1 with `selective_policy_v2` equal the replay predictions (4 automatic, 46 manual) and sum to 50.
- Its pool mapping rate and end-to-end success@1, @5 and @10 equal the independent ORCID diagnostics for the R2 pool, **per case** for the rank of the first mapped candidate.
- Its benchmark automatic precision numerator and denominator, and its coverage, equal those of the existing `metrics.selective_metrics`.
- Applying the one-primary-case-per-block rule to the real block structure yields 23 primary and 27 secondary cases, and two primary cases in one block raise an error.
- Output is deterministic and contains no ORCID.

## 3. Environment
Python 3.12.5, pytest 8.4.2, git `6d31cbe` (dirty tree). `metrics_c7.py` SHA-256 `0d3c2afad99d03fc069b8a230e52ad26f1fa4e66f3d5e8a4a4ebdbb4f05872ed`; `tests/test_metrics_c7_smoke.py` SHA-256 `4067d7cabc1d98a1257199f491cb8186662ae7e142e6b909eff3c45ea2b2d8a6`. Smoke data and benchmark files were opened read-only; the 254 files under `research_data/lagos_and_v2` were hashed before and after all runs and are unchanged. The database is unchanged (hash as in T001).

## 4. Data
`research_data/lagos_and_v2/smoke_v1/` (50 cases, 23 blocks, 92 captured responses, the saved replay predictions and retrieval files, and the ORCID diagnostics). The benchmark mapping (which pool candidate carries the case's benchmark ORCID) is built in memory from the raw captured bodies and the protected gold register. **No ORCID value is written to any output.** The smoke sample is **not a probability sample** and has no verified labels. A stand-in frame with every stratum a census (`N_h = n_h`) is used, so only arithmetic, not inference, is exercised. For the main arithmetic checks each case is given its own block identifier, which is not a valid sampling design. The real block structure is used in the separate block-rule test.

## 5. Procedure and commands
```
cd backend
PYTHONDONTWRITEBYTECODE=1 DATABASE_URL=sqlite+aiosqlite:///:memory: \
  .venv/bin/python -m pytest tests/test_metrics_c7_smoke.py -p no:cacheprovider -v --no-header
```
The tests skip automatically if the smoke artifacts are absent.

## 6. Results
| Check | Expected | Actual |
|---|---|---|
| `test_metrics_c7_smoke.py` | all pass | **5 passed**, 0.82 s |
| Label-free counts | `auto` 4, `manual` 46, total 50 | equal; `benchmark_derived` class 50, all other classes 0 |
| Pool mapping rate vs independent diagnostics | 38 of 50 | **38 of 50** |
| End-to-end success@1, @5, @10 | equal to the diagnostics' hit counts | equal (22, 34, 38 of 50) |
| Conditional recall denominator | 38 (cases with a mapped profile) | 38 |
| First mapped rank, every case | equal to the diagnostics' `first_rank_of_expected` | **equal for all 50 cases** |
| Benchmark precision vs `metrics.selective_metrics` | same numerator and denominator | equal; coverage 4 of 50 equal |
| One primary case per block | 23 primary, 27 secondary; duplicates raise | as expected |
| Determinism and leakage | identical JSON on rerun; no ORCID pattern; none of the 50 gold values present | as expected |
| Verified section | 4 automatic assignments `unverified`; `verification_complete` false | as expected (no independent labels exist) |

**Tool-check values** (full report: `RAW_OUTPUTS/T003_run1/c7_report_smoke_toolcheck.json`, SHA-256 `bcd2e00114107cb9269f552b6dadbc0295f81d1474884bc31f86788fd2998ff8`). These show that the output has the right form. **Do not quote them as results.** Pool mapping rate 0.76; end-to-end success@1 0.44, @5 0.68, @10 0.76; end-to-end MRR 0.5403; conditional recall@1 0.5789; conditional MRR 0.7109. Three of the four C1 automatic selections agree with the benchmark label (n = 4, not independent, smoke only). Their pooled interval is withheld under the sparse regime, and no interval is produced for the census strata.

## 7. Interpretation
The C7 module agrees exactly, case by case, with an independent diagnostic script and with the earlier metrics module on real captured data. This supports the claim that the module's retrieval and selective arithmetic is **implemented correctly**. It also shows that the case-accounting, one-primary-per-block and no-ORCID-output behaviour work on real inputs.

## 8. Limitations and sources of error
- Agreement with the diagnostics script shows consistency, not truth. Both use ORCID equality as the benchmark label, which is provisional and may be circular (Decision A).
- Smoke has 50 cases in 23 blocks, no verified labels, only the `auto` and `manual` outcomes, and no stratified or weighted structure. Weights, census handling and the bootstrap are validated in T002 only.
- The census stand-in frame cannot test interval behaviour on real data.

## 9. Artifacts
`RAW_OUTPUTS/T003_run1/`: `pytest_test_metrics_c7_smoke_verbose.txt`, `c7_report_smoke_toolcheck.json`, `scripts/emit_smoke_c7_report.py`. Hashes: `RAW_OUTPUTS/SHA256SUMS.txt`.

## 10. What we learned and next step
The C7 module is ready to be used on any future capture, subject to the ambiguities in T002 section 11. Next: obtain verified labels and a probability sample, which need the authorisations listed in integrated protocol section 10.
