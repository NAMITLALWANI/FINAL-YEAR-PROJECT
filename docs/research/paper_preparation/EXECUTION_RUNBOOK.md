# HAMMER execution runbook: from the verified archive to the paper tables

**Status:** ready on 20 November 2026. Every command below exists and is tested, except the two marked **TO BUILD**. Nothing here has been run on real study data. Run all commands from `backend/` unless stated. Paths: `SRC=../../LAGOS_SOURCE` (archive and protected catalogue, outside the repository). **Never commit `SRC`, any identity map, or any gold register.**

## Gates (nothing starts until its gate is met)
| Gate | What must be true | Who |
|---|---|---|
| G0 | `PARAMETER_RATIFICATION_SHEET.md` signed; freeze id chosen | director |
| G1 | `OPENALEX_API_KEY` set in your own shell or `.env` (never pasted in chat); mailto is not a personal address (the capture script refuses gmail, yahoo, outlook, hotmail) | you |
| G2 | Provider request ceiling and cost ceiling written in the sheet | director |
| G3 | Reviewer arrangements (names, attestations, hours) recorded | director |

## Steps
| # | Step | Command or action | Output | Test record to add |
|---|---|---|---|---|
| 1 | Freeze code and configuration | record `git rev-parse HEAD`, the dirty-state hash, SHA-256 of `config.py`, `policy.py`, `scoring.py`; confirm no `AUTHOR_*` environment override | freeze manifest | T-freeze |
| 2 | Draw the coverage pilot | `python scripts/build_selection_manifest.py --spec pilot_spec.json --out-dir out/pilot` (spec: catalog, seed, split `test`, smoke blocks, per-stratum sizes) | `manifest.json`, `identity_map.json` (PROTECTED) | |
| 3 | Pilot capture inputs | `python scripts/run_helpers.py seeds --manifest ... --identity-map ... --catalog ... --archive ... --capture-dir cap/pilot --protected-dir prot/pilot --include-secondary no` | `seeds.csv`, `doi_register.csv`, `seed_freeze.json` | |
| 4 | Pilot capture | `python scripts/capture_hammer_pilot.py --pilot-dir cap/pilot --budget <ceiling> --allow-network` (stops on 401, 403, 429) | hashed responses | |
| 5 | Pilot replay and coverage | `python scripts/replay_hammer_pilot.py --pilot-dir cap/pilot --out-dir out/pilot_replay`; `python scripts/run_helpers.py pilot-counts --predictions ... --seeds ... --condition C1 --policy selective_policy_v2 --out pilot_counts.json` | per-stratum automatic counts | |
| 6 | Size the main sample | `python scripts/size_hammer_main_sample.py --inputs sizing.json --out out/sizing.json` (inputs: the pilot's post-exclusion frame, floors, pilot counts, `m'`, beta, gamma, `N_max`) | primary, uniform-prior and lower-bound N | |
| 7 | Draw the main sample | `python scripts/build_selection_manifest.py --spec main_spec.json --out-dir out/main` | manifest (hash recorded), identity map | |
| 8 | Main capture inputs and capture | as steps 3 and 4 with `--include-secondary yes` or `no` (director's choice) | hashed responses | |
| 9 | Replay and **freeze predictions** | step 5 replay; record `sha256` of `predictions.csv` | predictions hash | |
| 10 | Audit draw | `python scripts/run_helpers.py audit-frame ...`; then `build_selection_manifest.py` with action `audit` (spec: seed, audit size, merge rule, predictions hash) | audit manifest, verification population | |
| 11 | Candidate-works capture (B2c) and packet driver | **BUILT in T017 (`hammer_pilot/review_driver.py`, `scripts/prepare_review_release.py`; the works capture has never contacted the provider):** capture of each selected case's candidate works (hashed, budgeted) and a driver that feeds `hammer_pilot.dossier` from the captures and the archive rows. The builder, scanner and release layout are built and tested; the driver and the works capture are not | released packets, scan reports, crosswalk | T014 |
| 12 | Reviewer-time pilot (B7) | about six smoke cases through step 11 and the review layer; `reviewer_time_summary` with the agreed hours | audit size and `m'` inputs | |
| 13 | Reviews and adjudication | reviewers fill the templates (`review_records.write_templates`); `resolve_case` per case; `to_c7_fields` | final labels | |
| 14 | C7 report | **BUILT in T016 (`scripts/assemble_c7_report.py`):** a script that assembles `metrics_c7.Case` records from the replay, manifests and final labels and writes the report JSON with `evaluate_primary`. The rehearsal test (`tests/test_rehearsal_end_to_end.py`) is the working template | `report.json` | T015 |
| 15 | Paper tables | `python ../paper/HAMMER_IEEE_PAPER/tools/make_result_tables.py --report report.json --out-dir ../paper/HAMMER_IEEE_PAPER/tables_generated [--agreement agreement.json]` (refuses while any parameter is unspecified, unless `--draft`) | `tables_generated/*.tex` | T013 |
| 16 | Write Results, Discussion, Abstract | only from the generated tables and the report | | |

## Paper claims and where they come from
| Claim in the paper | Source artifact |
|---|---|
| Archive verified; frame counts (Table frame) | T011 `catalog_summary.json` |
| Any retrieval, coverage or precision number | `report.json` through `tables_generated/` only |
| Audit error, group impurity | `report.json`, `audit_label_error` |
| Sample size and its sensitivity | `out/sizing.json` |
| Methodology validation numbers (simulation) | T010 `simulation_result_seed20261120.json` and the 1,000-run file |
| Leakage control evidence | T008 |

## Not allowed at any step
No parameter is changed after a result has been seen; no case is replaced; no tuning of thresholds or weights; the audit estimate is never used to correct a metric; reviewers never see HAMMER output, the crosswalk or the benchmark ORCID; a change to the protocol is a new version.


## Status update (20 November 2026)
Steps 1 and 2 are done for freeze `HAMMER-EVAL-F2` (`research_data/lagos_and_v2/eval_F2/`): the freeze manifest is written and verified, and the pilot is drawn (250 blocks) with its capture inputs built (step 3). **Step 4 (pilot capture) has not run: no OpenAlex credential is available.** The capture command now also takes `--cost-ceiling-usd` and stops on three consecutive server errors. Exact commands: `HUMAN_DEPENDENCIES_AND_NEXT_ACTIONS.md`.
