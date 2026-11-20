# HAMMER: project map (start here)

A guide for finding things and for following the code from one file to the next. Paths are relative to this folder. Nothing in the application code was changed to make this map.

## 1. Top-level folders
| Folder | What is in it | Use it for |
|---|---|---|
| `backend/` | The application (FastAPI), the evaluation toolkit and all tests | The demo and code questions |
| `frontend/` | The web interface (React + Vite) | The demo |
| `docs/` | Design notes, API and database docs, research protocol, testing record | Written answers; see `docs/README.md` |
| `paper/` | The IEEE research paper (LaTeX source, PDF, figures, references) | The paper |
| `research_data/` | Benchmark samples, captures, the evaluation freeze | Evidence behind the results |
| `whitebook/`, `presentation/` | The white book and the October slides | Submission material |
| `archive/` | Old files nothing uses any more (see `archive/README.md`) | Ignore for the demo |

## 2. Backend map (`backend/`)
**Entry point:** `main.py` creates the app and every URL (`/search`, `/author-resolutions/...`, `/publications/{id}`, `/evidence/search`, `/health`, `/metrics`). Settings and thresholds: `config.py`. Database tables: `database.py` (Alembic migration in `alembic/versions/`).

### 2a. "Search for a researcher's papers"
`frontend` search → `GET /search` in `main.py` → `services/search_service.py: search()` →
1. fetches each source with `ingestion/openalex.py`, `crossref.py`, `dblp.py`, `arxiv.py` (common interface in `ingestion/base.py`; optional Scholar and faculty scrapers in `ingestion/scrapers/`);
2. cleans each record with `deduplication/normalize.py: normalize()`;
3. finds duplicates with `deduplication/engine.py: deduplicate()` (DOI, edition and year vetoes, fuzzy title and author score);
4. saves records and merged papers with `_persist_publications()` into `database.py` tables `source_records`, `publications`, `duplicate_groups`, `similarity_logs`.

### 2b. "Which person does this name mean?" (the research part)
`POST /author-resolutions/candidates` in `main.py` → `author_resolution/resolver.py: AuthorResolutionService.generate_pool()` →
1. `author_resolution/candidates.py: OpenAlexCandidateService` asks OpenAlex for up to 10 author profiles (`clean_query_name()` tidies the name first);
2. `author_resolution/enrichment.py` (optional extra look-ups when papers or co-author IDs are given);
3. `author_resolution/evidence.py: extract_evidence()` gives the five clues: `name_similarity`, `institution_similarity`, `publication_overlap`, `coauthor_overlap`, `temporal_compatibility`;
4. `author_resolution/scoring.py: score_evidence()` combines them (weights in `config.py`; missing clues are left out, not counted as zero);
5. `author_resolution/policy.py: evaluate_decision()` applies the rules and safeguards and returns automatic, manual review or unresolved.

Then `POST /author-resolutions` saves the outcome (`resolver.py: create_resolution_detailed()`), and `GET /author-resolutions/{id}` returns it with its evidence. Query context (institution, years, DOIs): `author_resolution/context.py`.

### 2c. Semantic search and explanation
`POST /evidence/search` → `rag/retrieval.py: retrieve()` (ChromaDB index of paper text, model all-MiniLM-L6-v2) → optional `generate_explanation()` (Gemini; every cited paper ID is checked against the retrieved ones).

### 2d. Why some files look duplicated
`connectors/`, `pipeline/`, `services/author_*.py` and `services/scholarly_retrieval.py` are one-line forwarding files ("facades") kept so older imports still work. **The real code is in** `ingestion/`, `deduplication/`, `author_resolution/`, `rag/` and `explanation/`. `explanation/synthesis.py` also contains a second copy of the retrieval code; the active retrieval path is `rag/retrieval.py`.

### 2e. Supporting files
`cache.py`, `circuit_breaker.py`, `rate_limiter.py`, `log_config.py` (resilience and logging); `schemas/` (request shapes); `utils/security.py`; `mock_data/`, `demo_authors.json`, `scholar_profiles.json`, `site_profiles/` (sample and profile data used by connectors).

## 3. Evaluation toolkit (the research side, `backend/`)
| Folder | Role |
|---|---|
| `hammer_lagos/prep.py` | Reads the LAGOS-AND benchmark archive, builds the 50-case sample |
| `hammer_pilot/` | Capture and offline replay of provider responses, metrics (`metrics_c7.py`), sample-size planning (`sizing_c9.py`), sample selection, blinded review packets, freeze manifest |
| `scripts/` | Command-line tools that run the above; see `backend/scripts/README.md` |
| `tests/` | 591 automatic tests; file names say what they cover (`test_author_*` for the resolver, `test_dedup_*`, `test_metrics_c7*`, ...) |

## 4. Frontend map (`frontend/src/`)
`main.jsx` → `App.jsx` (page logic) → `services/api.js` (all calls to the backend, one function per URL).
- `features/search/`: `SearchBar` (input), `PaperCard` (a merged paper), `SemanticResultCard`, `StatsBar`
- `features/author_resolution/`: `AuthorContextForm` (optional institution, years, DOIs), `CandidateSelector` (ranked candidates with evidence and the Select button), `contextModel.js`
- `features/deduplication/MergeDetails.jsx`: shows how records were merged
- `features/monitoring/`: `SourceStatusPanel`, `SourceBadge` (which sources are healthy)

## 5. Running it
```bash
cd backend && python3.12 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/uvicorn main:app --reload --port 8000      # API docs at http://localhost:8000/docs
cd ../frontend && npm install && npm run dev            # http://localhost:5173
cd ../backend && ./.venv/bin/python -m pytest tests -q  # 591 tests
```

## 6. Likely questions and where the answer is
| Question | Look at |
|---|---|
| How do you decide two papers are the same? | `deduplication/engine.py: deduplicate()` and its vetoes; `docs/deduplication.md` |
| How is an author matched? | section 2b above; `docs/author_resolution_v1.md` |
| Why does it so rarely decide automatically? | `author_resolution/policy.py` (margin and dominance rules); paper Section VI-E |
| What are the weights and thresholds? | `config.py` (`AUTHOR_SCORE_WEIGHTS`, `AUTHOR_AUTO_*`); not tuned, stated as a limitation |
| What does the database store? | `database.py`; `docs/database.md` |
| How do you know it works? | `backend/tests/`; `docs/testing_validation/` (T001 to T020) |
| What was evaluated and what was not? | `docs/research/paper_preparation/FINAL_COMPLETION_REPORT.md` |
