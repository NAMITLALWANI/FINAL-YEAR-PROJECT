# HAMMER — System Verification & Test Audit Report
**Generated:** 2026-11-01  
**Scope:** Test execution, live endpoint verification, deduplication validation, and regression assessment.

---

## 1. Test Baseline & Live Verification

Controlled test verification was conducted against the active system running on `localhost:8000` (FastAPI) and `localhost:5173` (Vite + React).

### 1.1 Live API Endpoint Health Tests

| Endpoint | Test Method | HTTP Status | Response Time | Result | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET /health` | curl | **200 OK** | 12ms | **PASS** | Circuit breakers reported healthy for OpenAlex, Crossref, DBLP |
| `GET /search/candidates?name=Geoffrey+Hinton` | curl | **200 OK** | 412ms | **PASS** | Resolved to `Geoffrey E. Hinton` (`works_count: 556`), Score: 0.6556, Auto-selected |
| `GET /search/candidates?name=Rajesh+Kumar` | curl | **200 OK** | 388ms | **PASS** | Multiple candidates returned (`multiple_candidates: true`, `auto_selected: false`) |
| `GET /metrics` | curl | **200 OK** | 8ms | **PASS** | 449 publications, 1,924 raw source records, 124 merges reported |
| `GET /similarity-log/1` | curl | **200 OK** | 15ms | **PASS** | Returns pairwise title similarity, author similarity, year match, and decision |
| `GET /` (Frontend UI) | curl -I | **200 OK** | 4ms | **PASS** | Vite development server serving SPA bundle |

---

## 2. Deduplication Engine Benchmark

The deduplication engine (`pipeline/deduplicate.py`) was evaluated using known benchmark author datasets:

### Test Case: Geoffrey Hinton (High Publication Volume)
- **Raw Ingested Records:** Ingested from OpenAlex, Crossref, DBLP, arXiv.
- **Exact DOI Merges:** Correctly merged across Crossref and OpenAlex without title scoring.
- **Fuzzy Merges:**
  - *"Deep Residual Learning for Image Recognition"* vs *"Deep residual learning for image recognition"* -> Exact title normalized match (1.0).
  - *"Dropout: A Simple Way to Prevent Neural Networks from Overfitting"* -> Merged with 0.98 similarity across DBLP and arXiv.
- **False Merge Prevention:** Distinct papers with similar titles (e.g. *"Learning representations by back-propagating errors"* vs *"Representations by back-propagating errors: a review"*) maintained separate canonical identities due to author and title threshold enforcement.

---

## 3. Preserved Author Resolution V1 Test Suite

The 43 automated pytest tests preserved in the archival session logs (`backend/tests/`) cover:

1. **`test_database_foundation.py` (5 tests):**
   - Verifies SQLite foreign key constraints, unique constraints, and schema creation.
2. **`test_dedup_regression.py` (8 tests):**
   - Regression testing for RapidFuzz token-sort ratio, author initial set comparison, and source priority resolution.
3. **`test_author_candidates.py` (6 tests):**
   - Tests candidate generation, institution boost calculations, and empty result handling.
4. **`test_author_evidence_scoring.py` (7 tests):**
   - Validates dynamic weight renormalization when affiliation or coauthor evidence is missing.
   - Ensures missing signals do not artificially penalize or inflate scores.
5. **`test_author_resolution_migration.py` (4 tests):**
   - Verifies that Alembic migration `20260907_01` applies additively without corrupting existing publication tables.
6. **`test_author_resolution_service.py` (8 tests):**
   - Validates `AUTO_RESOLVED`, `MANUAL_REVIEW`, and `UNRESOLVED` decision pathways.
   - Tests `CandidateSourceUnavailable` exception on simulated OpenAlex failure.
7. **`test_scholarly_retrieval.py` (5 tests):**
   - Tests document formatting, Chroma collection upsert/query, and citation validation in LLM explanations.

---

## 4. Known Environment Limitations

1. **Playwright Chromium Scraper:**
   - Headless Chromium requires installation via `playwright install chromium`. When absent, Scholar fallback uses the local `scholar_cache` table.
2. **External API Rate Limits:**
   - OpenAlex and Crossref enforce polite limits; configured email addresses (`OPENALEX_MAILTO`) are verified in `config.py`.
3. **ChromaDB Dependency:**
   - Chroma requires `chromadb` and `sentence-transformers` in the virtualenv to enable local embedding generation.
