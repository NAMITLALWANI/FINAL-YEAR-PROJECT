# LAGOS-AND v2.0 sampling and benchmark seed report

**Date:** 19 November 2026. **Stage:** dataset preparation only. No OpenAlex, Gemini or API-key use, no capture, no replay; HAMMER weights, thresholds, policies and the pilot toolkit were not changed.  
**Labels:** **[V]** verified in this task from the data or code · **[I]** inference · **[U]** unknown.

## 1. Source verification [V]
| Item | Value |
|---|---|
| Record | Zenodo `10.5281/zenodo.7313353`, version 2.0, CC BY 4.0 |
| File | `LAGOS-AND-BLOCK-TRIMMED.csv.tar.gz`, 743,558,936 bytes (exact) |
| MD5 | `e9e6703f98d96294e93ba105d6c1c4ac` (matches Zenodo's listed value) |
| SHA-256 (computed) | `a0ac028b8955fcb4c6797b9fe1f5602fef43b45424f4044d0108c4f7d4bb6840` |
| Integrity | full gzip/tar stream read to the end; single member `LAGOS-AND-BLOCK-TRIMMED.csv`, 2,428,531,041 bytes in the header and the same number of bytes read |
| Handling | downloaded to `/private/tmp/` outside the repository, streamed (never extracted), **archive deleted after processing**; no extracted CSV ever existed |

## 2. Full-dataset statistics [V]
| Statistic | Value |
|---|---:|
| Data rows | 1,476,550 (0 malformed, 0 unparseable) |
| Name blocks | 80,294 |
| (block, ORCID) groups | 244,564 |
| Distinct ORCIDs | 244,564 (**every ORCID occurs in exactly one block**) |
| Blocks with one group | 0 (every block has at least 2 groups; max 188) |
| Groups per block | 2: 54,231 blocks; 3: 12,840; 4: 5,079; 5+: the rest |
| Rows per group | min 1, median 2, max 591 |
| Publication years | 1870 to 2022 |
| Row split flag `train1_test0_val2` | 1: 739,750 · 0: 370,194 · 2: 366,606 |
| Block split | train 40,253 · test 20,081 · val 19,960 blocks; **0 blocks with mixed split** |
| DOI shared by more than one ORCID | **0** |
| Duplicate-DOI rows inside a group | 15,279 (1.03%) |
| DOIs with more than one `pid` | 14,546 |
| Invalid DOI / ORCID / non-numeric `pid` rows | none reported (counters absent from the report) |
| Missing | `author_affiliation` 14.10%; `venue` 2.31%; `paper_abstract` 10.15%; all other columns 0% |
| Affiliation `#TAB#` marker | 34,837 rows |
| Author's own name inside `coauthors` | **all 1,476,550 rows** |

Compare with the prefix inspection: the earlier "4 single-group blocks" were an artefact of the cut prefix; the full file has none.

## 3. Sampling frame and method [V: code and outputs]
- **Unit:** complete name blocks; a block's every row is kept in `selected_block_rows.csv` (a test enforces row-for-row completeness).
- **Frame exclusions (counted):** 2,391 blocks with more than 8 ORCID groups (cap to keep complete blocks small); 7,552 blocks with no group having at least two unique DOIs (no usable query citation). Zero exclusions for mixed split, cross-group DOIs or single groups. **Eligible: 70,351 of 80,294 blocks.** By stratum: S 32,188 · M 33,698 · L 4,423 · XL 42.
- **Strata:** block size only, by unique DOIs (S 0-9, M 10-49, L 50-199, XL 200+), fixed in advance. No OpenAlex result, ORCID-match success or HAMMER outcome was used.
- **Order:** eligible blocks sorted by `sha256(seed|block)` within each stratum (deterministic across Python versions); round-robin across strata; a block is taken only if all its query-eligible groups fit the 50-case target.
- **Seed:** 20261119. **Re-run on the real archive reproduced every output byte-for-byte** (manifest identical apart from the recorded sampling date).
- **Designated query citation:** the minimum `sha256(seed|orcid|doi)` among the group's citations that have an affiliation (else any citation).

## 4. Actual sample [V]
50 cases from 23 complete blocks (6 S, 6 M, 6 L, 5 XL blocks); cases by stratum: L 17, M 12, XL 11, S 10 (large blocks supply more groups). Block group counts: 26 cases from 2-group blocks, 9 from 5-group, 7 from 4-group, 4 from 6-group, 4 from 3-group. Source split of cases: train 32, test 15, val 3. Citations per group: min 2, median 7, max 260. Designated-citation years 1987 to 2021 (median 2016). `c1_institution_missing`: 2 cases.

## 5. Files (in `research_data/lagos_and_v2/seed_v1/`, untracked)
`seeds.csv`, `gold_identity_register.csv`, `doi_purpose_register.csv`, `sampling_manifest.json`, `dataset_quality_report.json`, `dataset_quality_report.md`, plus `selected_block_rows.csv` (raw rows of the selected blocks without abstracts, for the completeness check).

## 6. Gold/query-context separation and DOI handling [V]
- **Seeds (the only file HAMMER may read):** opaque case ID, printed author name, opaque group ID and block ID, split, stratum, and two contexts: **C1** = the designated citation's affiliation (normalised) and its publication year as a one-year range; **C1x** = the designated citation's DOI, exploratory. No ORCID, no `pid`, no coauthor, no gold field appears in any seed (tests enforce this).
- **Gold register:** ORCID, opaque person ID, block name, designated DOI, source `pid` (named `designated_pid_source_id`; never an OpenAlex ID), row number. Not for HAMMER input.
- **DOI register (the pilot toolkit's convention):** 1,713 DOIs, each used by exactly one case; 1,663 `gold_evidence` (the group's other citations) and 50 `both` (the designated citation, with a written justification; C1x only). **No DOI is in primary C1.**
- **Coauthors:** never emitted; parsed only to count self-name occurrences.
- The designated citation's year and affiliation are properties of a group member; they leak group membership only weakly and are the same kind of information a user would have for a new paper. This is a stated design limitation.

## 7. Limitations and exclusions
- **Affiliation noise [V in the sample]:** strings contain other markers the `#TAB#` rule does not handle (`#R##N#`, `#N#`), long multi-institution text (median 82 characters, max 224 in the sample) and odd entries ("BiostatEpi VPO"). Only `#TAB#` was normalised, as specified; extending the rule would require regenerating the seed (the archive is deleted, so another approved read is needed).
- **One-year active range:** the temporal context is a single year, the weakest form of the temporal signal.
- **Sample bias [V/I]:** only ORCID holders; blocks with at least two groups; a cap of 8 groups per block excludes the largest homonym blocks; small sample (50) with 23 blocks, so cases within a block are not independent.
- **Split flag:** the sample is mostly `train`-flagged (32) because blocks are drawn by size stratum; HAMMER does not train, so the flag only tracks provenance.
- **Names:** query = the printed name of one citation; some are initials-first (4 of 50).
- No ORCID-to-OpenAlex mapping, no catalog coverage and no label-validity estimate exist yet. ORCID equality cannot be treated as independent ground truth (see `LAGOS_AND_SCHEMA_INSPECTION_REPORT.md`).

## 8. Reproducibility
```
cd backend
./.venv/bin/python scripts/prepare_lagos_and_seeds.py --archive <LAGOS-AND-BLOCK-TRIMMED.csv.tar.gz> --out-dir <new dir> --seed 20261119 --target-cases 50
```
The script verifies size, MD5 and tar integrity first and fails safely on header changes or more than 0.1% malformed rows. `sampling_manifest.json` records dataset DOI and version, archive checksums, seed, algorithm, counts, normalisation rules and counts, the SHA-256 of the code (`b28dd7f970b1fa1d76708b3b8f5f3390b486b851cecaca235045677f3e906de7`) and of every derived file; the only variable field is `sampling.sampling_date`. Code: `backend/hammer_lagos/prep.py`; tests: `backend/tests/test_hammer_lagos_prep.py` (16 tests, synthetic data only).

## 9. Remaining unknowns
OpenAlex coverage of the 50 persons and of their DOIs; whether OpenAlex author profiles carry these ORCIDs; the circularity of ORCID attribution; what the TRIMMED file removed relative to BLOCK; whether `pid` joins to OpenAlex through `ids.mag`.
