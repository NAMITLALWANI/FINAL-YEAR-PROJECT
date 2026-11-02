# HAMMER — Finalisation Gap Report

## 1. Completion Status

| Component | Status | Notes |
|-----------|--------|-------|
| Multi-source ingestion | ✅ Complete | OpenAlex, DBLP, ArXiv, Crossref |
| Normalisation pipeline | ✅ Complete | HTML strip, type coercion, canonical ID |
| Deduplication algorithm | ✅ Complete | Union-find, blocking, fuzzy, thresholds |
| Author resolution V1 | ✅ Complete | 5 signals, decision logic, HITL |
| Semantic retrieval | ✅ Complete | ChromaDB, 449 embeddings, 0.35 floor |
| Gemini LLM integration | ✅ LIVE VERIFIED | gemini-3.5-flash, citation validation |
| REST API | ✅ Complete | 10+ endpoints, rate limiting, circuit breaker |
| React frontend | ✅ Complete | Search, CandidateSelector, evidence display |
| Test suite | ✅ Complete | 55/55 passing |
| Database schema | ✅ Complete | 16 tables, Alembic migration |
| Research paper draft | ⚠️ Needs updates | Evaluation results not inserted, figures missing |
| Evaluation results in paper | ❌ Not done | Numbers exist in audit files, not in paper |
| Architecture figure | ❌ Not done | Diagram in docs, not in paper |
| Reproducibility appendix | ❌ Not done | Instructions scattered |
| Baseline comparison | ❌ Not done | No single-source vs multi-source table |

---

## 2. Outstanding Work (Prioritised)

### P1 — High Priority (Needed for Submission)

**P1.1 Insert evaluation metrics into research paper**
- Source: `docs/audit/phase4/results/`
- Target: Research paper Section 5
- Effort: 1-2 hours
- Impact: Makes paper's claims measurable

**P1.2 Add architecture diagram to paper**
- Source: Mermaid diagram in `01_ARCHITECTURE_OVERVIEW.md`
- Action: Export as PNG via mermaid-cli or online renderer
- Effort: 30 minutes
- Impact: Essential for any systems paper

**P1.3 Update LLM section with Phase 4B results**
- Source: `docs/audit/phase4b/HAMMER_GEMINI_LIVE_SMOKE_TEST.md`
- Target: Research paper LLM/integration section
- Effort: 1 hour

### P2 — Medium Priority (Recommended)

**P2.1 Add baseline comparison table**
- Compare: HAMMER vs single-source, vs no-dedup
- Evidence: Run new evaluation sweep (1-2 hours)
- Impact: Strengthens academic contribution claim

**P2.2 Expand related work section**
- Add: Entity resolution survey, ORCID system, OpenAlex paper
- Effort: 2-3 hours

**P2.3 Add limitations section**
- Note: Scholar disabled by default (rate limiting), no cross-source author graph, publication_authorships table empty
- Effort: 30 minutes

### P3 — Low Priority (Good to Have)

**P3.1 Add reproducibility appendix to paper**

**P3.2 Export paper from Markdown to LaTeX or PDF**

**P3.3 Tag a clean Git release commit**

---

## 3. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Gemini API unavailable during demo | Low | Medium | Fallback to deterministic summary; always responds |
| External API (OpenAlex/DBLP) down during demo | Medium | Medium | Circuit breaker shows "circuit_open"; cache entries available |
| Scholar bot detection | High | Low | Scholar disabled by default; not part of demo |
| ChromaDB index corruption | Very Low | High | Rebuild script at `scripts/build_vector_index.py`; 449 docs rebuild in <1 min |
| SQLite concurrent write conflict | Very Low | Low | Single-node deployment; aiosqlite is async-safe |
| Database shows 0 publications | Very Low | High | Backup at `backend/academic_search.db.backup-*` |

---

## 4. Not Implemented (Acknowledged Scope Boundaries)

The following items are architecturally designed for but not yet populated:

| Feature | Table/Component | Status |
|---------|-----------------|--------|
| Cross-source author authorship graph | `publication_authorships` | Table exists, 0 rows — requires cross-source ID resolution |
| Author affiliation history | `author_affiliations` | Table exists, 0 rows — populated from OpenAlex affiliation list on resolution |
| Author display name variants | `author_aliases` | Table exists, 0 rows — populated from OpenAlex aliases on resolution |
| Multi-source author linking | `author_external_ids` | 1 row — created on each auto-resolve |

These are genuine future extensions, not failures. The tables exist and are constraint-correct.

---

## 5. Infrastructure Notes

### Servers Currently Running

| Service | Port | PID Group |
|---------|------|-----------|
| FastAPI (uvicorn) | 8000 | task-1638 |
| React (Vite dev) | 5173 | task-138 |

### Database Backups

```
backend/academic_search.db                       ← live production DB
backend/academic_search.db.backup-20261101212549 ← backup before Phase 2
backups/                                          ← additional backup copies
```

### Rebuild Procedures

```bash
# Rebuild ChromaDB index from SQLite
backend/venv/bin/python backend/scripts/build_vector_index.py

# Re-run all tests
backend/venv/bin/python -m pytest backend/tests/ -v

# Check Alembic migration state
cd backend && venv/bin/alembic current
```

---

## 6. Finalisation Checklist

- [x] All 55 tests passing
- [x] Gemini API key configured and live verified
- [x] Backend and frontend servers tested
- [x] Database integrity verified (integrity_check passed)
- [x] `docs/finalisation/` package complete (12 documents)
- [ ] Evaluation metrics inserted into research paper
- [ ] Architecture diagram exported and embedded in paper
- [ ] LLM section updated with Phase 4B results
- [ ] Paper reviewed for claim accuracy
- [ ] Git release tag created

