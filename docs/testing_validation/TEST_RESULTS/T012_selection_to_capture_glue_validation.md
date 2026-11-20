# T012: selection-to-capture adapter and pipeline glue (seeds, pilot coverage counts, audit frame)

**Test ID:** T012 (run 1) | **Date:** 20 November 2026 | **Type:** unit tests on a synthetic archive; mutation sanity checks; in-memory scale check on the real archive with a dummy manifest | **Status:** PASS (14 tests; 7 of 7 and 5 of 5 mutants detected) | **No provider request, no real sample saved, no parameter chosen.**

> T001 to T011 and all their raw outputs are preserved unchanged.

## 1. Question and reason
The selector (T007) produces manifests, and the capture toolkit consumes `seeds.csv` and `doi_register.csv`, but nothing connected the two. Does the new adapter turn a manifest into exactly the capture inputs of the existing toolkit (same layout, designated-citation rule, DOI purposes), without any ORCID in the capture directory? Do the small glue commands that feed the sizing script (per-stratum pilot counts) and the audit draw (frame of primary cases) use only decision categories and the manifest's strata?

## 2. Expected behaviour
Seeds, DOI register and gold register follow the layouts and rules of `hammer_lagos.prep.build_cases`. Case identifiers come from the manifest. The designated citation is the smallest hash among the group's citations that have an affiliation. DOI purposes are `both` for the designated DOI and `gold_evidence` for the others. `seeds.csv`, `doi_register.csv` and `seed_freeze.json` hold no ORCID; the gold register is written to a separate, non-nested directory. Inconsistent inputs (identity-map mismatch, missing rows, incomplete block) are refused. Pilot counts use only the primary pair and every seeded case must have a prediction; the audit frame lists only primary cases.

## 3. Environment
Python 3.12.5, pytest 8.4.2, git `6d31cbe`, dirty tree (untracked files only). SHA-256: `backend/hammer_pilot/seeds_from_manifest.py` `f70e821622d6e87c44a45f0b33a243ff4d8457d8efee811d7ce70a432861a0ed`; `backend/hammer_pilot/run_helpers.py` `7e492dbc2ceabc5135cccfab51d58420f4a5e1b235ac7e80117c5f50ba3ad74f`; `backend/scripts/run_helpers.py` `ab908976702cb251c13e2e78df7f980a65b3b78f89a31449cbd8203a411fa535`; `backend/tests/test_seeds_from_manifest.py` `ebceff959ea8a717a53f5187c4d74d103f574b341d968f81388afde75f39ffa7`; `backend/tests/test_run_helpers.py` `28a1b6be93405d5266441350d97b7a681876df05081490af15919e77c1e9dfcb`.

## 4. Data
Synthetic archive (invented names, ORCIDs, DOIs) built by the existing test helper. Scale check: the real archive and the PROTECTED catalogue with a **dummy test manifest** (seed 1, 50 blocks), in memory only; counts printed, nothing saved, no ORCID or name printed.

## 5. Results
| Check | Expected | Actual |
|---|---|---|
| `test_seeds_from_manifest.py` + `test_run_helpers.py` | all pass | **14 passed**, 0.86 s |
| Layout and ids | seed, DOI and gold fields equal the toolkit's; ids from the manifest | as expected |
| Designated citation | smallest hash among affiliated citations; never an affiliation-less one when an affiliated one exists | as expected |
| ORCID in capture files | none in seeds, DOI register or freeze file | none; the gold register is in a separate directory |
| Contexts | the existing `derive_contexts` runs on the output; C1x holds only the designated DOI | as expected |
| Pilot counts and audit frame | primary pair only; primary cases only; incomplete inputs refused | as expected; the command-line chain (selection, seeds, counts, audit frame) runs end to end on the synthetic archive |
| Mutants V1 to V7 (adapter) | each detected | **7 of 7** (the first pass detected 6: the affiliation rule survived until a test with affiliation-less citations was added) |
| Mutants X1 to X5 (glue) | each detected | **5 of 5** |
| Real-archive scale check (dummy manifest, 50 blocks) | blocks found; no ORCID in seeds or DOI register | 50 of 50 blocks found in a 29 s second pass; 110 seeds (50 primary, 60 secondary); 1,195 DOI rows; 1 case without a C1 institution; no ORCID in seeds or DOI rows; every designated DOI is in its group's register |

## 6. Interpretation
The step from a frozen selection to capture inputs is implemented, reproducible and leak-free, and it works at real scale. This is evidence of **correct implementation**. The scale check used a dummy manifest and does not define any study case.

## 7. Limitations
The adapter relies on `hammer_lagos.prep` (a private helper `_key` is imported). The glue assumes the replay layout of the existing toolkit. The candidate-works capture and the packet driver (runbook step 11) and the report-assembly script (step 14) are not yet built.

## 8. Artifacts
`RAW_OUTPUTS/T012_run1/`: `pytest_seeds_and_helpers_verbose.txt`, `mutation_check_t012.txt`, `mutation_check_t012_helpers.txt`, `real_scale_seed_build_dry_run_output.txt`, `scripts/`. Hashes: `RAW_OUTPUTS/SHA256SUMS.txt`.
