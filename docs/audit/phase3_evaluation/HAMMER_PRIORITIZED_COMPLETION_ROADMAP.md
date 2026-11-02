# HAMMER Accelerated Completion Plan & Execution Roadmap

**Audit Phase:** Phase 3 — Complete System Evaluation  
**Date:** November 2026  
**Target Goal:** Final-Year Project Demonstration, Viva Defense & Thesis Submission  
**Estimated Timeline to Full Completion:** **30 – 36 Engineering Hours**  

---

## 1. Roadmap Architecture & Execution Philosophy

To maximize project quality and academic credibility without wasting time on low-value refactoring, the completion plan is divided into 5 sequential stages.

```
┌────────────────────────────────────────────────────────┐
│ Stage 1: Critical Corrections (Blocker Fixes)         │  ~2 Hours
│ - Fix /similarity-log/{pub_id} MultipleResultsFound bug│
│ - Fix whitespace query HTTP 503 validation flaw       │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Stage 2: Gemini Live Activation & Verification         │  ~2 Hours
│ - Configure GEMINI_API_KEY in backend/.env            │
│ - Validate smoke_llm_provider.py and UI explanation   │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Stage 3: Benchmark Annotation & Evaluation Run         │  ~14 Hours
│ - Annotate 100-query benchmark across 8 scenarios     │
│ - Run evaluate_benchmark.py and freeze metrics        │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Stage 4: End-to-End Demonstration Scripting            │  ~4 Hours
│ - Prepare scripted demo flow with verified seed inputs │
│ - Test offline demo fallback mode                     │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Stage 5: Documentation, Thesis & Viva Defense Pack    │  ~10 Hours
│ - Finalize architecture diagrams & methodology chapters│
│ - Prepare examiner slide deck & viva cheat sheet      │
└────────────────────────────────────────────────────────┘
```

---

## 2. Stage-by-Stage Implementation Breakdown

### Stage 1: Critical Corrections (Blockers)
*Priority: P0 / P1 | Estimated Effort: 2 Hours | Essential: Yes*

- **Task 1.1: Fix `/similarity-log/{pub_id}` Bug in `backend/main.py`**
  - *Action:* Change line 366 from `grp_res.scalar_one_or_none()` to `grp_res.scalars().first()`. Add unit test in `test_author_resolution_api.py`.
  - *Completion Criteria:* `GET /similarity-log/1` returns HTTP 200 with similarity log entries.
- **Task 1.2: Fix Empty Author Query Validation**
  - *Action:* Add `@field_validator('author_name')` in `AuthorCandidateSearchRequest` ensuring stripped length >= 2.
  - *Completion Criteria:* Sending `"   "` returns HTTP 422 Unprocessable Entity instead of 503.

### Stage 2: Gemini Live Activation & Verification
*Priority: P1 | Estimated Effort: 2 Hours | Essential: High Value*

- **Task 2.1: Configure Environment Variable**
  - *Action:* Add `GEMINI_API_KEY=<key>` to `backend/.env`.
- **Task 2.2: Execute Live Provider Smoke Verification**
  - *Action:* Run `backend/scripts/smoke_llm_provider.py`.
  - *Completion Criteria:* Script exits with code `0`, returning `usable_explanation: true` and `citations_passed_validation: true`.
- **Task 2.3: Live UI Verification**
  - *Action:* Search an author in `http://localhost:5173` and verify that the explanation panel renders a natural language summary with clickable citation badges.

### Stage 3: Benchmark Annotation & Research Evaluation
*Priority: P1 | Estimated Effort: 14 Hours | Essential: Yes (For Thesis Research)*

- **Task 3.1: Curate 100 Evaluation Query Seeds**
  - *Action:* Populate `docs/evaluation/templates/identity_query_seed.csv` with 100 diverse author queries covering all 8 scenarios (distinctive, common, multiple affiliations, changed institutions, sparse metadata, multiple profiles, limited publications, negative controls).
- **Task 3.2: Generate Blinded Annotation Packets**
  - *Action:* Run `backend/scripts/prepare_identity_review.py` to produce candidate evidence packets.
- **Task 3.3: Complete Independent Annotation & Adjudication**
  - *Action:* Annotate ground-truth targets for the 100 queries using the independent reviewer protocol. Run `merge_identity_reviews.py`.
- **Task 3.4: Freeze Split & Seal Manifest**
  - *Action:* Run `freeze_split_manifest.py` (60 train / 20 dev / 20 test with author-level isolation) and `seal_evaluation_manifest.py`.
- **Task 3.5: Execute Research Benchmark**
  - *Action:* Run `backend/scripts/evaluate_benchmark.py` and output definitive Precision, Recall, F1, and Selective Accuracy curves into the project thesis.

### Stage 4: End-to-End Viva Demonstration Preparation
*Priority: P1 | Estimated Effort: 4 Hours | Essential: Yes*

- **Task 4.1: Scripted Demonstration Flow**
  - *Action:* Create a 5-minute repeatable demonstration script featuring 4 specific live queries:
    1. **Geoffrey Hinton:** Demonstrates distinctive author candidate retrieval, evidence scoring, the split-profile self-tie, manual review selection, and multi-source deduplication (OpenAlex + Crossref + arXiv).
    2. **Rajesh Kumar:** Demonstrates common-name handling, candidate ambiguity, and safe abstention.
    3. **J. Smith:** Demonstrates negative control, ambiguous initials, and the "Mark Unresolved" workflow.
    4. **ImageNet Semantic Search:** Demonstrates ChromaDB vector retrieval in 175ms and grounded AI explanation.
- **Task 4.2: Pre-warm Local Cache for Offline Resilience**
  - *Action:* Ingest the demo queries once so that even if the university Wi-Fi drops during the viva, HAMMER runs seamlessly from local SQLite and ChromaDB cache (`cache_hit: true`).

### Stage 5: Documentation, Viva Defense & Thesis Pack
*Priority: P2 | Estimated Effort: 10 Hours | Essential: Yes*

- **Task 5.1: Architecture Diagrams & Flowcharts**
  - *Action:* Render high-resolution Mermaid diagrams of the Ingestion Pipeline, Deduplication Union-Find, Author Resolution V1 Scoring, and Citation Validation.
- **Task 5.2: Thesis Chapter Drafting**
  - *Action:* Integrate the Phase 3 evaluation reports directly into Chapter 4 (Implementation) and Chapter 5 (Experimental Results & Evaluation) of the final-year project report.
- **Task 5.3: Examiner Q&A Defense Guide**
  - *Action:* Prepare concise answers to anticipated tough examiner questions (e.g., *"Why is auto-resolution coverage 0% on Hinton?"*, *"How does your deduplication prevent false merges across different authors?"*, *"How do you guarantee Gemini does not hallucinate citations?"*).

---

## 3. What Can Safely Be Postponed Beyond the Final-Year Project?

To ensure timely completion, the following non-critical tasks can safely be omitted:
1. **Database Reconciliation (Merging root and backend SQLite databases):** The backend database (`backend/academic_search.db`) is completely self-contained, contains all 454 publications and 16 tables, and operates reliably. Merging is unnecessary for the project submission.
2. **DBLP Reverse Engineering / Cloudflare Bypassing:** Not required; OpenAlex and Crossref provide comprehensive computer science coverage.
3. **Live Playwright Headless Browser on Server:** Not required; mock data and SQLite cache adequately support Google Scholar demonstrations.
4. **Complex Frontend Redesign:** The existing React/Vite interface is clean, professional, and communicates technical concepts effectively.

---

## 4. Immediate Next Authorized Action

The exact next action the user should authorize:
> **Authorize Stage 1:** Apply the one-line fix to line 366 of `backend/main.py` (`MultipleResultsFound` bug) and add input validation to `AuthorCandidateSearchRequest`.