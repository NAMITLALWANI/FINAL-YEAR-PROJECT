# HAMMER Complete System Architecture & Subsystem Evaluation

**Audit Phase:** Phase 3 — Complete System Evaluation  
**Date:** November 2026  
**Auditor:** Software Architecture, QA & System Forensics  
**Status:** Evaluation Baseline Established  

---

## 1. Executive Summary & Mission Alignment

HAMMER (Holistic Academic Metadata Matching, Disambiguation & Reconciliation) is an academic search, publication deduplication, and author entity resolution system. Following the completion of Phase 2 (Author Resolution V1 restoration and integration), Phase 3 conducts an exhaustive, evidence-based evaluation of the entire system.

The central research and engineering question of this evaluation is:
> *"Does HAMMER reliably retrieve, reconcile, disambiguate, and explain academic publication information, and can we demonstrate this with measurable evidence?"*

The system was evaluated end-to-end across:
**Frontend (React/Vite) → API (FastAPI) → Pipeline & Domain Services → Databases (SQLite & ChromaDB) → External Academic Providers & LLMs.**

### High-Level Verdict
- **Core Academic Ingestion:** Operational across OpenAlex, Crossref, and arXiv (100% request success in live tests). DBLP is blocked by upstream HTTP 202 bot challenges; Google Scholar and Faculty Scrapers require local headless browser environments.
- **Publication Deduplication:** Fully functional multi-stage pipeline (exact DOI match, normalized title token sort ratio, author overlap, year tolerance, and Union-Find grouping). In the authoritative database, 271 source records have been deduplicated into 121 multi-source canonical publications across OpenAlex, Crossref, and arXiv.
- **Author Resolution V1:** Fully restored, deterministic, and 100% compliant with frozen thresholds (auto: 0.75, margin: 0.15, dominance: 1.35, min_signals: 2). In live empirical tests across 8 representative scenarios, the resolver correctly abstains from false merges on common and ambiguous names, requiring human-in-the-loop manual review. However, because OpenAlex frequently splits a single prominent scholar into multiple profile entities, duplicate external profiles create self-ties that prevent automatic resolution even on distinctive names.
- **Semantic Retrieval:** Fully operational via ChromaDB (`all-MiniLM-L6-v2`, 449 indexed documents). Average retrieval latency is 206ms. Semantic similarity is strictly isolated from author resolution scoring and never overrides deterministic identity decisions.
- **Gemini Integration:** Fully implemented with structured JSON schema prompting, citation validation, and deterministic fallback. However, it is **integrated but not live-tested** due to the absence of `GEMINI_API_KEY` in the active environment.
- **Software Quality:** 51/51 pytest tests pass (100% pass rate in 2.27s). Frontend builds cleanly in 634ms. Live browser testing confirmed end-to-end functionality for search, candidate review, manual resolution persistence, and publication rendering. One critical backend bug (HTTP 500 on `/similarity-log/{pub_id}`) was discovered and documented.

---

## 2. Complete Architecture & Subsystem Inventory (20 Subsystems)

Each of the 20 core subsystems was inspected across code, API, database, tests, and runtime behavior.

| # | Subsystem | Code Entry Point | API Endpoint | Database Tables | Status | Viva Necessity |
|---|---|---|---|---|---|---|
| 1 | **Academic Ingestion Orchestrator** | `pipeline/ingest.py` | `GET /search` | `source_records`, `cache_entries` | Fully Operational | Essential |
| 2 | **OpenAlex Connector** | `connectors/openalex.py` | Indirect via ingest | `source_records`, `cache_entries` | Fully Operational | Essential |
| 3 | **Crossref Connector** | `connectors/crossref.py` | Indirect via ingest | `source_records`, `cache_entries` | Fully Operational | Essential |
| 4 | **DBLP Connector** | `connectors/dblp.py` | Indirect via ingest | `source_records`, `cache_entries` | Broken (Upstream Bot Challenge) | Optional |
| 5 | **arXiv Connector** | `connectors/arxiv.py` | Indirect via ingest | `source_records`, `cache_entries` | Fully Operational | Essential |
| 6 | **Google Scholar Connector** | `connectors/scholar.py` | Indirect via ingest | `scholar_cache` | Operational w/ Limitations (Missing Playwright binary) | Optional |
| 7 | **Faculty Scraper** | `connectors/faculty_scraper.py` | Indirect via ingest | `source_records` | Operational w/ Limitations (Missing Playwright binary) | Optional |
| 8 | **Publication Normalization** | `pipeline/normalize.py` | Internal service | `source_records` | Fully Operational | Essential |
| 9 | **DOI Exact Matching** | `pipeline/deduplicate.py` | Internal service | `publications` | Fully Operational | Essential |
| 10 | **Publication Deduplication & Merging** | `pipeline/deduplicate.py` | `GET /search` | `publications`, `duplicate_groups`, `similarity_logs` | Operational w/ Limitations (Bug in log query) | Essential |
| 11 | **Author Candidate Generation** | `services/author_candidates.py` | `POST /author-resolutions/candidates`, `GET /search/candidates` | `author_candidates` | Fully Operational | Essential |
| 12 | **Author Evidence Extraction** | `services/author_evidence.py` | Internal service | `author_resolution_evidence` | Fully Operational | Essential |
| 13 | **Author Scoring & Resolution (V1)** | `services/author_resolution.py`, `services/author_scoring.py` | `POST /author-resolutions/candidates` | `author_resolutions`, `authors` | Fully Operational | Essential |
| 14 | **Manual Identity Review** | `services/author_resolution.py` | `POST /author-resolutions` | `author_resolutions`, `authors` | Fully Operational | Essential |
| 15 | **Unresolved Identity Handling** | `services/author_resolution.py` | `POST /author-resolutions` | `author_resolutions` | Fully Operational | Essential |
| 16 | **Semantic Retrieval (ChromaDB)** | `services/scholarly_retrieval.py` | `POST /evidence/search` | ChromaDB collection `scholarly_records_v1` | Fully Operational | Essential |
| 17 | **Gemini Explanation Integration** | `services/scholarly_retrieval.py` | `POST /evidence/search`, `POST /author-resolutions/candidates` | None | Integrated but Unverified Live (Missing API Key) | High |
| 18 | **Citation Verification** | `services/scholarly_retrieval.py` | Internal validation | None | Fully Operational (Deterministic Fallback) | Essential |
| 19 | **Frontend Search & Candidate UI** | `frontend/src/App.jsx`, `CandidateSelector.jsx` | React UI (`http://localhost:5173`) | Local browser state | Fully Operational | Essential |
| 20 | **Evaluation & Benchmark Tooling** | `backend/scripts/` | CLI scripts | SQLite, ChromaDB snapshots | Operational w/ Limitations (Templates empty) | High |

---

## 3. Subsystem Classification Details

### 1. Fully Operational Subsystems
- **OpenAlex, Crossref, arXiv Ingestion:** 100% request success rate, rich metadata, rapid response (2.6s - 3.5s latency).
- **Publication Normalization:** Unicode normalization, title case folding, punctuation stripping, and author string normalization are verified and regression-tested.
- **Author Resolution V1:** Complete 5-signal extraction, candidate persistence, weighted scoring, and decision rules execute deterministically.
- **Semantic Retrieval:** ChromaDB operates with 449 documents, cosine similarity, and sub-250ms query latency.
- **Frontend User Workflow:** End-to-end search, candidate selection, resolution persistence, paper list rendering, and stats display verified via live browser subagent execution.

### 2. Operational with Limitations
- **Publication Deduplication:** Merging and Union-Find logic work excellently; however, `GET /similarity-log/{pub_id}` throws HTTP 500 when multiple duplicate groups exist for a single publication (`MultipleResultsFound`).
- **Google Scholar & Faculty Scrapers:** Code paths are intact, caching tables exist in SQLite, but live Playwright execution fails because Chromium headless shell is not installed in the local environment cache.
- **Evaluation Infrastructure:** Manifest sealing, split validation, and replay scripts are implemented and tested, but the gold standard ground-truth evaluation dataset contains only template headers and an exploratory 12-episode pilot.

### 3. Integrated but Not Live-Tested
- **Gemini Explanation Integration:** Complete async httpx client, JSON prompt templates, structured output parser, and citation validator are implemented and pass all 12 unit tests under mocked providers. However, no live API key is configured in the environment, so live calls default to deterministic fallback.

### 4. Broken Subsystems
- **DBLP Ingestion:** DBLP's public search API endpoint (`https://dblp.org/search/publ/api`) returns an HTTP 202 challenge page (`<title>Making sure you're not a bot!</title>`) against automated python clients, throwing `json.decoder.JSONDecodeError`.

---

## 4. End-to-End Trace: Frontend to External Providers

```
[User Browser: http://localhost:5173]
       │
       ▼ (Search query "Geoffrey Hinton")
[FastAPI Backend: http://localhost:8000]
       │
       ├──► Step 1: POST /author-resolutions/candidates
       │         │
       │         ├──► OpenAlexCandidateService: queries OpenAlex API
       │         │    └── Receives candidate profiles (A5108093963, A5153609875)
       │         │
       │         ├──► extract_evidence(): computes 5 deterministic signals
       │         ├──► score_evidence(): applies weights & dynamic renormalization
       │         ├──► decide(): evaluates auto threshold (0.75), margin (0.15), dominance (1.35)
       │         │    └── Margin = 0.0357 < 0.15 ──► Returns "manual_selection_required"
       │         │
       │         ├──► ChromaDB retrieve(): fetches top-3 semantic hits (206ms)
       │         └──► generate_explanation(): checks GEMINI_API_KEY
       │              └── Key missing ──► Returns local deterministic fallback explanation
       │
       ▼ (User views candidate cards and selects Canonical Profile)
[Frontend CandidateSelector Component]
       │
       ├──► Step 2: POST /author-resolutions
       │         └── Persists manual resolution row to SQLite `author_resolutions` table
       │
       └──► Step 3: GET /search?name=Geoffrey+Hinton&candidate_id=...
                 │
                 ├──► Ingestion Orchestrator: queries OpenAlex, Crossref, arXiv
                 │    └── Gathers 75 raw source records
                 ├──► Normalization: builds CanonicalRecords
                 ├──► Deduplication: DOI exact match + RapidFuzz token_sort_ratio
                 │    └── Deduplicates 75 raw records into 65 merged publications
                 └──► Persists MergedPublications & DuplicateGroups to SQLite
```

---

## 5. Architectural Invariant Verification

1. **Deterministic Isolation:** Semantic vector search (ChromaDB) is strictly separated from author resolution scoring. Vector scores are NEVER ingested into the 5 author evidence signals.
2. **Conservative Abstention:** Author resolution never auto-selects a candidate unless margin (>=0.15) and dominance (>=1.35) are satisfied. In ties or near-ties, it defaults safely to manual review.
3. **Audit Provenance:** All candidate snapshots, evidence signals, and user selections are persisted with timestamps and raw JSON payloads in `backend/academic_search.db`.