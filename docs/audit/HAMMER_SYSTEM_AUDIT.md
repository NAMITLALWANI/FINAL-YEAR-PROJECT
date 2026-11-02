# HAMMER — Full System Forensic Audit & Architectural Recovery Report
**System Name:** HAMMER (Hybrid Academic Metadata & Entity Resolution) / Academic Metadata Aggregator  
**Audit Date:** 2026-11-01  
**Auditor Roles:** Principal Software Architect, Senior Backend Engineer, Senior Frontend Engineer, QA Lead  
**Scope:** Full codebase, git topology, multi-agent historical rollouts, database integrity, and pipeline verification  

---

## 1. Executive Summary & Forensic Discovery

A thorough forensic audit of the project was conducted across the local filesystem, Git history, and agent rollout archives.

### 1.1 The Root Cause of Architectural Fragmentation
Forensic analysis reveals that the repository was developed across two disconnected working trees by different coding agents between May and October 2026:
1. **The Active Local Git Clone (Baseline ProjectX):**
   - **Path:** `/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search`
   - **Git Remote:** `https://github.com/NAMITLALWANI/FINAL-YEAR-PROJECT.git` (`origin/main` at commit `2c4c5a9 ui improvements`)
   - **Current State:** Contains the functional Phase 1 Academic Metadata Aggregator (FastAPI backend + React frontend + SQLite database + RapidFuzz deduplication engine).
2. **The Advanced Agent Sandbox (Author Resolution V1 & ChromaDB):**
   - **Historical Path:** `/Users/nileshlalwani/Documents/Codex/2026-09-07/https-github-com-namitlalwani-final-year`
   - **Historical State:** Between September 7 and October 15, 2026, an AI agent developed:
     - **Author Resolution V1 Subsystem:** Deterministic multi-signal evidence extraction, dynamically renormalized scoring, dominance-ratio thresholding, and Alembic database migration foundation (`20260907_01`).
     - **Derived Semantic Retrieval Layer:** ChromaDB vector index (`scholarly_publications_v1`) utilizing `all-MiniLM-L6-v2` embeddings as an auxiliary, rebuildable evidence index.
     - **Citation-Validated Explanation Layer:** Gemini / LLM explanation integration with strict citation-ID membership verification.
     - **Comprehensive Test Suite:** 43 automated pytest unit and integration tests passing.
   - **Why It Disappeared From Disk:** The sandbox directory in `~/Documents/Codex` was closed and removed when the session ended, and its uncommitted changes were never pushed to `origin/main` or merged into the Desktop repository.
   - **Preservation Status:** 100% preserved with full byte fidelity in the local session archives (`~/.codex/sessions/2026/09/07/*.jsonl` and `2026/10/15/*.jsonl`).

---

## 2. Baseline Environment Audit

### 2.1 Git Status & Version Control
- **Repository Root:** `/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search`
- **Current Branch:** `main`
- **HEAD Commit:** `2c4c5a93dd181e0e0aad3c557cef2e3c716a1c62` (*ui improvements*)
- **Remote:** `origin https://github.com/NAMITLALWANI/FINAL-YEAR-PROJECT.git`
- **Working Tree Status:** Clean with respect to tracked files; untracked local virtualenv `backend/venv/` and uncommitted local database updates.

### 2.2 Database & Persistence Baseline
The system utilizes SQLite with SQLAlchemy 2.0 Async (`aiosqlite`).
Two database instances exist:
1. **Authoritative Backend Database:** `backend/academic_search.db`
   - **Integrity Check:** `ok` (PRAGMA integrity_check passed)
   - **Current Tables & Row Counts:**
     - `source_records`: 1,924 rows
     - `publications`: 449 rows
     - `duplicate_groups`: 955 rows
     - `similarity_logs`: 124 rows
     - `cache_entries`: 16 rows
     - `scholar_cache`: 2 rows
     - `circuit_breaker_state`: 4 rows
2. **Root SQLite Database:** `academic_search.db` (546 publications, 857 source records)
   - **Finding:** A legacy/root database file created during early prototype testing. `config.py` defaults to `./academic_search.db`, which when executed from `backend/` correctly targets `backend/academic_search.db`.

### 2.3 Runtime Environment & Dependencies
- **Python Runtime:** Python 3.12.10 in `backend/venv/`
  - Core installed: `fastapi (0.111.0)`, `uvicorn (0.29.0)`, `sqlalchemy (2.0.29)`, `aiosqlite (0.20.0)`, `rapidfuzz (3.9.1)`, `playwright (1.43.0)`, `httpx (0.27.0)`, `feedparser (6.0.11)`, `beautifulsoup4 (4.12.3)`, `lxml (5.2.1)`.
- **Node & Frontend Runtime:** Node.js v20+, Vite 5.4.21, React 18.3.1
  - Build test: `npm run build` succeeds in 532ms (`dist/index.html` 0.84 kB, `dist/assets/index-Dpo4gfDO.js` 156.82 kB).

---

## 3. Pipeline Architecture Analysis

### 3.1 Scholarly Metadata Ingestion
- **OpenAlex Connector (`connectors/openalex.py`):**
  - Implements REST query with polite pool mailto (`OPENALEX_MAILTO`).
  - Supports author filtering (`filter=author.id:...`) and text search.
  - Reconstructs abstracts from OpenAlex inverted index structure.
  - Generates candidate author profiles via `search_authors()`.
- **DBLP Connector (`connectors/dblp.py`):**
  - Queries `dblp.org/search/publ/api`.
  - Strong Computer Science bibliographic precision; lacks abstracts and citation metrics.
- **arXiv Connector (`connectors/arxiv.py`):**
  - Queries `export.arxiv.org/api/query` and parses Atom XML feed.
  - Enforces `ARXIV_DELAY_SECONDS = 3.0` for polite harvesting.
- **Crossref Connector (`connectors/crossref.py`):**
  - Queries `api.crossref.org/works`.
  - Authoritative source for DOI resolution and publisher-registered citations.
- **Google Scholar Scraper (`connectors/scholar.py`):**
  - Uses Playwright headless Chromium browser via `BrowserManager` singleton.
  - Scrapes author profile citations and publication tables.
  - Caches raw HTML in `scholar_cache` table to mitigate CAPTCHAs.
- **Faculty Page Scraper (`connectors/faculty_scraper.py`):**
  - Site profile scraper (e.g. `kjsomaiya.json`).
  - Scrapes university departmental faculty web pages.
- **Circuit Breaker & Resilience:**
  - `circuit_breaker.py` tracks per-source consecutive failures.
  - 5 failures trip circuit into `OPEN` state for 15 minutes, preventing cascade timeouts.

### 3.2 Normalization & Deduplication Subsystem
- **Normalization Layer (`pipeline/normalize.py`):**
  - Normalizes raw records into `CanonicalRecord`.
  - Strips HTML entities, collapses whitespace, extracts 4-digit years.
  - Generates deterministic `canonical_id`:
    `doi_<sha256[:16]>` > `sid_<sha256[:16]>` > `ttl_<sha256[:16]>`.
  - Normalizes author keys: `FIRST_INITIAL + LAST_NAME` (e.g., `G_HINTON`).
- **Deduplication Engine (`pipeline/deduplicate.py`):**
  - Union-Find disjoint-set clustering.
  - Stage 1: Exact DOI matching.
  - Stage 2: Exact normalized title matching.
  - Stage 3: Blocking filter (DOI match, +/- 1 year, author initial overlap, or title 5-char prefix).
  - Stage 4: Weighted fuzzy scoring:
    Score = 0.6 * TitleSim + 0.3 * AuthorSim + 0.1 * YearMatch
  - Adaptive thresholding: Stricter for Scholar/Crossref pairs (0.95), lenient for OpenAlex/Crossref (0.80), default 0.85.
  - Canonical field synthesis uses `SOURCE_PRIORITY`: `crossref (1) > openalex (2) > dblp (3) > arxiv (4) > scholar (5) > faculty_page (6)`.
  - Full audit logging of pairwise scores >= 0.70 into `similarity_logs`.

### 3.3 Author Identity Resolution V1
- **Current Active State (`search_service.py`):**
  - Candidate selection via OpenAlex with heuristic dominance ratio:
    Dominance Ratio = TopWorks / (SecondWorks + 1)
  - Auto-selects if Score > 0.60 and Dominance Ratio > 3.0.
  - Otherwise returns candidate profiles for manual user resolution.
- **Recovered V1 Architecture (from archival session):**
  - Modular pipeline: `author_candidates.py` -> `author_evidence.py` -> `author_scoring.py` -> `author_resolution.py`.
  - Dynamically renormalized weights when signals (affiliations, coauthors) are sparse or missing.
  - Explicit three-way decision policy: `AUTO_RESOLVED`, `MANUAL_REVIEW`, `UNRESOLVED`.
  - Strict abstention policy: sparse evidence does not inflate confidence.
  - Prevents silent failure: throws `CandidateSourceUnavailable` on API outages instead of returning empty results.

### 3.4 Semantic Retrieval & LLM Explanation
- **Derived ChromaDB Layer (`services/scholarly_retrieval.py`):**
  - Rebuildable vector projection in `vector_index/`.
  - Embeddings generated locally with Sentence-Transformers `all-MiniLM-L6-v2`.
  - Decoupled from author resolution: semantic similarity surfaces related work context for human reviewers but **never** determines author identity.
- **LLM Explanation Layer (`generate_explanation`):**
  - Integrated with Gemini / OpenAI-compatible endpoint.
  - Citation-ID validation ensures claims cite only retrieved document IDs. Hallucinated or unknown citations trigger immediate deterministic fallback.

---

## 4. Verification & Health Summary

| Subsystem | Execution Path | Current Live Status | Verification Level |
| :--- | :--- | :--- | :--- |
| **Backend API** | FastAPI / Uvicorn (Port 8000) | **LIVE** (HTTP 200) | Verified End-to-End |
| **Frontend UI** | Vite + React (Port 5173) | **LIVE** (HTTP 200) | Verified End-to-End |
| **Database** | SQLite `backend/academic_search.db` | **HEALTHY** (Integrity OK) | Verified End-to-End |
| **Deduplication** | RapidFuzz + Union-Find | **OPERATIONAL** | Verified with Hinton Benchmark |
| **Connectors** | OpenAlex, DBLP, Crossref, arXiv | **OPERATIONAL** | Verified Live |
| **Scholar Scraper** | Playwright Chromium Scraper | **OPERATIONAL** | Verified (Cache Active) |
| **Candidate Flow** | Dominance Ratio / Selector UI | **OPERATIONAL** | Verified Live |
| **Author Resolution V1** | Multi-signal Deterministic Resolver | **ARCHIVED IN SESSION** | Code Intact, Needs Consolidation |
| **ChromaDB Index** | Persistent Vector Store | **ARCHIVED IN SESSION** | Code Intact, Needs Consolidation |
| **Alembic Migrations** | Version `20260907_01` | **ARCHIVED IN SESSION** | DDL Intact, Needs Consolidation |
