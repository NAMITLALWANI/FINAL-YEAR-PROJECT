# Five-signal data-source feasibility

**Status:** Phase A deliverable for the five-signal implementation task. Written **before** the enrichment code.  
**Baseline commit:** `bee7eabfba2d88c4a03c12d227ac6b04624fb8c8` (implementation then proceeds on the working tree; nothing is committed).  
**Method:** static code reading plus OpenAlex documentation pages (`help.openalex.org`, read as documentation only). **No live provider call was made** in this task, so every statement about live OpenAlex behaviour is "per documentation, not verified against the live service".

## 1. Current data sources, per signal

| Signal | Query-side source today | Candidate-side source today | Reaches the evidence layer today? |
|---|---|---|---|
| Name | `author_name` | OpenAlex `display_name`, `display_name_alternatives` | Yes |
| Institution | `institution_hint` (UI hard-codes `null`, `App.jsx:164`) | OpenAlex `last_known_institutions` + `affiliations` | API only |
| Publication overlap | `context.publications` (API only) | **None.** `candidates.py:265` sets `sample_publications=None` | **No** |
| Coauthor overlap | `context.coauthors` (API only) | **None.** `candidates.py:267` sets `coauthor_summary=None` | **No** |
| Temporal | `context.active_year_start/end` (API only) | `counts_by_year` min/max | API only |

## 2. Required input schema (what the typed context now represents)

Query side (`QueryContext`): aliases; institutions as `{name, openalex_id?, ror?}`; publication identifiers (DOIs and OpenAlex work IDs only); coauthors as `{name?, openalex_id?}`; `active_year_start/end`. Candidate side: canonical OpenAlex author ID, display name and aliases, affiliations with institution IDs and ROR, publication-link evidence, coauthor evidence, observed year range. Unknown, empty, unavailable and failed are distinct statuses (see section 7).

> **Amendment (after pre-commit review):** section 3.4's name-basis coauthor matching was removed. Only OpenAlex author IDs score coauthor evidence; names are diagnostics only. The coauthor works sample now uses the explicit sort `publication_date:desc,cited_by_count:desc`. Where this report says name entries may match, it is superseded by `FIVE_SIGNAL_IMPLEMENTATION_NOTES.md`.

## 3. Signal-by-signal findings

### 3.1 Name
- **Existing:** RapidFuzz `token_sort_ratio` on casefolded, whitespace-collapsed strings (`candidates.normalize_name`), maximum over display name and aliases.
- **Gaps (not changed):** no diacritic folding or transliteration, so "José" and "Jose" differ; initials are compared as tokens. NFC is applied only to the *query sent to OpenAlex* (`clean_query_name`), not inside the similarity function.
- **Added:** optional query-side aliases (the best matching pair is recorded).
- **Risk:** a name score is never identity evidence on its own; the decision policy now requires corroboration (section 9).
- **Class:** available now.

### 3.2 Institution
- **Existing:** `token_set_ratio` over hint × affiliation names. Verified in the diagnostic: "Example Institute of Technology" vs "Example Institute" scored 1.0 because `token_set_ratio` treats a token subset as a full match.
- **Candidate data:** `last_known_institutions` (most recent publication year with any institution) and `affiliations` with `years`, which OpenAlex documents as capped at roughly the last ten years. OpenAlex institution IDs are kept (`source_institution_id`); ROR is now also kept when present in the payload.
- **Change:** name comparison uses `token_sort_ratio` (order-insensitive, **not** subset-lenient); exact OpenAlex-institution-ID or ROR equality gives 1.0; an absent query institution or absent candidate affiliations is *unavailable*, never a mismatch. This changes institution score values relative to older runs; it changes no weight and no threshold. It deviates from the Stage 2 text ("maximum institution token-set similarity"), which therefore needs a documentation correction and owner acknowledgement.
- **Limitation:** affiliation *intervals* are not used for temporal relevance; the documented ten-year cap makes older affiliations invisible. A non-match on an ID is therefore weak evidence of a different person.
- **Class:** available now (UI field added).

### 3.3 Publication overlap
- **Sources considered, in the requested order:**
  1. *Local scholarly records* (`publications`, `source_records`, `publication_authorships`): they hold author **name strings** from providers, with no stable link to an OpenAlex author ID, and they are an application database, not an evaluation snapshot. Linking by name would fabricate identity. **Rejected.**
  2. *Publication identifiers in the request:* feasible. DOIs and OpenAlex work IDs are accepted, normalised and validated. Title-only entries are **not** compared (recorded as ignored).
  3. *OpenAlex works endpoint:* feasible and used, but in the **reverse direction**: look up the query's own DOIs once per query (`works?filter=doi:...|...`, OR of up to 100 values per documentation), then test whether each candidate's OpenAlex author ID appears in those works' authorships. Compared with fetching each candidate's full works list this is exact for the supplied works (no truncation question), needs **one** request per query instead of one per candidate, and compares genuinely corresponding works.
  4. Other providers: not justified.
- **Score:** matched query works ÷ query works that OpenAlex could resolve. Identifiers OpenAlex cannot resolve are excluded from the denominator and listed; works with truncated author lists are excluded and listed.
- **Failure modes:** DOI absent from OpenAlex (excluded, not a conflict); OpenAlex author fragmentation (a real person's work can sit on another profile ID, so zero overlap is observed evidence about *this profile*, not about the person); request failure (status `retrieval_failed`, signal unavailable).
- **Limits:** at most 50 identifiers per query (input bound); chunked at 50 per request, so one request per query; no pagination needed. Freshness: OpenAlex at request time; the retrieval timestamp is recorded.
- **Class:** requires provider integration (OpenAlex works endpoint, already the approved provider, no new credentials). Unverified against the live service in this task.

### 3.4 Coauthor overlap
- **Sources:** candidate-side coauthors can only be derived from the candidate's **actual works' authorships**. Per candidate, one bounded retrieval: `works?filter=author.id:{id}&per-page=100&page=1..2` with a fixed page cap (200 works). Basic paging is documented as limited to 10,000 results; cursor paging beyond the first page requires an API key per documentation, so **cursor paging is not used**. Retrieval is performed **only if** the query supplied coauthors.
- **Identity:** coauthors are OpenAlex author IDs from authorships; the candidate's own ID is excluded; entries are deduplicated by ID, with up to three supporting work IDs retained as evidence.
- **Query side:** coauthors may be given as OpenAlex author IDs (identity-level) or as names. A name entry matches only by **exact normalised full-name equality** with a candidate-coauthor display name, requires at least two tokens of at least two characters each (initials and single tokens are *unresolvable* and listed, not matched), and is recorded with basis `display_name_exact`. This is the weakest defensible rule; it is flagged for research-director review (section 14).
- **Truncation:** a positive overlap is positive evidence. Zero overlap when the author's works were **not fully covered** is *inconclusive* (signal unavailable), not a conflict.
- **Failure modes:** common names; works with truncated author lists; collaborations with very many authors; request failure (signal unavailable, status recorded).
- **Class:** requires provider integration. Unverified against the live service.

### 3.5 Temporal
- **Existing:** query range vs candidate range from `counts_by_year`. OpenAlex documentation does not state which years that array covers, so the candidate range may be a recent window.
- **Change:** range validity is enforced (1800–2200, start ≤ end); query years are never inferred from candidate data. If the ranges do not overlap **and the query range lies entirely before the candidate's observed start**, the result is *inconclusive* (unavailable), because earlier activity may simply be outside the observed window. A query range entirely after the candidate's observed end is an observed 0.0.
- **Class:** available now (UI fields added). Works-derived years were not added (would duplicate the bounded coauthor sample and need its own coverage rules).

## 4. Provider and API dependencies
OpenAlex only: `authors` (existing), `works` (new use). Authentication is the existing optional `api_key` and polite-pool `mailto` from configuration; no new credentials, no paid API, no new provider. Secrets are not logged; request logs carry candidate IDs and status codes, never query text, DOIs or coauthor names.

## 5. Local versus remote data
Evidence extraction and scoring stay **pure and offline**: they read only the typed candidate (including its stored enrichment) and the typed query context. All remote access is in a separate enrichment service that runs between candidate retrieval and persistence. Local scholarly tables are **not** read for evidence (reason in 3.3).

## 6. Completeness limitations
OpenAlex author profiles are fragmented and merged by an automated process; works lists and authorships can be incomplete; affiliations and counts-by-year are windowed; DOIs may be missing for works. All of these are recorded as limitations, and none is converted into positive evidence.

## 7. Evidence status vocabulary (additive; no schema migration)

`observed` (a score exists; may be 0.0 as observed non-support) · `unavailable_query_input_absent` · `unavailable_candidate_data_absent` · `unavailable_not_retrieved` (including "retrieved for a different context") · `unavailable_retrieval_failed` · `unavailable_inconclusive` · `unavailable_input_unresolvable`. Stored in the existing `source_provenance_json`; the DB `availability` column keeps its approved values.

## 8. Rate-limit and failure handling
Per-request timeout from existing config; a bounded number of requests per query: 1 (query-works lookup, only if publications were supplied) + at most 2 pages per candidate × at most 10 candidates (only if coauthors were supplied) = at most 21. HTTP 429, timeouts, HTTP errors and malformed bodies produce `retrieval_failed` for the affected signal only; they never fail the candidate pool and never count as agreement. Any failed enrichment in the pool blocks automatic assignment.

## 9. Caching and provenance
The existing `cache.py` caches search results by author name; it is not suitable for per-author works. Enrichment results are stored on the existing `author_candidates` row (`sample_publications_json`, `coauthor_summary_json`, and an `enrichment` block inside `raw_payload_json`), with retrieval timestamp, endpoint, parameters (without secrets), counts, truncation flag and a hash of the query-side identifiers used. A stored publication result is reused only when that hash matches the current context; otherwise it is reported as *not retrieved for this context*, with no hidden network request. No new tables or migrations.

## 10. False-match risks (summary)
Name-only coauthor matching; fragmented profiles producing zero overlap; DOI typos; shared DOIs of collaborative works with truncated author lists; institution-name variants; an author who moved institutions outside the ten-year window.

## 11. Feasibility classification

| Signal | Class | Implemented |
|---|---|---|
| Name (+ aliases) | Available now | Yes |
| Institution (names, IDs, ROR) | Available now | Yes, stricter matching |
| Publication overlap | Requires provider integration (existing provider) | Yes, offline-tested only |
| Coauthor overlap | Requires provider integration | Yes, offline-tested only; name-basis match flagged |
| Temporal | Available now | Yes, with inconclusive-before-window rule |
| Title-based publication matching | Not reliably obtainable | **Not implemented** (title strings are ignored) |
| Coauthors from local scholarly tables | Not reliably obtainable (no stable IDs) | **Not implemented** |

## 12. Recommended implementation sequence
Typed context and identifier normalisation → enrichment service (mocked) → evidence extractors and statuses → scoring metadata → decision policy and comparability gate → empty/failed/partial handling in service and API → frontend optional context → dedup edition regex → tests → documentation.

## 13. Policy approach selected for candidate comparability (Phase E)

| Option | Interpretability | False-merge risk | Coverage cost | Protocol impact | Decision |
|---|---|---|---|---|---|
| A. Require equal evidence sets to rank | High | Lowest | Highest; changes ranking | Changes the committed ranking that Stage 2 policies 2 and 3 share | Rejected |
| B. Compare on a common subset | Medium | Low | Medium | Changes the score used for margin | Alternative for director |
| C. Separate sufficiency/comparability gate | High | Low | Medium | Ranking untouched | **Combined with D** |
| D. Keep ranking, block automatic assignment when incomparable | High | Low | Medium–high | Ranking and scores untouched | **Selected** |

Ranking order and weights are preserved exactly; only the **automatic** outcome is gated, so the forced-top-1 policies in the Stage 2 protocol are unaffected.

## 14. Decisions needing research-director approval

1. **Corroboration rule:** automatic assignment requires at least one observed, non-zero signal among institution, publication or coauthor evidence (temporal and name alone do not suffice). This tightens the policy without a new number.
2. **Hard-conflict rule:** automatic assignment is blocked if the top candidate has any observed signal with score exactly 0.0.
3. **Comparability rule:** automatic assignment requires every competitor to have been scored on the same signal set as the top candidate; option B is the alternative.
4. **Single-candidate pool:** margin and dominance are not applicable, but the corroboration, conflict and enrichment gates still are.
5. **Name-basis coauthor matching:** allow exact full-name matches (current choice), or restrict to ID-level matches only.
6. **Institution function change** from token-set to token-sort similarity (and the matching Stage 2 wording).
7. **Enrichment bounds:** 2 pages × 100 works per candidate for the coauthor sample.
8. **Ranking comparability (not changed):** the ranking itself still sorts candidates scored on different signal sets together (the diagnostic's case H). This is outside the automatic gate and needs a decision before forced-top-1 baselines are frozen.
