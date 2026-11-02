# HAMMER — Stage 1: Current Architecture & Repository Structure Audit

**Document ID:** 01_CURRENT_ARCHITECTURE_AUDIT.md  
**Audit Date:** 2026-11-02  
**Role:** Senior Software Architect & Repository Restructuring Specialist  
**System:** HAMMER (Hybrid Academic Metadata Aggregator and Evidence-Guided Author Entity Resolution System)

---

## 1. Executive Summary & Purpose

Before undertaking any structural refactoring, this audit establishes a complete, read-only baseline of the physical layout, file responsibilities, component dependencies, runtime entry points, and structural deficits across the HAMMER repository. 

Currently, the codebase reflects an organic progression across multiple development sprints (Phases 1–4 and Days 1–7). While the business logic is functionally mature, robust, and supported by 78 passing tests, the file organization is fragmented:
- Critical domain logic is split arbitrarily between root-level modules (`backend/cache.py`, `backend/circuit_breaker.py`, `backend/database.py`, `backend/main.py`), generic subdirectories (`backend/services/`, `backend/pipeline/`), and root-level scripts.
- Author resolution logic is dispersed across five separate service files (`author_candidates.py`, `author_evidence.py`, `author_resolution.py`, `author_scoring.py`, `scholarly_retrieval.py`) without a unifying domain boundary.
- Dense semantic vector search and LLM citation synthesis are bundled together inside a single 500-line service file (`scholarly_retrieval.py`).
- Deduplication and normalization are tucked inside a generic `pipeline/` directory that obscures the algorithmic boundary between legacy V1 and production V2 safeguards.
- The frontend houses all React components in a single flat directory (`frontend/src/components/`) rather than grouping by feature domain.

---

## 2. Inventory of Current Codebase Assets

### 2.1 Backend Core Modules (`backend/`)
| Current File Path | Lines | Architectural Responsibility | Current Subsystem Owner | Deficit / Misplacement |
|---|:---:|---|---|---|
| `backend/main.py` | 511 | FastAPI app setup, CORS, lifespan, routes for search, candidates, author resolutions, metrics, circuit breakers, and Chroma status. | Web API / Presentation | Overloaded with routing, service calls, and lifecycle management in one file. |
| `backend/config.py` | 139 | Environment loading (`.env`, `.env.dev`), thresholds, weights, and database paths. | Core Infrastructure | Good centralization, but mixes author resolution weights with scraper timing and timeouts. |
| `backend/database.py` | 364 | SQLAlchemy models (`Publication`, `Author`, `AuthorCandidate`, `AuthorResolution`, etc.), engine initialization, and session generator. | Persistence Layer | Combines data models across publication management, deduplication, and author resolution in a single monolithic file. |
| `backend/circuit_breaker.py` | 74 | In-memory + SQLite circuit breaker tracking connector failure states. | Ingestion Infrastructure | Placed at backend root instead of ingestion infrastructure. |
| `backend/cache.py` | 44 | General query caching table helper. | Infrastructure | Placed at backend root. |
| `backend/rate_limiter.py` | 12 | SlowAPI limiter instance. | API Infrastructure | Placed at backend root. |
| `backend/log_config.py` | 68 | Structured logging configuration and source fetch loggers. | Core Infrastructure | Placed at backend root. |

### 2.2 Ingestion & Connectors (`backend/connectors/`)
| Current File Path | Architectural Responsibility | Dependencies |
|---|---|---|
| `connectors/base.py` | Abstract `BaseConnector` class with timeout and error handling. | `log_config.py`, `config.py` |
| `connectors/openalex.py` | OpenAlex HTTP connector for works and author profiles. | `BaseConnector`, `config.py` |
| `connectors/crossref.py` | Crossref REST API connector. | `BaseConnector`, `config.py` |
| `connectors/dblp.py` | DBLP computer science bibliographic API connector. | `BaseConnector`, `config.py` |
| `connectors/arxiv.py` | arXiv OAI/API connector for preprints. | `BaseConnector`, `config.py` |
| `connectors/scholar.py` | Headless Playwright scraper adapter for Google Scholar. | Scraper subpackage |
| `connectors/faculty_scraper.py`| Web scraper adapter for university faculty directory pages. | `utils/security.py` |
| `connectors/scrapers/scholar/*`| Browser management, HTML parsing, profile scraping logic. | Playwright, `database.py` |

### 2.3 Normalization & Deduplication (`backend/pipeline/`)
| Current File Path | Architectural Responsibility | Dependencies |
|---|---|---|
| `pipeline/normalize.py` | Text sanitization, Unicode NFC, punctuation stripping, and DOI normalization. | Standard library |
| `pipeline/deduplicate.py` | Publication deduplication: legacy V1 algorithm (`deduplicate_v1`) and V2 engine (`deduplicate`) with 5 guards. | `normalize.py`, `config.py` |

### 2.4 Author Resolution Services (`backend/services/author_*.py`)
| Current File Path | Architectural Responsibility | Target Architectural Subsystem |
|---|---|---|
| `services/author_candidates.py` | OpenAlex candidate harvesting, compound surname queries, and name cleaning. | `author_resolution/candidate_generation` |
| `services/author_evidence.py` | Feature extraction: name similarity, affiliation Jaccard, pub overlap, coauthor network, temporal compatibility. | `author_resolution/evidence` |
| `services/author_scoring.py` | Weighted scoring ($S(c, q)$) and version metadata. | `author_resolution/scoring` |
| `services/author_resolution.py` | Non-linear decision gates (score $\ge 0.75$, margin $\ge 0.15$, dominance $\ge 1.35$), persistence orchestration. | `author_resolution/decision_engine` |
| `schemas/author_resolution.py` | Pydantic DTOs for resolution requests, candidate payloads, and evidence breakdown. | `author_resolution/schemas` |

### 2.5 Semantic Retrieval & Explanation (`backend/services/scholarly_retrieval.py`)
| Current File Path | Lines | Architectural Responsibility | Issue / Deficit |
|---|:---:|---|---|
| `services/scholarly_retrieval.py` | 510 | Dense vector indexing (`all-MiniLM-L6-v2`), ChromaDB collection querying, prompt generation for Gemini 2.5 Flash, JSON schema response parsing, and citation ID containment validation. | Conflates **Vector Retrieval** (ChromaDB search) with **Generative Synthesis & Citation Defense** (Gemini LLM). These should be decoupled into a dedicated `rag/` or `retrieval/` module and an `explanation/` module. |

### 2.6 Search Orchestration (`backend/services/search_service.py`)
| Current File Path | Lines | Architectural Responsibility |
|---|:---:|---|
| `services/search_service.py` | 275 | Orchestrates multi-source federated fetching, pipeline normalization, deduplication, SQLite canonical persistence, and candidate retrieval routing. |

---

## 3. Frontend Architecture (`frontend/src/`)

### 3.1 Current Component Structure
```text
frontend/src/
├── App.jsx                     # Monolithic page layout handling search, state, and modals
├── api.js                      # Flat API client combining search, candidates, resolutions, metrics
├── index.css                   # Global styles
├── main.jsx                    # React 18 DOM mount
└── components/                 # Flat directory of components across different features
    ├── CandidateSelector.jsx   # Feature: Author Resolution Disambiguation Modal
    ├── MergeDetails.jsx        # Feature: Publication Deduplication Inspection
    ├── PaperCard.jsx           # Feature: Publication Search Results
    ├── SearchBar.jsx           # Feature: Search Query Input
    ├── SourceBadge.jsx         # Feature: Ingestion Source Provenance Tag
    ├── SourceStatusPanel.jsx   # Feature: Ingestion / Circuit Breaker Monitoring
    └── StatsBar.jsx            # Feature: Search & Aggregate Analytics
```

### 3.2 Frontend Deficits
- **Lack of Feature Boundaries:** Author resolution components (`CandidateSelector.jsx`) sit alongside generic search inputs (`SearchBar.jsx`) and circuit breaker displays (`SourceStatusPanel.jsx`).
- **Monolithic API Client:** `api.js` combines unrelated HTTP calls for author resolution with publication retrieval and system health checks.
- **State Coupling in App.jsx:** Modal state, resolution feedback, candidate selection, search filters, and active tab states are all crammed into a single React component (420+ lines).

---

## 4. Current Test Suite Mapping (`backend/tests/`)

The backend test suite consists of 13 test files containing **78 collected and passing tests**:
1. `test_annotation_workflow.py` (4 tests) — Evaluation review merging scripts.
2. `test_api_defects_regression.py` (3 tests) — FastAPI defect regressions and timeout handling.
3. `test_author_candidates.py` (9 tests) — OpenAlex candidate harvesting and normalization.
4. `test_author_evaluator_regression.py` (4 tests) — Author evaluator decision regressions.
5. `test_author_evidence_scoring.py` (4 tests) — Feature signal extraction and scoring weights.
6. `test_author_resolution_api.py` (1 test) — FastAPI author resolution endpoints.
7. `test_author_resolution_migration.py` (1 test) — Alembic migration schema verification.
8. `test_author_resolution_service.py` (2 tests) — Resolution persistence and manual review logging.
9. `test_candidate_normalization.py` (15 tests) — Unicode NFC and compound surname normalization.
10. `test_database_foundation.py` (2 tests) — SQLAlchemy model relationships and SQLite persistence.
11. `test_dedup_regression.py` (5 tests) — Deduplication V2 guards (DOI, edition, year, prefix, floor).
12. `test_evaluation_benchmark.py` (15 tests) — Benchmark manifest integrity and schema validation.
13. `test_scholarly_retrieval.py` (13 tests) — ChromaDB indexing, semantic search, and Gemini citation validation.

---

## 5. Critical Runtime Paths & Invariants (Must Be Preserved)

1. **Active Database Path:** In `backend/config.py`, `DATABASE_URL` resolves by default to `backend/academic_search.db`. Reorganizing must not alter this relative path or create a detached SQLite database.
2. **Vector Index Path:** In `backend/services/scholarly_retrieval.py`, `INDEX_PATH` resolves to `backend/vector_index` (containing 449 dense embeddings in `chroma.sqlite3`). This path must remain active and intact.
3. **Alembic Root:** `backend/alembic.ini` and `backend/alembic/` must maintain unbroken references to the application models.
4. **FastAPI Root Application:** `backend/main.py` is the application entry point referenced by uvicorn runners (`uvicorn main:app`).
