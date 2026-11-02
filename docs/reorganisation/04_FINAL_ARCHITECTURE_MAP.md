# HAMMER — Final Architecture Map & Subsystem Navigation Guide

**Document ID:** 04_FINAL_ARCHITECTURE_MAP.md  
**Audit Date:** 2026-11-02  
**Role:** Senior Software Architect  
**Status:** Architecture-Driven Reorganization Certified & Operational

---

## 1. High-Level System Topology

HAMMER is organized around five core functional domains, supported by authoritative transactional persistence and downstream derived vector stores:

```
academic-search/
├── backend/
│   ├── author_resolution/    --> Author identity candidate harvesting, scoring & decision logic
│   ├── deduplication/        --> Normalization & Deduplication Engine V2 with deterministic vetoes
│   ├── ingestion/            --> Multi-source bibliographic connectors (OpenAlex, Crossref, DBLP, arXiv)
│   ├── rag/                  --> Derived dense vector index & bi-encoder retrieval (all-MiniLM-L6-v2)
│   ├── explanation/          --> Zero-trust generative synthesis & citation containment validator
│   ├── search/               --> Federated search orchestration & persistence coordinator
│   ├── database/             --> Authoritative SQLite schemas, SQLAlchemy ORM & session management
│   ├── app/                  --> Core config, structured logging, and circuit breakers
│   ├── tests/                # 78 passing automated unit, regression & benchmark tests
│   ├── scripts/              # Evaluation manifests, benchmarking & replay runners
│   ├── vector_index/         # Derived ChromaDB store (449 vectors, 384-dim)
│   └── academic_search.db    # Authoritative relational database (396 publications)
│
├── frontend/
│   └── src/
│       ├── features/         --> Domain-oriented UI features
│       │   ├── search/       --> SearchBar, PaperCard, StatsBar
│       │   ├── author_resolution/ --> CandidateSelector disambiguation modal
│       │   ├── deduplication/--> MergeDetails & duplicate group inspector
│       │   └── monitoring/   --> SourceStatusPanel & SourceBadge
│       ├── services/         --> Unified API communication layer
│       └── app/              --> Root application container
│
└── docs/                     --> Architecture, research, evaluation & reorganisation specifications
```

---

## 2. Subsystem Navigation Matrix

| Subsystem | Main Directory | Main Entry Point | Core Implementation | Key Test File | Architectural Documentation |
|---|---|---|---|---|---|
| **Author Resolution** | `backend/author_resolution/` | `resolver.py` (`AuthorResolutionService`) | `candidates.py`, `evidence.py`, `scoring.py`, `resolver.py` | `tests/test_author_evidence_scoring.py`, `tests/test_author_candidates.py` | [`docs/finalisation/05_AUTHOR_RESOLUTION.md`](file:///Users/nileshlalwani/Desktop/FINAL%20YEAR%20PROJECT/academic-search/docs/finalisation/05_AUTHOR_RESOLUTION.md) |
| **Publication Deduplication** | `backend/deduplication/` | `engine.py` (`deduplicate`) | `normalize.py`, `engine.py` | `tests/test_dedup_regression.py` | [`docs/finalisation/04_INGESTION_AND_DEDUPLICATION.md`](file:///Users/nileshlalwani/Desktop/FINAL%20YEAR%20PROJECT/academic-search/docs/finalisation/04_INGESTION_AND_DEDUPLICATION.md) |
| **Multi-Source Ingestion** | `backend/ingestion/` | `base.py` (`BaseConnector`) | `openalex.py`, `crossref.py`, `dblp.py`, `arxiv.py`, `scholar.py` | `tests/test_api_defects_regression.py` | [`docs/finalisation/04_INGESTION_AND_DEDUPLICATION.md`](file:///Users/nileshlalwani/Desktop/FINAL%20YEAR%20PROJECT/academic-search/docs/finalisation/04_INGESTION_AND_DEDUPLICATION.md) |
| **Dense Vector Retrieval (RAG)**| `backend/rag/` | `retrieval.py` (`retrieve`, `build_index`)| `retrieval.py`, ChromaDB PersistentClient | `tests/test_scholarly_retrieval.py` | [`docs/finalisation/06_SEMANTIC_RETRIEVAL_AND_LLM.md`](file:///Users/nileshlalwani/Desktop/FINAL%20YEAR%20PROJECT/academic-search/docs/finalisation/06_SEMANTIC_RETRIEVAL_AND_LLM.md) |
| **Generative Explanation** | `backend/explanation/` | `synthesis.py` (`generate_explanation`) | `synthesis.py`, Citation Validator | `tests/test_scholarly_retrieval.py` | [`docs/finalisation/06_SEMANTIC_RETRIEVAL_AND_LLM.md`](file:///Users/nileshlalwani/Desktop/FINAL%20YEAR%20PROJECT/academic-search/docs/finalisation/06_SEMANTIC_RETRIEVAL_AND_LLM.md) |
| **Federated Search** | `backend/search/` | `search_service.py` (`search`) | `services/search_service.py` | `tests/test_api_defects_regression.py` | [`docs/finalisation/03_EXECUTION_WALKTHROUGH.md`](file:///Users/nileshlalwani/Desktop/FINAL%20YEAR%20PROJECT/academic-search/docs/finalisation/03_EXECUTION_WALKTHROUGH.md) |
| **Persistence (Relational)** | `backend/database.py` | `database.py` (`get_db`, `Base`) | SQLite schema, SQLAlchemy ORM | `tests/test_database_foundation.py` | [`docs/finalisation/07_DATA_MODELS.md`](file:///Users/nileshlalwani/Desktop/FINAL%20YEAR%20PROJECT/academic-search/docs/finalisation/07_DATA_MODELS.md) |
| **Frontend UI Features** | `frontend/src/features/` | `frontend/src/App.jsx` | `search/`, `author_resolution/`, `deduplication/`, `monitoring/` | `npm run build` | [`docs/finalisation/01_ARCHITECTURE_OVERVIEW.md`](file:///Users/nileshlalwani/Desktop/FINAL%20YEAR%20PROJECT/academic-search/docs/finalisation/01_ARCHITECTURE_OVERVIEW.md) |

---

## 3. Dataflow Between Subsystems

1. **Ingestion & Invariant Storage:**
   User Query $\to$ `search/` $\to$ `ingestion/` (parallel source fetch) $\to$ `source_records` table $\to$ `deduplication/` (normalization & V2 veto matching) $\to$ `publications` & `duplicate_groups` tables in SQLite.
2. **Author Entity Resolution Pipeline:**
   Publication or Author Query $\to$ `author_resolution/candidates.py` (Unicode NFC & OpenAlex query) $\to$ `evidence.py` (5 extracted signals) $\to$ `scoring.py` ($S(c, q)$) $\to$ `resolver.py` (Decision gates: $S_1 \ge 0.75$, $\Delta S \ge 0.15$, $R_{\text{dom}} \ge 1.35$) $\to$ `auto_selected` or `manual_selection_required` in `author_resolutions` table.
3. **Derived Semantic Retrieval & Synthesis:**
   `publications` $\to$ `rag/retrieval.py` (ChromaDB background embedding) $\to$ Semantic Search (cosine floor $\tau = 0.35$) $\to$ Top-8 hits $\to$ `explanation/synthesis.py` (Gemini 2.5 Flash prompt) $\to$ Citation ID Containment Validator $\to$ Verified UI synthesis summary.
