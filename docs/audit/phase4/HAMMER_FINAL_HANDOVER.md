# HAMMER Phase 4: Final Handover & Operational Guide

**System:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Date:** 2026-11-01T17:58:41.015778+00:00  
**Status:** Completed, Verified, and Defensible  

---

## 1. System Execution Commands

### To Run the Backend:
```bash
cd "/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search"
backend/venv/bin/uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

### To Run the Frontend:
```bash
cd "/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search/frontend"
npm run dev
# Accessible at http://localhost:5173
```

### To Run the Full Automated Test Suite:
```bash
cd "/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search"
backend/venv/bin/pytest backend/tests/ -v
```

### To Run Frontend Production Build:
```bash
cd "/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search/frontend"
npm run build
```

---

## 2. Phase 4 Deliverables Manifest

All 21 required Phase 4 documents are preserved in `docs/audit/phase4/`:
1. `HAMMER_PHASE4_BASELINE.md`
2. `HAMMER_PHASE4_ARCHITECTURE_AND_DEPENDENCY_MAP.md`
3. `HAMMER_AUTHOR_RESOLUTION_BENCHMARK.md`
4. `HAMMER_AUTHOR_PROFILE_CLUSTERING_DESIGN.md`
5. `HAMMER_AUTHOR_RESOLUTION_ERROR_ANALYSIS.md`
6. `HAMMER_DEDUPLICATION_EVALUATION.md`
7. `HAMMER_DEDUPLICATION_IMPLEMENTATION.md`
8. `HAMMER_SEMANTIC_RETRIEVAL_EVALUATION.md`
9. `HAMMER_SEMANTIC_RETRIEVAL_IMPLEMENTATION.md`
10. `HAMMER_GEMINI_LIVE_VERIFICATION.md`
11. `HAMMER_GEMINI_SECURITY_AND_CITATION_SAFETY.md`
12. `HAMMER_CONNECTOR_RELIABILITY.md`
13. `HAMMER_PHASE4_IMPLEMENTATION_PLAN.md`
14. `HAMMER_PHASE4_IMPLEMENTATION_REPORT.md`
15. `HAMMER_PHASE4_CHANGELOG.md`
16. `HAMMER_VIVA_DEMONSTRATION_SCRIPT.md`
17. `HAMMER_DEMO_DATASET_AND_RESET_GUIDE.md`
18. `HAMMER_OFFLINE_READINESS.md`
19. `HAMMER_FINAL_YEAR_READINESS.md`
20. `HAMMER_VIVA_QUESTION_BANK.md`
21. `HAMMER_FINAL_HANDOVER.md`
