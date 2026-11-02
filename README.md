# HAMMER: Hybrid Academic Metadata Aggregator & Entity Resolution

HAMMER is an evidence-guided, human-in-the-loop software architecture for multi-source academic publication discovery, publication deduplication, and author entity resolution.

---

## 1. Architecture Overview

HAMMER organizes scholarly metadata processing into distinct, modular functional subsystems:

- **Authoritative Persistence (SQLite):** `backend/database.py` acts as the immutable system of record for canonical publications, duplicate groups, and author resolution decisions.
- **Multi-Source Ingestion:** `backend/ingestion/` federates queries across OpenAlex, Crossref, DBLP, and arXiv with polite pooling and rate limiting.
- **Publication Deduplication:** `backend/deduplication/` implements Deduplication Engine V2 with deterministic veto safeguards (hard DOI conflict vetoes, edition conflict guards, multi-year divergence vetoes, prefix-aware matching, and title similarity floors).
- **Author Entity Resolution:** `backend/author_resolution/` provides multi-strategy candidate harvesting against OpenAlex, extracts 5 evidence signals, and executes non-linear decision gates (score $\ge 0.75$, margin $\ge 0.15$, dominance $\ge 1.35$), prioritizing precision over recall.
- **Derived Semantic Retrieval (RAG):** `backend/rag/` manages a rebuildable ChromaDB collection (`all-MiniLM-L6-v2`, 384-dim) with an empirical cosine similarity floor ($\tau = 0.35$).
- **Generative Explanation:** `backend/explanation/` provides zero-trust Gemini 2.5 Flash synthesis validated by a deterministic Citation ID Containment Validator.
- **Feature-Oriented Frontend:** `frontend/src/features/` organizes UI components by domain (`search/`, `author_resolution/`, `deduplication/`, `monitoring/`).

---

## 2. Directory Navigation

| Subsystem | Directory | Key Implementation |
|---|---|---|
| **Author Resolution** | `backend/author_resolution/` | `candidates.py`, `evidence.py`, `scoring.py`, `resolver.py` |
| **Deduplication** | `backend/deduplication/` | `normalize.py`, `engine.py` |
| **Ingestion** | `backend/ingestion/` | `openalex.py`, `crossref.py`, `dblp.py`, `arxiv.py` |
| **Semantic Retrieval (RAG)** | `backend/rag/` | `retrieval.py` |
| **Explanation & Citation Defense** | `backend/explanation/` | `synthesis.py` |
| **Frontend Features** | `frontend/src/features/` | `search/`, `author_resolution/`, `deduplication/`, `monitoring/` |
| **Architecture Documentation** | `docs/reorganisation/` | `04_FINAL_ARCHITECTURE_MAP.md` |

---

## 3. Quick Start

### Backend Setup & Execution
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

### Running Backend Tests
```bash
cd backend
pytest tests/ -q
```
*(All 78 tests pass in ~21s)*

### Frontend Setup & Execution
```bash
cd frontend
npm install
npm run dev
```

### Building Frontend for Production
```bash
cd frontend
npm run build
```

---

## 4. Documentation

- **Architecture Map & Subsystem Navigation:** [`docs/reorganisation/04_FINAL_ARCHITECTURE_MAP.md`](docs/reorganisation/04_FINAL_ARCHITECTURE_MAP.md)
- **Reorganization Report & Audit:** [`docs/reorganisation/05_REORGANISATION_REPORT.md`](docs/reorganisation/05_REORGANISATION_REPORT.md)
- **Research Paper (Revised Draft):** [`docs/research/HAMMER_RESEARCH_PAPER_REVISED_DRAFT.md`](docs/research/HAMMER_RESEARCH_PAPER_REVISED_DRAFT.md)
- **Research Claim-to-Evidence Matrix:** [`docs/research/CLAIM_EVIDENCE_MATRIX.md`](docs/research/CLAIM_EVIDENCE_MATRIX.md)
