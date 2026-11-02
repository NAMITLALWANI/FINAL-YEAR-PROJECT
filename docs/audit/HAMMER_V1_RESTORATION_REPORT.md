# HAMMER — Phase 2: Controlled V1 Restoration & Integration Report

**Execution Timestamp:** 2026-11-01T22:15:00+05:30  
**Repository Working Directory:** `/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search`  
**Git Branch:** `main` | **HEAD Commit:** `2c4c5a93dd181e0e0aad3c557cef2e3c716a1c62`  
**Phase Status:** **SUCCESSFULLY COMPLETED** (All 51 test cases passing; 0 failures)

---

## 1. Executive Summary

In accordance with Phase 2 authorization, the recovered **Author Resolution V1 Subsystem** and related scholarly retrieval components have been restored and cleanly integrated into the active HAMMER application. 

Every constraint and safety protocol specified in the authorization was strictly observed:
1. **Zero Database Reconciliation or Destructive Cleanup**: Neither SQLite database was dropped, merged, moved, or deleted. Both databases remain independently preserved and cryptographically verified.
2. **Migration Preservation**: Alembic revision `20260907_01` was verified as already present in `backend/academic_search.db`. No redundant `alembic upgrade` command was executed.
3. **Database Path Hardening**: Connection resolution was hardened so that relative paths resolve deterministically to `backend/academic_search.db` regardless of execution working directory, while respecting explicit `DATABASE_URL` environment overrides.
4. **Scoring Threshold Invariance**: All conservative scoring thresholds and weights (`AUTHOR_AUTO_SCORE_THRESHOLD = 0.75`, `AUTHOR_AUTO_MARGIN_THRESHOLD = 0.15`, `AUTHOR_AUTO_DOMINANCE_THRESHOLD = 1.35`, `AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO = 2`) were maintained without alteration.
5. **ChromaDB Index Preservation**: The existing 449-document vector index at `backend/vector_index/` was verified as 100% healthy and in exact 1-to-1 correspondence with the canonical SQLite publications; no rebuilding was performed.
6. **Full Test & Integration Verification**: All 51 backend unit, service, API, migration, and benchmarking tests pass at 100%. The frontend production bundle (`npm run build`) builds cleanly with zero errors.

---

## 2. Baseline Establishment & Database Preservation

Before initiating any integration modifications, full system baselines were recorded and immutable backups created:

| Resource | Original Path | Baseline Metrics / Status | Independent Backup Location | Integrity Verification (`PRAGMA integrity_check`) |
| :--- | :--- | :--- | :--- | :--- |
| **Root Database** | `academic_search.db` | 25,493,504 bytes, 546 publications, 857 source records | `backups/baseline_20261101_215722/root_academic_search.db` | `[('ok',)]` |
| **Backend Database** | `backend/academic_search.db` | 46,047,232 bytes, 449 publications, 1,924 source records, 8 Alembic author tables | `backups/baseline_20261101_215722/backend_academic_search.db` | `[('ok',)]` |
| **Full Project State** | Repo root | 56 uncommitted items preserved | `backups/baseline_20261101_215722/academic_search_state_20261101_215722.tar.gz` (208 MB) | Verified tar gzip archive |
| **Alembic Revision** | `backend/alembic.ini` | Revision: `20260907_01` | Table `alembic_version` verified | `20260907_01 (head)` |
| **ChromaDB Index** | `backend/vector_index` | 449 records, `scholarly_records_v1`, `all-MiniLM-L6-v2` | Preserved in place | `status: ready`, 100% SQLite correspondence |

---

## 3. Files Restored & Cryptographic Hashes

All modules and test suites verified in `HAMMER_ARCHIVE_VERIFICATION.md` have been placed in their authoritative paths:

| Component | Path | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- |
| **Candidate Generation** | `backend/services/author_candidates.py` | `f9511a2d6b5342c49494281bedbaa9113cfbdc64e1202e3d702ea440c8333d31` | Verified Restored |
| **Evidence Extraction** | `backend/services/author_evidence.py` | `d15221034cd3c809b3495d009ba061433c52ffb90e5470166d6c8232964f3d7e` | Verified Restored |
| **Renormalized Scoring** | `backend/services/author_scoring.py` | `63f1e3b2aa9be1c28e7026d6cadaf80ce95fbb0ada8dbed6b21b9da0acc063df` | Verified Restored |
| **Author Resolution V1** | `backend/services/author_resolution.py` | `85a1a1db79986348ef53d8641154c9c61d50c76db33391782e44d56d78701e40` | Integrated & Hardened |
| **Semantic Retrieval** | `backend/services/scholarly_retrieval.py` | `7efa227f6fd073ef46d69921eae58f359b2433492a64efabb7d03da1165bb7a6` | Verified Restored |
| **V1 Schemas** | `backend/schemas/author_resolution.py` | `5a6a78bc2beae14d84cd776457d41c10d6beed7a3b559fc48fd85138f2f0e4ab` | Verified Restored |
| **Alembic V1 DDL** | `backend/alembic/versions/20260907_01_author_resolution_foundation.py` | `b0ba7abc454d50274a6db3c6cc2862b007510ffd7250a7740d01864b753af501` | Verified Restored |
| **Candidate Unit Tests** | `backend/tests/test_author_candidates.py` | `6dfad9ca4619ea2068cfab8d64f0f1c213a1b6c9538c8f0e7db167ca88fef365` | Verified Restored |
| **Evidence Scoring Tests**| `backend/tests/test_author_evidence_scoring.py` | `b9770340ae2573af5c1e93512b0e8ae19050c636a91fb9606cc7f8a4c804058b` | Verified Restored |
| **Retrieval Tests** | `backend/tests/test_scholarly_retrieval.py` | `88f527a2b4fc6f61b95f056162a6cd8457891daf63b7eb2d1ad0d4d6bdf3acc4` | Verified Restored |
| **Migration Tests** | `backend/tests/test_author_resolution_migration.py` | `d8624bcaad7143e80344b7d544db26453eecb739be5617f90ce61f32470dc475` | Verified Restored |
| **Foundation Tests** | `backend/tests/test_database_foundation.py` | `611593c66f97f7bbffad4a949392e2729a6b57d6050b4d45d81b37373f76903a` | Verified Restored |
| **Dedup Regression Tests**| `backend/tests/test_dedup_regression.py` | `fc2ab4409e5ee9fb1f03f568600d8d4ec093122c676d91f24d1d91bb3a3a41c2` | Verified Restored |
| **Service Tests** | `backend/tests/test_author_resolution_service.py` | `0f507b975e5264b189ff4c2b97fe109c18f1a4e5ee6162319ef36873523f85e1` | Verified Restored |
| **API Integration Tests** | `backend/tests/test_author_resolution_api.py` | `e9f2911b3fc1702f3bcbc3558694ae9efda1dbefec3631f92e76f62f3a693c0d` | Verified Restored |
| **Annotation Tests** | `backend/tests/test_annotation_workflow.py` | `4dd2f088873eab65f10f1c7c96f70a23f0cb034e79915dacaf2e076a61b961ac` | Verified Restored |
| **Benchmark Tests** | `backend/tests/test_evaluation_benchmark.py` | `5fbb1f6d3967885b5fa998a4ff8217bbba9c71994e43cf6dd2c1f93df8291f48` | Verified Restored |

---

## 4. Files Modified and Rationale

| File Modified | Key Changes Made | Rationale |
| :--- | :--- | :--- |
| **`backend/config.py`** | Hardened `DATABASE_URL` resolution logic to resolve relative paths relative to `_base` (`backend/`). | Ensures deterministic database selection regardless of process execution directory (`/`, `backend/`, or CLI). Preserves explicit `DATABASE_URL` environment overrides. |
| **`backend/main.py`** | Integrated `AuthorResolutionService` singleton, added `POST /evidence/search`, `POST /author-resolutions/candidates`, `POST /author-resolutions`, `GET /author-resolutions/{id}`, and extended `GET /search` to accept `resolution_id`. | Exposes the verified Author Resolution V1 workflow on the authoritative FastAPI application routes without breaking existing `/search` contracts. |
| **`backend/services/author_resolution.py`** | Hardened `create_resolution` to support `candidate_ids: Optional[list[str]]`, prevent redundant upstream calls when cached, unwrap persisted candidate payloads safely, and reuse existing `AuthorExternalId` / internal `Author` records. | Prevents unique constraint collisions on re-selection, eliminates duplicate network calls, and records signal-level audit evidence. |
| **`backend/scripts/evaluation_dataset.py`** | Removed un-scoped variable reference in `validate_annotation_rows` and eliminated duplicated check lines. | Fixes runtime `NameError: dataset_frozen_at` in frozen benchmark validation suite. |
| **`backend/scripts/merge_identity_reviews.py`**| Ensured reviewer identity distinction check runs before reviewer confidence validation. | Matches standard error priority when reviewers share identical identifiers. |
| **`frontend/src/components/CandidateSelector.jsx`** | Added multi-signal evidence breakdown, resolved undefined `confClass` variable, added retrieved scholarly context panel with explicit disclaimer, and added "Mark identity unresolved" button. | Restores transparent author disambiguation UI with multi-signal evidence explanation and safe manual controls. |
| **`frontend/src/api.js`** | Added `fetchAuthorCandidatesV1`, `createAuthorResolution`, `getAuthorResolutionDetails`, and extended `searchAuthor` with `resolutionId`. | Allows frontend to seamlessly interact with V1 resolution endpoints while preserving legacy fallback paths. |
| **`frontend/src/App.jsx`** | Integrated V1 candidate workflow: fetches V1 candidates with evidence, persists selections or unresolved actions, and displays informative resolution status banners. | Wires the frontend UI to the authoritative V1 resolver. |

---

## 5. Existing Files Preserved Without Unintended Alterations

All core pipeline, connector, and schema files remain untouched and fully intact:
- `backend/connectors/openalex.py`, `dblp.py`, `arxiv.py`, `crossref.py`, `scholar.py`, `faculty_scraper.py`
- `backend/services/search_service.py` (legacy search fallback fully maintained)
- `backend/services/merge_service.py` & `dedup_service.py` (all deduplication and similarity scoring logic intact)
- `backend/circuit_breaker.py`, `rate_limiter.py`, `log_config.py`
- Root database `academic_search.db` (untouched, independent)

---

## 6. Database & Migration Verification

The database layer was audited and verified:
1. **Alembic Head Verification**:
   ```sql
   SELECT * FROM alembic_version;
   -- Output: 20260907_01
   ```
2. **Schema Verification**:
   The 8 required Author Resolution V1 tables are present with all constraints:
   - `authors`: Primary identity table
   - `author_external_ids`: Source-scoped external identifiers with `(source, external_id)` UNIQUE constraint
   - `author_candidates`: Snapshot table for retrieved candidates with query normalization
   - `author_resolutions`: Decision audit table (recording `auto_selected`, `manual_selected`, or `unresolved`)
   - `author_resolution_evidence`: Signal-level scores, contributions, and raw evidence provenance
   - `author_reviews`: Blinded double-reviewer annotation table
   - `author_review_adjudications`: Conflict adjudication table
   - `author_split_manifest`: Train / development / test partition assignments
3. **No Migration Reapplied**: Revision `20260907_01` was already fully landed; running `alembic upgrade head` was correctly bypassed.

---

## 7. ChromaDB Semantic Retrieval Verification

Verification of the local vector store confirmed complete operational readiness:
- **Collection Name**: `scholarly_records_v1`
- **Persistence Path**: `./backend/vector_index`
- **Document Count**: 449 records
- **Embedding Model**: `all-MiniLM-L6-v2` (`hnsw:space: cosine`, `index_version: scholarly-record-v1`)
- **Metadata Integrity**: Verified 100% valid JSON and key attributes (`publication_id`, `canonical_id`, `title`, `doi`)
- **SQLite Correspondence**: Exact 1-to-1 correspondence (`chroma_pub_ids == sqlite_pub_ids: True` for all 449 publications)
- **Search Verification**: Query `"deep learning neural networks"` returned top cosine matches (scores 0.5399, 0.5333) with full citation references.
- **Missing Query Behavior**: Obscure / non-matching queries gracefully return safe fallbacks without throwing exceptions.
- **Index Rebuild Decision**: Preserved in place; zero index rebuild operations performed.

---

## 8. Actual Test Results

The full backend test suite was executed using Pytest:

```bash
./backend/venv/bin/pytest backend/tests/ -v
```

### Complete Test Results Summary:

| Test File | Test Suite Focus | Tests Run | Passed | Failed | Skips |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `test_annotation_workflow.py` | Double-blind annotation, merging, and reviewer adjudication | 4 | 4 | 0 | 0 |
| `test_author_candidates.py` | Candidate generation, provenance, normalization, timeout & error safety | 9 | 9 | 0 | 0 |
| `test_author_evidence_scoring.py` | Evidence signal extraction, publication overlap, conservative decision policy | 4 | 4 | 0 | 0 |
| `test_author_resolution_api.py` | End-to-end FastAPI resolution workflow, evidence persistence, blocked search | 1 | 1 | 0 | 0 |
| `test_author_resolution_migration.py` | Alembic V1 DDL migration availability and schema validation | 1 | 1 | 0 | 0 |
| `test_author_resolution_service.py` | Manual selection persistence, duplicate external ID reuse, empty candidate caching | 2 | 2 | 0 | 0 |
| `test_database_foundation.py` | Core model creation, relationships, and provenance persistence | 2 | 2 | 0 | 0 |
| `test_dedup_regression.py` | Deduplication funnel and exact DOI merge preservation | 1 | 1 | 0 | 0 |
| `test_evaluation_benchmark.py` | Dataset manifest validation, split freeze checks, read-only replay | 15 | 15 | 0 | 0 |
| `test_scholarly_retrieval.py` | ChromaDB retrieval, citation verification, fallback behavior, timeout handling | 12 | 12 | 0 | 0 |
| **TOTAL** | **Full System Test Battery** | **51** | **51** | **0** | **0** |

**Pass Rate:** **100% (51 passed, 0 failed, 4 minor deprecation/autoflush warnings)**.

---

## 9. End-to-End Live Workflow Verification

Live integration checks were executed against the active backend server (`http://localhost:8000`):

### 1. Geoffrey Hinton Search Workflow
- **Candidate Retrieval**: `POST /author-resolutions/candidates` for `"Geoffrey Hinton"` returned 5 candidate profiles (University of Toronto, Microsoft, etc.) along with retrieved scholarly evidence hits.
- **Selection Persistence**: `POST /author-resolutions` recorded candidate `2fbd86c5` (University of Toronto) as `manual_selected`, persisted `author_id: 31c585a2`, and linked 25 evidence signal rows in `author_resolution_evidence`.
- **Publication Retrieval**: Subsequent `GET /search?name=Geoffrey+Hinton&resolution_id=aeaa390e...` returned **53 reconciled publications** tagged with `identity_context: {"status": "manual_selected"}`.

### 2. Common-Name Ambiguity Workflow ("Rajesh Kumar")
- **Candidate Retrieval**: `POST /author-resolutions/candidates` for `"Rajesh Kumar"` returned 10 distinct institutional profiles (Harvard, NIILM, Northwestern, etc.).
- **Conservative Disambiguation**: Because available signals did not satisfy auto-resolution separation, the system mandated manual review.
- **Unresolved Action**: `POST /author-resolutions` with `mark_unresolved: true` persisted status `unresolved` (`author_id: None`).
- **Blocked Search Enforcement**: Calling `GET /search?name=Rajesh+Kumar&resolution_id=67ae274f...` returned HTTP 200 with `papers: []` and message: `"Resolution is marked unresolved; no multi-source search was started."`

### 3. Frontend Production Build
```bash
npm run build
# vite build -> 39 modules transformed -> built in 540ms (0 errors, 0 warnings)
```

---

## 10. Remaining Issues and Limitations

1. **Dual SQLite Databases**: `academic_search.db` (root, 25.5 MB) and `backend/academic_search.db` (backend, 46.0 MB) remain separate. No reconciliation or merging was performed in this phase.
2. **Playwright Chromium Binary**: The optional Scholar scraper browser daemon logs a missing local binary (`chrome-headless-shell`); other academic connectors (OpenAlex, DBLP, Crossref, arXiv) operate at 100%.
3. **External LLM Provider**: The Gemini explanation provider is unconfigured by default, causing retrieval explanations to safely fall back to the deterministic citation validator.

---

## 11. Stop Condition

Phase 2 objectives are **completely achieved**:
- Author Resolution V1 subsystem fully restored and integrated.
- Database path hardened and verified.
- All 51 unit, integration, and regression tests passing at 100%.
- Both SQLite databases independently backed up and verified.
- No database reconciliation, destructive cleanup, or threshold modification occurred.

**Status:** Completed. Awaiting user authorization for Phase 3.
