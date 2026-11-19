# HAMMER implementation facts for the paper

**Commit inspected:** `bee7eabfba2d88c4a03c12d227ac6b04624fb8c8` (remote `main` = local `HEAD`, verified with `git ls-remote`).  
**Method:** static reading of committed files. **No code was run, no test was executed, no database or vector index was opened, no live provider or Gemini call was made.**  
**Paths** are relative to the repository root. Line numbers are as read at this commit.

> **Update after the five-signal implementation (19 November 2026).** Sections 6-10 and 16-19 below describe commit `bee7eab`. A later, uncommitted working-tree change adds typed query context (`author_resolution/context.py`), OpenAlex works enrichment (`enrichment.py`, `enrichment_types.py`), signal statuses (`evidence.py`), evidence-sufficiency safeguards (`policy.py`), a structured empty/failed distinction, optional UI context fields, and the edition-regex fix. Where this file says that publication and coauthor evidence is never available, that was true at `bee7eab` and is now conditional on supplied context and a successful enrichment. Where it lists defects D1-D8 and D11-D12, see `FIVE_SIGNAL_IMPLEMENTATION_NOTES.md` for which were corrected. The text below is kept as the record of `bee7eab`.

## 0. How to read the evidence labels

| Label | Meaning |
|---|---|
| **[Inspected]** | Read directly in the code at this commit. |
| **[Reported]** | Stated by the recovery report or roadmap (`docs/PROJECT_EXECUTION_ROADMAP.md`); not independently confirmed here. |
| **[Not verified]** | Cannot be established without running something. |
| **[Not evaluated]** | Implemented, but no empirical evaluation supports a research claim. |

Stage 2 documents name `d41378c` as their software baseline. Between `d41378c` and `bee7eab`, only `backend/author_resolution/resolver.py` and `backend/rag/retrieval.py` changed inside the author-resolution, retrieval, explanation, deduplication and config directories (`git diff --stat`). The diff in `resolver.py` restructures persistence and transactions; the lines defining `rank_candidates`, `decide`, thresholds and weights are not in the diff. `config.py`, `candidates.py`, `evidence.py` and `scoring.py` are byte-identical across the two commits. **Any frozen experiment baseline must name `bee7eab` (or later), not `d41378c`.**

## 1. System overview [Inspected]

HAMMER is a FastAPI backend (`backend/main.py`) with a SQLite system of record (`backend/database.py`), a React frontend (`frontend/`), multi-provider publication ingestion, publication deduplication, an OpenAlex-based author-candidate and decision subsystem, a Chroma-based dense retrieval index, and an optional Gemini explanation layer with a deterministic fallback.

The author-resolution subsystem is **independent of the retrieval and explanation layers**. `main.py:237` returns the note "Retrieval context provides topical relevance; it does not change deterministic identity decisions", and the retrieval call at `main.py:191` happens *after* candidates are ranked and does not feed back into scoring.

## 2. Architecture and module layout [Inspected]

| Area | Real implementation | Facade/duplicate |
|---|---|---|
| Author resolution | `backend/author_resolution/{candidates,evidence,scoring,resolver,schemas}.py` | `backend/services/author_resolution.py` re-exports `author_resolution.resolver` |
| Dedup | `backend/deduplication/{engine,normalize}.py` | `backend/pipeline/deduplicate.py`, `normalize.py` re-export these (`services/search_service.py:10-11` imports via `pipeline`) |
| Connectors | `backend/ingestion/*.py` | `backend/connectors/*.py` re-export (`connectors/dblp.py` is a partial exception: it imports `ingestion.base` directly) |
| Dense retrieval | `backend/rag/retrieval.py` | `backend/services/scholarly_retrieval.py:1-4` star-imports `rag.retrieval` and then imports `generate_explanation` from `explanation.synthesis` |
| Explanation | `backend/explanation/synthesis.py` | `rag/retrieval.py:458-540` contains a **second copy** of `generate_explanation`; the facade makes the `explanation.synthesis` copy the active one |

**Duplication caveat for architecture figures.** `explanation/synthesis.py:340-440` also contains a copy of the retrieval `_search`/`retrieve` code, including the **pre-recovery invalid Chroma filter keys** (`{"": value}` at `synthesis.py:357-365`). The recovery commit corrected only `rag/retrieval.py`. As read, the active retrieval path is `rag.retrieval`, so the stale copy appears unused for retrieval; this is a reading of imports, not a run. An architecture figure should show one retrieval path and not suggest `explanation/` owns retrieval.

## 3. Data sources [Inspected]

Feature flags (`backend/config.py:19-25`): `ENABLE_OPENALEX`, `ENABLE_DBLP`, `ENABLE_CROSSREF`, `ENABLE_ARXIV` default **true**; `ENABLE_SCHOLAR` and `ENABLE_FACULTY` default **false**; `USE_MOCK_DATA` default false. Source priority (`config.py:31-38`): Crossref 1, OpenAlex 2, DBLP 3, arXiv 4, Scholar 5, faculty page 6.

The recovery report says Playwright Chromium was installed "because the configured Scholar source is enabled" **[Reported]**. In the committed code Scholar is off by default, so that refers to a local environment setting, not a code default. Which sources were enabled when any historical result was produced is **[Not verified]**.

Author candidates come from **one source only**: the OpenAlex `authors` endpoint (`author_resolution/candidates.py:29`, `OPENALEX_AUTHORS_URL`). Author-resolution candidates are not drawn from DBLP, Crossref, arXiv or Scholar.

## 4. Publication ingestion and metadata integration [Inspected]

`services/search_service.py` fans out to enabled connectors (`:25-47`), persists source records and merged publications (`:248`), and uses `deduplicate` from `pipeline.deduplicate` (`:11`), which forwards to `deduplication.engine`. A circuit breaker and a cache are used per source (`:102-121`; `circuit_breaker.py`, `cache.py`).

Provenance in this layer is source-record retention: every `SourceRecord` row keeps its provider and raw metadata (`database.py:27-44`). "Provenance" here means retained source records and a candidate/evidence audit trail, **not** formal why/where-provenance. [Not evaluated]

## 5. Publication deduplication (relevant only if RQ1 is kept) [Inspected]

- Two engines in `deduplication/engine.py`: `deduplicate_v1` (`:271`, legacy baseline) and `deduplicate` (`:364`, "V2" with veto safeguards at `:407-420`: DOI conflict, edition conflict, year gap, with title-similarity floor and prefix matching described in the module docstring `:11-17`).
- Thresholds (`config.py:41-44`): default 0.85, lenient 0.80, strict 0.92, log 0.70; selected by source pair (`engine.py:82-85`).
- **Known defect, still present:** `_EDITION_RE` at `engine.py:90-93` begins and ends with a U+0008 (backspace) byte instead of a `\b` word-boundary escape. Verified by byte count (two `0x08` bytes in the file). As written the regex looks for literal backspace characters, so ordinary edition strings will not match and `_has_edition_conflict` (`:121-125`) will return `False`. This is inferred from the regex text; I did not run it. A regression test file exists (`tests/test_dedup_regression.py`) but whether it covers editions was not checked.
- The README and the `engine.py` docstring still advertise "edition conflict guards" as a working safeguard. That statement is unverified and probably wrong at this commit.

## 6. Author candidate generation [Inspected]

`OpenAlexCandidateService.generate` (`candidates.py:373-531`):

1. Blank name → `failed`, `invalid_query` (`:376-383`).
2. Input matching institutional patterns ("department of", "institute of", "laboratory", ...) → `failed`, `unsupported_input` (`:386-394`; patterns `:93-100`).
3. `clean_query_name` (`:48-89`): Unicode NFC, whitespace collapse, and a narrow merge of "Le"/"La" with the next capitalised alphabetic token longer than two characters. It does **not** lowercase, remove particles or truncate.
4. Request: `GET https://api.openalex.org/authors` with `filter=display_name.search:{query}`, `per-page=10` (`max_candidates`, `:367`, `:401-405`), `mailto`, and an optional `api_key`. **One page only; no pagination.**
5. Failure mapping (`:409-474`): timeout, request error, HTTP 429 (`rate_limited`), other HTTP errors, malformed JSON, missing `results` list → `failed` with an error code.
6. Parsing (`:476-484`): non-object results dropped; items without an ID or non-blank `display_name` dropped (`from_openalex`, `:236-272`); duplicate IDs removed, first seen kept; **API order preserved**.
7. **Initial-only fallback** (`:492-524`): only if zero candidates **and** the cleaned query contains an initial token (regex `\b[A-Za-z]\.`, `:116-118`), retry with `search={query}` and append unseen IDs. A fallback network or HTTP failure is logged and swallowed, so the result can end as `empty` even though the fallback failed (`:523-524`).
8. Status: `ok` if any candidate, else `empty` (`:526-531`).

README text describing "multi-strategy candidate harvesting" overstates this: the code has one primary request plus one conditional fallback.

**Candidate fields populated from OpenAlex** (`from_openalex`, `:236-272`): display name, aliases (from alternative-name fields), affiliations (from `last_known_institutions` and `affiliations`), `works_count`, citation count, topics, active-year range (min/max of `counts_by_year`). **Always `None`:** `sample_publications` (`:265`) and `coauthor_summary` (`:267`), with the code comment that they "remain absent until a later evidence-collection stage retrieves them". No such stage was found anywhere in `backend/` outside tests (searched). See section 7.

**Persistence of candidates** (`persist_candidates`, `:533-558`): idempotent on `(query_normalized, source, source_author_id)`. If a row exists it is **reused as is**; its stored payload is not refreshed. Consequence: a repeated query within the same database reuses an older captured payload and `retrieved_at`. This matters for replay and for any claim of "live" retrieval.

## 7. Evidence signals [Inspected]

Defined in `author_resolution/evidence.py`; combined in `scoring.py`.

| Signal | Function | Computation | When unavailable |
|---|---|---|---|
| `name_similarity` | `evidence.py:47-59` | `max` over display name and aliases of RapidFuzz `token_sort_ratio(normalize_name(query), normalize_name(variant)) / 100`; `normalize_name` = trim, casefold, collapse whitespace (`candidates.py:33-35`) | Blank query or no name variants |
| `institution_similarity` | `:62-75` | `max` RapidFuzz `token_set_ratio` over all hint × affiliation pairs / 100 | No institution hint in context, or candidate has no affiliations |
| `publication_overlap` | `:78-92` | Matched DOIs/normalised titles ÷ `max(1, min(size of query DOI/title set, size of candidate DOI/title set))`, capped at 1 | Context `publications` not a list **or** candidate `sample_publications` not a list |
| `coauthor_overlap` | `:95-102` | Shared normalised coauthor names ÷ min set size | Either set empty |
| `temporal_compatibility` | `:105-115` | Overlap years of two year ranges ÷ shorter span, capped at 1 | Context lacks `active_year_start`/`active_year_end`, or candidate range missing |

`extract_evidence` (`:118-123`) returns all five in that order.

### Effective availability in the committed paths (key finding)

- `publication_overlap` and `coauthor_overlap` need candidate fields that `from_openalex` always sets to `None`. So **both are unavailable for every live OpenAlex candidate**. They can be available only in unit tests or any path that builds candidates with those fields filled. [Inspected]
- `temporal_compatibility` needs `active_year_start/end` in the *request context*. The UI sends only `author_name` and `institution_hint` (`frontend/src/services/api.js:59-62`); the Day 5 evaluation script builds `AuthorCandidateInput(author_name=name, institution_hint=inst)` (`backend/scripts/run_day5_e2e_evaluation.py:92`). So in those two paths it is also unavailable. [Inspected]
- Therefore, **in the UI and in the historical Day 5/V3 evaluation path, at most two signals (name, institution) can contribute, and only when an institution hint is given.** The API accepts a free-form `context` (`main.py:91-94`) so a caller can add years (making three) and `institution_hints`. The frozen-replay script reads a `context_json` per query (`scripts/replay_frozen_resolver.py:89-123`), so a future protocol could supply richer context, but the committed candidates still carry no publications or coauthors.
- These are readings of the code; they should be **confirmed by one dry run by Codex** before the paper states how many signals are effective.

## 8. Evidence weights and missing-signal behaviour [Inspected]

Weights (`config.py:56-62`): name 0.35, institution 0.25, publication 0.20, coauthor 0.10, temporal 0.10. They are constants in code (no environment override), and are heuristic, not fitted.

`score_evidence` (`scoring.py:40-58`): keep only evidence with a non-null normalised score whose name is in the weight table; if none, return score `None`, 0 signals; otherwise each contribution = `weight × score / Σ(weights of available signals)`, and the score is the rounded sum (6 dp). Missing signals are **omitted and the remaining weights renormalised**. A zero-valued available signal still counts as available.

Worked consequence: with only name and institution available, score = (0.35·n + 0.25·i) / 0.60. With only name available, score = n.

## 9. Decision thresholds and gates [Inspected]

Defaults and overrides (`config.py:47-51`, environment-overridable): auto score **0.75**, margin **0.15**, dominance **1.35**, manual score **0.45**, minimum available signals for auto **2**. Versions (`config.py:53-55`): resolver, scoring and threshold versions all default `v1`.

`rank_candidates` (`resolver.py:68-74`): sorts by (score is not None, score, `source_author_id`), **reverse**. Equal scores are therefore ordered by **descending** source ID. This is display ordering; it is not an identity assertion.

`decide` (`resolver.py:77-89`):

1. No candidates, or top score `None` → `unresolved`, reason "Insufficient comparable evidence."
2. `margin = top − second` (or `top` if there is no second); `dominance = top / second` if `second > 0`, else `None`.
3. **Auto** if `top ≥ 0.75` **and** top's available-signal count `≥ 2` **and** (no second **or** (`margin ≥ 0.15` **and** (`dominance` is `None` **or** `≥ 1.35`))).
4. Else **manual review** if `top ≥ 0.45`.
5. Else **unresolved**.

Observations from reading the gate (not changes):

- If the second-ranked candidate has no usable score, `second` is `None`, so the margin and dominance gates are skipped and auto needs only `top ≥ 0.75` and ≥ 2 signals. Since candidates without scores sort last, this occurs when there is one candidate or the rest have no evidence.
- The "≥ 2 signals" gate counts **available (non-null)** signals, including zero-valued ones. The module docstring (`resolver.py:14`) says "non-zero signals in >= 2 independent categories". The code does not test non-zero.
- Given section 7, auto-selection in the UI path requires an institution hint that matches at least one OpenAlex affiliation well enough that the combined score ≥ 0.75; name similarity alone can never trigger `auto_selected`.
- `main.py:218` labels candidates "High"/"Medium"/"Low" using hard-coded 0.75/0.45 cut-offs that duplicate, but are not read from, the config values. This is a display label, not a calibrated confidence and not the auto gate.

## 10. Automatic / manual / unresolved workflow and persistence [Inspected]

Statuses (`resolver.py:51-54`; DB check constraint at `database.py:~350`): `auto_selected`, `manual_selection_required`, `unresolved`, `manual_selected`, plus `expired` allowed by the constraint.

API flow (`main.py`):
1. `POST /author-resolutions/candidates` (`:158-238`): `generate_and_rank` → persists candidate rows and commits → returns ranked candidates with per-signal evidence, then attempts topical retrieval (failure tolerated).
2. `POST /author-resolutions` (`:241-286`): `create_resolution` (`resolver.py:113-275`).
3. `GET /author-resolutions/{id}` (`:289-`): returns the stored decision and evidence rows.

`create_resolution`:
- If `candidate_ids` is supplied, it re-reads those stored candidate rows, rebuilds candidates **from the stored raw payload**, re-ranks, and decides (`:132-163`). It rejects rows that do not belong to the normalised query. Candidates whose payload fails to parse are **silently dropped** (`except Exception: pass`, `:160-161`).
- Otherwise it calls `generate_and_rank` (a live OpenAlex request) (`:165`).
- **Any non-`ok` generation status raises `CandidateSourceUnavailable`** (`:166-167`). Because a successful but empty OpenAlex response has status `empty`, an empty pool in this path is reported as "source unavailable" (HTTP 503 at `main.py:257-261`) and **no resolution row is written**, whereas `/author-resolutions/candidates` treats `empty` as success (`main.py:174`). This contradicts the Stage 2 rule that successful-empty and failed results must be recorded separately; an offline evaluator must not inherit this mapping.
- A manual selection or `mark_unresolved` overrides the algorithmic status; the algorithmic scores are retained except for `mark_unresolved`, which nulls them (`:173-185`).
- Persisted `AuthorResolution` stores query, normalised query, institution hint, status, selected candidate, top/second score, margin, dominance, `confidence_level="engineering_heuristic"` for auto only, reason, resolver/scoring/threshold versions, timestamps (`:186-203`).
- For a selected candidate it finds or creates an `Author` and an `AuthorExternalId` with `provenance_json` stating that a source profile was selected and that this is "not cross-source proof" (`:206-229`).
- Per candidate and signal it writes `AuthorResolutionEvidence` rows with `normalized_score`, raw value JSON, explanation, source provenance JSON and `weighted_contribution`; the stored `weight` column is **`None`** (`:233-246`). The effective renormalised weight is recoverable only from the contribution and the score, not from a stored column.
- Database errors trigger `rollback()` and re-raise (`:108-110`, `:272-274`); `main.py:267-273` maps them to HTTP 500 without recording success.

The `AuthorCandidate` model is at `database.py:258-305`, `AuthorResolution` at `:307-365`, `AuthorResolutionEvidence` at `:367-410`. The Alembic revision file is `backend/alembic/versions/20260907_01_author_resolution_foundation.py`. That the live database is at that revision is **[Reported]**, not verified here.

## 11. Embedding model, vector store and distance [Inspected]

- Embedding model: `all-MiniLM-L6-v2` (`rag/retrieval.py:46`); the code raises if `EMBEDDING_MODEL` is set to anything else (`:47-48`). It is used through Chroma's default ONNX MiniLM embedding function (`:233-244`), with the model cache under the index directory (`:240`).
- Store: `chromadb.PersistentClient`, collection `scholarly_records_v1`, index version `scholarly-record-v1` (`:45`, `:50`), default path `backend/vector_index` (`VECTOR_INDEX_PATH` overrides, `:49`). `backend/chroma_db/` also exists in the tree; which one the running app uses depends on environment and was not checked.
- **Distance: cosine.** The collection is created with `"hnsw:space": "cosine"` (`:243`) and similarity is computed as `1 − distance`, clipped to [−1, 1] (`:384`). Hits below `min_score = 0.35` (default parameter, `:348`) are discarded.
- **Stale documentation:** the header of `rag/retrieval.py` (`:11-15`) describes "Euclidean distance … `1.0 − d/2.0`" and says the 0.35 floor "eliminate[s] 100% of out-of-domain and gibberish false acceptances". The code contradicts the first statement and no evidence for the second was inspected. Do not repeat either.
- The 0.35 floor is a constant. Whether it was ever tuned or validated is **[Not verified]**; the 20-query evaluation described in earlier audits was a threshold check, not a ranking-relevance study.
- The Chroma index being "ready with 449 documents" is **[Reported]** (roadmap); it was not opened here. Earlier documents quote 696 canonical publications and 2,186 source records for the database at an earlier time; those numbers are historical.

## 12. Gemini and other model integration [Inspected]

- `generate_explanation` (`explanation/synthesis.py:455-540`; duplicate at `rag/retrieval.py:458-540`) calls `{GEMINI_BASE_URL}/models/{model}:generateContent` with `x-goog-api-key`, temperature 0, JSON response type, 12 s timeout and up to 2 attempts.
- **The model name is read from the environment variable `GEMINI_MODEL`** (`synthesis.py:464`), default empty. If the key or model is missing, a deterministic fallback is returned (`status: provider_not_configured`). Module docstrings and the README name "Gemini 2.5 Flash"; the code does not pin it. No fixed model identity can be asserted for any result unless an experiment manifest records it.
- No live Gemini call was made in this task. Earlier documents report later live attempts failing (403/404). [Reported by repository documents; not re-checked]
- `generate_explanation` is invoked on the topical-retrieval path only; it does not influence candidate scores or decisions (`main.py:190-199`).

## 13. Provenance and citation handling [Inspected]

- Claims returned by the model are kept only if each cited `document_id` is in the set of retrieved hits (`explanation/synthesis.py:511-513`; identical logic in the duplicate at `rag/retrieval.py:514-516`). The "summary" shown is rebuilt from validated claim text. If none survive, a deterministic fallback summary is returned with status `citation_validation_failed_fallback`.
- This is **membership checking of identifiers**, not entailment. The module docstring says so. **Semantic citation faithfulness is not established.** Explanation quality is not evaluated.
- Author evidence rows keep per-signal `source_provenance_json` and `raw_value_json` (`evidence.py:27-35`).

## 14. Frontend [Inspected, minimal]

`frontend/src/services/api.js:59-62` sends `author_name` and `institution_hint` to `/author-resolutions/candidates`. The recovery commit changed `App.jsx` and `CandidateSelector.jsx` (empty candidate list and save-failure handling) **[Reported by the roadmap; not read in detail here]**.

## 15. Tests and reported verification

- Static count: **80** `def test_` functions across 13 test files in `backend/tests/` (3+4+9+4+1+4+1+3+2+15+15+14+5). This matches the reported "80 passed"; **the tests were not run here**, and parametrised tests could make runtime counts differ from the static count. [Reported]
- Tests relevant to RQ2 exist for candidate parsing and normalisation (`test_author_candidates.py`, `test_candidate_normalization.py`), evidence scoring and gating (`test_author_evidence_scoring.py`), service persistence (`test_author_resolution_service.py`), API (`test_author_resolution_api.py`), migration (`test_author_resolution_migration.py`), and benchmark/evaluator tooling (`test_evaluation_benchmark.py`, `test_author_evaluator_regression.py`, `test_annotation_workflow.py`).
- Recovery items reported by the roadmap (Alembic head, integrity checks, backup, `/health`, frontend build, 449-document index) are **[Reported]**. Manual **live-provider end-to-end verification remains an open limitation**; the repository contains no new evidence proving otherwise.

## 16. Known defects and risks for the paper

| # | Item | Evidence | Effect |
|---|---|---|---|
| D1 | Edition regex uses U+0008 instead of `\b` | `engine.py:90-93` | RQ1 unverified; edition guard probably inactive |
| D2 | Publication and coauthor evidence never available for live candidates | `candidates.py:265,267`; searched `backend/` | "Five-signal" claim overstated; effective signals fewer |
| D3 | `empty` OpenAlex response mapped to "source unavailable" in `create_resolution` | `resolver.py:166-167` | Must not be reused in an evaluator; contradicts Stage 2 failed-vs-empty rule |
| D4 | Fallback request failure swallowed; status can end `empty` | `candidates.py:523-524` | Failed vs empty indistinguishable for fallback (already noted in Stage 2) |
| D5 | Existing candidate rows reused without payload refresh | `candidates.py:550-552` | Replay and "live" claims need captured responses |
| D6 | Silent drop of unparsable stored payloads | `resolver.py:160-161, 267-268` | Possible silent evidence loss |
| D7 | Second candidate with no score ⇒ margin/dominance gates skipped | `resolver.py:78-84` | Auto-selection on a thin pool is easier than the gate list suggests |
| D8 | "≥2 signals" counts available, not non-zero | `resolver.py:84` vs docstring `:14` | Description mismatch |
| D9 | Hard-coded High/Medium/Low label | `main.py:218` | Can be misread as calibrated confidence |
| D10 | Stored evidence `weight` is `None` | `resolver.py:243` | Effective weights not stored |
| D11 | Duplicate retrieval/explanation code, stale invalid filter in `synthesis.py` | `synthesis.py:340-440` | Architecture figure and maintenance risk |
| D12 | Tie-break by descending source ID | `resolver.py:74` | Equal-score ordering is arbitrary but deterministic |

## 17. Unverified functionality

- Any live provider end-to-end behaviour, including OpenAlex rate-limit behaviour in practice.
- Whether the committed `rag/retrieval.py` filter fix works with the installed Chroma version.
- Whether Alembic is at head and Chroma holds 449 documents (reported only).
- Whether the regression test for editions fails or passes.
- Actual signal availability rates on any real query (section 7 is a code reading).
- Whether Scholar/faculty connectors run and which sources contributed historical data.
- Frontend behaviour beyond the API call shapes.

## 18. Research functionality not empirically evaluated

Everything in RQ2: retrieval recall, ranking, automatic precision, coverage, selective risk; the name-only comparison; the behaviour of the gates on independent labels. Also: semantic retrieval ranking quality, explanation quality, citation faithfulness, scalability, latency, multilingual or cross-domain behaviour, and the reviewer UI's usability. Historical V3/Day 5 numbers are exploratory and misaligned (see `docs/research/HISTORICAL_EVIDENCE_TIMELINE.md`).

## 19. Differences between current implementation and earlier descriptions

| Earlier statement | Where | Current implementation |
|---|---|---|
| Name similarity is Jaro-Winkler; institution is Jaccard; temporal is Gaussian decay | `scoring.py:7-11` docstring | RapidFuzz `token_sort_ratio`, RapidFuzz `token_set_ratio`, and year-range overlap ratio (`evidence.py`) |
| Auto needs "non-zero signals in >= 2 independent categories" | `resolver.py:14` | `available_signals >= 2` (non-null) |
| Chroma distance is Euclidean, similarity `1 − d/2`; floor "eliminates 100%" of OOD | `rag/retrieval.py:11-15` | Cosine space, `1 − d`; no validation of the claim inspected |
| "Multi-strategy candidate harvesting" | `README.md` | One request plus one conditional initial-only fallback |
| "Gemini 2.5 Flash" | README, `synthesis.py` docstring | Model from `GEMINI_MODEL`, unpinned |
| "Edition conflict guards" work | README, `engine.py` docstring | Regex defect (D1) |
| 10-query pilot and ≥100 author queries | `docs/evaluation/dataset.md` | Approved pilot is 10 resolved + 5 unresolved; main-study size deferred (Stage 2 decision register D09) |
| Evidence computed from local DB/index state | `EXPERIMENT_PROTOCOL_RQ2.md` | `evidence.py` uses only candidate payload and request context |
| Software baseline `d41378c` | Stage 2 documents | Current commit `bee7eab`; resolver persistence and Chroma filters changed |
| 696 publications / 2,186 source records | `docs/research-paper.md`, `dataset.md` | Historical database counts; index reported at 449 documents; do not reuse |
