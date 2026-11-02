# System Architecture

The Hybrid Academic Metadata Aggregator is designed for high-precision author-centric search by fanning out queries to multiple bibliographic sources and merging them using a multi-stage deduplication pipeline.

## Component Overview

```mermaid
graph TD
    User((User)) -->|Search Request| Frontend[React SPA]
    Frontend -->|API Call| FastAPI[FastAPI Backend]
    
    subgraph "Backend Services"
        FastAPI --> SearchService[Search Service]
        SearchService --> CandSelector[Candidate Selection Service]
        SearchService --> Aggregator[Aggregation Engine]
    end
    
    subgraph "External Connectors"
        Aggregator --> OpenAlex[OpenAlex Connector]
        Aggregator --> DBLP[DBLP Connector]
        Aggregator --> ArXiv[ArXiv Connector]
        Aggregator --> Crossref[Crossref Connector]
        Aggregator --> Scholar[Scholar Scraper]
        Aggregator --> Faculty[Faculty Page Scraper]
    end
    
    subgraph "Data Pipeline"
        Aggregator --> Normalizer[Normalization Layer]
        Normalizer --> Dedup[Deduplication Engine]
    end
    
    subgraph "Persistence"
        SearchService --> Cache[(SQLite Cache)]
        Dedup --> DB[(SQLite Database)]
        Scholar --> ScholarCache[(Scholar Cache)]
        DB --> Indexer[Explicit canonical index builder]
        Indexer --> Chroma[(Persistent Chroma index)]
        Chroma --> Evidence[Ranked scholarly evidence]
        Evidence --> Explanation[Optional cited explanation]
        Evidence --> FastAPI
        Explanation --> FastAPI
    end
```

The Chroma collection is a rebuildable retrieval projection. The SQL database remains authoritative for publications, provenance, author candidates, and resolution decisions. `backend/scripts/build_vector_index.py` performs initial and incremental indexing; ordinary requests never re-index the corpus. Semantic hits are displayed as context and currently do not alter V1 scoring or identity decisions.

## Key Technologies
- **Frontend**: React, Vite, Vanilla CSS.
- **Backend**: Python, FastAPI, SQLAlchemy (Async).
- **Database**: SQLite (Development/Demo).
- **Scraping**: Playwright (Headless Chromium).
- **Deduplication**: RapidFuzz (Token-sort ratio).
- **Semantic evidence retrieval**: Chroma persistent collection with local `all-MiniLM-L6-v2` ONNX Sentence Transformers embeddings.
- **Explanation**: optional Gemini `generateContent` provider; generated claim document IDs are validated against retrieved hits, with deterministic fallback.
