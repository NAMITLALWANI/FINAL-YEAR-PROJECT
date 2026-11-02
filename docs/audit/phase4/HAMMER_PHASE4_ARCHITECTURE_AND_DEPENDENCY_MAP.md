# HAMMER Phase 4: Subsystem Architecture & Dependency Map

**System:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Layer:** Architecture, Component Dependencies & Data Flow  

---

## 1. High-Level Subsystem Architecture

```mermaid
graph TD
    UI[Frontend: React + Vite Single-Page App] -->|HTTP / JSON REST API| API[Backend: FastAPI main.py]
    
    subgraph Ingestion_Connectors [Multi-Source Connectors]
        OA[OpenAlex API]
        CR[Crossref API]
        AX[arXiv API]
        DB[DBLP API - Cloudflare Restricted]
        GS[Scholar Scraper - Bot Restricted]
        FS[Faculty Scraper - Playwright]
    end
    
    subgraph Normalization_Pipeline [Normalization & Deduplication]
        NORM[normalize.py: CanonicalRecord]
        DEDUP[deduplicate.py: Blocking + Fuzzy + UnionFind]
    end
    
    subgraph Author_Resolution_Subsystem [Author Resolution V1]
        CAND[services/author_candidates.py: OpenAlex Candidate Gen]
        EVID[services/author_evidence.py: Signals Extraction]
        SCORE[services/author_scoring.py: Weighted Scoring]
        DECIDE[services/author_resolution.py: Conservative Decision]
    end
    
    subgraph Semantic_Retrieval_Subsystem [Semantic Retrieval & Gemini]
        CHROMA[(backend/vector_index: ChromaDB Collection)]
        RETRIEVE[services/scholarly_retrieval.py: retrieve & dedup]
        GEMINI[Gemini 1.5 Flash/Pro + Zero-Trust Claim Validator]
        FALLBACK[Deterministic Local Evidence Summarizer]
    end
    
    subgraph Relational_Storage [Authoritative Relational Database]
        DB_SQL[(backend/academic_search.db: SQLite 16 Tables)]
    end

    API --> Ingestion_Connectors
    Ingestion_Connectors --> NORM
    NORM --> DEDUP
    DEDUP --> DB_SQL
    
    API --> CAND
    CAND --> EVID
    EVID --> SCORE
    SCORE --> DECIDE
    DECIDE --> DB_SQL
    
    API --> RETRIEVE
    RETRIEVE --> CHROMA
    RETRIEVE --> GEMINI
    GEMINI -->|On Fail/Unconfigured| FALLBACK
```

---

## 2. Component Dependency Table

| Module | Source Files | Depends On | Dependent Consumers | Role & Responsibility |
|---|---|---|---|---|
| **API Entry** | `backend/main.py` | `database.py`, `config.py`, `services/*` | Frontend (`api.js`) | FastAPI endpoints, request validation, error translation |
| **Relational DB** | `backend/database.py`, `alembic/` | SQLAlchemy, SQLite | All backend services | Authoritative record persistence (16 tables) |
| **Ingestion** | `backend/connectors/*` | `httpx`, `asyncio` | `search_service.py` | Multi-source academic harvest |
| **Deduplication** | `backend/pipeline/deduplicate.py` | `thefuzz`, `normalize.py` | `search_service.py` | Reversible clustering & canonicalization |
| **Author Candidates** | `services/author_candidates.py` | `httpx`, `database.py` | `main.py`, `author_resolution.py` | OpenAlex candidate generation & persistence |
| **Author Scoring** | `services/author_scoring.py` | `evidence.py`, `config.py` | `author_resolution.py` | Multi-signal weighted score calculation |
| **Author Resolver** | `services/author_resolution.py` | `scoring.py`, `config.py` | `main.py`, evaluation scripts | Conservative decision tree (margin, dominance) |
| **Vector Index** | `services/scholarly_retrieval.py` | `chromadb`, `sentence-transformers` | `main.py` | Dense vector similarity search & filtering |
| **LLM Provider** | `services/scholarly_retrieval.py` | `httpx`, Gemini REST API | `main.py` | Explanations with zero-trust claim validation |

---

## 3. Disconnected / Dead Code Analysis

- **`root_academic_search.db`:** Legacy 7-table database from Phase 1. Disconnected from active backend, preserved read-only as archive baseline.
- **`scholar_cache` / `circuit_breaker_state` tables:** Schema exists in SQLite; active connectors use in-memory circuit breaking or fallbacks.
- **DBLP / Scholar Connectors:** Kept disabled or optional by default due to Cloudflare challenges and upstream CAPTCHA blocks.
