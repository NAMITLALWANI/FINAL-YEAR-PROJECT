# HAMMER — Stage 2: Target Architecture & Modular Design

**Document ID:** 02_TARGET_ARCHITECTURE.md  
**Audit Date:** 2026-11-02  
**Role:** Senior Software Architect  
**Design Philosophy:** Domain-Driven Modular Layout with Explicit Architectural Boundaries and Zero Runtime Regressions.

---

## 1. Architectural Design Principles

The reorganized repository enforces five core architectural standards:

1. **Subsystem Navigability (Directory as Architecture):** A new developer or viva examiner can inspect the root directories and immediately identify where ingestion, publication deduplication, author entity resolution, dense vector retrieval, and generative explanation reside.
2. **Cohesive Domain Subpackages:** Related functionality (e.g., candidate harvesting, evidence extraction, candidate scoring, and non-linear decision gates) lives in one cohesive package (`backend/author_resolution/`).
3. **Decoupled RAG & Explanation Subsystems:** The dense vector index (ChromaDB) and bi-encoder embedding generator are structured under `backend/rag/`, while prompt synthesis, JSON schema validation, and citation containment validation are organized under `backend/explanation/`.
4. **Clean API & Infrastructure Boundary:** Database models, caching, circuit breaking, and structured logging belong to explicit infrastructure/core layers rather than cluttering root entry points.
5. **Feature-Sliced Frontend:** Frontend React components and API functions are grouped by user-facing capability (`search/`, `author_resolution/`, `deduplication/`, `monitoring/`) rather than flat, arbitrary component lists.

---

## 2. Proposed Target Repository Layout

```text
academic-search/
├── backend/
│   ├── app/                    # Application Core & API Routing Layer
│   │   ├── api/                # FastAPI Routers & Middleware
│   │   │   ├── routes/         # Modular endpoint routers (search, authors, metrics, rag)
│   │   │   └── dependencies.py # Shared API dependencies (database session, rate limiters)
│   │   ├── core/               # Cross-cutting foundational infrastructure
│   │   │   ├── config.py       # Pydantic / dotenv environment settings & thresholds
│   │   │   ├── logging.py      # Structured logger initialization & formatters
│   │   │   └── circuit.py      # Multi-source circuit breaker & rate limiter
│   │   └── main.py             # FastAPI entry point (main:app)
│   │
│   ├── database/               # Authoritative Relational Persistence (SQLite / SQLAlchemy)
│   │   ├── models.py           # Unified declarative SQLAlchemy models (Publication, Author, etc.)
│   │   ├── session.py          # Asynchronous engine & sessionmaker definitions
│   │   └── cache.py            # SQLite query cache entries
│   │
│   ├── ingestion/              # Multi-Source Bibliographic Ingestion Subsystem
│   │   ├── base.py             # BaseConnector abstraction
│   │   ├── openalex.py         # OpenAlex REST connector
│   │   ├── crossref.py         # Crossref REST connector
│   │   ├── dblp.py             # DBLP XML/JSON connector
│   │   ├── arxiv.py            # arXiv OAI connector
│   │   ├── scholar.py          # Google Scholar headless scraper
│   │   ├── faculty.py          # Faculty directory web scraper
│   │   └── scrapers/           # Subpackage for browser & DOM parsing logic
│   │
│   ├── deduplication/          # Publication Normalization & Deduplication Subsystem
│   │   ├── normalize.py        # Text & DOI normalization routines
│   │   ├── algorithms.py       # Legacy V1 heuristic baseline & similarity formulas
│   │   └── engine.py           # Production Deduplication Engine V2 (5 deterministic veto guards)
│   │
│   ├── author_resolution/      # Evidence-Guided Author Entity Resolution Subsystem
│   │   ├── candidates.py       # Candidate harvesting & OpenAlex query normalization
│   │   ├── evidence.py         # Multi-signal feature extraction (name, inst, pub, coauthor, temporal)
│   │   ├── scoring.py          # Weighted evidence scoring ($S(c, q)$)
│   │   ├── resolver.py         # Non-linear decision gates (0.75, 0.15, 1.35) & resolution orchestrator
│   │   └── schemas.py          # Pydantic DTOs for candidate pools & decision evidence
│   │
│   ├── rag/                    # Derived Dense Vector Retrieval Subsystem
│   │   ├── embeddings.py       # SentenceTransformers bi-encoder wrapper (all-MiniLM-L6-v2)
│   │   ├── vector_store.py     # ChromaDB PersistentClient collection manager
│   │   └── service.py          # Top-k dense similarity search with cosine similarity floors
│   │
│   ├── explanation/            # Generative Synthesis & Citation Defense Subsystem
│   │   ├── provider.py         # Gemini 2.5 Flash API connector & zero-trust prompt builder
│   │   ├── validator.py        # Deterministic Citation ID Containment Validator
│   │   └── fallback.py         # Deterministic metadata synthesis fallback
│   │
│   ├── search/                 # Federated Search Orchestrator Subsystem
│   │   └── service.py          # Multi-source fan-out, deduplication, and persistence coordinator
│   │
│   ├── tests/                  # Centralized Automated Test Suite (78 Tests)
│   ├── scripts/                # Evaluation, benchmarking, and administrative CLI scripts
│   ├── alembic/                # Database schema migrations
│   ├── vector_index/           # Active production ChromaDB collection (449 vectors)
│   ├── academic_search.db      # Active operational SQLite database
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── app/                # Root React setup
│       │   ├── App.jsx         # Main application orchestrator
│       │   └── main.jsx        # DOM entry point
│       │
│       ├── features/           # Domain-Oriented Frontend Features
│       │   ├── search/         # Publication search & display components
│       │   │   ├── SearchBar.jsx
│       │   │   ├── PaperCard.jsx
│       │   │   └── StatsBar.jsx
│       │   ├── author_resolution/ # Disambiguation modal & candidate selection
│       │   │   └── CandidateSelector.jsx
│       │   ├── deduplication/  # Publication merge details & provenance inspection
│       │   │   └── MergeDetails.jsx
│       │   └── monitoring/     # Ingestion & connector status badges
│       │       ├── SourceBadge.jsx
│       │       └── SourceStatusPanel.jsx
│       │
│       ├── services/           # API communication layer
│       │   └── api.js          # Unified typed API client
│       └── index.css           # Global design system
│
└── docs/                       # Architectural & Research Documentation
    ├── architecture/           # System topology & dataflow specifications
    ├── reorganisation/         # Migration plans, audits, and completion reports
    └── research/               # Formal research paper, matrices, and evaluation manifests
```

---

## 3. Backward Compatibility & Non-Breaking Invariants

To guarantee that no runtime scripts, tests, or uvicorn runners break during migration:
1. **Root Facade Imports:** We will maintain backward-compatible import shims where appropriate (e.g., `from database import Publication` will continue to resolve via `backend/database.py` forwarding to `backend/database/models.py`).
2. **Main Application Compatibility:** `backend/main.py` will expose the FastAPI `app` instance, internally importing modular routers from `app/api/`. Running `uvicorn main:app` from `backend/` will work seamlessly.
3. **ChromaDB Path Invariance:** Vector index paths will continue resolving to `backend/vector_index/` by default.
4. **SQLite Path Invariance:** `academic_search.db` will remain in `backend/` as the single authoritative database.
