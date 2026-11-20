# HAMMER testing master register

**Purpose:** the single index of every testing activity. Every new test or milestone must be added here, with a report in `TEST_RESULTS/` and unedited outputs in `RAW_OUTPUTS/`. **Rules:** no result is recorded without supporting evidence; a rerun gets a new run record and never overwrites an earlier one; synthetic, smoke, benchmark and human-reviewed results are labelled as such; dates are real, and times are recorded only when known.

**Last updated:** 20 November 2026 (T014 to T020 added). **Repository:** git `main` at `6d31cbe`; working tree dirty throughout (untracked `docs/`, `paper/`, and the new C7 files; tracked `backend/academic_search.db` modified and never touched by tests). Nothing has been staged or committed by the testing work.

**Evidence classes:** `SYN` synthetic fixtures | `SMOKE` the 50-case smoke capture (operational, not a probability sample) | `BENCH` benchmark experiment (none yet) | `HUMAN` human-reviewed labels (none yet).

## Index
| ID | Date | Component | Class | Status | Report |
|---|---|---|---|---|---|
| T001 | 20 Nov 2026 | Whole offline baseline: test suites, replay, reproducibility, capture integrity, leakage, safeguards | SYN + SMOKE | PASS (with a documented gap) | `TEST_RESULTS/T001_offline_baseline_validation.md` |
| T002 | 20 Nov 2026 | `hammer_pilot/metrics_c7.py` (Decision C7 metrics) | SYN | PASS (49 of 49; 6 of 6 mutants detected) | `TEST_RESULTS/T002_c7_metrics_validation.md` |
| T003 | 20 Nov 2026 | `metrics_c7.py` against independent artifacts on the smoke capture | SMOKE | PASS (5 of 5) | `TEST_RESULTS/T003_c7_smoke_crosscheck.md` |
| T004 | 20 Nov 2026 | `metrics_c7.py` after the five director rulings (derived audit error, ground-truth unresolved versus HAMMER abstention, R2 pool, complete-judgment rule) | SYN (+ SMOKE regression) | PASS (36 new tests; full suite 326; 11 of 11 mutants detected) | `TEST_RESULTS/T004_c7_director_rulings_validation.md` |
| T005 | 20 Nov 2026 | `metrics_c7.py` after the four director clarifications (pure/impure/unresolved purity; group validity apart from case-level verification; overall retrieval never adjusted; conditional verified retrieval categories) | SYN (+ SMOKE regression) | PASS (16 new tests; full suite 342; 10 of 10 mutants detected) | `TEST_RESULTS/T005_c7_group_validity_and_verified_retrieval_validation.md` |
| T006 | 20 Nov 2026 | `hammer_pilot/sizing_c9.py` and `scripts/size_hammer_main_sample.py` (stratified predictive sizing, Decision C9 rev 3) | SYN | PASS (86 new tests; full suite 428; 15 of 15 mutants detected) | `TEST_RESULTS/T006_c9_sizing_script_validation.md` |
| T007 | 20 Nov 2026 | `hammer_pilot/selector_c1c.py`, `scripts/build_selection_manifest.py`, `scripts/build_block_catalog.py` (pilot, main and audit selection; manifests) | SYN | PASS (30 tests; 12 of 12 mutants) | `TEST_RESULTS/T007_selector_and_manifest_builder_validation.md` |
| T008 | 20 Nov 2026 | `hammer_pilot/dossier.py` (allow-list packets, shuffle, opaque ids, leak scan, release layout) | SYN + SMOKE (in memory only) | PASS (25 tests; 12 of 12 mutants) | `TEST_RESULTS/T008_dossier_builder_and_leak_scan_validation.md` |
| T009 | 20 Nov 2026 | `hammer_pilot/review_records.py` (two-stage records, adjudication, kappa, conversion to C7) | SYN | PASS (31 tests; 11 of 11 mutants) | `TEST_RESULTS/T009_review_records_and_adjudication_validation.md` |
| T010 | 20 Nov 2026 | End-to-end rehearsal (selector, sizing, packets, reviewers, C7) and Monte Carlo validation of estimators, intervals and sizing | SYN | PASS (12 tests; full suite 526); two methodological findings | `TEST_RESULTS/T010_end_to_end_rehearsal_and_methodology_simulation.md` |
| T011 | 20 Nov 2026 | Real LAGOS-AND archive (verification), catalogue reader and selector at real scale; eligible test-frame counts | BENCH-INFRASTRUCTURE | PASS (9 of 9 recorded totals reproduced) | `TEST_RESULTS/T011_real_archive_verification_and_frame_counts.md` |
| T012 | 20 Nov 2026 | `seeds_from_manifest.py`, `run_helpers.py` and CLIs (manifest to capture inputs; pilot counts; audit frame) | SYN + real-scale dry run (in memory) | PASS (14 tests; 12 of 12 mutants) | `TEST_RESULTS/T012_selection_to_capture_glue_validation.md` |
| T013 | 20 Nov 2026 | `paper_tables.py` and the table script; static validation of the proposed manuscript changes | SYN | PASS (10 tests; 8 of 8 mutants); manuscript text not changed | `TEST_RESULTS/T013_paper_tables_and_manuscript_readiness.md` |
| T014 | 20 Nov 2026 | Full-archive scan of `pub_year` (reconciles 1963 to 2022 with 1870 to 2022) | BENCH-INFRASTRUCTURE | PASS (range 1870 to 2022 confirmed over 1,476,550 rows; the earlier value came from a 16,710-row prefix) | `TEST_RESULTS/T014_dataset_year_range_reconciliation.md` |
| T015 | 20 Nov 2026 | `freeze.py` and `freeze_evaluation.py` (evaluation freeze F2, derived seeds); coverage-pilot draw and capture inputs | SYN + real-catalogue draw (offline) | PASS (8 tests; 4 of 4 mutants); **pilot capture not run (no provider credential)** | `TEST_RESULTS/T015_evaluation_freeze_and_coverage_pilot_draw.md` |
| T016 | 20 Nov 2026 | `report_assembly.py` and `assemble_c7_report.py` | SYN + SMOKE (read-only) | PASS (7 tests; 5 of 5 mutants) | `TEST_RESULTS/T016_c7_report_assembly.md` |
| T017 | 20 Nov 2026 | `guarded_transport.py` (cost and consecutive-failure stops), `review_driver.py` (works capture, packet release), `prepare_review_release.py` | SYN + SMOKE dry run (scratch) | PASS (20 tests; 19 of 19 mutants after strengthening; full suite 585) | `TEST_RESULTS/T017_capture_guard_and_review_driver.md` |
| T018 | 20 Nov 2026 | Claim-level check of five key references; manuscript update (Sections 1, 2, 5, 7, 9) | LITERATURE | PARTIAL (LAGOS-AND journal paper not readable) | `TEST_RESULTS/T018_reference_claim_check_and_manuscript_update.md` |
| T019 | 20 Nov 2026 | Free-tier exploratory capture (18 real cases), two integration defects found and fixed, benchmark-derived exploratory evaluation of smoke and exploratory samples | SMOKE + EXPLORATORY real (benchmark-derived) | PARTIAL (18 of 50 drawn cases captured; nothing verified); 591 tests | `TEST_RESULTS/T019_free_tier_exploratory_capture_and_benchmark_derived_evaluation.md` |
| T020 | 20 Nov 2026 | Manuscript compile (tectonic 0.17.0) and page-by-page visual check of 22 pages | LITERATURE / MANUSCRIPT | PASS (0 undefined references; four layout and content defects found and fixed) | `TEST_RESULTS/T020_manuscript_compile_and_page_check.md` |

**Version note.** The hashes recorded in T002 and T003 refer to the module and test files as they were **before** T004. Those exact versions are preserved in `RAW_OUTPUTS/T004_run1/pre_T004_versions/` (`pre_T004_hashes.txt`). The versions before T005 (T004's) are preserved in `RAW_OUTPUTS/T005_run1/pre_T005_versions/` (`pre_T005_hashes.txt`). The current versions are listed in T005.

## T001: offline baseline validation (historical baseline; not a result of the C7 module)
- **Date performed:** 20 November 2026 (run 1 original; run 2 evidence re-capture, same day).
- **Component tested:** HAMMER backend test suites; pilot replay and reproducibility toolkit; capture integrity; resolver safeguards; leakage; existing `metrics.py`.
- **Objective:** establish a trustworthy offline baseline before any new work.
- **Why necessary:** every later claim (evaluation, paper, viva) depends on the system being reproducible and on no benchmark label leaking into predictions.
- **Methodology:** run the existing suites; replay the saved smoke capture offline; replay twice and byte-compare; verify stored SHA-256 of 92 provider responses; scripted checks of automatic assignments against the policy safeguards; exact-string and pattern search for gold ORCIDs in every artifact; synthetic probe of the existing metrics module.
- **Exact commands:** see T001 section 5 (run from `backend/`, `PYTHONDONTWRITEBYTECODE=1`, in-memory database).
- **Dataset or fixture:** the existing test fixtures (`SYN`); the 50-case, 23-block smoke capture (`SMOKE`).
- **Expected result:** all pass; byte-identical replay; no hash mismatch; no leakage; safeguards respected.
- **Actual result:** 236 passed; replay 450 predictions, 100 retrieval rows, 150 evidence snapshots; reproducibility `identical: True` (1,897,516 bytes compared in run 1, 1,897,618 in run 2 because the manifest lists the new module); 92 of 92 capture hashes match; preserved failed attempt 40 of 40 HTTP 401; 0 gold-ORCID hits in predictions, evidence, seeds, diagnostics and manifest; 11 of 11 automatic rows within the safeguards.
- **Status:** PASS. Gap recorded: `metrics.py` differs from C7 (coverage denominator drops uncertain cases; no end-to-end success@k; mapping rate on the union of pools and still called `catalog_coverage`; no brackets, strata, weights or bootstrap).
- **Numerical results and artifacts:** replay outputs SHA-256 `a007ccb0…`, `a65f8b1d…`, `5dbd88a5…` (full values in T001). Raw outputs: `RAW_OUTPUTS/T001_run1/`, `RAW_OUTPUTS/T001_run2/`. Integrity list: `RAW_OUTPUTS/SHA256SUMS.txt`.
- **Known limitations:** replay does not test live provider behaviour; only `auto` and `manual` outcomes occur in the smoke data; the leak scan finds exact strings only; smoke cases are not independent.
- **Related tests:** T002, T003.

## T002: C7 metrics module, synthetic validation
- **Date performed:** 20 November 2026.
- **Component tested:** `backend/hammer_pilot/metrics_c7.py`.
- **Objective:** confirm that the module implements the C7 quantities, denominators and verified scoring table, and the C5 inference regimes, and that it fails loudly on bad input.
- **Why necessary:** the existing metrics module disagreed with C7 (T001); the denominators are central to every precision, coverage and retrieval claim.
- **Methodology:** hand-computed expected values for small synthetic case sets; mutation sanity check with six deliberate defects.
- **Exact command:** `PYTHONDONTWRITEBYTECODE=1 DATABASE_URL=sqlite+aiosqlite:///:memory: .venv/bin/python -m pytest tests/test_metrics_c7.py -p no:cacheprovider -v --no-header` (from `backend/`). Mutation: `RAW_OUTPUTS/T002_run1/scripts/mutate.py`.
- **Dataset or fixture:** synthetic only (`SYN`).
- **Expected result:** all tests pass; every mutant is detected.
- **Actual result:** 49 passed in 1.24 s; full suite 290 passed; mutants M1 to M6 detected (3, 3, 1, 1, 1, 2 failing tests); module restored byte-identically.
- **Status:** PASS. Five methodological ambiguities listed for the director (T002 section 11).
- **Numerical results and artifacts:** module SHA-256 `0d3c2afa…`; test file `a27067af…`; raw outputs `RAW_OUTPUTS/T002_run1/`.
- **Known limitations:** tests encode my reading of C7; the bootstrap is checked for reproducibility, plausibility and withholding rules, not for nominal coverage; default settings are provisional, not frozen.
- **Related tests:** T001 (motivation), T003 (cross-check).

## T003: C7 module cross-check on the smoke capture
- **Date performed:** 20 November 2026.
- **Component tested:** `metrics_c7.py` and its replay-row builder on real captured data.
- **Objective:** confirm agreement with independently produced artifacts and with the existing metrics module.
- **Why necessary:** synthetic tests can share a misreading with the code; independent artifacts cannot.
- **Methodology:** build cases from the saved replay and captures; benchmark mapping built in memory from raw bodies and the protected gold register; compare outcome counts, mapping rate, success@k and per-case first rank with the ORCID diagnostics; compare benchmark precision and coverage with `metrics.selective_metrics`; apply the one-primary-case-per-block rule to the real blocks.
- **Exact command:** `PYTHONDONTWRITEBYTECODE=1 DATABASE_URL=sqlite+aiosqlite:///:memory: .venv/bin/python -m pytest tests/test_metrics_c7_smoke.py -p no:cacheprovider -v --no-header` (from `backend/`).
- **Dataset or fixture:** `smoke_v1` (`SMOKE`), read-only. A census stand-in frame is used, which exercises arithmetic only.
- **Expected result:** exact agreement everywhere; 23 primary and 27 secondary cases; no ORCID in output.
- **Actual result:** 5 passed in 0.82 s. Mapping 38 of 50; success@1, @5, @10 = 22, 34, 38 of 50; first mapped rank equal for all 50 cases; precision and coverage equal the existing module (4 of 50 automatic).
- **Status:** PASS (tooling validation; no performance claim).
- **Numerical results and artifacts:** `RAW_OUTPUTS/T003_run1/c7_report_smoke_toolcheck.json` (SHA-256 `bcd2e001…`).
- **Known limitations:** agreement shows consistency, not truth (ORCID equality is a provisional label); smoke has no verified labels and only two outcome categories.
- **Related tests:** T001, T002.

## T004: C7 metrics module, director rulings
- **Date performed:** 20 November 2026.
- **Component tested:** `backend/hammer_pilot/metrics_c7.py` (587 lines after T004) and the three C7 test files.
- **Objective:** implement and validate the five rulings approved on the T002 ambiguities: derived audit-label error; Uncertain class for cannot-verify automatic cases; ground-truth unresolved distinct from HAMMER abstention; R2 pool primary; "no matching candidate" only when every candidate is judged.
- **Why necessary:** each ruling changes a numerator, denominator or class that a reviewer can challenge.
- **Methodology:** module patch (scripted and preserved); earlier tests re-run and their fixtures updated for the deliberate API change; 36 new tests, one group per ruling; mutation sanity check with 11 defects; full-suite re-run.
- **Exact commands:** see T004 section 6.
- **Dataset or fixture:** synthetic (`SYN`); the T003 smoke test re-run unchanged (`SMOKE` regression, read-only).
- **Expected result:** all new and earlier tests pass; each mutant detected.
- **Actual result:** 36 new tests passed; 54 earlier tests passed after fixture updates; baseline without C7 files 236; full suite 326 passed; mutants N1 to N11 all detected; module restored byte-identically.
- **Status:** PASS. Four new ambiguities for the director (T004 section 11).
- **Numerical results and artifacts:** module SHA-256 `08e15501…`; `test_metrics_c7.py` `7609afc9…`; `test_metrics_c7_rulings.py` `563ed6d8…`; raw outputs in `RAW_OUTPUTS/T004_run1/`.
- **Known limitations:** the derived audit definition is an operationalisation of the ruling; hand-built fixtures only; no real Stage A or Stage B records exist.
- **Related tests:** T002 (ambiguities raised), T003 (regression), T001.
- **Superseded in part by T005:** the T004 audit definitions for a pure unresolved group (now indeterminate) and for an uncertain case with an impure group (now indeterminate, impurity reported separately). The T004 report is preserved unedited.

## T005: C7 metrics module, director clarifications on group validity and verified retrieval
- **Date performed:** 20 November 2026.
- **Component tested:** `backend/hammer_pilot/metrics_c7.py` (620 lines after T005) and the four C7 test files.
- **Objective:** implement and validate the four approved clarifications: pure unresolved groups indeterminate with purity states pure, impure and unresolved; benchmark-group validity reported apart from case-level verification (uncertain cases outside the definite-label denominator, impurity reported separately, bracket preserved); overall benchmark-derived retrieval never adjusted by verification; conditional verified retrieval unchanged with every other judgment category reported.
- **Why necessary:** these decisions change the audit error-rate denominator and separate verified from benchmark-derived retrieval, which every later claim depends on.
- **Methodology:** scripted module patch; the three T004 tests that encoded superseded definitions updated; 16 new tests, one group per clarification; mutation check with 10 defects; full-suite re-run.
- **Exact commands:** see T005 section 6.
- **Dataset or fixture:** synthetic (`SYN`); the T003 smoke test re-run unchanged (`SMOKE` regression, read-only).
- **Expected result:** all new and earlier tests pass; every mutant detected.
- **Actual result:** 16 new tests passed; 90 earlier C7 tests passed after three updates; baseline without C7 files 236; full suite 342 passed; mutants P1 to P10 all detected; module restored byte-identically.
- **Status:** PASS. Three points for the director (T005 section 11).
- **Numerical results and artifacts:** module SHA-256 `776e02e8…`; `test_metrics_c7_t005.py` `27e75226…`; raw outputs in `RAW_OUTPUTS/T005_run1/`.
- **Known limitations:** hand-built fixtures; author-chosen mutants; no real Stage A or Stage B records exist.
- **Related tests:** T004 (superseded in part), T003 (regression), T002, T001.

## T006: stratified predictive sizing script (Decision C9)
- **Date performed:** 20 November 2026.
- **Component tested:** `backend/hammer_pilot/sizing_c9.py` (335 lines), `backend/scripts/size_hammer_main_sample.py`, `backend/tests/test_sizing_c9.py`.
- **Objective:** implement and validate the C9 procedure: Jeffreys and uniform priors, per-stratum beta-binomial predictive distributions, exact convolution, C3 allocation (floors, census, redistribution, largest remainder), guarded smallest-N search through N_max, Bonferroni lower-bound sensitivity, explicit zero-pilot handling, and infeasibility and N_max failure reporting.
- **Why necessary:** the sample size of the main evaluation will come from this calculation; an error would silently under- or over-size it. Largest-remainder allocation is provably non-monotone in N, so the guard is essential.
- **Methodology:** exact rational arithmetic as an independent reference; a seeded simulation; regression to the illustrative C9 values (including N = 390 and 413 for m = 32, c = 0.10) with exact rational confirmation; boundary, census, zero-pilot, floor and rounding tests; a non-monotone allocation fixture; numerical-stability and input-validation tests; a 15-defect mutation check.
- **Exact commands:** see T006 section 6.
- **Dataset or fixture:** synthetic only (`SYN`). No frame counts, pilot data, sample or provider request.
- **Expected result:** all pass; the C9 values reproduced; the guard returns the later N in the dip fixture; every mutant detected.
- **Actual result:** 86 passed; full suite 428 passed; all ten illustrative values reproduced and exactly confirmed; 390 and 413 obtained; guard: first meeting N = 31, failing N = 33, answer 34; 14 mutants detected by clean failing runs and the 15th (Q9) by a targeted rerun after the full run exhausted resources; module restored byte-identically.
- **Status:** PASS. A real numerical defect in the first implementation (log-gamma difference for very large pilots) was found by the built-in normalisation check and fixed; it is covered by a regression test and a mutant.
- **Numerical results and artifacts:** `sizing_c9.py` SHA-256 `b9a2abc1…`; raw outputs, validation table and synthetic CLI example in `RAW_OUTPUTS/T006_run1/`.
- **Known limitations:** accuracy about 1e-13; one seeded simulation fixture; assumptions of C9 unverified for real coverage; numpy not listed in `requirements.txt`; three implementation choices for the director (T006 section 11). **No open parameter was chosen or frozen.**
- **Related tests:** none depends on T001 to T005; the C7 test files were re-run unchanged (106 passed).

## T007 to T010: tooling for the main evaluation (summary entries; full detail in each report)
- **T007** (selector): deterministic SHA-256 selection, exact inclusion probabilities, disjoint smoke, pilot and main blocks, C3 allocation, audit draw bound to the frozen predictions; 30 tests, 12 of 12 mutants. Not run on the LAGOS archive. Command: `pytest tests/test_selector_c1c.py`.
- **T008** (dossiers): allow-list packets, hash-seeded shuffle, opaque ids, separate crosswalk, zero-match leak scan; the real smoke payloads leak the gold ORCID in raw form and 0 times after the allow-list (in memory only); 25 tests, 12 of 12 mutants. No dossier was generated. Command: `pytest tests/test_dossier.py`.
- **T009** (review records): independence, completeness, adjudication, kappa with counts, crosswalk conversion to C7; 31 tests, 11 of 11 mutants. No reviewer assumed. Command: `pytest tests/test_review_records.py`.
- **T010** (rehearsal and simulation): the whole pipeline on a synthetic world matches an independent computation from the hidden truth; E1 and E2 estimators unbiased with correct weights; per-stratum intervals conservative (0.96 to 0.97); pooled bootstrap 0.935 against 0.95 nominal; predictive sizing 0.899 when the prior matches and 0.881 under a mismatched generator (target 0.90); plug-in rule 0.55 to 0.68. Commands in T010 section 5.
- **Limitations common to all four:** synthetic data only; author-chosen mutants; the real frame, pilot, capture and reviewers do not exist. Evidence class: `SYN`.
- **Related tests:** T005 (C7 semantics), T006 (sizing); the full suite is 526 passed.

## Readiness before the paper is written (20 November 2026)
**Done and tested offline:** resolver and replay (T001); C7 metrics and definitions (T002 to T005); sizing (T006); selector and manifests (T007); blinded packets and leak scan (T008); review records and adjudication (T009); the whole pipeline rehearsed and the statistical procedures simulated (T010).
**Blocked, with the exact blocker:** (1) **resolved:** the LAGOS archive is now on disk and verified, and the pre-pilot test-frame counts are computed (T011); the coverage pilot and main draw still need director parameters; (2) pilot and main capture need an approved provider budget, cost ceiling and key; (3) the open parameters (*m*, *m′*, β, γ, *N*_max, floors, pilot size, bootstrap minimum, negligible-weight rule, seeds) need the director; (4) independent Stage A and Stage B labels need reviewers (deferred); (5) the manuscript's Section 5 edits and the Results, Discussion and Abstract cannot be written until (1) to (4) exist. **No accuracy or precision claim is supported yet.**

## T011: real archive verification and frame counts
- **Date performed:** 20 November 2026 (download approved in chat).
- **Component tested:** the LAGOS-AND archive (v2.0, block-trimmed), `catalog_from_archive`, `eligible_frame`, the selector at real scale.
- **Objective:** confirm the archive is the recorded dataset; reproduce every recorded total; compute the eligible test-frame counts.
- **Result:** size, MD5 and SHA-256 equal the recorded values; 9 of 9 cross-checks equal; eligible test frame S 8,039, M 8,363, L 1,173, XL 12 (17,587); after excluding the 23 smoke blocks S 8,038, M 8,360, L 1,173, XL 9. Selector scale check passed (test parameters, nothing saved).
- **Status:** PASS. Notable: the XL stratum has only 9 test blocks after the smoke exclusion (T011 section 6).
- **Handling:** the archive and the PROTECTED catalogue are outside the repository (`SYSTEM/LAGOS_SOURCE/`) and must not be committed. No sample was drawn, no parameter chosen.
- **Related tests:** T007 (selector), T006 (sizing).

## T012 and T013 (summary entries; full detail in each report)
- **T012:** the adapter from a selection manifest to the capture inputs, and the glue commands for pilot counts and the audit frame; 14 tests, 12 of 12 mutants; real-archive scale check with a dummy manifest (in memory). Command: `pytest tests/test_seeds_from_manifest.py tests/test_run_helpers.py`.
- **T013:** the LaTeX result-table generator (traceable to a C7 report; refuses unspecified parameters) and static validation of the proposed manuscript changes on a scratch copy; 10 tests, 8 of 8 mutants. Command: `pytest tests/test_paper_tables.py`. The manuscript sections were **not** changed; the proposed text and a guarded apply script are in `docs/research/paper_preparation/proposed/`.
- **Full suite after T013:** 550 passed.

## Readiness update (20 November 2026, later)
Added since the previous readiness note: the verified archive and frame counts (T011); the selection-to-capture glue (T012); the table generator and the proposed manuscript changes (T013); the execution runbook and the parameter ratification sheet in `docs/research/paper_preparation/`. **Still blocked:** (a) director signature on the parameter sheet; (b) your OpenAlex API key in your own environment, plus the cost ceiling; (c) the candidate-works capture with its packet driver, and the thin report-assembly script (runbook steps 11 and 14), which must be built before any review; (d) reviewers (deferred); (e) your decision on applying the proposed manuscript changes.

## Manuscript update applied (20 November 2026)
On the user's approval the proposed Section 5, 6 and 8 changes were applied to `paper/HAMMER_IEEE_PAPER` (see T013 addendum). The paper still states no result. Overleaf package: `paper/HAMMER_IEEE_PAPER.zip` (rebuilt without the backup and tools folders).

## Not yet performed (no record exists, and none may be claimed)
Real coverage pilot; reviewer-time pilot (B7); selector, packet builder, leak scan and audit draw on REAL data (the tools are tested on synthetic data only); any live provider capture beyond the 92 saved responses; any human-reviewed (`HUMAN`) labelling; any benchmark experiment (`BENCH`); the main evaluation. Each needs its own authorisation under integrated protocol section 10.


## T014 to T018: execution preparation (summary entries; full reports in `TEST_RESULTS/`)
- **T014** reconciled the dataset year range: the full scan gives 1870 to 2022; the schema inspection's 1963 to 2022 described a 16,710-row prefix. Raw output: `RAW_OUTPUTS/T014_run1/`.
- **T015** wrote and verified the evaluation freeze `HAMMER-EVAL-F2` (F1 was superseded before any request), derived the seeds, drew the 250-block coverage pilot (frame afterwards S 7,938, M 8,260, L 1,123, XL 9) and built its capture inputs with no benchmark ORCID. **Known limitation: the pilot capture was not run because no OpenAlex credential exists in the environment.** Raw outputs: `RAW_OUTPUTS/T015_run1/`.
- **T016** built and tested the C7 report assembly; **T017** built and tested the capture stop-condition guard and the review driver (works capture and blinded release) and ran a scratch dry run on the smoke data (16 packets, zero leak findings). Mutation check: 16 of 19 detected on the first pass (outputs preserved), 19 of 19 after three tests were added. Raw outputs: `RAW_OUTPUTS/T017_run1/`.
- **T018** checked five key references against their texts (one only partly, because the journal paper returned HTTP 403) and updated the manuscript. Nothing was compiled.
- **Failed or negative items recorded:** F1 freeze superseded; first mutation pass left three survivors; the Wiley copy of the LAGOS-AND paper could not be fetched; the provider credential is absent so no live capture exists.

## T019: free-tier exploratory capture and benchmark-derived evaluation (summary entry; full report in `TEST_RESULTS/`)
Two integration defects were found by the first real executions and fixed with regression tests: the seed-freeze file format (no request made) and the stop guard's handling of compressed responses (70 requests wasted, all recorded as decoding errors, kept as a negative result). Freeze F4 replaced F3 and F2. The capture used OpenAlex's free keyless tier and ended on HTTP 429 after 18 complete cases. Benchmark-derived exploratory results for the smoke sample (50) and the exploratory sample (18) are in the manuscript. **Known limitations:** tiny and clustered samples; provisional labels; no verification; a confirmatory sample needs a new freeze. Raw outputs: `RAW_OUTPUTS/T019_run1/`.

## T020: manuscript compile (summary entry)
First compile of the paper. It exposed a table overlap, a math-mode placeholder rendering error, a cramped table header and one inaccurate sentence; all fixed. **Known limitation:** tectonic lacks bold Times shapes, so bold run-in headings render regular in the proof PDF. Raw outputs: `RAW_OUTPUTS/T020_run1/`.
