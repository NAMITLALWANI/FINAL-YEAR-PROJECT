# HAMMER — Code Duplication & Multi-Agent Conflict Report
**Generated:** 2026-11-01  
**Scope:** Forensic analysis of competing implementations, duplicate assets, disconnected components, and authoritative resolutions.

---

## 1. Executive Summary of Duplications

Due to multiple AI coding sessions operating independently across different directories (Desktop vs `Documents/Codex`), several parallel implementations and duplicate artifacts were introduced. This report analyzes each conflict and establishes the authoritative implementation.

---

## 2. Inventory of Competing Implementations & Conflicts

### 2.1 Author Candidate Resolution: Lightweight vs Modular V1
- **Implementation A (Active in Desktop):**
  - **File:** `backend/services/search_service.py` (`get_author_candidates`)
  - **Mechanism:** Inlines OpenAlex search, calculates dominance ratio:
    Dominance Ratio = TopWorks / (SecondWorks + 1)
    Auto-selects if Score > 0.60 and Dominance Ratio > 3.0.
  - **Pros:** Minimal dependencies, already wired into `main.py` and React UI.
  - **Cons:** Hardcoded heuristic, lacks evidence breakdown, lacks persistence of resolution decisions, does not support multi-signal evidence or manual review audits.
- **Implementation B (Preserved in Agent Session):**
  - **Files:** `backend/services/author_candidates.py`, `author_evidence.py`, `author_scoring.py`, `author_resolution.py`
  - **Mechanism:** Modular deterministic resolver. Separates candidate extraction, evidence signal evaluation, dynamically renormalized scoring, and three-way decision policy (`AUTO_RESOLVED`, `MANUAL_REVIEW`, `UNRESOLVED`). Persists evidence audit trail.
  - **Pros:** Architecturally rigorous, evidence-grounded, handles missing signals cleanly, covered by 43 unit and integration tests.
  - **Cons:** Was left in the Codex sandbox and disconnected from the active Desktop `main.py`.
- **Authoritative Resolution:**
  - **Select Implementation B (Modular V1)** as the authoritative identity engine.
  - Retain the dominance ratio formula as one of the constituent signals inside `author_evidence.py` so that no useful heuristic behavior is lost.

### 2.2 Database Persistence: Root vs Backend SQLite Files
- **File 1:** `/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search/backend/academic_search.db` (449 publications, 1,924 source records, 955 duplicate groups)
- **File 2:** `/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search/academic_search.db` (546 publications, 857 source records, 546 duplicate groups)
- **Analysis:**
  - In `config.py`, `DATABASE_URL` is configured as `"sqlite+aiosqlite:///./academic_search.db"`.
  - When the application is launched from `backend/`, SQLite resolves `./academic_search.db` to `backend/academic_search.db`.
  - The root file is an early prototype snapshot from May 2026. The backend file has the complete, active duplicate groups and similarity logs.
- **Authoritative Resolution:**
  - **`backend/academic_search.db` is authoritative.**
  - Modify `config.py` to use an absolute path or explicit path resolved relative to `__file__`:
    `Path(__file__).parent / "academic_search.db"`
  - Archive the root `academic_search.db` into `archive/` to eliminate directory-dependent database confusion.

### 2.3 CandidateSelector React Component Variations
- **Variation A (Active Desktop):**
  - **File:** `frontend/src/components/CandidateSelector.jsx`
  - **Capabilities:** Renders candidate cards with name, institution, works count, citations, and confidence badge.
- **Variation B (Archived Session):**
  - **File:** Patched `CandidateSelector.jsx`
  - **Capabilities:** All features of Variation A, plus:
    - Evidence panel (`candidate-evidence`) displaying retrieved publication hits from semantic index.
    - Explicit disclaimer: *"Index record X; retrieval rank Y. Similarity is not an identity probability."*
    - "Mark identity unresolved" button for safe human abstention.
    - Handles retrieval unavailability gracefully without blocking deterministic selection.
- **Authoritative Resolution:**
  - **Consolidate Variation B into `CandidateSelector.jsx`.**
  - Variation B preserves all existing UI functionality while adding evidence explanations and human abstention controls.

### 2.4 Duplicate / Redundant Test Data & Logs
- `candidates_test_results.json` exists in both root and `backend/`.
- `dev.log` and `server.log` exist in both `frontend/` and `backend/`.
- `presentation_visuals.html` and `visuals/` exist in root.
- **Authoritative Resolution:**
  - Keep historical test logs in `backend/` for regression tracking.
  - Add `*.log` and temporary test outputs to `.gitignore`.

---

## 3. Recommended Actions Summary

| Component | Competing Artifacts | Recommended Authoritative | Action Required |
| :--- | :--- | :--- | :--- |
| **Author Resolution** | `search_service.py` vs `services/author_*.py` | Modular V1 (`services/author_*.py`) | Consolidate V1 into backend; connect routes |
| **SQLite Database** | Root vs `backend/academic_search.db` | `backend/academic_search.db` | Update `config.py` path; archive root db |
| **Frontend Selector** | Basic Selector vs Evidence-Enhanced Selector | Evidence-Enhanced Selector | Update `CandidateSelector.jsx` with evidence panel |
| **Vector Index** | None (missing in Desktop) | `services/scholarly_retrieval.py` | Restore vector indexing service & Chroma projection |
| **Alembic Migrations** | None in Desktop vs `20260907_01` in session | `alembic/versions/20260907_01_*.py` | Restore migration scripts; verify non-destructive run |
