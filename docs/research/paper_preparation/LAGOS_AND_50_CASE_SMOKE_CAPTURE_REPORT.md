# LAGOS-AND 50-case OpenAlex smoke capture

**Date:** 19 November 2026. **Nature:** feasibility capture, not a benchmark evaluation. No Gemini call, no dataset download, no weight/threshold/policy change, no database or Chroma change, no commit.  
**Reading rule:** all counts describe a **50-case sample drawn from 23 source blocks**; cases within a block are not independent, so no confidence intervals are reported and none of this is a confirmatory result. ORCID equality below is an **automatic label-availability diagnostic, not independent identity accuracy.**

## 1. Preflight
Branch `main`, HEAD `bee7eab`, uncommitted work preserved, nothing staged. All six seed-directory files matched `sampling_manifest.json` hashes before use. Database hash `3659ab2867e43b47` and Chroma digest (sorted-file method) `acf4a8f598f6` unchanged. Free disk 17 GiB. Seeds copied unchanged into `research_data/lagos_and_v2/smoke_v1/` (`seeds.csv` sha256 `76c9232d…`, `doi_register.csv` = `doi_purpose_register.csv` `57fcc099…`); the gold register was **not** copied and the capture never read it.

## 2. Authentication and attempts
- **Attempt 1 (failed):** the key found in the tracked `backend/.env.example` was a placeholder: 40 requests, all HTTP 401 "Invalid or missing API key". The toolkit did not stop on 401, so it ran all 50 cases; this was a defect. Records kept in `smoke_v1/captures_attempt1_failed_401/`, not used.
- **Toolkit fix before attempt 2:** the capture now stops immediately on HTTP 401, 403 or 429 (response saved and hashed first; resume refused), with a test (`test_authentication_or_rate_limit_response_stops_the_capture_immediately`).
- **Attempt 2:** a key supplied by the user in the git-ignored `backend/.env.local` (`APP_ENV=local`); present and non-placeholder; never printed. A scan found it in **0** files. Polite-pool email: the non-personal placeholder.

## 3. Capture results (attempt 2)
| Item | Result |
|---|---|
| Actual HTTP requests | **92** of the 150 cap (42 author searches, 50 works lookups); all **HTTP 200**; 0 failures, 0 malformed, 0 empty-after-error |
| Why 42 author requests for 50 cases | R0 and R2 primary requests were **identical for all 50 cases** (query normalisation changed nothing), so each was issued once and shared; 10 cases repeat another case's printed name; plus 2 initials fallbacks. A shared response is **one** observation, not two |
| Works lookups (50) | C1x only: one lookup per case for the designated DOI; C1 and C0 need none; no coauthor requests (names only, excluded) |
| Provider-reported cost | `meta.cost_usd` summed **$0.047** over the 92 responses (all carried the field) |
| Hash integrity | 92 responses, 92 body files, **0 hash mismatches** |
| Request/response record | `captures/capture_index.jsonl` sha256 `cd9ece81…`; per-case summaries in `captures/cases/` |

## 4. ORCID-field availability [V]
- The `orcid` key is present on **every** returned candidate (299 of 299 in R0 pools, 306 of 306 in R2 pools). It holds a value for **172 of 299 (57.5%)** R0 and **176 of 306 (57.5%)** R2 candidates; the rest are null.
- Five cases returned a successful pool where **no** candidate carried an ORCID value, so these cases cannot be labelled automatically.

## 5. Expected-ORCID coverage and rank diagnostics (descriptive)
| Classification | R0 | R2 |
|---|---:|---:|
| 1. Expected ORCID found in the pool | 36 | 38 |
| 2. Expected ORCID absent from a successful pool (some candidates carry ORCIDs) | 7 | 7 |
| 3. ORCID field null in every candidate | 5 | 5 |
| 4. Empty pool (successful empty response) | 2 | 0 |
| 5. Provider failure | 0 | 0 |
| 6. Malformed response | 0 | 0 |

Classes 2-6 are **not** false identity predictions: they are retrieval, labelling-availability or catalog situations.
- **Rank of the first expected-ORCID candidate** (cases where found): R0: rank 1 in 21, ranks 2-10 in 15; R2: rank 1 in 22, rank ≤5 in 34 cases, ≤10 in 38. First-hit at 1/5/10 (counts of 50): R0 21 / 32 / 36; R2 22 / 34 / 38.
- **Several candidates carry the expected ORCID** in 2 cases per arm (profile duplicates).
- **R0 vs R2:** pools identical in 48 of 50 cases. The 2 that differ are the cases (LG030, LG048) where R0's successful empty response triggered the initials-only fallback in R2 and R2 found a pool. R2's normalisation alone never changed a request in this sample.
- **Pool sizes:** median 6.5, maximum 10 (the existing one-page limit); 20 full pools per arm.
- **By source split (R2, expected found / cases):** train 25/32, test 10/15, val 3/3. Not pooled into a test result; the split flag is only a provenance attribute here.
- **Unknown:** how much of the 7 + 5 "no label" cases is OpenAlex coverage versus fragmentation versus the dataset's ORCID attribution; that needs the independent label audit.

## 6. Offline replay (no network)
The toolkit accepted the LAGOS seed schema without code change: extra seed columns are ignored, the freeze file and register file name were created by copying/renaming the hash-verified seed files. The 15-case validator was **not** run (its composition and reviewer-file rules do not apply to this track).
- Replay: 450 prediction rows (50 cases × 3 conditions × 3 policies), 100 retrieval rows, 150 evidence snapshots; no network; sources of evidence only from frozen captures.
- Reproducibility: two replays byte-identical (4 artifacts, 1.9 MB compared, fixed run ID).
- Manifest: 102 logical requests over 42 physical responses recorded with shared-response provenance; `working_tree_clean: false` (expected).

Outcome counts (50 cases each; **no correctness is scored here; coauthor excluded; labels not applied**):
| Condition | forced_top1 | selective_policy_v2 | legacy_gates_plus_p3 |
|---|---|---|---|
| C0 name only | 50 selected | 50 manual (0 auto: structural) | 50 manual |
| C1 institution + one-year range | 50 selected | 4 auto / 46 manual | 4 auto / 46 manual |
| C1x C1 + designated DOI (exploratory) | 50 selected | 7 auto / 43 manual | 26 auto / 24 manual |

C0 automatic coverage is **zero by design**. Signal availability for the top-ranked candidate in C1: institution observed in 29, candidate has no affiliation data in 19, and no institution in the query for 2; temporal observed 36, inconclusive 14 (a query year before the candidate's observed range); publication and coauthor unavailable (not supplied). In C1x publication overlap was observed for **all 50** top candidates (the designated DOI is a member of the group, so this is the expected leakage-prone signal, exploratory only). The temporal context is the **designated citation's publication year as a one-year range**, not a career active-year range.

## 7. Block dependence, privacy, files
- 50 cases from 23 blocks; block IDs are preserved in the diagnostics for later clustered analysis.
- Gold ORCID values appear **only in the raw provider response bodies** (they are public candidate data returned by OpenAlex; 78 of 92 bodies contain one). They do not appear in seeds, predictions, retrieval tables, evidence snapshots or the diagnostics (booleans, counts and ranks only).
- Files: `smoke_v1/{captures/, replay/, diagnostics/}` (5.0 MB); diagnostics script `backend/scripts/analyze_lagos_smoke_capture.py`; capture hardening in `backend/hammer_pilot/capture.py` and `backend/scripts/capture_hammer_pilot.py`.

## 8. Safety verification
Hashes verified; 0 secrets in captures or reports; database hash and Chroma digest unchanged; nothing staged or committed; the only tracked file that changed during the session is the macOS `.DS_Store` (Finder/TextEdit metadata). Tests: capture/replay/dry-run suites 67 passed; full backend suite **236 passed**.

## 9. Limitations and next decisions
1. 50 cases, 23 blocks; descriptive only; not tuned; no clustered inference yet.
2. ORCID coverage (57.5% of candidates have a value) bounds any ORCID-based label; 12 of 50 cases are unlabelled or absent. Independent audit still required for circularity.
3. R0 vs R2 produced no normalisation difference here; the comparison is mostly the initials fallback (2 cases).
4. C1x publication overlap is leakage-prone and must stay exploratory.
5. Coauthor evidence is not supported by this dataset.
6. Decisions for the director: authorise the independent label audit; whether to scale beyond 50 cases (request cost so far about 1.8 requests per case and about $0.001 per case); whether to improve affiliation normalisation (`#R##N#`, `#N#` markers) before the main sample.
