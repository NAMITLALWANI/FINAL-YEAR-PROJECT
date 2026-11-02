# HAMMER Phase 4: Changelog

**Release:** Phase 4 Controlled Evaluation & Viva Readiness  

---

### Changed
- `backend/services/scholarly_retrieval.py`:
  - `_search()` now filters out results with cosine similarity `< 0.35`.
  - `_search()` now tracks seen titles and DOIs to eliminate duplicate result presentation.
- `backend/services/search_service.py`:
  - `_persist_publications()` now performs secondary lookups on `doi` and `title` to prevent duplicate publication insertion.

### Added
- `backend/tests/test_scholarly_retrieval.py`:
  - Added `test_retrieval_similarity_floor_and_title_dedup`.
- `docs/audit/phase4/*`:
  - 21 comprehensive audit, benchmark, evaluation, and viva readiness documents.
- `docs/audit/phase4/results/*`:
  - Raw JSON evaluation artifacts for 100 author queries, 50 dedup pairs, 20 retrieval queries, 9 citation safety cases, and 6 connectors.
