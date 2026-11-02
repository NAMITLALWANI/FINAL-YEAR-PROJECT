# HAMMER — Complete Feature Inventory & Verification Matrix
**Generated:** 2026-11-01  
**Scope:** Exhaustive catalog of every discovered, implemented, planned, and archived capability in HAMMER.

---

## 1. Feature Classification Legend
- **IMPLEMENTED AND VERIFIED:** Code exists, is wired into the application, executes, and has been tested with expected outputs.
- **IMPLEMENTED BUT NOT VERIFIED:** Code exists and is wired, but requires external credentials or live network responses to verify.
- **PARTIALLY IMPLEMENTED:** Core logic exists but lacks complete integration or error handling.
- **DISCONNECTED FROM APPLICATION:** Code exists in repository or session archives but is not currently imported or reachable from `main.py` / UI.
- **BROKEN:** Code exists but fails execution or raises unhandled runtime exceptions.
- **DUPLICATED:** Multiple competing implementations exist for the same responsibility.
- **LEGACY / POSSIBLY OBSOLETE:** Outdated prototype or superseded logic.

---

## 2. Feature Inventory Matrix

| Feature Name | Intended Purpose | Entry Point / Route | Backend Service | DB Models | External Dependencies | Status | Verification Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **OpenAlex Search** | Query OpenAlex API for works by author | `GET /search` | `connectors/openalex.py` | `SourceRecord` | OpenAlex REST API | **IMPLEMENTED AND VERIFIED** | Tested live with Geoffrey Hinton; returns works with parsed abstracts |
| **DBLP Search** | Retrieve Computer Science publications | `GET /search` | `connectors/dblp.py` | `SourceRecord` | DBLP API | **IMPLEMENTED AND VERIFIED** | Verified; returns titles, venues, DOIs |
| **arXiv Search** | Ingest preprint metadata & abstracts | `GET /search` | `connectors/arxiv.py` | `SourceRecord` | arXiv Atom API | **IMPLEMENTED AND VERIFIED** | Verified; enforces 3.0s delay |
| **Crossref Search** | Authoritative DOI & publisher citations | `GET /search` | `connectors/crossref.py` | `SourceRecord` | Crossref REST API | **IMPLEMENTED AND VERIFIED** | Verified; resolves DOIs and citations |
| **Google Scholar Scraper** | Scrape citation counts & profiles | `GET /search` | `connectors/scholar.py` | `ScholarCache`, `SourceRecord` | Playwright Chromium | **IMPLEMENTED AND VERIFIED** | Verified with persistent SQLite cache; avoids CAPTCHAs |
| **Faculty Page Scraper** | Scrape university department profile | `GET /search` | `connectors/faculty_scraper.py` | `SourceRecord` | BeautifulSoup | **PARTIALLY IMPLEMENTED** | Implemented for `kjsomaiya`, disabled by default |
| **Circuit Breaker** | Prevent cascading failure on API outages | Automatic wrapper | `circuit_breaker.py` | `CircuitBreakerState` | None | **IMPLEMENTED AND VERIFIED** | Trips after 5 failures for 15 minutes; reported in `/health` |
| **Metadata Normalization** | Coerce raw records into CanonicalRecord | Automatic in pipeline | `pipeline/normalize.py` | None (In-memory) | None | **IMPLEMENTED AND VERIFIED** | Cleans HTML, extracts 4-digit years, generates deterministic IDs |
| **RapidFuzz Deduplication** | Disjoint-set merge of duplicate papers | Automatic in pipeline | `pipeline/deduplicate.py` | `Publication`, `DuplicateGroup` | RapidFuzz | **IMPLEMENTED AND VERIFIED** | Exact DOI + exact title + weighted fuzzy match (0.6/0.3/0.1) |
| **Merge Audit Trail** | Log pairwise comparison scores | `GET /similarity-log/{id}` | `pipeline/deduplicate.py` | `SimilarityLog` | None | **IMPLEMENTED AND VERIFIED** | Logs comparisons with score >= 0.70 with detailed breakdown |
| **Query Caching** | Cache final merged search responses | Automatic in search | `services/search_service.py` | `CacheEntry` | None | **IMPLEMENTED AND VERIFIED** | Verified; warm cache returns `cache_hit: true` in <15ms |
| **Candidate Generation (Basic)** | OpenAlex candidate search with dominance ratio | `GET /search/candidates` | `services/search_service.py` | None | OpenAlex REST API | **IMPLEMENTED AND VERIFIED** | Active in current UI; calculates dominance ratio |
| **Author Resolution V1 Engine** | Deterministic multi-signal evidence resolver | `/search/candidates` | `services/author_resolution.py` | `AuthorResolution`, `Evidence` | OpenAlex API | **DISCONNECTED / ARCHIVED** | 100% complete in session archive; needs restoration |
| **Dynamic Weight Renormalization** | Rebalance weights over available signals | Internal to scoring | `services/author_scoring.py` | None | None | **DISCONNECTED / ARCHIVED** | Handles missing affiliations/coauthors without inflating score |
| **Human Review & Abstention** | Mark identity as manual review or unresolved | UI button / API | `services/author_resolution.py` | `AuthorResolution` | None | **DISCONNECTED / ARCHIVED** | UI button designed in session; needs reconnection |
| **Alembic Identity Schema** | Relational tables for authors & affiliations | `alembic upgrade head` | `alembic/versions/20260907_01` | `authors`, `author_affiliations` | Alembic | **DISCONNECTED / ARCHIVED** | Additive DDL migration ready to be applied |
| **Semantic Vector Retrieval** | Contextual evidence retrieval from Chroma | `POST /evidence/retrieve` | `services/scholarly_retrieval.py`| ChromaDB | Sentence-Transformers | **DISCONNECTED / ARCHIVED** | Chroma rebuildable projection ready to be restored |
| **Citation-Grounded LLM Explanation** | Verified summary of publication evidence | Internal to retrieval | `services/scholarly_retrieval.py`| None | Gemini / OpenAI API | **DISCONNECTED / ARCHIVED** | Validates citation IDs; deterministic fallback |
| **Candidate Review UI** | Interactive author selection cards | React Component | `components/CandidateSelector.jsx`| None | None | **IMPLEMENTED AND VERIFIED** | Active in UI; renders confidence badges and candidate stats |
| **Merge Details Modal** | Inspect provenance & source records | React Component | `components/MergeDetails.jsx` | None | None | **IMPLEMENTED AND VERIFIED** | Displays source breakdown for merged publications |
| **Search Stats & Status Bar** | Display timing, raw vs merged counts | React Component | `components/StatsBar.jsx` | None | None | **IMPLEMENTED AND VERIFIED** | Renders latency, raw counts, and circuit breaker status |
