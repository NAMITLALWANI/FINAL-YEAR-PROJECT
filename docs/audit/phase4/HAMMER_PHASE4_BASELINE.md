# HAMMER Phase 4: Baseline and Forensic System Audit

**Generated:** 2026-11-01T17:58:41.011779+00:00  
**System:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Evaluator:** Principal Systems Auditor & Research Software Architect  

---

## 1. System Identity and Environment Baseline

| Parameter | Observed Evidence | Verification Method |
|---|---|---|
| **Repository Path** | `/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search` | `pwd` |
| **Git Branch** | `main` | `git status` |
| **Git HEAD Commit** | `2c4c5a93dd181e0e0aad3c557cef2e3c716a1c62` | `git rev-parse HEAD` |
| **Remote Origin** | `https://github.com/NAMITLALWANI/FINAL-YEAR-PROJECT.git` | `git remote -v` |
| **Python Interpreter** | `backend/venv/bin/python` (Python 3.12.5) | `sys.version` |
| **Node / Vite** | Vite 5.4.21, React 18.3.1 | `package.json` |
| **Active Backend Database** | `backend/academic_search.db` (50,720,768 bytes, 16 tables) | SQLite inspection |
| **Alembic Revision** | `20260907_01` (`author_resolution_foundation`) | `alembic current` |
| **Active ChromaDB Collection**| `scholarly_records_v1` in `backend/vector_index` (449 docs) | Chroma PersistentClient |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) | `config.py` |
| **LLM Provider** | Google Gemini (`gemini-1.5-flash` / `gemini-1.5-pro`) | `services/scholarly_retrieval.py` |

---

## 2. Forensic Preservation and Backup Audit

Prior to any execution or evaluation in Phase 4, independent verification and snapshot preservation were executed:

- **Backup Snapshot Directory:** `backups/phase4_baseline_20261101_173430/`
- **Codebase Snapshot:** `codebase_state_20261101_173430.tar.gz` (189,297,659 bytes)
- **Authoritative Database (`backend/academic_search.db`):**
  - SHA-256: `90f37cfaff6fc49d708655932397819f9aa5fd602958fe3f3cb39c204686adc4`
  - Integrity Check: `ok`
  - Record Counts: 454 publications, 2053 source records, 960 duplicate groups, 15 candidate snapshots, 2 resolutions.
- **Reference Database (`root_academic_search.db`):**
  - SHA-256: `b9117aac20b6a9a90cf767547ab2059b175c5c8c1d0c6cd041e01fe032b70d44`
  - Integrity Check: `ok`
  - Record Counts: 546 publications, 7 tables. Preserved read-only.
- **ChromaDB SQLite Index (`backend/vector_index/chroma.sqlite3`):**
  - SHA-256: `4ec4a790f447ba4fb6bea2d1627632bc80b365819be98b32be0ce3bcfdb8da7b`
  - Integrity Check: `ok`
  - Embedding Collection: `scholarly_records_v1` (449 embeddings).

---

## 3. Test Suite Baseline Execution

The baseline automated test suite was executed prior to modifications using `backend/venv/bin/pytest backend/tests/ -v`:

- **Total Tests Run:** 54
- **Passed:** 54 (100%)
- **Failed:** 0
- **Skipped:** 0
- **Runtime:** 3.64 seconds
- **Database Mutation:** Zero. Post-test database hash was re-verified against baseline SHA-256 (`90f37cfaff...`), confirming that tests use isolated temporary databases or mock fixtures.

---

## 4. Key Observations and Baseline Inconsistencies

1. **Author Resolution Conservative Abstention:**
   The V1 author resolution engine abstains (`manual_selection_required`) on prolific researchers due to profile fragmentation in upstream sources (e.g. OpenAlex profiles yielding identical name/signal similarity).
2. **Retrieval Nearest-Neighbor Noise:**
   ChromaDB queries lack a cosine similarity floor filter, causing out-of-domain and gibberish queries to return AI papers with low cosine similarities (~0.17–0.25).
3. **Duplicate Results in Top Hits:**
   Because SQLite contains 100 duplicate publications with `raw_*` canonical IDs from a legacy DBLP run, semantic search frequently returned duplicate titles in top-5 hits.
4. **Gemini Configuration State:**
   No `GEMINI_API_KEY` was configured in the environment files. Deterministic fallback is active and fully functional.
