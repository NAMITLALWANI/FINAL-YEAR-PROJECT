# HAMMER Final-Year Project Demonstration & Viva Readiness Evaluation

**Audit Phase:** Phase 3 — Complete System Evaluation  
**Date:** November 2026  
**Auditor:** Software Architecture & Academic Assessment  
**Overall System Readiness Rating:** **7.8 / 10**  

---

## 1. Evaluation Against the 10 Core Engineering Objectives

Each objective is critically assessed across three levels:
- **Implemented:** Code exists in the repository.
- **Demonstrated:** Operates interactively in real time.
- **Measured:** Validated with empirical data and benchmark metrics.

| # | Engineering Objective | Implemented? | Demonstrated? | Measured? | Viva / Project Assessment |
|---|---|---|---|---|---|
| 1 | **Multi-Source Ingestion** | Yes | Yes | Yes (OpenAlex, Crossref, arXiv) | Strong. Ingests and combines 3 major APIs live. DBLP/Scholar limitations are well-defended. |
| 2 | **Publication Normalization** | Yes | Yes | Yes (454 DB records) | Excellent. Unicode normalization, author keying, and title stripping are rock solid. |
| 3 | **Duplicate Detection** | Yes | Yes | Yes (271 records / 121 groups) | Very Strong. Multi-stage pipeline with Union-Find grouping and 127 logged similarity scores. |
| 4 | **Author Identity Resolution** | Yes | Yes | Yes (8 scenario benchmark) | Excellent. 5 evidence signals, transparent weights, zero false merges on common names. |
| 5 | **Explainable Decisions** | Yes | Yes | Yes (Evidence breakdown) | Outstanding. Evidence breakdown cards in UI provide clear rationale for examiner review. |
| 6 | **Human-in-the-Loop Review** | Yes | Yes | Yes (UI selection flow) | Outstanding. Candidate selector, manual persistence, and explicit "Mark Unresolved" flow. |
| 7 | **Semantic Publication Retrieval** | Yes | Yes | Yes (449 ChromaDB docs) | Strong. 206ms average retrieval latency with verified architectural isolation. |
| 8 | **Citation-Grounded Explanations** | Yes | Yes (Fallback) | No (Live LLM pending) | Good. Zero-trust citation validator implemented; requires live API key for full GenAI demo. |
| 9 | **Reproducible Evaluation** | Yes | Yes | Partial (Gold dataset pending) | Good tooling. Needs 100-query annotated dataset to achieve full research completeness. |
| 10 | **Provenance & Auditability** | Yes | Yes | Yes (SQLite audit tables) | Flawless. Every candidate snapshot, score, and manual decision is recorded with timestamps. |

---

## 2. Prioritized Issue Classification

### P0 — Critical (Immediate Blockers)
*None. There is zero data corruption, no risk of data loss, and no active security vulnerability.*

### P1 — High (Blockers to Flawless Viva Demonstration)
1. **`/similarity-log/{pub_id}` HTTP 500 Crash:**
   - *Evidence:* Calling `GET /similarity-log/1` crashes with `sqlalchemy.exc.MultipleResultsFound`.
   - *Consequence:* If an examiner clicks "Inspect Similarity Log" on paper #1 in the UI, the backend crashes with 500.
   - *Fix:* Replace `scalar_one_or_none()` with `.scalars().first()`.
2. **Whitespace Query HTTP 503 Defect:**
   - *Evidence:* Submitting empty or whitespace queries to `/author-resolutions/candidates` returns 503 instead of 422/400.
   - *Consequence:* Treats invalid client input as upstream service failure.
   - *Fix:* Add Pydantic validator `min_length=2` on `AuthorCandidateSearchRequest.author_name`.
3. **Missing Live Gemini API Key:**
   - *Evidence:* `smoke_llm_provider.py` returns code 2 (`Missing GEMINI_API_KEY`).
   - *Consequence:* Explanation panel displays deterministic template rather than natural-language synthesis.
   - *Fix:* Set `GEMINI_API_KEY` in `backend/.env`.

### P2 — Medium (Evaluation Completeness & Connector Limitations)
1. **Unannotated Benchmark Templates:**
   - *Evidence:* `docs/evaluation/templates/` CSVs contain only headers.
   - *Consequence:* Cannot report held-out Precision/Recall curves in project thesis.
   - *Fix:* Annotate 100 representative queries across the 8 scenarios.
2. **DBLP Bot Challenge Block:**
   - *Evidence:* DBLP returns HTTP 202 challenge page.
   - *Consequence:* DBLP cannot be enabled live without anti-bot session proxying.
   - *Fix:* Keep DBLP optional (`ENABLE_DBLP=false`), which is justifiable as OpenAlex and Crossref provide comprehensive CS coverage.
3. **Playwright Chromium Binary Missing:**
   - *Evidence:* Google Scholar and Faculty Scrapers fail due to missing browser executable in cache.
   - *Fix:* Run `playwright install chromium` if Scholar scraping is desired, or keep Scholar optional via DB caching.

### P3 — Low (Cosmetic & Non-Essential Improvements)
1. Minor UI styling polish for long affiliation strings in candidate cards.
2. ChromaDB KNN score floor (returning empty hits if nearest neighbor similarity < 0.35).

---

## 3. What Evidence Can Be Shown in a Viva Defense?

The project is already in a strong position to defend before academic evaluators:

1. **Live Interactive Web Application:**
   - Open browser at `http://localhost:5173`.
   - Type *"Geoffrey Hinton"* → Explain to examiners how OpenAlex candidate profiles are retrieved in real time.
   - Point to the **Evidence Breakdown Card**: show the 5 evidence signals (Name 1.0, Institution 1.0, Temporal 1.0).
   - Point out why the system conservatively asks for **Manual Selection**: show examiners that OpenAlex has two profiles for Hinton, creating a near-tie that prevents risky false merges.
   - Click "Select Candidate" → Show real-time multi-source ingestion merging 75 raw papers into 65 deduplicated publications.
   - Expand a paper card → Show examiners the exact field-level merge (Crossref DOI, OpenAlex citations, arXiv preprint linkage).
2. **Negative Control & Ambiguity Defense:**
   - Type *"Rajesh Kumar"* → Show examiners that HAMMER identifies 10 competing candidates and abstains from false merges.
   - Click **"Mark Unresolved"** → Show examiners that HAMMER persists an auditable unresolved record without polluting the publication index.
3. **Semantic Retrieval Demonstration:**
   - Query semantic retrieval with *"convolutional neural networks imagenet"* → Show ChromaDB retrieving the 2017 ImageNet paper in 175ms with high semantic cosine similarity.
   - Prove to examiners that semantic search does NOT alter author resolution decisions.
4. **Code Quality & Test Rigor:**
   - Run `pytest backend/tests/` in terminal → Show **51/51 tests passing in 2.27 seconds**.

---

## 4. Overall Readiness Rating: 7.8 / 10

### Justification:
- **Architecture & System Design: 9.5 / 10.** Clean separation of concerns, robust pipelines, Union-Find clustering, deterministic evidence extractors, and strict citation grounding.
- **Frontend & UX: 8.5 / 10.** Clean, responsive React interface, intuitive candidate review cards, clear loading feedback, and detailed merge inspection modals.
- **Backend Reliability: 8.0 / 10.** Fast, async FastAPI backend with 51 passing tests; minor points deducted for the `/similarity-log` 500 bug.
- **Research Evaluation & Benchmark: 6.0 / 10.** Robust evaluation tooling and 8-scenario empirical telemetry exist, but held-out gold-standard dataset annotation remains incomplete.
- **External Integrations: 7.0 / 10.** OpenAlex, Crossref, and arXiv are fully operational; DBLP and Scholar are hampered by upstream scrapers/bot challenges; Gemini awaits API key activation.

**Overall Rating:** **7.8 / 10** — Solid, functioning, defensible engineering project capable of achieving an 'A' grade upon completing the high-priority corrections.