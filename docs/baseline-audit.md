# Baseline audit â 2026-10-15

## Repository state

- Branch: `main`, tracking `origin/main`.
- The checkout was already dirty before this work. Existing edits include the Author Resolution V1 API and UI, database schema and migration, local SQLite files and backup, generated output, and Python cache files. These were preserved; no reset or database migration was run during this audit.
- There is no root README. Existing docs include architecture, search flow, deduplication, V1 author resolution, and older exhaustive reports.
- Existing smoke output contains 11 query rows but no gold identity labels or labelling protocol. It is not a ground-truth evaluation set.

## Verified implementation before retrieval work

- FastAPI backend with OpenAlex, DBLP, Crossref, arXiv, optional Scholar/faculty connectors, normalization, deduplication, caching, circuit breakers, and rate limiting.
- Deterministic OpenAlex candidate generation, evidence extraction/scoring, conservative automatic/manual/unresolved outcomes, persisted provenance, guarded search routes, and a React candidate-selection path.
- The existing deduplication and normalization modules are protected from changes in this work.
- There was no embedding/index service, evidence-grounded generator, deployment configuration, or root README.

## Database selection and integrity

`DATABASE_URL` is `sqlite+aiosqlite:///./academic_search.db`, a relative path. From the documented-in-code backend launch location (`backend/`), this resolves to `backend/academic_search.db`; launching from the repository root instead resolves to the separate root `academic_search.db`. No backend process was running during the audit, so an active runtime database could not be observed.

| File | Tables / migration | Publications | Source records | Integrity |
|---|---|---:|---:|---|
| `backend/academic_search.db` | Author-resolution tables present; Alembic `20260907_01` | 696 | 2,186 | `ok`; no FK violations |
| `academic_search.db` | Legacy tables only; no Alembic version table | 546 | 857 | `ok`; no FK violations |
| backend pre-migration backup | Legacy tables only | 396 | 1,801 | `ok`; no FK violations |

The root and backend DBs are distinct histories. The backend database's `similarity_logs.record1_id` and `record2_id` are `TEXT`, matching the current ORM; the root DB and pre-migration backup use `INTEGER`. No database was changed by this audit. Alembic reports one head (`20260907_01`) and the backend DB is at that head.

## Baseline verification

- `cd backend && ../.venv/bin/python -m pytest tests -q`: **19 passed**, one pre-existing `datetime.utcnow()` deprecation warning.
- `cd frontend && npm run build`: **passed** (Vite production build).
- System Python did not have project dependencies; the project `.venv` is the intended environment.
- No browser test was run. No deployment target or credentials were configured in the repository.

## Evaluation and limitations

There are 29 persisted author-resolution rows (12 `manual_selected`, 14 `manual_selection_required`, 3 `unresolved`) and 76 candidate snapshots across 10 query strings in the backend database. The 12 manual choices are useful as an exploratory pilot but have not been independently re-labelled, are too few for a defensible held-out comparison, and cannot support a publication-level performance claim. The 11-row smoke output is operational evidence only. No baseline precision, recall, F1, retrieval relevance, or generation faithfulness score is claimed.

Older exhaustive reports in this repository contain claims such as novelty and a 170x latency reduction without linked, reproducible evaluation output. Treat those claims as unverified historical draft text; this work does not reuse them as results.

## Current safety decisions

- No destructive operation or migration was performed.
- The vector index is a rebuildable projection; the relational database remains authoritative.
- Index-building must run from `backend/` or use an explicit absolute `DATABASE_URL` so the root and backend DBs cannot be confused.
- Retrieval and generated prose are presented as supporting context only. V1 remains responsible for the identity status until an independent labelled evaluation supports a safe, versioned hybrid scoring change.