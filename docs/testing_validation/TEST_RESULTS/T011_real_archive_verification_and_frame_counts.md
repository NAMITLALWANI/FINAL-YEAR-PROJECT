# T011: real LAGOS-AND archive verification, catalog cross-check and eligible test-frame counts

**Test ID:** T011 (run 1) | **Date:** 20 November 2026 | **Type:** real-data verification (read-only) and scale check of the selector | **Status:** PASS (9 of 9 cross-checks equal; selector scale check passed) | **No pilot or main sample was drawn or saved, no parameter chosen, no provider request made.**

> Evidence class: `BENCH-INFRASTRUCTURE`. This is verification of the benchmark data and the tooling, not a performance experiment. T001 to T010 and their raw outputs are preserved unchanged.

## 1. Question and reason
The selector and the frame definition (T007) were tested on synthetic catalogues only. Is the archive I obtained the exact dataset recorded in the earlier quality report, and does the selector's catalogue reader reproduce every recorded total on the real data? Decision C4 also requires the exact eligible test-frame size per band before the freeze.

## 2. Expected behaviour
The archive matches the recorded name, size, MD5 and SHA-256 and passes tar and gzip integrity. The catalogue built from it reproduces the earlier totals exactly: 80,294 blocks; 1,476,550 rows; 244,564 block-ORCID pairs; 70,351 eligible blocks; eligible blocks by band S 32,188, M 33,698, L 4,423, XL 42; exclusions 2,391 (more than 8 groups) and 7,552 (no group with two unique DOIs); block splits 20,081, 40,253, 19,960 with no mixed-split block; and the 23 smoke blocks are found.

## 3. Procedure, commands and environment
Python 3.12.5, git `6d31cbe`. The user approved the download in chat after the file name, source and size were stated.
1. Zenodo API record 7313353 read to confirm the file entry (name, size, MD5, license CC BY 4.0) before download.
2. `curl -L -C - -o LAGOS-AND-BLOCK-TRIMMED.csv.tar.gz https://zenodo.org/api/records/7313353/files/LAGOS-AND-BLOCK-TRIMMED.csv.tar.gz/content`. Only this file; the two larger files of the record were not downloaded. It was saved **outside the repository** in `SYSTEM/LAGOS_SOURCE/` so it cannot be committed by accident.
3. `hammer_lagos.prep.verify_archive` with the recorded expectations (the repository's strict check).
4. `scripts/build_block_catalog.py --archive <file> --out <new file outside the repository>` (the catalogue contains benchmark ORCIDs and is **PROTECTED**).
5. `RAW_OUTPUTS/T011_run1/scripts/summarize_catalog.py` (counts only; no ORCID, block name or author name is written).
6. `RAW_OUTPUTS/T011_run1/scripts/selector_scale_dry_run.py` (in memory, test parameters, nothing saved).

## 4. Results
| Check | Expected | Actual |
|---|---|---|
| Download | name, size and MD5 as in the Zenodo record | HTTP 200, 743,558,936 bytes, 370 s |
| `verify_archive` | size and MD5 match; tar integrity ok; one member | size 743,558,936; MD5 `e9e6703f98d96294e93ba105d6c1c4ac`; SHA-256 `a0ac028b8955fcb4c6797b9fe1f5602fef43b45424f4044d0108c4f7d4bb6840` (**equal to the SHA-256 recorded in the earlier sampling manifest**); member 2,428,531,041 bytes; integrity ok; 10 s |
| Catalogue build | 80,294 blocks | 80,294 blocks, 89 s |
| Cross-checks against the recorded quality report | 9 equal | **9 of 9 equal**: blocks 80,294; rows 1,476,550; block-ORCID pairs 244,564; eligible 70,351; eligible by band 32,188 / 33,698 / 4,423 / 42; split counts 20,081 / 40,253 / 19,960; mixed-split blocks 0; exclusion reasons 2,391 and 7,552; smoke blocks found 23 |

**Eligible blocks by split and band (before any exclusion; informational):**
| Split | S | M | L | XL | Total |
|---|---:|---:|---:|---:|---:|
| test | 8,039 | 8,363 | 1,173 | 12 | 17,587 |
| train | 16,197 | 16,897 | 2,124 | 17 | 35,235 |
| validation | 7,952 | 8,438 | 1,126 | 13 | 17,529 |

**Test-split frame after excluding the 23 smoke blocks** (7 of them are in the test split: S 1, M 3, XL 3): S 8,038, M 8,360, L 1,173, **XL 9**; total 17,580. Shares of that frame: S 45.7%, M 47.6%, L 6.7%, XL 0.05%.

**Selector scale check (test parameters only, nothing saved).** Frame computed in 0.05 s; two pilot draws (one with a shuffled catalogue) in 0.37 s with identical manifests; a main draw of 300 cases gave allocation S 137, M 143, L 20, XL 0 with 267 secondary cases; smoke, pilot and main blocks disjoint; manifests verify; no ORCID in a manifest; an XL floor above its size gave a census (12).

## 5. Interpretation
The archive is the recorded dataset, and the selector's reader reproduces every recorded total on the real data, so the frame definition used by the sampling tools is the one the earlier analysis used. This is evidence that **the data and the frame logic are correct**. It is not a performance result.

## 6. Points for the research director
1. **XL is almost empty in the test split (9 blocks after the smoke exclusion).** A pilot taken from the test split would remove XL blocks from the main frame (feasibility rule C-O17); with any floor of 9 or more the main sample takes all of them, and no XL block remains for a test-split pilot. XL would then carry a pilot-free predictive (prior only) or a train or validation fallback with its stated transfer assumption (train has 17, validation 13).
2. **L is also small (1,173).** A pilot of a few dozen L blocks has a non-trivial sampling fraction.
3. The counts above are the pre-pilot frame; the final post-exclusion counts depend on the pilot draw (X-02). Open item C-O16 is now partly resolved (the pre-pilot counts exist).

## 7. Limitations and handling
- Only this archive version (v2.0, block-trimmed) was verified. ORCID equality remains a provisional label.
- The archive and the catalogue are outside the repository and must not be committed. The catalogue contains ORCIDs and author names; only counts appear in `docs/`.
- The scale check used a dummy seed and sizes; none of its draws is a study draw.

## 8. Artifacts
`RAW_OUTPUTS/T011_run1/`: `catalog_summary.json` (counts only), `selector_scale_dry_run_output.txt`, `scripts/`. Hashes: `RAW_OUTPUTS/SHA256SUMS.txt`. Outside the repository: `SYSTEM/LAGOS_SOURCE/LAGOS-AND-BLOCK-TRIMMED.csv.tar.gz`, `block_catalog_PROTECTED.json`, `download_log.txt`.
