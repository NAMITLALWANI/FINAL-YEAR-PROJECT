# HAMMER — Stage 3: Phased Migration & Verification Plan

**Document ID:** 03_MIGRATION_PLAN.md  
**Audit Date:** 2026-11-02  
**Role:** Senior Software Architect  
**Execution Strategy:** Step-by-Step Modular Extraction with Continuous Test Verification.

---

## 1. Migration Phases Overview

| Phase | Target Module | Scope of File Operations | Verification Checkpoint |
|---|---|---|---|
| **Phase 1** | **Author Resolution** (`author_resolution/`) | Group `author_candidates.py`, `author_evidence.py`, `author_scoring.py`, `author_resolution.py`, and `schemas/author_resolution.py` into a unified `backend/author_resolution/` package with backward-compatible shims in `backend/services/`. | Run author resolution test suite (`pytest -k author`). |
| **Phase 2** | **Deduplication** (`deduplication/`) | Restructure `backend/pipeline/` into a dedicated `backend/deduplication/` package, separating normalization, legacy V1, and V2 engine, while retaining `backend/pipeline/` shims. | Run deduplication regression test suite (`pytest tests/test_dedup_regression.py`). |
| **Phase 3** | **Ingestion & Connectors** (`ingestion/`) | Transition `backend/connectors/` to `backend/ingestion/`, cleanly isolating source adapters and scrapers, with shims in `backend/connectors/`. | Run connector regression tests (`pytest tests/test_api_defects_regression.py`). |
| **Phase 4** | **RAG & Explanation** (`rag/` & `explanation/`) | Decouple `services/scholarly_retrieval.py` into `backend/rag/` (vector store and dense search) and `backend/explanation/` (Gemini API and citation containment validator). | Run retrieval test suite (`pytest tests/test_scholarly_retrieval.py`). |
| **Phase 5** | **Frontend Modularization** (`frontend/src/features/`) | Restructure `frontend/src/components/` into `frontend/src/features/{search,author_resolution,deduplication,monitoring}` and update `App.jsx` imports. | Execute `npm run build` in `frontend/`. |
| **Phase 6** | **Full Verification & Integrity Audit** | Execute all 78 backend tests, run frontend build, verify SQLite integrity, and check ChromaDB collections. | All 78 tests passing, 0 database corruption. |

---

## 2. Risk Mitigation & Rollback Strategy

1. **Facade & Forwarding Modules:** For every moved file, the original path will retain a 2-line re-export facade (e.g., in `backend/pipeline/deduplicate.py`: `from deduplication.engine import *`). This eliminates any chance of breaking third-party scripts, evaluation harnesses, or legacy tests.
2. **Database & Index Immutability:** No database file or vector index file will be moved, renamed, or modified during this refactoring.
3. **Continuous Execution:** After each phase, pytest will be run immediately to verify zero import regressions.
