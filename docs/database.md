# Database and migrations

## Canonical storage

SQLAlchemy models in `backend/database.py` define source-record and publication records, duplicate groups, pairwise similarity logs, response/Scholar caches, circuit-breaker state, and additive author-resolution tables. Source records retain provider-native IDs and raw payload; canonical publications retain merged fields, source list, and provenance fields. Author candidates are hypotheses; persisted author resolutions and feature evidence preserve outcome and resolver/scoring/threshold versions. `publication_authorships` records source identity strength explicitly and must not be interpreted as a verified cross-source link without its provenance.

## Current local database caution

The backend and root `academic_search.db` files are distinct histories. From `backend/`, the default relative URL points to `backend/academic_search.db`; from the repository root, it points to the other file. The audited backend DB is at Alembic revision `20260907_01`; the root DB has legacy tables only. See [baseline audit](baseline-audit.md). Do not use one as a substitute for the other.

## Migration workflow

1. Resolve `DATABASE_URL` to a specific absolute path without exposing credentials.
2. Query Alembic current revision and heads; inspect the migration source.
3. Take a copy/backup while the app is stopped or SQLite is checkpointed. Verify backup integrity and row counts.
4. Apply `cd backend && ../.venv/bin/alembic upgrade head` only to the selected database.
5. Re-run schema/revision, SQLite `integrity_check`, `foreign_key_check`, and row-count checks. Keep a rollback/restore plan.

`20260907_01_author_resolution_foundation.py` adds author identity, candidate, affiliation/alias/external ID, resolution/evidence, and publication-authorship tables. It does not alter the legacy publication/dedup tables. Retrieval uses a rebuildable Chroma directory and adds no SQL migration.

Repeated selection of the same source-scoped profile reuses the existing author linked to that `(source, external_id)` pair. It does not create a duplicate external-ID row or a second internal author for the same provider profile.

Repeated selection of the same source-scoped profile reuses the existing author linked to that `(source, external_id)` pair. It does not create a duplicate external-ID row or a second internal author for the same provider profile.

## Backup and test safety

Never point tests at a real application database. Existing tests use disposable databases. Keep database snapshots and WAL/SHM files out of version control; do not overwrite the user-provided local DB or its backup. Production must use persistent storage and a verified restore process. SQLite should remain single-instance for concurrent writes; multi-instance deployment requires a planned PostgreSQL migration.