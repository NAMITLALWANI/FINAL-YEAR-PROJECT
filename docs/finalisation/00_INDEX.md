# HAMMER — Finalisation Documentation Package

**Project**: HAMMER — Hybrid Academic Metadata & Entity Resolution  
**Degree**: BTech AI & Data Science, Final Year Project  
**Documentation Generated**: 2026-11-02  
**Phase**: Post-Phase 4B (Live Gemini Verified)

---

## Document Index

| # | File | Contents |
|---|------|----------|
| 01 | [ARCHITECTURE_OVERVIEW.md](./01_ARCHITECTURE_OVERVIEW.md) | System architecture, component map, Mermaid diagrams |
| 02 | [TRACEABILITY_MAP.md](./02_TRACEABILITY_MAP.md) | Requirements → code mapping, module responsibility table |
| 03 | [EXECUTION_WALKTHROUGH.md](./03_EXECUTION_WALKTHROUGH.md) | Step-by-step request lifecycle with code excerpts |
| 04 | [INGESTION_AND_DEDUPLICATION.md](./04_INGESTION_AND_DEDUPLICATION.md) | Multi-source ingestion, normalisation, dedup algorithm |
| 05 | [AUTHOR_RESOLUTION.md](./05_AUTHOR_RESOLUTION.md) | Candidate generation, evidence signals, decision logic |
| 06 | [SEMANTIC_RETRIEVAL_AND_LLM.md](./06_SEMANTIC_RETRIEVAL_AND_LLM.md) | ChromaDB retrieval, Gemini integration, citation validation |
| 07 | [DATA_MODELS.md](./07_DATA_MODELS.md) | All 16 SQLite tables, relationships, Alembic migration path |
| 08 | [API_REFERENCE.md](./08_API_REFERENCE.md) | All REST endpoints with parameters, responses, examples |
| 09 | [TEST_SUITE.md](./09_TEST_SUITE.md) | 55-test suite breakdown, coverage, execution instructions |
| 10 | [RESEARCH_PAPER_REVISION_PLAN.md](./10_RESEARCH_PAPER_REVISION_PLAN.md) | Gap analysis, claim audit, revision roadmap |
| 11 | [VIVA_READINESS.md](./11_VIVA_READINESS.md) | Anticipated questions, defensible answers, demo script |
| 12 | [FINALISATION_GAP_REPORT.md](./12_FINALISATION_GAP_REPORT.md) | Outstanding gaps, risk register, completion checklist |

---

## System Status at Documentation Date

| Metric | Value |
|--------|-------|
| SQLite publications | 454 |
| SQLite source records | 2,053 |
| ChromaDB embeddings | 449 |
| Automated tests passing | 55 / 55 (100%) |
| Gemini integration | LIVE VERIFIED (`gemini-3.5-flash`) |
| Citation validation | Zero-trust, doc-ID verified |
| Frontend build | Vite production clean |
| Git branch | `main` (HEAD: `2c4c5a9`) |

