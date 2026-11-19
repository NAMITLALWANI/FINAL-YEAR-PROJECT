# HAMMER: Hybrid Academic Metadata Aggregator & Entity Resolution

HAMMER is an evidence-guided, human-in-the-loop software architecture for multi-source academic publication discovery, publication deduplication, and author entity resolution.

---

## 1. Architecture Overview

HAMMER organizes scholarly metadata processing into distinct, modular functional subsystems:

- **Authoritative Persistence (SQLite):** `backend/database.py` acts as the immutable system of record for canonical publications, duplicate groups, and author resolution decisions.
- **Multi-Source Ingestion:** `backend/ingestion/` federates queries across OpenAlex, Crossref, DBLP, and arXiv with polite pooling and rate limiting.
- **Publication Deduplication:** `backend/deduplication/` implements Deduplication Engine V2 with deterministic veto safeguards (hard DOI conflict vetoes, edition conflict guards (regex corrected from backspace bytes to word boundaries; regression-tested, not yet replayed against the 50-pair benchmark), multi-year divergence vetoes, prefix-aware matching, and title similarity floors).
- **Author Entity Resolution:** `backend/author_resolution/` retrieves OpenAlex author candidates (one query plus an initials-only fallback), optionally enriches them with works-derived evidence, extracts up to five heuristic evidence signals (name, institution, publication overlap, coauthor overlap, temporal), and applies decision gates (score $\ge 0.75$, margin $\ge 0.15$, dominance $\ge 1.35$, at least 2 available signals) plus evidence-sufficiency safeguards that can only withhold automatic assignment. Which signals contribute depends on the context the caller supplies (see `docs/research/paper_preparation/FIVE_SIGNAL_DATA_SOURCE_FEASIBILITY.md`); the weighted score is a heuristic, not a probability, and the five-signal pipeline has not been empirically evaluated.
- **Derived Semantic Retrieval (RAG):** `backend/rag/` manages a rebuildable ChromaDB collection (`all-MiniLM-L6-v2`, 384-dim) with an empirical cosine similarity floor ($\tau = 0.35$).
- **Generative Explanation:** `backend/explanation/` provides optional Gemini synthesis (the model is taken from the `GEMINI_MODEL` environment variable and is not pinned) validated by a deterministic Citation ID Containment Validator.
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

### Backend setup and execution

HAMMER is verified with Python 3.12. Use an isolated project environment; do
not rely on an unrelated system Python installation.

```bash
cd backend
python3.12 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/uvicorn main:app --reload --port 8000
```

`backend/academic_search.db` is the configured local operational database.
The root-level SQLite file is a separate historical snapshot; do not copy,
merge, or overwrite either database. Author-resolution tables are managed by
Alembic, not `init_db()` or broad `create_all()` calls. Before applying a
migration to an existing database, make and verify a backup, confirm the
resolved `DATABASE_URL`, then run the explicit Alembic command from
`backend/`. See [deployment operations](docs/deployment.md) and
[troubleshooting](docs/troubleshooting.md) for the guarded procedure.

### Running backend tests

```bash
cd backend
./.venv/bin/python -m pytest -p no:cacheprovider tests -q
```

The recovery baseline has 80 passing backend tests. The test suite is designed
to avoid live provider requests and embedding-model downloads.

### Scholar browser runtime (optional)

Only when `ENABLE_SCHOLAR=true`, install Playwright's local browser runtime:

```bash
cd backend
./.venv/bin/python -m playwright install chromium
```

Scholar remains an optional source. A missing browser must not be treated as an
empty author or publication result.

### Frontend setup and execution

Use a supported Node.js runtime (Node 20 or newer) without changing the
project's architecture or lockfile.

```bash
cd frontend
npm ci
npm run dev
```

### Building frontend for production

```bash
cd frontend
npm run build
```

The production build writes only ignored `frontend/dist/` output. The existing
Chroma index is a derived, preserved asset; do not rebuild or replace it as
part of normal setup. `/health` reports its status and document count.

---

## 4. Documentation

- **Architecture Map & Subsystem Navigation:** [`docs/reorganisation/04_FINAL_ARCHITECTURE_MAP.md`](docs/reorganisation/04_FINAL_ARCHITECTURE_MAP.md)
- **Reorganization Report & Audit:** [`docs/reorganisation/05_REORGANISATION_REPORT.md`](docs/reorganisation/05_REORGANISATION_REPORT.md)
- **Research Paper (Revised Draft):** [`docs/research/HAMMER_RESEARCH_PAPER_REVISED_DRAFT.md`](docs/research/HAMMER_RESEARCH_PAPER_REVISED_DRAFT.md)
- **Research Claim-to-Evidence Matrix:** [`docs/research/CLAIM_EVIDENCE_MATRIX.md`](docs/research/CLAIM_EVIDENCE_MATRIX.md)
- **Current Recovery and Research Tracker:** [`docs/PROJECT_EXECUTION_ROADMAP.md`](docs/PROJECT_EXECUTION_ROADMAP.md)
- **Deployment Operations:** [`docs/deployment.md`](docs/deployment.md)
- **Troubleshooting:** [`docs/troubleshooting.md`](docs/troubleshooting.md)
