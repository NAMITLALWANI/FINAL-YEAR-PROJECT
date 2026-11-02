# HAMMER — Architecture Overview

## 1. System Purpose

HAMMER (Hybrid Academic Metadata & Entity Resolution) is a scholarly publication discovery system that aggregates records from multiple heterogeneous APIs, normalises and deduplicates them into canonical records, resolves ambiguous author identities using weighted multi-signal evidence, and explains retrieved evidence using a live Gemini LLM with zero-trust citation validation.

---

## 2. High-Level Component Map

```
┌─────────────────────────────────────────────────────────────────┐
│                         React Frontend                          │
│  SearchBar · PaperCard · CandidateSelector · SourceStatusPanel  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP REST (Vite → port 5173)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Application  (port 8000)               │
│  main.py  ·  rate_limiter  ·  circuit_breaker  ·  log_config   │
├─────────────┬──────────────┬──────────────────┬────────────────┤
│  /search    │  /evidence/  │  /author-        │  /metrics      │
│  GET        │  search POST │  resolutions     │  /similarity   │
│             │              │  POST            │  -log          │
└──────┬──────┴──────┬───────┴──────┬───────────┴────────────────┘
       │             │              │
       ▼             ▼              ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────────────────────┐
│ search_     │ │ scholarly_   │ │  author_resolution.py        │
│ service.py  │ │ retrieval.py │ │  author_candidates.py        │
│             │ │              │ │  author_evidence.py          │
│ Orchestrates│ │ ChromaDB     │ │  author_scoring.py           │
│ connectors  │ │ dense search │ │                              │
│ + pipeline  │ │ + Gemini LLM │ │  OpenAlexCandidateService    │
└──────┬──────┘ └──────┬───────┘ └──────────────────────────────┘
       │               │
       ▼               ▼
┌──────────────────┐  ┌────────────────────────┐
│   Connectors     │  │  ChromaDB              │
│  openalex.py     │  │  vector_index/         │
│  dblp.py         │  │  449 embeddings        │
│  arxiv.py        │  │  all-MiniLM-L6-v2      │
│  crossref.py     │  └────────────────────────┘
│  scholar.py      │
│  faculty_scraper │
└──────┬───────────┘
       │
       ▼
┌────────────────────────────────────┐
│  Pipeline                          │
│  normalize.py  →  deduplicate.py  │
│  CanonicalRecord  →  MergedPub    │
└──────────────────┬─────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SQLite  (academic_search.db)                    │
│  16 tables · 454 publications · 2,053 source records            │
│  Author resolution history · Evidence audit trail               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. End-to-End Request Flows

### 3a. Publication Search Flow

```mermaid
sequenceDiagram
    participant U as User (React)
    participant F as FastAPI /search
    participant S as search_service
    participant C as Connectors (×4)
    participant N as normalize.py
    participant D as deduplicate.py
    participant DB as SQLite

    U->>F: GET /search?name=Geoffrey Hinton
    F->>S: run_search(author_name, ...)
    S->>C: asyncio.gather(_fetch_from_connector × N)
    C-->>S: raw_records (list[dict])
    S->>N: normalize(raw) → CanonicalRecord
    S->>D: deduplicate(records) → MergedPublication[]
    S->>DB: upsert Publications + SourceRecords
    DB-->>S: persisted IDs
    S-->>F: {papers, source_statuses, stats}
    F-->>U: JSON response
```

### 3b. Author Resolution Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as FastAPI /author-resolutions
    participant AR as author_resolution.py
    participant OA as OpenAlex Author API
    participant AE as author_evidence.py
    participant SC as author_scoring.py
    participant DB as SQLite

    U->>F: POST /author-resolutions {author_name}
    F->>AR: create_resolution(author_name, ...)
    AR->>OA: search_authors(name) → candidates[]
    OA-->>AR: OpenAlexCandidate objects
    AR->>AE: extract_evidence(candidate, context)
    AE-->>AR: Evidence[] (5 signals)
    AR->>SC: score_evidence(evidence[]) → CandidateScore
    SC-->>AR: weighted score + contributions
    AR->>AR: decide(ranked) → auto_selected|manual_required|unresolved
    AR->>DB: INSERT AuthorResolution + AuthorResolutionEvidence
    DB-->>AR: resolution.id
    AR-->>F: AuthorResolution object
    F-->>U: {status, resolution_id, top_score, candidates}
```

### 3c. Evidence Explanation Flow (Gemini)

```mermaid
sequenceDiagram
    participant U as User
    participant F as FastAPI /evidence/search
    participant SR as scholarly_retrieval.py
    participant CD as ChromaDB
    participant G as Gemini API (gemini-3.5-flash)

    U->>F: POST /evidence/search {query}
    F->>SR: retrieve(query, top_k=5, min_score=0.35)
    SR->>CD: query(embeddings) → distances + documents
    CD-->>SR: hits with cosine scores
    SR->>SR: filter < 0.35, dedup by title/canonical_id
    SR-->>F: RetrievalHit[] (≤5)
    F->>SR: generate_explanation(query, hits)
    SR->>G: POST /v1beta/models/gemini-3.5-flash:generateContent
    Note over G: systemInstruction + untrusted context<br/>responseMimeType: application/json
    G-->>SR: {summary, claims: [{text, document_ids}]}
    SR->>SR: validate each claim.document_ids ∈ hit_by_id
    SR-->>F: {status, provider, summary, valid_claims, token_usage}
    F-->>U: explanation response
```

---

## 4. Technology Stack

| Layer | Technology | Version / Notes |
|-------|------------|-----------------|
| Backend framework | FastAPI | async, with SlowAPI rate limiting |
| ASGI server | Uvicorn | production-ready |
| ORM | SQLAlchemy 2 (async) | `AsyncSession`, mapped columns |
| Database | SQLite + aiosqlite | `academic_search.db`, 16 tables |
| Migration | Alembic | `alembic/versions/20260907_01_…` |
| Vector index | ChromaDB | `vector_index/`, 449 embeddings |
| Embedding model | `all-MiniLM-L6-v2` | SentenceTransformers, local |
| LLM provider | Google Gemini | `gemini-3.5-flash` via REST |
| HTTP client | httpx (async) | Gemini + external API calls |
| Fuzzy matching | rapidfuzz | dedup + evidence scoring |
| Frontend | React + Vite | port 5173 |
| Testing | pytest-asyncio | 55 tests, 100% pass |

---

## 5. Connector Source Priority

Crossref (1) → OpenAlex (2) → DBLP (3) → ArXiv (4) → Scholar (5) → Faculty Page (6)

Lower number = higher authority for field selection during merging.

---

## 6. Feature Flags (config.py)

| Flag | Default | Controls |
|------|---------|----------|
| `ENABLE_OPENALEX` | `true` | OpenAlex ingestion |
| `ENABLE_DBLP` | `true` | DBLP ingestion |
| `ENABLE_CROSSREF` | `true` | Crossref ingestion |
| `ENABLE_ARXIV` | `true` | ArXiv ingestion |
| `ENABLE_SCHOLAR` | `false` | Google Scholar (rate-limited) |
| `ENABLE_FACULTY` | `false` | Faculty page scraper |
| `DEMO_MODE` | `false` | Forces fast deterministic response |
