# Five-signal implementation notes

**Baseline:** commit `bee7eabfba2d88c4a03c12d227ac6b04624fb8c8`. All changes are **uncommitted** in the working tree.  
**Not done:** no live provider call, no experiment, no annotation, no benchmark change, no commit, no push. New OpenAlex works requests have only been exercised against mocked HTTP transports.  
**Unchanged:** the five weights (0.35/0.25/0.20/0.10/0.10), the thresholds (0.75/0.15/1.35/0.45/min 2 signals), the research questions, the protocols. `config.py` changed by 8 additive lines (enrichment retrieval bounds); a test asserts the weights and thresholds.

## 1. What now exists

| Layer | File | Purpose |
|---|---|---|
| Typed query context | `backend/author_resolution/context.py` | Aliases, institutions (name/OpenAlex ID/ROR), DOI and OpenAlex work-ID publications, coauthors (name or OpenAlex ID), active years. Validated, bounded (≤50 publications/coauthors), absent ≠ empty. Title-only publications are counted as ignored, never compared. |
| Enrichment types | `enrichment_types.py` | `PublicationLinkEvidence`, `CoauthorEvidence` with statuses `not_requested/ok/empty/failed`, retrieval timestamp, provenance, error code. |
| Enrichment (only network code for works evidence) | `enrichment.py` | One query-level works lookup (DOIs/work IDs → authorships) and a bounded per-candidate coauthor sample (2 pages × 100 works, basic paging). Failures and partial success recorded per signal; HTTP 429 stops further requests. |
| Evidence extraction | `evidence.py` | Pure; seven statuses; stricter institution matching; query aliases; temporal inconclusive-before-window. |
| Scoring | `scoring.py` | Score unchanged; now also records `signal_set` and `effective_weights`. |
| Decision policy | `policy.py` | Approved gates unchanged + five evidence-sufficiency safeguards. |
| Service | `resolver.py` | `generate_pool` (structured status), `create_resolution_detailed`, `CandidateSourceUnavailable.error_code`. `create_resolution` and `decide` keep their old signatures. |
| API | `main.py` | Validated context; additive response fields (`candidate_retrieval_status`, `algorithmic_assessment`, `context_received`, `enrichment`, per-evidence `status`/`weight`, `decision_source`). |
| Persistence | existing tables, **no migration** | Enrichment stored in `sample_publications_json`, `coauthor_summary_json` and an `enrichment` block in `raw_payload_json`; evidence `weight` column now holds the effective renormalised weight; evidence status in `source_provenance_json`. |
| Frontend | `AuthorContextForm.jsx`, `contextModel.js`, `CandidateSelector.jsx`, `App.jsx`, `api.js` | Optional context fields; context sent on both candidate search and the review decision; all five signals always listed, unavailable ones labelled; advisory system assessment; "Confidence" relabelled "Heuristic score band". |
| Dedup | `deduplication/engine.py:91` | Two U+0008 bytes replaced by `\b`. |

## 2. Five-signal verification matrix

| Signal | Actual input | Source | When available | Provenance recorded | Failure behaviour | Tests |
|---|---|---|---|---|---|---|
| Name | Query name (+ optional aliases) vs OpenAlex `display_name` and alternatives | Candidate payload | Always for a valid candidate | Best query/candidate pair, compared names | n/a | `test_author_evidence_scoring.py` |
| Institution | Supplied institution (text, OpenAlex ID, ROR) vs candidate affiliations | Request; OpenAlex `last_known_institutions` + `affiliations` | Institution supplied **and** candidate has affiliations | Basis (`ror_equal`, `openalex_id_equal/different`, `name_token_sort`), best pair, coverage note | Absent query or candidate data → unavailable (never a mismatch); IDs that cannot be compared → `unresolvable` | same |
| Publication overlap | Supplied DOIs / OpenAlex work IDs vs authorships of those works | OpenAlex works lookup (1 request per query) | Publications supplied **and** lookup succeeded **and** at least one work comparable | Matched/comparable/unresolved/truncated work IDs, retrieval time, context fingerprint | Failed → `retrieval_failed`; empty or all truncated → `inconclusive`; stale context → `not_retrieved` | `test_author_enrichment.py`, `test_author_evidence_scoring.py`, `test_author_provider_status.py` |
| Coauthor overlap | Supplied coauthors vs coauthors from candidate's own works' authorships | OpenAlex works sample (≤200 works/candidate) | Coauthors supplied **and** sample succeeded **and** a resolvable match exists, or the sample is complete | Matches with basis (`openalex_id` / `display_name_exact`) and supporting work IDs, unresolvable names | Failed → `retrieval_failed`; zero overlap in an incomplete sample → `inconclusive`; initials/single-token names → `unresolvable` | same |
| Temporal | Supplied year range vs min/max year in `counts_by_year` | Request; OpenAlex author | Years supplied **and** candidate range present | Both ranges, coverage note | Query range before the candidate's observed range → `inconclusive`; after it → observed 0.0 | `test_author_evidence_scoring.py` |

"Available" always means the *request supplied the input and the data was obtained*. In a name-only UI search only name is available, exactly as before; the architecture now allows the others when context exists.

## 3. Decisions made (each is a candidate for research-director review)

| # | Decision | Reason | Alternative |
|---|---|---|---|
| P1 | Automatic assignment requires an observed, non-zero institution/publication/coauthor signal | Conservative design assumption that name and temporal agreement alone are insufficient (not an empirical finding) | Count temporal as corroboration (previous behaviour) |
| P2 | Observed signal with score exactly 0.0 on the top candidate blocks automation | Prevents a strong name from overriding zero-support evidence; no new number | Allow, report |
| P3 | Competitors must have the same signal set as the top candidate for automation (option D) | Avoids comparing scores built from different evidence; ranking untouched | Option B: compare on a common signal subset |
| P4 | Unscored competitor in a multi-candidate pool fails closed; single-candidate pools skip margin/dominance only | Distinguishes "no competitor" from "competitor with no evidence" | Always send single-candidate pools to manual review |
| P5 | Any retrieval failure in the pool, or an unreadable candidate, blocks automation | A provider error must not become agreement | Block only when the failed candidate is the top one |
| P6 | **Amended:** only OpenAlex author IDs score coauthor evidence; name-only input is `unavailable_input_unresolvable`, with count-only diagnostics | A name is not an identity; no automatic name-to-ID mapping | Name matching (rejected after pre-commit review) |
| P7 | Institution comparison: ID/ROR equality, else `token_sort_ratio` (was `token_set_ratio`); **provisional, awaiting protocol approval; not equivalent to the protocol's token-set wording** | A token subset scored 1.0 | Keep token-set |
| P8 | Reviewer decisions append the algorithmic assessment to `decision_reason` | Distinguishes reviewer from algorithm without a migration | New column (migration) |
| P9 | Coauthor sample bound: 2 pages × 100 works, explicit sort `publication_date:desc,cited_by_count:desc` | Bounded; sort is documented; cursor paging needs an API key. Recency bias and undocumented tie order are accepted limitations | Other bounds |
| P10 | Ranking order unchanged (review option C) | No new numeric parameter; forced top-1 definitions intact | Common-subset ranking (not adopted). **Candidates scored on different signal sets are not necessarily directly comparable, including for forced top-1.** |

## 4. Defects from earlier audits: status

| Earlier item | Status |
|---|---|
| D1 edition regex | **Fixed**, regression-tested (same-year cases) |
| D2 publication/coauthor never available | **Addressed**: available from supplied context + successful enrichment; unavailable otherwise |
| D3 empty response treated as unavailable | **Fixed** (service and API) |
| D4 fallback failure swallowed (`candidates.py` initials fallback) | **Not changed**; capture both request outcomes in any evaluation |
| D5 existing candidate rows reused without payload refresh | **Partly**: enrichment is merged; the OpenAlex profile snapshot is still the first capture |
| D6 silent drop of unparsable stored payloads | **Fixed**: reported and blocks automation |
| D7 missing second score skips gates | **Fixed** (fails closed) |
| D8 "≥2 signals" docstring | **Corrected** in `resolver.py` and `scoring.py` docstrings; the code still counts available (non-null) signals |
| D9 hard-coded High/Medium/Low label | **Relabelled in the UI** as "Heuristic score band"; the API key `confidence` and its hard-coded 0.75/0.45 cut-offs remain, plus `score_is_heuristic: true` |
| D10 stored `weight` was `None` | **Fixed**: effective renormalised weight stored |
| D11 duplicate retrieval code in `explanation/synthesis.py` | Not touched (out of scope) |
| D12 tie-break by descending source ID | Not changed |
| Ranking mixes candidates scored on different signal sets (case H) | **Not changed.** Only automation is gated. Needs a decision before forced top-1 baselines are frozen |

## 5. Engineering test results (not research performance evidence)

Commands, run from the repository root:

```
cd backend && PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest tests -q -p no:cacheprovider
node --test frontend/src/features/author_resolution/contextModel.test.js
cd frontend && npm run build
```

Results at the time of the first implementation: backend **145 passed, 0 failed, 0 skipped** (baseline before the change: 80 passed); frontend pure-function tests **8 passed**; `npm run build` **succeeded**. Not run: `backend/test_scraper_local.py` (a stray root-level file that pytest collects by default and which fails on a missing async plugin; it is outside `tests/` and unrelated). Not covered by automated tests: React component rendering and save-failure presentation (the repository has no frontend test framework and none was added); live OpenAlex behaviour; real browser use.

## 6. Limitations and caveats

1. **Live verification is partial.** See `FIVE_SIGNAL_LIVE_VERIFICATION.md`: request shapes, sort and paging were accepted live; a positive publication/coauthor match for a real author was not demonstrated (the chosen profile was a fragment). Mocked tests do not represent live operation.
2. **Coauthor evidence needs OpenAlex author IDs**, which most users will not have; the UI therefore rarely produces it.
3. **OpenAlex author fragmentation:** a real person's work may sit on another profile ID, so zero publication overlap is evidence about the *profile*, not the person.
4. **Temporal:** the candidate range comes from `counts_by_year`, whose covered window OpenAlex does not document; affiliation intervals are not used.
5. **Name normalisation** still has no diacritic folding or transliteration.
6. **Coverage cost of P3/P5:** these safeguards may reduce automatic-assignment coverage. Coverage has not been measured and must not be claimed.
7. **UI never auto-accepts.** It records manual selections or unresolved; the algorithmic assessment is advisory.
8. **Nothing here has been empirically evaluated.** The paper may describe the architecture and policy, not performance.

## 7. What the paper may and may not say

May: a heuristic evidence resolver with up to five signals whose availability depends on supplied context and successful enrichment; explicit signal statuses and provenance; a conservative automatic-assignment policy with evidence-sufficiency safeguards; a structured distinction between empty retrieval and provider failure.  
May not: that all five signals are used in ordinary queries; that the score is a probability or calibrated; that the safeguards improve precision (untested); anything about coverage, accuracy, recall, or the live behaviour of the works requests.
