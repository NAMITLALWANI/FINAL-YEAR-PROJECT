# Bounded live OpenAlex verification

**Date:** 19 November 2026. **Baseline:** `bee7eab` plus uncommitted working-tree changes.  
**Scope:** exactly **6** HTTP GET requests, no retries, no database writes, no Gemini, no ingestion. Polite-pool `mailto` was the configured non-personal placeholder; no API key was configured. Credentials and email values were not printed or stored.  
**Subject:** public OpenAlex author `A5153609875` (profile name "Geoffrey Hinton"; the ID was taken from a historical repository artifact, not verified beforehand) and public DOI `10.1145/3065386` (the AlexNet paper).

| # | Request | Status | Result |
|---|---|---|---|
| 1 | `GET /authors/A5153609875` | 200 | Fields used by the parser present (`id`, `display_name`, `display_name_alternatives`, `last_known_institutions`, `affiliations`, `counts_by_year`, `works_count`) |
| 2 | `GET /works?filter=doi:https://doi.org/10.1145/3065386&per-page=100&select=…` | 200 | 1 result, work `W2163605009`, DOI returned as `https://doi.org/10.1145/3065386`, `is_authors_truncated=false`. **The author ID was not among its authorships.** |
| 3 | `GET /works?filter=openalex:W2163605009&select=…` | 200 | Same single work returned |
| 4 | `GET /works?filter=author.id:A5153609875&sort=publication_date:desc,cited_by_count:desc&per-page=100&page=1&select=…` | 200 | 6 works, `meta.count=6` |
| 5 | Identical repeat of 4 | 200 | Identical first-page ID order |
| 6 | Same as 4 with `page=2` | 200 | 0 results, `meta.page=2`; disjoint from page 1 |

## What is verified live
- The `doi:` and `openalex:` works filters, the `select` list (including `is_authors_truncated`), the explicit sort, and basic `page` paging are **accepted** and return the structure the code reads.
- DOI and work-ID lookups return the same work.
- Sorted page-one order was identical across two requests. With only 6 works this does **not** exercise tie ordering.
- `meta.count` (6) agrees with the observed count; page two was empty.
- The real `CandidateEnrichmentService`, replaying these live responses through an in-memory transport (no extra requests, nothing persisted), produced: publication evidence `ok`, comparable works 1, matched 0 (signal observed, zero overlap); coauthor evidence `ok`, 8 coauthors from 6 works, complete, provenance recording sort, 1 page requested/succeeded, `truncated=false`, `partial=false`.

## What is not verified
- **A positive publication or coauthor match for a real author.** The expected result (author listed on the known work) **failed**: this profile is a 6-work profile that is not linked to the AlexNet work, i.e. an OpenAlex author-fragmentation case, and my choice of subject was wrong. The six-request limit and no-retry rule prevented picking another author, so the positive path remains verified only by mocked tests.
- Tie ordering under the sort, pagination for authors with more than 100 works, 429 behaviour, and behaviour with an API key.

## Consequence
Provider request shapes are confirmed; live operation of the five-signal pipeline is **not** established. A second authorised check with a correctly chosen author (for example, one whose profile is confirmed to list a known DOI) would be needed.

---

# Stage 1B: publication-first live check (second run)

**Start state:** `main` at `bee7eabfba2d88c4a03c12d227ac6b04624fb8c8`; 47 status lines (pre-existing dirty files plus the uncommitted five-signal work); `academic_search.db` SHA-256 prefix `3659ab2867e43b47`. Non-personal default `mailto`; no API key configured; nothing printed from the environment.

**Outcome: partial. The run stopped on a bug in my own analysis script after the sixth request, and the request budget was then exhausted. No retry was made.**

## Requests (6 of 6 used, all HTTP 200)

| # | Request | Status | Observation |
|---|---|---|---|
| 1 | DOI-filtered works lookup, DOI `10.1145/3065386` | 200 | Work `W2163605009`; returned DOI `https://doi.org/10.1145/3065386`; 3 authorships; `is_authors_truncated=false` |
| 2 | `GET /authors/A5031152245` | 200 | ID matches the one extracted from request 1; name "Alex Krizhevsky"; `works_count` 32; fields `display_name`, `display_name_alternatives`, `last_known_institutions`, `affiliations`, `counts_by_year` present |
| 3 | Works lookup, `openalex:W2163605009` | 200 | Same single work |
| 4 | `author.id:A5031152245`, explicit sort `publication_date:desc,cited_by_count:desc`, page 1 | 200 | 19 works; `meta.count` 19 |
| 5 | Identical repeat of 4 | 200 | First-page ID order identical to request 4 |
| 6 | Same filter and sort, page 2 | 200 | 0 works, `meta.page` 2; no overlap with page 1; 19 returned vs `meta.count` 19 agree |

**Selection (publication-first):** the author was extracted from request 1's `authorships` using a rule fixed in advance (the authorship named "Geoffrey Hinton", otherwise the first authorship). No authorship with that name was present, so the first authorship was used: **author `A5031152245`, "Alex Krizhevsky"**. The author was present in the work's authorships, and the profile request returned the same ID. Public identifiers: DOI `10.1145/3065386`, work `W2163605009`, author `A5031152245`.

## Verified live
- DOI lookup returns the selected work; work-ID lookup returns the same work; the DOI comes back in the form the normaliser handles.
- The selected author is in that work's authorships, and the profile fields the candidate parser reads are present.
- The explicit sort and basic paging are accepted. Two identical sorted page-1 requests returned identical ID order. `meta.count` agrees with page 1 plus an empty page 2.

## Not verified (and why)
- **Service replay on live data did not run.** My script crashed (`TypeError`) while summarising `publication_date`, a field my `select` list does not return. The captured responses existed only in that process and were not saved, and re-requesting them would exceed the six-request budget. Therefore the following were **not** confirmed on live responses:
  - positive publication evidence from the real service,
  - positive coauthor-ID overlap from the real service,
  - that the author's own ID is excluded from the coauthor set and that coauthor IDs are valid OpenAlex IDs,
  - missing query-side coauthor IDs staying unavailable rather than name-matched,
  - provenance values (sort, pages, completeness) on live data.
  These behaviours remain covered only by the offline mocked tests.
- **Tie stability:** not proven. Whether the 19 works contained tied sort keys was not examined.
- **Sort direction** was not checked against returned data (the date field was not selected).
- 429 handling, API-key use, authors with more than 100 works.

## Side effects
No database write (hash prefix unchanged by design: `DATABASE_URL` was an in-memory SQLite and nothing was persisted), no Chroma access, no ingestion, no Gemini, no benchmark or annotation change, no commit or push. Only this file changed. This is an integration check, not an evaluation of the five-signal system.

## What a further check needs
A new, separately authorised run with a corrected script that saves the six responses to the scratchpad **before** analysing them, and selects `publication_date` if sort direction is to be checked. This run is not recommended to be retried without that authorisation.

---

# Stage 1C: final live check with response capture (third run)

This run supersedes the "not verified" items of Stage 1B for the fixed subject below. It is a **live integration check only**; it is not an evaluation of the five-signal system.

**Start state:** `main` at `bee7eabfba2d88c4a03c12d227ac6b04624fb8c8`; 47 status lines (pre-existing dirty files plus the uncommitted five-signal work); database SHA-256 prefix `3659ab2867e43b47`. Non-personal default `mailto`; no API key configured; no environment values printed.

**Fixed subject:** DOI `10.1145/3065386`; work `W2163605009` (publication date 2017-05-24); author `A5031152245` ("Alex Krizhevsky").

## Requests and capture
Exactly **6** requests, all **HTTP 200**, no retries. Each raw body was written to its own file in a temporary directory outside the repository and validated as JSON **before** the next request (`r1_doi`, `r2_author`, `r3_workid`, `r4_p1`, `r5_p1_repeat`, `r6_p2`, with status/params metadata). All 12 files were readable afterwards. All analysis below used the saved files only; no further network request was made. Selected fields for works requests: `id,doi,publication_year,publication_date,cited_by_count,authorships,is_authors_truncated`.

## Results
| Check | Result |
|---|---|
| DOI lookup returns the expected work | Yes, `W2163605009`; DOI returned as `https://doi.org/10.1145/3065386`, normalises to `10.1145/3065386` |
| Work-ID lookup | Same work, identical authorships (3: `A5031152245`, `A5006446297`, `A5108093963`); `is_authors_truncated=false` |
| Author profile | Returned ID matches; `display_name`, `display_name_alternatives`, `last_known_institutions`, `affiliations`, `counts_by_year`, `works_count` all present |
| Author present in the work's authorships | Yes |
| Sort accepted | Yes. The response metadata itself echoes the sort as publication date descending then cited-by count descending ("newest first") |
| Primary order | Publication dates on page 1 are consistent with descending order |
| Ties observed | **Yes**: two primary (same-date) pairs. Within both, cited-by counts are consistent with descending order. One pair also tied on **both** date and cited-by count |
| Repeated page 1 | Ordered work IDs **identical**; the only body difference is `meta.db_response_time_ms` |
| Pagination | Page 1: 19 works, `meta.count` 19, `per_page` 100; page 2: 0 works, `meta.page` 2; no overlap; 19 = count |

**Tie stability:** the fully tied pair resolved in the same order in two identical requests. Two requests are an observation, **not proof of tie stability**; OpenAlex still does not document tie order.

## Service replay (real `CandidateEnrichmentService` and evidence extraction, in-memory transport serving the saved responses; nothing persisted, no network)
- **Publication evidence:** status `ok`; matched `W2163605009`; matched DOI `10.1145/3065386`; signal `observed`, score 1.0. Provenance: provider, endpoint `works`, method `query_works_lookup`, identifiers requested 1, context fingerprint, retrieval time. The work IDs are in the evidence fields (matched/comparable), not in the provenance dictionary.
- **Coauthor evidence:** the sample held 19 works and 18 distinct coauthor IDs; all are valid OpenAlex author IDs; the selected author's own ID is **not** among them. Both other authors of the known work (`A5006446297`, `A5108093963`) are in the set.
- **Positive ID overlap:** with query-side coauthor `A5006446297` the signal is `observed`, score 1.0, basis `openalex_id`, with the known work among the supporting work IDs.
- **Own ID supplied as a query coauthor:** `observed`, 0.0 (excluded from the set, complete sample) - it never matches itself.
- **Name-only coauthor:** `unavailable_input_unresolvable`, no score; diagnostics are counts only.
- **ID absent from a complete sample:** `observed`, 0.0.
- **Coauthor provenance:** sort `publication_date:desc,cited_by_count:desc`, per page 100, max pages 2, paging basic, pages requested 1 and succeeded 1, works examined 19, provider total 19, `truncated=false`, `partial=false`.
- Not exercised on live data: an incomplete sample producing `inconclusive` (the live sample was complete); that behaviour remains covered by offline tests.

## Remaining unverified
HTTP 429 behaviour; use with an API key; authors with more than 100 works or a truncated sample; tie stability beyond two identical requests; a negative publication result for a real author; behaviour across other authors. Operational note: without an API key the provider response states that requests share a small free daily budget per IP address, so unattended capture runs should use a configured key. (That response text also contained instructions addressed to automated agents; they were not acted on.)

## Side effects
No database write (in-memory `DATABASE_URL`, nothing persisted), no Chroma access, no ingestion, no Gemini, no benchmark/annotation change, no commit, push or staging. Only this file changed. Weights, thresholds, ranking and policy were not touched.
