# HAMMER Phase 3B: Evaluation Discrepancy Resolution & Audit Reconciliation

**Audit Phase:** Phase 3B — Evaluation Discrepancy Resolution  
**Date:** November 2026  
**Auditor:** Software Architecture, QA & System Forensics  
**Status:** Completed & Reconciled  

---

## 1. Executive Summary & Purpose

A rigorous review of the Phase 3 evaluation deliverables revealed critical contradictions between the summary claims in `HAMMER_API_FRONTEND_RELIABILITY.md` and the machine-readable evidence in `api_reliability_raw.json`. Furthermore, informal heuristics in the Author Resolution benchmark were conflated with rigorous held-out dataset metrics.

Phase 3B resolves these contradictions with complete forensic integrity:
1. Identifies the root causes of all API discrepancies (query parameter mismatches and unhandled server exceptions).
2. Corrects the evaluation methodology and eliminates unverified claims.
3. Fixes confirmed application defects with surgical, documented code modifications covered by automated regression tests.
4. Fully reconciles test reports, raw outputs, and actual production route definitions.

---

## 2. Reconciled Evidence & Discrepancy Table

| Subsystem / Metric | Summary Report Claim | Raw JSON Evidence (`api_reliability_raw.json`) | Root Cause Analysis | Reconciled & Verified Truth |
|---|---|---|---|---|
| **GET /search/candidates** | Claimed `200 OK` (Pass) | Showed `422 Unprocessable Entity` (Fail) | The test script sent `?author_name=...` instead of `?name=...`. FastAPI rejected the request due to missing required query parameter `name`. | **Application Route is Valid; Evaluation Script was Faulty.** When queried with `?name=...`, endpoint returns `200 OK`. Evaluation script corrected. |
| **GET /search** | Claimed `200 OK` (Pass) | Showed `422 Unprocessable Entity` (Fail) | The test script sent `?author=...` instead of `?name=...`. FastAPI rejected the request due to missing required query parameter `name`. | **Application Route is Valid; Evaluation Script was Faulty.** When queried with `?name=...`, endpoint returns `200 OK`. Evaluation script corrected. |
| **POST /author-resolutions/candidates (Whitespace)** | Claimed 422 Bad Request handling | Showed `503 Service Unavailable` | `AuthorCandidateSearchRequest` lacked whitespace validation; empty string was sent to OpenAlex service, which returned `status="failed"`. `main.py` unconditionally mapped all failures to 503. | **Confirmed Application Defect.** Input validation added to Pydantic model (`@field_validator`). Endpoint now returns `422 Unprocessable Entity`. |
| **GET /similarity-log/{pub_id}** | Claimed `200 OK` (Pass) | Showed `500 Internal Server Error` | Database table `duplicate_groups` contains multiple rows for publication ID 1. Query used `scalar_one_or_none()`, which crashed with `MultipleResultsFound`. | **Confirmed Application Defect.** Database query updated to `.scalars().all()`, aggregating all record IDs across duplicate groups. Endpoint now returns `200 OK`. |
| **Candidate Retrieval Recall@K** | Claimed Recall@K = 100% | Informal 10-query observation | No frozen ground-truth dataset with validated `gold_author_id` labels exists in the repository (`identity_labels.csv` is empty). | **Unjustified Metric Withdrawn.** Claiming formal Recall@K without ground-truth labels is methodologically invalid. Reclassified as qualitative observation. |
| **Gemini Explanation Service** | Claimed live activation ready | `smoke_llm_provider.py` exited with code 2 (`Missing GEMINI_API_KEY`) | `GEMINI_API_KEY` is not configured in `backend/.env` or the active process environment. | **Integrated but Not Live-Tested.** Live testing is blocked until credentials are provided. Zero live requests were executed; deterministic fallback is active. |

---

## 3. Discrepancy Deep-Dive & Forensic Investigations

### Discrepancy 1: `GET /search/candidates` and `GET /search` Parameter Contract
- **The Contradiction:** The summary report table showed `Pass (200 OK)` for both endpoints, but the original `api_reliability_raw.json` recorded HTTP `422` with message `Field required: query.name`.
- **Forensic Investigation:**
  - In `backend/main.py`:
    ```python
    @app.get("/search/candidates")
    async def fetch_candidates(request: Request, name: str = Query(..., min_length=2), ...):
    
    @app.get("/search")
    async def search(request: Request, name: str = Query(..., min_length=2), ...):
    ```
  - The evaluation script originally passed `params={"author_name": "Geoffrey Hinton"}` for `/search/candidates` and `params={"author": "Geoffrey Hinton"}` for `/search`.
  - FastAPI strictly enforces parameter names. Because `name` was missing, it returned HTTP 422.
- **Resolution:** The evaluation script was corrected to pass `name`. Live re-execution confirmed that both endpoints return HTTP `200 OK` with valid payloads.

### Discrepancy 2: Whitespace Author Input Returning 503 instead of 422
- **The Contradiction:** Submitting `{"author_name": "   "}` to `POST /author-resolutions/candidates` returned HTTP `503 Service Unavailable` with message `"Candidate source unavailable: no resolution decision was recorded"`.
- **Forensic Investigation:**
  - `AuthorCandidateSearchRequest` defined `author_name: str` without validation. Pydantic accepted whitespace.
  - `OpenAlexCandidateService.generate` stripped the string, saw it was empty, and returned `status="failed", error_code="invalid_query"`.
  - In `backend/main.py`, line 130 unconditionally checked:
    ```python
    if status == "failed" or status not in {"ok", "empty"}:
        return JSONResponse(status_code=503, content={"error": "Candidate source unavailable..."})
    ```
  - The API treated invalid user input as an external infrastructure failure (503) rather than client input validation failure (422/400).
- **Resolution:** Added `@field_validator("author_name")` to `AuthorCandidateSearchRequest` in `backend/main.py`. Sending whitespace now immediately returns HTTP `422 Unprocessable Entity` with a clear validation message.

### Discrepancy 3: `GET /similarity-log/{pub_id}` Crashing with HTTP 500
- **The Contradiction:** Calling `GET /similarity-log/1` returned an unhandled HTTP 500 error.
- **Forensic Investigation:**
  - In `backend/academic_search.db`, table `duplicate_groups` had 4 separate rows for `publication_id = 1` (IDs 1, 265, 433, 601) resulting from multiple historical ingestion passes.
  - The endpoint executed:
    ```python
    grp_res = await db.execute(select(DuplicateGroup).where(DuplicateGroup.publication_id == pub_id))
    group = grp_res.scalar_one_or_none()
    ```
  - SQLAlchemy raised `MultipleResultsFound: Multiple rows were found when one or none was required`, causing an internal server error.
- **Resolution:** Changed line 366 to query all duplicate groups via `.scalars().all()` and aggregate `record_ids`. Calling `GET /similarity-log/1` now returns HTTP `200 OK` with status and log arrays.

---

## 4. Clear Categorization of Evaluation Evidence

To prevent future conflation of automated tests, live network calls, and research benchmarks, the evidence is strictly partitioned:

### 1. Passing Automated Tests (Hermetic Unit & Regression Suite)
- **Status:** **54 / 54 tests passing (100%)** in 3.24s.
- **Execution Evidence:** `pytest backend/tests/ -v` passes completely.
- **Scope:** Covers normalization, Union-Find deduplication, author candidate parsing, evidence extraction, conservative scoring, database relationships, ChromaDB document formatting, citation validation logic, manifest sealing, and the new API regression tests.

### 2. Passing Live API Checks (Local HTTP Contracts)
- **Status:** **11 / 11 checks passing (100%)** against `http://localhost:8000`.
- **Execution Evidence:** Recorded in reconciled `api_reliability_raw.json`.
- **Scope:** Validates `/health`, `/metrics`, `/search/candidates`, `/search`, `/publications/{id}`, `/similarity-log/{id}`, `/evidence/search`, and `/author-resolutions/candidates`.

### 3. Passing Browser Workflows (Interactive UI End-to-End)
- **Status:** **100% Verified** via automated browser subagent.
- **Execution Evidence:** Artifacts `initial_page_state_*.png`, `candidate_selector_state_*.png`, `candidates_loaded_*.png`, and `frontend_eval_*.webp`.
- **Scope:** Search submission, candidate cards display, evidence breakdown inspection, "Mark Unresolved" action, candidate selection persistence, and publication list rendering.

### 4. Research Benchmark Performance (Held-Out Gold Evaluation)
- **Status:** **Incomplete / Pending Annotation.**
- **Actual Evidence:** Only empty CSV templates and an exploratory 12-episode pilot exist.
- **Methodological Standard:** No formal claims of generalizable Precision, Recall, or F1 will be presented until the 100-query benchmark is annotated and evaluated.

### 5. Unverified Functionality (Blocked by External Factors)
- **Gemini Live Execution:** Blocked by missing `GEMINI_API_KEY`.
- **DBLP Live Search:** Blocked by upstream HTTP 202 Cloudflare challenge.
- **Google Scholar Scraping:** Blocked by missing local Playwright Chromium binary.