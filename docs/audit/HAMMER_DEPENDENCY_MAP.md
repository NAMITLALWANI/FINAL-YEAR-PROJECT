# HAMMER — System Dependency Map & Component Architecture
**Generated:** 2026-11-01  
**Scope:** End-to-end component traceability, API endpoints, internal service linkages, and data contracts.

---

## 1. System Architecture Topology

```mermaid
graph TD
    User((User / Browser)) -->|HTTP 5173| Frontend[React + Vite Frontend]
    Frontend -->|HTTP / API Proxy| FastAPI[FastAPI Backend Engine :8000]

    subgraph "API Ingestion & Orchestration Layer"
        FastAPI --> SearchService[search_service.py / Author Orchestrator]
        FastAPI --> MetricsEndpoint[/metrics, /health, /similarity-log]
    end

    subgraph "Identity Resolution Subsystem"
        SearchService --> CandService[author_candidates.py / OpenAlex Candidates]
        CandService --> EvidenceExtractor[author_evidence.py / Signal Extraction]
        EvidenceExtractor --> EvidenceScorer[author_scoring.py / Dynamic Renormalization]
        EvidenceScorer --> ResolverEngine[author_resolution.py / Decision Policy]
    end

    subgraph "Bibliographic Ingestion Connectors"
        SearchService --> OpenAlex[OpenAlex Connector]
        SearchService --> DBLP[DBLP Connector]
        SearchService --> ArXiv[arXiv Connector]
        SearchService --> Crossref[Crossref Connector]
        SearchService --> Scholar[Scholar Playwright Scraper]
        SearchService --> Faculty[Faculty Scraper]
    end

    subgraph "Data Processing Pipeline"
        OpenAlex & DBLP & ArXiv & Crossref & Scholar & Faculty --> Normalizer[normalize.py / CanonicalRecord]
        Normalizer --> Deduplicator[deduplicate.py / RapidFuzz + Union-Find]
    end

    subgraph "Authoritative Persistence (SQLite)"
        Deduplicator --> PubTable[(publications)]
        Deduplicator --> SrcTable[(source_records)]
        Deduplicator --> SimTable[(similarity_logs)]
        Deduplicator --> GrpTable[(duplicate_groups)]
        ResolverEngine --> AuthTable[(authors & author_resolutions)]
    end

    subgraph "Derived Semantic Retrieval (ChromaDB)"
        PubTable -.->|scripts/build_vector_index.py| VectorBuilder[Chroma Rebuild Engine]
        VectorBuilder -.-> ChromaDB[(ChromaDB: scholarly_publications_v1)]
        FastAPI --> RetrievalService[scholarly_retrieval.py]
        RetrievalService --> ChromaDB
        RetrievalService --> LLM[Optional Gemini Citation Explanation]
        LLM -.->|Contextual Evidence| Frontend
    end
```

---

## 2. API Route & Contract Map

| Route | Method | Backend Handler | Dependencies | Description |
| :--- | :--- | :--- | :--- | :--- |
| `/health` | GET | `main.py:health` | `circuit_breaker.py`, `database.py` | Health check reporting circuit breaker states and database status |
| `/search/candidates` | GET | `main.py:fetch_candidates` | `services/search_service.py`, `connectors/openalex.py` | Returns candidate authors matching name and optional institution hint |
| `/search` | GET | `main.py:search` | `search_service.py`, all connectors, `pipeline/` | Executes parallel fan-out search, normalization, deduplication, and caching |
| `/publications/{id}` | GET | `main.py:get_publication` | `database.py:Publication` | Fetches canonical merged record by publication ID |
| `/similarity-log/{id}` | GET | `main.py:get_similarity_log` | `database.py:SimilarityLog`, `DuplicateGroup` | Returns pairwise similarity scores and merge audit trail |
| `/metrics` | GET | `main.py:metrics` | `database.py:Publication`, `SourceRecord` | System telemetry: total publications, raw records, merge counts, source distribution |
| `/debug/raw-response` | GET | `main.py:debug_raw_response` | Individual connectors | Debug route returning un-normalized raw source payloads |
| `/evidence/retrieve` *(V1 Extension)* | POST | `scholarly_retrieval.py:retrieve` | `ChromaDB`, `all-MiniLM-L6-v2` | Retrieves semantically similar publications for candidate review context |
| `/author-resolutions` *(V1 Extension)* | POST | `author_resolution.py:create_resolution` | `database.py:AuthorResolution` | Persists explicit author identity resolution decisions |

---

## 3. Database Schema Dependency Map

### 3.1 Core System Tables (Active in `database.py`)
- `publications`: Canonical merged publication records.
  - Primary Key: `id` (Integer)
  - Key Columns: `canonical_id` (Unique text), `title`, `authors` (JSON), `year`, `abstract`, `doi`, `venue`, `citations`, `best_source`, `confidence_score`, `source_count`, `source_list`.
- `source_records`: Unmodified ingested records from upstream scholarly APIs.
  - Foreign relationship: Linked to `publications` via `duplicate_groups`.
- `duplicate_groups`: Maps canonical publication `id` to set of `source_record_ids`.
- `similarity_logs`: Pairwise comparisons (`record1_id`, `record2_id`, `title_sim`, `author_sim`, `year_match`, `score`, `decision`).
- `cache_entries`: Serialized search responses keyed by `query_key` with expiration timestamps.
- `scholar_cache`: Cached Google Scholar raw HTML to prevent bot detection.
- `circuit_breaker_state`: State tracking for upstream API failures (`source`, `failure_count`, `disabled_until`).

### 3.2 Author Resolution V1 Relational Tables (Defined in Alembic `20260907_01`)
- `authors`: Canonical researcher identities (`id`, `display_name`, `normalized_name`, `resolution_state`).
- `author_external_ids`: Cross-system identifiers (`author_id`, `source`, `external_id`, `url`).
- `author_aliases`: Known name variations (`author_id`, `name`, `clean_name`).
- `author_affiliations`: Institutional history (`author_id`, `institution_name`, `country`, `start_year`, `end_year`).
- `author_candidates`: Raw snapshot of candidate profiles returned during searches.
- `author_resolutions`: Audit record of resolution decisions (`decision`, `selected_author_id`, `confidence_score`).
- `author_resolution_evidence`: Audit trail of individual evidence signal scores.
- `publication_authorships`: Links `publications.id` to `authors.id`.

---

## 4. External Dependencies & Integration Contracts

| Dependency | Category | Purpose | Contract / Protocol | Fallback / Failure Mode |
| :--- | :--- | :--- | :--- | :--- |
| **OpenAlex** | External API | Author profiles & publication metadata | HTTPS REST (`api.openalex.org`) with mailto | Circuit breaker trips after 5 failures |
| **DBLP** | External API | Computer Science bibliographic records | HTTPS REST (`dblp.org/search/publ/api`) | Empty list returned; search proceeds with other sources |
| **arXiv** | External API | Pre-print metadata & abstracts | HTTP Atom XML Feed (`export.arxiv.org`) | Rate limiter delay (3s); circuit breaker on timeout |
| **Crossref** | External API | DOI validation & publisher metadata | HTTPS REST (`api.crossref.org`) with mailto | Empty list returned; DOI matching falls back to title |
| **Google Scholar** | Scraper | Citation counts & profile scraping | Playwright Headless Chromium | SQLite `scholar_cache`; skipped if browser unavailable |
| **Sentence-Transformers** | Local ML Model | Auxiliary publication embeddings | ONNX `all-MiniLM-L6-v2` | Retrieval returns empty; V1 deterministic flow unaffected |
| **ChromaDB** | Vector DB | Derived semantic publication index | Local persistent collection in `vector_index/` | Rebuildable from SQLite `publications` at any time |
| **Gemini / OpenAI API** | Optional LLM | Explaining publication evidence | HTTPS REST Chat Completion | Deterministic textual fallback; citations strictly checked |
