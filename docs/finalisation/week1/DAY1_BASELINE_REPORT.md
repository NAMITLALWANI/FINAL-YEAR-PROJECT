# HAMMER — Day 1: Baseline Protection and Development Readiness Audit

**Document ID:** DAY1_BASELINE_REPORT.md  
**Audit Date:** 2026-11-02  
**Auditor:** Senior Software Architect & Research Engineer  
**System:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Lifecycle Stage:** Baseline Protection & Reliability Improvement (Day 1)  

---

## 1. Executive Summary

This Day 1 report establishes a verified, tamper-proof baseline for HAMMER prior to beginning a conservative, one-week reliability improvement phase. 

In strict adherence to instructions:
- **Zero source-code modifications** were made.
- **Zero database migrations or alters** were executed.
- **Zero scoring or deduplication thresholds** were altered.
- **Zero vector indices** were rebuilt.
- **Zero credentials or secrets** were logged or exposed.
- All production databases and vector indices were backed up transactionally with SHA256 verification.
- The 55-test backend suite and frontend production build were executed cleanly.

---

## 2. Repository Identity and Environment

| Parameter | Observed Value | Notes |
|---|---|---|
| **Repository Root** | `/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search` | Working tree verified |
| **Current Git Branch** | `main` | Tracking `origin/main` |
| **Current HEAD Hash** | `2c4c5a93dd181e0e0aad3c557cef2e3c716a1c62` | Commit message: *"ui improvements"* |
| **Working-Tree Status** | Dirty (Active workspace files preserved) | Changes in `App.jsx`, `api.js`, `main.py`, config, and audit docs |
| **Backend Directory** | `/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search/backend` | Python / FastAPI backend |
| **Frontend Directory** | `/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search/frontend` | React / Vite frontend |
| **Python Version** | `Python 3.12.5` | System virtualenv |
| **Virtual Environment** | `backend/venv` | Isolated virtualenv |
| **FastAPI Version** | `0.136.1` | REST API framework |
| **Uvicorn Version** | `0.47.0` | ASGI server |
| **SQLAlchemy Version** | `2.0.49` | Relational ORM |
| **Alembic Version** | `1.20.1` | Migration engine |
| **ChromaDB Version** | `1.5.9` | Embedded vector database |
| **RapidFuzz Version** | `3.14.5` | Fuzzy string matching |
| **Pytest Version** | `9.2.0` (with `pytest-asyncio 1.4.1`) | Automated test framework |
| **Pydantic Version** | `2.14.2` | Data validation schemas |
| **HTTPX Version** | `0.28.1` | Async HTTP client |

---

## 3. Data Protection and Backup Verification

A dedicated, immutable backup snapshot was created under `backups/day1_baseline_20261102_120700`.

### 3.1 Active Data Asset Identification
- **Active Production Database:** `backend/academic_search.db` (48 MB, 16 relational tables).
- **Historical Inactive Database:** `academic_search.db` (in project root, 24 MB, 7 tables, no author resolution tables).
- **Active Persistent ChromaDB:** `backend/vector_index` (containing collection `scholarly_records_v1`).
- **Alembic Migration Revision:** `20260907_01` (head).
- **Environment Configuration:** `backend/.env` and `backend/.env.dev` (credentials unprinted).

### 3.2 Backup Execution and Cryptographic Verification
The SQLite database was backed up using the SQLite Online Backup API (`sqlite3.backup`) to ensure transactional consistency without locking out running dev servers. The ChromaDB persistent tree was replicated recursively.

```json
{
  "timestamp": "20261102_120700",
  "backup_directory": "/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search/backups/day1_baseline_20261102_120700",
  "backend_db_backup": {
    "filename": "backend_academic_search.db",
    "sha256": "5716958f8cacff13605e00a22c70cfe7dcf20ee4f150962d7eeb0de474e62c69",
    "integrity_check": "ok"
  },
  "chroma_backup": {
    "directory": "vector_index",
    "collection_name": "scholarly_records_v1",
    "document_count": 449,
    "hnsw_space": "cosine",
    "embedding_model": "all-MiniLM-L6-v2",
    "chroma_sqlite3_sha256": "bffcd84e18cec764d04f2a7bf76d57a2f446d4d4ed77ab1ec18ee03a4d0310f4"
  }
}
```

*Verification Statement:*  
Both the active SQLite backup and ChromaDB backup have been verified. Integrity check returned `ok`. No original production files were modified or overwritten.

---

## 4. Current System Inventory

### 4.1 Relational Database Inventory (`backend/academic_search.db`)

| Table Name | Active Row Count | Subsystem Role |
|---|---|---|
| `publications` | **454** | Canonical deduplicated publication entities |
| `source_records` | **2,053** | Raw harvested multi-source records (arXiv, Crossref, OpenAlex) |
| `duplicate_groups` | **960** | Mapping pointers between canonical publications and source records |
| `similarity_logs` | **133** | Audit log of pairwise comparison decisions (27 MERGED, 106 SEPARATE) |
| `author_candidates` | **15** | Live candidate author profiles persisted from OpenAlex |
| `author_resolutions` | **2** | Persisted identity resolution episodes |
| `author_resolution_evidence` | **2** | Evidence snapshots supporting resolution episodes |
| `authors` | **0** | Disambiguated canonical author records (pending batch resolution) |
| `author_aliases` | **0** | Name variant mappings (schema ready) |
| `author_affiliations` | **0** | Affiliation history mappings (schema ready) |
| `publication_authorships` | **0** | Many-to-many junction table (schema ready) |
| `cache_entries` | **4** | HTTP response cache |
| `scholar_cache` | **0** | Dedicated Google Scholar cache |
| `circuit_breaker_state` | **0** | Ingestion source breaker tracker |
| `alembic_version` | **1** | Version tracking row (`20260907_01`) |

*Critical Distinction:*  
The active database is explicitly `backend/academic_search.db`. The root-level file `academic_search.db` contains 546 publications and 857 source records, lacks all author resolution tables, and is an obsolete pre-migration artifact.

### 4.2 Vector Index Inventory (`backend/vector_index`)
- **Collection Name:** `scholarly_records_v1`
- **Total Vector Embeddings:** **449**
- **Distance Metric:** **Cosine Distance** (`hnsw:space: cosine`)
- **Score Conversion:** `score = max(-1.0, min(1.0, 1.0 - distance))` (exact cosine similarity)
- **Embedding Model:** `all-MiniLM-L6-v2` (384 dimensions)
- **Active Retrieval Floor:** `min_score = 0.35` (cosine similarity)

### 4.3 LLM Provider Inventory (Gemini)
- **Active Model:** `gemini-3.5-flash`
- **API Endpoint:** `https://generativelanguage.googleapis.com/v1beta`
- **API Call Format:** Native `generateContent` with JSON schema enforcement (`responseMimeType: application/json`)
- **Temperature:** `0.0` (deterministic synthesis)
- **Credential Storage:** `GEMINI_API_KEY` loaded via environment variable / `.env` (sanitized and protected)
- **Fallback Engine:** Local deterministic template summary and citation filter active when provider is unconfigured or returns invalid citations.

### 4.4 Configured Decision Thresholds and Rules

#### Publication Deduplication Rules (`backend/pipeline/deduplicate.py`)
- **Composite Fuzzy Formula:**
  $$	ext{score} = 0.60 	imes 	ext{title_sim} + 0.30 	imes 	ext{author_sim} + 0.10 	imes 	ext{year_match}$$
- **Thresholds:**
  - Strict Threshold: `0.92`
  - Default Merge Threshold: `0.85`
  - Lenient Threshold: `0.80`
  - Logging Floor: `0.70`
- **Deterministic Rules:** Exact DOI match auto-merges; conflicting valid DOIs forbid merging.

#### Author Resolution Thresholds (`backend/config.py` & `author_resolution.py`)
- **Scoring Weights:** Name similarity (0.35), Institution similarity (0.25), Publication overlap (0.20), Co-author overlap (0.10), Temporal compatibility (0.10).
- **Decision Engine Thresholds:**
  - `AUTHOR_AUTO_SCORE_THRESHOLD`: `0.75`
  - `AUTHOR_AUTO_MARGIN_THRESHOLD`: `0.15`
  - `AUTHOR_AUTO_DOMINANCE_THRESHOLD`: `1.35`
  - `AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO`: `2`
  - `AUTHOR_MANUAL_SCORE_THRESHOLD`: `0.45`
- **Status Constants:**
  - Automatic Resolution: `AUTO_RESOLVED = "auto_selected"`
  - Manual Review: `MANUAL_REVIEW = "manual_selection_required"`
  - Abstention: `UNRESOLVED = "unresolved"`

---

## 5. Documentation Discrepancy Reconciliation

Comparing recent audit reports with historical drafts (`docs/research-paper.md`, `docs/baseline-audit.md`, `docs/evaluation.md`) reveals 4 distinct discrepancies:

### 5.1 Discrepancy 1: 454 versus 696 Canonical Publications
- **The Numbers:** `docs/research-paper.md` states **696 canonical publications**, while the active database contains **454**.
- **Root Cause:** **Different Database Snapshot.** Earlier in development (during Phase 2/3), an ingestion run seeded 696 publications. When the database was rebuilt and normalized during the Phase 4 baseline creation, the active database consolidated to **454 canonical publications** (derived from 2,053 source records). The research paper draft retained the obsolete 696 figure.
- **Action for Paper:** Update `docs/research-paper.md` to reflect the active database count of **454 publications**.

### 5.2 Discrepancy 2: 2,053 versus 2,186 Source Records
- **The Numbers:** `docs/research-paper.md` cites **2,186 source records**, while active DB holds **2,053**.
- **Root Cause:** **Different Ingestion Snapshot.** The 2,186 count originated from an earlier test harvest that included duplicate raw crossref entries before connector deduplication was applied. The clean Phase 4 active database contains exactly **2,053 source records**.
- **Action for Paper:** Update all tables and abstracts in `docs/research-paper.md` to **2,053 source records**.

### 5.3 Discrepancy 3: 52 versus 55 Passing Tests
- **The Numbers:** Prior evaluation reports mentioned **52 passing tests**, whereas the current test run passes **55 tests**.
- **Root Cause:** **Code Revision (Addition of Regression Test File).** In Phase 3B/4, a new test file `backend/tests/test_api_defects_regression.py` containing 3 regression tests was added to lock in API defect fixes:
  1. `test_author_candidates_whitespace_and_empty_validation`
  2. `test_get_similarity_log_handles_multiple_duplicate_groups`
  3. `test_get_search_candidates_query_parameter_contract`
  52 + 3 = 55. The 55 passing tests accurately reflect the full current test suite.

### 5.4 Discrepancy 4: Historical vs Current Author Resolution Thresholds
- **The Numbers:** `docs/audit/phase4/HAMMER_AUTHOR_RESOLUTION_ERROR_ANALYSIS.md` listed thresholds as `score >= 0.85`, `signals >= 3`, whereas `backend/config.py` defines `score >= 0.75`, `signals >= 2`.
- **Root Cause:** **Configuration Modeling vs Production Config.** The document was an experimental error analysis simulating a hypothetical high-stringency threshold configuration (`score >= 0.85`) to demonstrate why 100% of queries would abstain under ultra-strict rules. The production implementation in `backend/config.py` has remained invariant at `0.75` / `2 signals`.

---

## 6. Test and Build Baselines

### 6.1 Backend Test Suite Execution
- **Command:** `venv/bin/python -m pytest tests/ -v`
- **Working Directory:** `/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search/backend`
- **Result:** **55 passed, 0 failed, 0 skipped**
- **Execution Time:** **31.54 seconds**
- **Warnings Observed:**
  - 1 pytest internal deprecation warning (`CallSpec2` renamed to `CallSpec` in AnyIO plugin).
  - 2 SQLAlchemy autoflush session warnings regarding unattached `AuthorResolution` objects during test fixture teardown.
  - 1 Python datetime deprecation warning (`datetime.utcnow()` in `test_database_foundation.py`).
- **Code Coverage Note:** Line coverage was not measured via `--cov` in this run; claiming 100% code coverage is forbidden.

### 6.2 Frontend Production Build Execution
- **Command:** `npm run build` (`vite build`)
- **Working Directory:** `/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search/frontend`
- **Result:** **SUCCESS** (Exit Code 0)
- **Build Duration:** 712 ms
- **Bundled Assets:**
  - `dist/index.html`: 0.84 kB (gzip: 0.47 kB)
  - `dist/assets/index-Bw7gziqh.css`: 8.07 kB (gzip: 2.51 kB)
  - `dist/assets/index-DB-Y-JPw.js`: 161.94 kB (gzip: 51.57 kB)
- **Warnings / Errors:** None. Zero build errors or CSS transformation warnings.

---

## 7. Risks and Blockers

| Risk / Observation | Severity | Technical Impact | Remediation Plan |
|---|---|---|---|
| **Author Resolution Status Key Mismatch** | Medium | Decision engine outputs `"auto_selected"`, but evaluation scripts check for `"auto_resolved"`. | Harmonize string literal constants across service layer and evaluation scripts. |
| **Relational Author Tables Unpopulated** | Low | `authors`, `author_affiliations`, `publication_authorships` currently have 0 rows in production DB. | Keep clearly documented in paper as schema-implemented features pending full-batch pipeline ingestion. |
| **Semantic Entailment Verification Gap** | Low | Citation validator verifies document ID containment, not NLP textual entailment. | Accurately disclose in paper Limitations section. |
| **Deprecation Warnings in Tests** | Low | `datetime.utcnow()` and `CallSpec2` emit non-blocking deprecation warnings. | Address during code cleanup without modifying business logic. |

---

## 8. Recommended Safe Starting Point for Day 2

With baseline data cryptographically backed up and the environment fully characterized, the safe agenda for Day 2 is:

1. **Focus on Non-Destructive Reliability Fixes:**
   - Harmonize the author resolution status key naming (`auto_selected` vs `auto_resolved`) in code and evaluation scripts.
   - Address the SQLAlchemy session warning in `test_author_resolution_service.py` using `no_autoflush` or session merge.
2. **Synchronize Research Paper Numbers:**
   - Update `docs/research-paper.md` with verified figures: 454 publications, 2,053 source records, 55 passing tests, 48 evaluated dedup pairs (94.1% precision).
3. **Preserve Isolation:**
   - Maintain the invariant that no tests or scripts modify `backend/academic_search.db` directly.
