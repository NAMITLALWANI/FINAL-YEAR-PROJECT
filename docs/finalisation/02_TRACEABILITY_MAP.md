# HAMMER — Implementation Traceability Map

## 1. Research Objective → Code Module Mapping

| Research Objective | Implemented Module(s) | Key Functions / Classes |
|---|---|---|
| Multi-source ingestion | `connectors/openalex.py`, `connectors/dblp.py`, `connectors/arxiv.py`, `connectors/crossref.py` | `fetch()`, `_fetch_impl()` |
| Normalisation | `pipeline/normalize.py` | `normalize()`, `CanonicalRecord` |
| Publication deduplication | `pipeline/deduplicate.py` | `deduplicate()`, `_fuzzy_score()`, `_threshold()` |
| Author candidate generation | `services/author_candidates.py` | `OpenAlexCandidateService.generate()` |
| Author evidence extraction | `services/author_evidence.py` | `extract_evidence()`, 5 signal functions |
| Author resolution decision | `services/author_resolution.py` | `AuthorResolutionService.create_resolution()`, `decide()` |
| Weighted evidence scoring | `services/author_scoring.py` | `score_evidence()`, `CandidateScore` |
| Semantic retrieval | `services/scholarly_retrieval.py` | `retrieve()`, `_search()` |
| LLM-powered explanation | `services/scholarly_retrieval.py` | `generate_explanation()` |
| Citation validation | `services/scholarly_retrieval.py` | claim doc-ID cross-reference loop |
| Deterministic fallback | `services/scholarly_retrieval.py` | `_fallback_summary()` |
| Rate limiting | `rate_limiter.py` | SlowAPI decorators on endpoints |
| Circuit breaker | `circuit_breaker.py` | `is_source_available()`, `record_failure()` |
| Response caching | `cache.py` | `CacheEntry` table queries |
| REST API | `main.py` | FastAPI route definitions |
| Database persistence | `database.py` | SQLAlchemy ORM models |
| Human-in-the-loop review | `main.py` (`/author-resolutions` routes) | Manual selection endpoints |

---

## 2. Module Responsibility Table

### `backend/main.py`
- FastAPI application setup, CORS, rate limiter initialisation
- All REST route definitions (10+ endpoints)
- Dependency injection (`get_db`)
- Orchestration of service calls within route handlers

### `backend/config.py`
- Environment profile loading (`.env.dev` → `.env`)
- Feature flags, source priority, thresholds (dedup, author resolution)
- Author scoring weights, timeout values, connection strings

### `backend/database.py`
- SQLAlchemy 2 `Base` declarative models for all 16 tables
- `init_db()` — creates legacy tables (Alembic controls author-resolution tables)
- `get_db()` — async session dependency

### `backend/pipeline/normalize.py`
- `CanonicalRecord` dataclass — the canonical representation
- `normalize(raw: dict) → CanonicalRecord` — type-safe field extraction
- `_make_canonical_id()` — DOI > source_id > title-hash precedence
- Helper utilities: `normalized_title_for_compare()`, `author_key_set()`

### `backend/pipeline/deduplicate.py`
- `deduplicate(records, exclusions)` — union-find algorithm
- `_blocking_pass()` — cheap pre-filter (DOI, year, author prefix, title prefix)
- `_fuzzy_score()` — 60% title + 30% author + 10% year composite
- `_threshold()` — source-pair-aware thresholds (0.80–0.95)
- `_merge_group()` — source-priority field election + citation maximisation

### `backend/services/search_service.py`
- `run_search()` — async fan-out to all enabled connectors
- `_fetch_from_connector()` — circuit-breaker-aware fetch wrapper
- `_persist_publications()` — idempotency guard (canonical_id + DOI + norm_title)
- `get_author_candidates()` — lightweight candidate shortlist for UI

### `backend/connectors/` (base + 5 connectors)
- `base.py` → `BaseConnector.fetch()` — cache-first, circuit-breaker-aware template
- `openalex.py` — REST API, polite pool mailto, author ID direct lookup
- `dblp.py` — XML/JSON DBLP search
- `arxiv.py` — arXiv atom feed parsing with rate-limit delay
- `crossref.py` — Crossref Works API, DOI-authoritative
- `scholar.py` + `scrapers/scholar/` — optional, rate-limited Google Scholar

### `backend/services/author_candidates.py`
- `OpenAlexCandidateService` — searches OpenAlex `/authors` endpoint
- `OpenAlexCandidate` — typed candidate with affiliations, aliases, works
- `persist_candidates()` — stores candidates to `author_candidates` table
- `rank_candidates()` — applies `score_evidence` + sorts by weighted score

### `backend/services/author_evidence.py`
- Five deterministic evidence extractors (all return `Evidence` dataclass):
  1. `name_similarity` — rapidfuzz token_sort_ratio vs display_name + aliases
  2. `institution_similarity` — token_set_ratio vs affiliation names
  3. `publication_overlap` — DOI + normalised-title intersection
  4. `coauthor_overlap` — normalised name set intersection
  5. `temporal_compatibility` — year-range overlap fraction
- `extract_evidence()` — assembles all five into a list

### `backend/services/author_scoring.py`
- `score_evidence()` — normalised weighted sum
- Weights from `config.AUTHOR_SCORE_WEIGHTS`:
  - name_similarity: 0.35, institution_similarity: 0.25, publication_overlap: 0.20, coauthor_overlap: 0.10, temporal_compatibility: 0.10

### `backend/services/author_resolution.py`
- `AuthorResolutionService.create_resolution()` — full resolution pipeline
- `decide(ranked)` — conservative decision tree:
  - `auto_selected`: score ≥ 0.75 AND margin ≥ 0.15 AND dominance ≥ 1.35 AND ≥2 signals
  - `manual_selection_required`: score ≥ 0.45 but not dominant
  - `unresolved`: score < 0.45
- Creates `Author` + `AuthorExternalId` on auto-resolve
- Stores `AuthorResolutionEvidence` for every signal × candidate

### `backend/services/scholarly_retrieval.py`
- `retrieve()` — async ChromaDB query with min_score=0.35 floor
- `_search()` — blocking thread, deduplicates by (canonical_id, doi, norm_title)
- `generate_explanation()` — Gemini REST API with structured JSON output
- Citation validation: every `claim.document_ids` cross-referenced against `hit_by_id`
- `_fallback_summary()` — deterministic fallback when Gemini unavailable

---

## 3. Key Configuration Constants (config.py)

| Constant | Default | Purpose |
|----------|---------|---------|
| `DEDUP_DEFAULT_THRESHOLD` | 0.85 | Default fuzzy merge threshold |
| `DEDUP_LENIENT_THRESHOLD` | 0.80 | openalex+crossref pair |
| `DEDUP_STRICT_THRESHOLD` | 0.92 | any pair involving Scholar |
| `AUTHOR_AUTO_SCORE_THRESHOLD` | 0.75 | Minimum score for auto-resolve |
| `AUTHOR_AUTO_MARGIN_THRESHOLD` | 0.15 | Minimum score gap between top-2 |
| `AUTHOR_AUTO_DOMINANCE_THRESHOLD` | 1.35 | Minimum score ratio top/second |
| `AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO` | 2 | Must have ≥2 scoreable signals |
| `RETRIEVAL_TIMEOUT_SECONDS` | 15 | Connector fetch timeout |

---

## 4. Test → Module Traceability

| Test File | Module Under Test |
|-----------|------------------|
| `test_database_foundation.py` | `database.py` — table creation, constraints |
| `test_dedup_regression.py` | `pipeline/deduplicate.py` |
| `test_author_candidates.py` | `services/author_candidates.py` |
| `test_author_evidence_scoring.py` | `services/author_evidence.py`, `author_scoring.py` |
| `test_author_resolution_service.py` | `services/author_resolution.py` |
| `test_author_resolution_api.py` | `main.py` → author-resolution routes |
| `test_author_resolution_migration.py` | Alembic migration integrity |
| `test_annotation_workflow.py` | Human-in-the-loop annotation endpoints |
| `test_api_defects_regression.py` | Known API bug regressions |
| `test_scholarly_retrieval.py` | `services/scholarly_retrieval.py` |
| `test_evaluation_benchmark.py` | Evaluation harness correctness |

