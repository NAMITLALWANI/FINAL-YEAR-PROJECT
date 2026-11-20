# T015: evaluation freeze manifest and coverage-pilot draw

**Test ID:** T015 (run 1) | **Date:** 20 November 2026 | **Type:** unit tests; mutation sanity check; offline draw on the real catalogue | **Status:** PASS for the tooling and the draw; **the pilot capture has NOT been run** | **No provider request was made.**

> T001 to T014 and all their raw outputs are preserved unchanged.

## 1. Question and reason
Before any capture the code, configuration, parameters and seeds must be recorded in a way that makes later tuning detectable, and the label-free pilot sample must be drawn by the approved rule. Can this be done reproducibly, with seeds that are derived and not chosen?

## 2. Expected behaviour
The freeze refuses if any `AUTHOR_*`, `ENABLE_AUTHOR_*` or `DEDUP_*` environment override is set; hashes every frozen file; records git head and dirty state, the effective configuration and the adopted parameters; derives each seed as the first eight hex digits of SHA-256 of `HAMMER|<role>|<freeze id>`; and `verify` reports any later change. The pilot draw uses the pilot seed, the test split, excludes the 23 smoke blocks, takes whole blocks, and leaves no ORCID in any repository-side file.

## 3. Environment
Python 3.12.5, pytest 8.4.2, git `6d31cbe`, dirty tree. SHA-256: `backend/hammer_pilot/freeze.py` `b54a8d750df02b9bc0666686bd634478b0f0996e31dd2179d0c0b4144bc6a0d0`; `backend/scripts/freeze_evaluation.py` `5c6a5b4918fb844263175fc5bb7881e82ca41795209718ce6dee9934ca227726`; `backend/tests/test_freeze.py` `a0d4218ffa8d34a11ebb8681c576bee676cf42d60b2b655d89dd9ed3e6e1c669`; parameters `docs/research/paper_preparation/PARAMETERS_ADOPTED_F2.json` `78448f0f49eaba50a68224e26b2ceb3db4cb95d684975eeb803cfb478b308408`.

## 4. Data
Synthetic temporary directory with a fake git runner (unit tests). The real block catalogue (outside the repository) for the draw.

## 5. Results
| Check | Expected | Actual |
|---|---|---|
| `test_freeze.py` | all pass | **8 passed** |
| Mutants Y1 to Y4 (seed slice, override prefix, file-hash comparison, dirty flag) | each detected | **4 of 4** |
| Freeze F1 (`HAMMER-EVAL-F1`) | | written, then **superseded by F2** before any provider request, because the stop-condition guard and the packet seed role were added to the frozen file set (T017). Kept with a `SUPERSEDED.txt` |
| Freeze F2 (`HAMMER-EVAL-F2`), manifest SHA-256 | verifies | `245759abbacf5802594f9edb841a1a6281cf734da2fb6ce16a9b677b37884898`; `verify`: no differences. Seeds: pilot 1211704781, main 211427201, audit 3070674674, packets 2926222443 |
| Smoke blocks recovered | 23 | 23 |
| Pilot draw | 100 S, 100 M, 50 L, 0 XL blocks | 250 primary cases from 250 whole blocks (plus 264 secondary cases that are not captured); manifest hash `f3dce94560cd0cba50d9b3f37ec61645339c04e1ac7b5be31adac1abf84a8df7` |
| Frame after the smoke exclusion | S 8,038, M 8,360, L 1,173, XL 9 (T011) | equal |
| Frame after the pilot | | **S 7,938, M 8,260, L 1,123, XL 9** |
| Capture inputs (`seeds.csv`, `doi_register.csv`, `seed_freeze.json`) | built, leak-free | 250 seeds; 2,855 DOI-register rows; **0 of 514 benchmark ORCIDs present** in any repository-side pilot file (a DOI that merely resembles the ORCID pattern was inspected and is not an ORCID) |
| Capture command without `--allow-network` | refused | refused; no request was made |

## 6. Parameters adopted
Every value in `PARAMETERS_ADOPTED_F2.json` is the recommendation of the ratification sheet, adopted under the 20 November autonomous-execution instruction. **Not chosen:** `m`, `m'` and the audit size, which depend on reviewer capacity. The research director may still change any adopted value before the pilot capture by writing a new freeze (a new identifier gives a new derived pilot draw).

## 7. Interpretation and limitations
The freeze and the draw are implemented, reproducible and leak-free. The freeze records a **dirty working tree** (nothing may be committed); the hashes of the frozen files, not a commit, identify the code. The pilot cannot be captured because the environment has no OpenAlex credential. This is a dependency on the user, not a defect.

## 8. Artifacts
`RAW_OUTPUTS/T015_run1/`: `freeze_F2_output.txt`, `pilot_spec_output_F2.txt`, `pilot_draw_output_F2.txt`, `pilot_seeds_output_F2.txt` (and the F1 equivalents), `scripts/make_pilot_spec.py`; `RAW_OUTPUTS/T017_run1/mutation_check_t015_t017.txt`. Freeze and pilot files: `research_data/lagos_and_v2/eval_F2/`. The identity map and gold register are in `LAGOS_SOURCE/protected/`, outside the repository.
