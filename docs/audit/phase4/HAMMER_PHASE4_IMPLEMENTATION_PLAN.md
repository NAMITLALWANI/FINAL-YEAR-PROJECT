# HAMMER Phase 4: Prioritized Implementation Plan

**System:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Status:** Approved & Executed Implementation Plan  

---

## 1. Priority Classification

- **P0 (Correctness / Safety Defect):**
  - Semantic Retrieval duplicate result suppression and cosine similarity floor (`0.35`).
- **P1 (Core Research Functionality):**
  - Ingestion idempotency guard in `_persist_publications`.
  - Non-destructive author profile clustering architecture design.
- **P2 (Reliability & Testing):**
  - Retrieval regression test additions in `test_scholarly_retrieval.py`.
- **P3 (Viva Demonstration & Handover):**
  - Demonstration script, dataset reset guide, question bank.

---

## 2. Risk & Rollback Management

Every implementation was designed to be strictly non-destructive:
- Zero SQL table schema changes required.
- Zero rows deleted from `publications` or `source_records`.
- Full backward compatibility maintained with existing API routes.
