# HAMMER — Research Paper Gap Analysis & Revision Plan

## 1. Current Research Paper Status

**File**: `docs/research-paper.md`  
**Approximate length**: ~30 KB  
**Format**: Markdown (not yet exported to LaTeX/PDF)

---

## 2. Claim Audit

The following claims made in the research paper are audited against the implemented system.

| Claim | Implemented? | Evidence |
|-------|-------------|---------|
| "Multi-source ingestion from 4+ scholarly APIs" | ✓ YES | OpenAlex, DBLP, ArXiv, Crossref all implemented and tested |
| "Normalisation pipeline with HTML stripping and type coercion" | ✓ YES | `pipeline/normalize.py` with full test coverage |
| "Deduplication using blocking + fuzzy scoring" | ✓ YES | Union-find algorithm, source-pair thresholds, 0.6/0.3/0.1 formula |
| "Canonical ID generation from DOI/source_id/title hash" | ✓ YES | `_make_canonical_id()` |
| "Author disambiguation using five evidence signals" | ✓ YES | name/institution/publication/coauthor/temporal |
| "Conservative auto-resolution threshold (0.75 score)" | ✓ YES | Configured in `config.py`, enforced in `decide()` |
| "Human-in-the-loop fallback for ambiguous cases" | ✓ YES | PATCH endpoints + frontend CandidateSelector |
| "Semantic retrieval using dense vector embeddings" | ✓ YES | ChromaDB + all-MiniLM-L6-v2 |
| "LLM explanation with citation validation" | ✓ YES | Live verified with gemini-3.5-flash |
| "Circuit breaker for source reliability" | ✓ YES | `circuit_breaker.py`, `circuit_breaker_state` table |
| "Evaluation dataset with 454 publications" | ✓ YES | Verified by DB query |
| "55 automated tests passing" | ✓ YES | pytest confirms 55/55 |

### Claims Requiring Clarification

| Claim | Issue | Recommendation |
|-------|-------|----------------|
| "Deduplication achieves X% precision" | No published precision/recall number | Run `evaluate_benchmark.py` and report result in paper |
| "Author resolution accuracy = Y%" | Pilot evaluation was conducted but not finalized | Report pilot result with confidence interval |
| "Retrieval MAP@5 = Z" | Phase 4 benchmark run; value not inserted in paper | Extract from `docs/audit/phase4/results/` and add |
| "Model F1 score" | Not in current paper draft | Not applicable — no classification model trained |

---

## 3. Gap Analysis

### 3a. Missing Evaluation Results

The paper describes experiments but is missing their outputs.

**Action**: Insert concrete evaluation numbers from existing benchmark results:

```
Location: docs/audit/phase4/results/
Files:
  - retrieval_benchmark_results.json    → MAP@5, precision@1, recall@5
  - resolution_pilot_results.json       → precision, recall, F1 per threshold
  - dedup_regression_results.json       → merge accuracy on labelled pairs
```

### 3b. No Baseline Comparison

Current paper lacks comparison against:
- A naïve merge-everything baseline
- Single-source retrieval (no dedup)

**Action**: Add a table in Section 4/5 comparing:
- HAMMER vs no-deduplication (how many more papers shown?)
- HAMMER vs single-source (coverage increase from multi-source)

### 3c. Shallow Related Work Section

Current related work does not cite:
- ORCID disambiguation literature
- Prior academic knowledge graph papers (OpenKG, OpenAlex itself)
- Entity resolution surveys (Getoor & Machanavajjhala, 2012)

**Action**: Expand related work with 3-5 targeted citations on entity resolution and scholarly metadata systems.

### 3d. Architecture Diagram Missing from Paper

The paper describes the architecture in prose but has no figure.

**Action**: Convert the Mermaid diagram from `01_ARCHITECTURE_OVERVIEW.md` into a paper-ready PNG figure and include it as Figure 1.

### 3e. LLM Integration Section Needs Updating

The paper likely pre-dates the Phase 4B live Gemini verification.

**Action**: Update Section X to note:
- Live integration with `gemini-3.5-flash`
- Zero-trust citation validation mechanism
- Fallback hierarchy
- Observed token usage and latency (3,801 tokens, ~2.1s)

### 3f. Reproducibility Section Missing

No section describes how to reproduce results.

**Action**: Add a Reproducibility Appendix:
```
1. Clone repository
2. cd backend && python -m venv venv && source venv/bin/activate
3. pip install -r requirements.txt
4. alembic upgrade head
5. python scripts/build_vector_index.py
6. uvicorn main:app --host 0.0.0.0 --port 8000
7. pytest tests/ -v
```

---

## 4. Prioritised Revision Roadmap

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| P1 | Insert actual evaluation metrics (MAP, precision, F1) | Low | High |
| P1 | Add architecture figure | Low | High |
| P1 | Update LLM section with live verification results | Low | High |
| P2 | Add baseline comparison table | Medium | High |
| P2 | Expand related work | Medium | Medium |
| P3 | Add reproducibility appendix | Low | Medium |
| P3 | Add limitations section | Low | Medium |

---

## 5. Suggested Section Structure (Revised)

```
1. Introduction
2. Related Work
   2.1 Scholarly Metadata Aggregation
   2.2 Author Name Disambiguation
   2.3 Dense Retrieval and LLM Explanations
3. System Architecture
   3.1 Overview (Figure 1)
   3.2 Multi-Source Ingestion
   3.3 Normalisation and Deduplication
   3.4 Author Resolution
   3.5 Semantic Retrieval and LLM Integration
4. Implementation Details
   4.1 Technology Stack
   4.2 Data Models
   4.3 Configuration and Thresholds
5. Evaluation
   5.1 Deduplication Precision
   5.2 Author Resolution Accuracy
   5.3 Retrieval MAP@5
   5.4 LLM Citation Validation Rate
   5.5 Baseline Comparisons
6. Discussion and Limitations
7. Conclusion
Appendix A: Reproducibility
Appendix B: API Reference
```

