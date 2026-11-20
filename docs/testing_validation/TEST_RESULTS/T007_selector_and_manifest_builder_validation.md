# T007: one-case-per-block selector and manifest builder (Decisions C1c, C3, C4, C9; Decision A audit)

**Test ID:** T007 (run 1) | **Date:** 20 November 2026 | **Type:** unit and statistical-sanity tests on synthetic catalogues, mutation sanity check | **Status:** PASS (30 tests; 12 of 12 mutants detected) | **The selector was not run on the LAGOS archive, no real frame count was computed, and no real pilot or main sample was drawn.**

> T001 to T006 and all their raw outputs are preserved unchanged.

## 1. Question and reason
Does the selector implement the locked sampling design deterministically and reproducibly: eligible test-split frame, fixed S/M/L/XL bands, SHA-256 hash order, one primary case per block with secondary cases recorded, pilot drawn before the main sample, post-exclusion counts computed before sizing (clarification X-02), C3 allocation, and the Decision A audit draw bound to the frozen predictions? A mistake here would invalidate every later estimate (wrong inclusion probabilities, overlapping samples, an irreproducible draw).

## 2. Expected behaviour
Frame = eligible blocks (existing `hammer_lagos.prep.eligibility`) of one split minus excluded blocks, by band. Draws are the first *n_h* blocks in SHA-256 order of `seed|role|block` (equivalent to simple random sampling without replacement), identical for identical inputs, independent of catalogue order, and different for different seeds and roles. The primary case per block is the group with the smallest `sha256(seed|primary|block|orcid)`; other case-eligible groups are secondary. Inclusion probabilities are exact fractions (*n_h*/*N_h*; *n_h*/(*N_h g*)). Manifests contain no ORCID (the identity map is separate) and carry a SHA-256 and the selector's source hash. Smoke, pilot and main blocks are disjoint. The main allocation equals the C3 allocation of the sizing script over the post-exclusion frame. The audit is a proportional stratified draw (largest remainder, hash order) from the non-automatic frame with a pre-declared merging rule, with every automatic case in the verification population.

## 3. Environment
Python 3.12.5, pytest 8.4.2, macOS Darwin 25.5.0, git `6d31cbe`, dirty tree (untracked files only added by this work; nothing staged or committed). SHA-256: `backend/hammer_pilot/selector_c1c.py` `b7ef4758f4ae28b0c0627363f607c2365a9a41a37542884bd5347c609c975a00` (229 lines); `backend/scripts/build_selection_manifest.py` `fa5cda5309f61bcf87680c487b4d4ad2e056d1de04df2304465bc2bae58a33de`; `backend/scripts/build_block_catalog.py` `304939a13688c68bd3a4e6d301bf5e196c863ee53e1554c94a9eec9522dafcad`; `backend/tests/test_selector_c1c.py` `7c1c66daed07aaa30cd0bf32d3943daafe8a5431cd7d8d231034dc002b77dd62` (355 lines).

## 4. Data
**Synthetic only:** a seeded 600-block catalogue with invented block identifiers and ORCID-shaped strings, and a tiny synthetic archive for the catalogue reader. The LAGOS-AND archive (743.6 MB) is not on this machine and was not touched. No parameter (seeds, sample sizes, *N*, floors, audit size, merging rule) is chosen; every one is a required argument, and the values in the tests are test values.

## 5. Procedure and commands
From `backend/`: `PYTHONDONTWRITEBYTECODE=1 DATABASE_URL=sqlite+aiosqlite:///:memory: .venv/bin/python -m pytest tests/test_selector_c1c.py -p no:cacheprovider -v --no-header`; mutation check `RAW_OUTPUTS/T007_run1/scripts/mutate_t007.py`. Command-line use (not run on real data): `scripts/build_block_catalog.py --archive <LAGOS archive> --out <new file>` (strict: checks the recorded size and MD5 of the archive) and `scripts/build_selection_manifest.py --spec <json> --out-dir <new dir>`.

**Test groups.** Frame by band and split, band boundaries, exclusion reasons. Pilot determinism, seed sensitivity and catalogue-order independence; smoke exclusion; post-exclusion frame; refusal of oversized or unknown requests. Primary and secondary cases; exact inclusion probabilities; no ORCID in manifests and a separate identity map; hash sealing and tamper detection. Main allocation equals the C3 allocation; explicit floors; census; disjointness. Role-specific hash keys. Audit allocation, hash order, merging rule, binding to the predictions hash, input validation. A uniformity check over 1,500 seeds (each block drawn with probability *n*/*N*; each group primary with probability 1/*g*). The two command-line scripts and a synthetic archive.

## 6. Results
| Check | Expected | Actual |
|---|---|---|
| `test_selector_c1c.py` | all pass | **30 passed**, about 1 s |
| Full backend suite | 428 earlier + new tests | 526 passed (all T007 to T010 tests included) |
| Mutants R1 to R12 | each detected | **12 of 12** (the first pass detected 11; see below) |
| Uniformity (1,500 seeds) | each block selected with probability *n*/*N* within 5 standard errors | within |

Mutants: seed ignored; primary case taken as the largest hash; smoke exclusion ignored; pilot blocks not removed from the post-exclusion frame; ORCID written into the manifest; person inclusion probability ignoring *g*; main ignores the pilot exclusion; pilot and main share the ordering role; audit order by case id; audit allocation not proportional; manifest hash not recomputed; merging rule ignored.

## 7. Interpretation
The selector is deterministic and reproducible, its probabilities are exact, and its sampling is uniform in simulation, with the locked exclusion and disjointness rules enforced. This is evidence of **correct implementation on synthetic catalogues**. It says nothing about the real frame, whose eligible test counts remain uncomputed.

## 8. Development history
- First mutation pass: 11 of 12 detected. Mutant R8 (pilot and main sharing the ordering role) survived because the role test compared a pilot sample with a main sample of different composition. The test was replaced by one that checks each stratum's draw against its own role key; the second pass detected all 12. The first pass's raw output was overwritten by the second.
- Two weak assertions (`... or True`) were found on review and replaced by real checks before the final run.

## 9. Limitations and points for the director
- The real catalogue, frame counts and the XL stratum size are unknown until the archive is available (approval needed for a 743.6 MB download).
- The audit merging rule must be declared before the draw; the selector enforces that it is an explicit argument, not that it was declared in time.
- Seeds must be chosen and recorded at the freeze; none is chosen here.
- The catalogue file contains benchmark ORCIDs and is PROTECTED.

## 10. Artifacts
`RAW_OUTPUTS/T007_run1/`: `pytest_test_selector_c1c_verbose.txt`, `mutation_check_t007.txt`, `scripts/mutate_t007.py`. Hashes: `RAW_OUTPUTS/SHA256SUMS.txt`.
