# HAMMER — Test Suite

## 1. Summary

| Metric | Value |
|--------|-------|
| Total tests | 55 |
| Passing | 55 (100%) |
| Failing | 0 |
| Skipped | 0 |
| Test runner | pytest-asyncio |
| Test DB | In-memory SQLite (isolated per test) |

**Last verified**: 2026-11-01 (Phase 4B)

---

## 2. Test Files and Coverage

### `test_database_foundation.py`
Tests that all 16 tables can be created, have correct schema, and enforce constraints.

- `test_tables_created` — verifies all legacy + author-resolution tables exist
- `test_publication_canonical_id_unique` — enforces UNIQUE on canonical_id
- `test_source_record_insert` — roundtrip insert+select
- `test_author_resolution_check_constraints` — verifies status enum constraint
- `test_similarity_log_roundtrip` — insert and retrieve similarity entry

---

### `test_dedup_regression.py`
Regression tests for the deduplication algorithm preventing known failures.

- `test_exact_doi_match_merged` — two records with same DOI always merge
- `test_exact_title_match_merged` — same normalised title always merges
- `test_blocking_pass_year_only` — year anchor triggers fuzzy scoring
- `test_scholar_crossref_threshold_strict` — scholar+crossref requires ≥0.95
- `test_openalex_crossref_lenient` — openalex+crossref allows ≥0.80
- `test_author_key_normalisation` — INITIAL_LASTNAME extraction cases
- `test_merge_field_priority_crossref_wins` — crossref field takes precedence
- `test_citation_max_across_sources` — highest citation count selected
- `test_no_false_positive_different_author` — different authors stay separate
- `test_canonical_id_doi_preferred` — DOI-based ID chosen over title-hash

---

### `test_author_candidates.py`
Tests OpenAlex candidate generation and persistence.

- `test_candidate_generation_from_fixture` — generates candidates from mock API response
- `test_candidate_persistence` — stores candidates to `author_candidates` table
- `test_candidate_dedup_on_source_id` — same source_author_id not inserted twice
- `test_works_count_mapped_correctly` — works_count from OpenAlex preserved
- `test_aliases_stored_as_json` — aliases list serialised correctly

---

### `test_author_evidence_scoring.py`
Tests all five evidence extractors and the scoring formula.

- `test_name_similarity_exact_match` — identical names score 1.0
- `test_name_similarity_alias_match` — match via alias list scores 1.0
- `test_institution_similarity_unavailable_without_hint` — returns UNAVAILABLE
- `test_institution_similarity_partial_match` — partial institution name scores > 0
- `test_publication_overlap_doi` — matching DOI contributes to score
- `test_publication_overlap_title_fallback` — normalised title match counted
- `test_coauthor_overlap_empty` — no coauthors returns UNAVAILABLE
- `test_temporal_no_overlap` — non-overlapping year ranges score 0
- `test_temporal_full_overlap` — contained range scores 1.0
- `test_scoring_renormalises_missing_signals` — absent signals redistributed
- `test_scoring_all_unavailable_returns_none` — no available signals → None score

---

### `test_author_resolution_service.py`
Integration tests for the resolution decision logic.

- `test_auto_resolution_high_score` — high score + margin → auto_selected
- `test_manual_required_low_margin` — high score but insufficient margin
- `test_unresolved_low_score` — score < 0.45 → unresolved
- `test_resolution_persisted_to_db` — resolution stored in author_resolutions
- `test_evidence_rows_stored` — author_resolution_evidence populated
- `test_author_created_on_auto_resolve` — authors table entry created
- `test_external_id_linked` — author_external_ids row inserted
- `test_mark_unresolved_override` — mark_unresolved=True overrides scoring

---

### `test_author_resolution_api.py`
HTTP-level tests for author resolution endpoints.

- `test_post_creates_resolution` — POST returns resolution_id and status
- `test_get_returns_resolution` — GET /author-resolutions/{id} works
- `test_patch_manual_selection` — PATCH with candidate_id updates status
- `test_patch_mark_unresolved` — PATCH mark_unresolved changes status
- `test_get_evidence` — /evidence endpoint returns signal rows
- `test_resolution_not_found_404` — invalid ID returns 404
- `test_candidate_validation_mismatch` — wrong candidate returns 400

---

### `test_author_resolution_migration.py`
Tests that the Alembic migration creates all required tables and columns.

- `test_migration_creates_author_tables` — all 9 tables exist post-migration
- `test_alembic_version_row` — version table has correct revision stamp

---

### `test_annotation_workflow.py`
End-to-end tests for human-in-the-loop review workflow.

- `test_present_candidates_for_manual_review` — candidates presented correctly
- `test_manual_select_then_search` — select candidate, then trigger search
- `test_unresolved_blocks_search` — unresolved resolution returns appropriate message
- `test_resolution_id_in_search_injects_candidate` — resolution_id passed to /search applies candidate

---

### `test_api_defects_regression.py`
Regression tests for API bugs identified and fixed during evaluation.

- `test_search_candidates_requires_name_param` — missing name → 422
- `test_search_candidates_name_min_length` — 1-char name → 422
- `test_evidence_search_empty_query_rejected` — empty query handled
- `test_metrics_endpoint_returns_counts` — /metrics responds correctly

---

### `test_scholarly_retrieval.py`
Tests for ChromaDB retrieval and Gemini integration.

- `test_timeout_falls_back_and_smoke_preflight_never_sends_without_configuration` — unconfigured key uses fallback
- `test_smoke_command_reports_synthetic_validated_result_without_network` — mock Gemini response parsed correctly
- `test_smoke_does_not_call_fallback_claims_provider_validated` — valid claims prevent fallback
- `test_retrieval_similarity_floor_and_title_dedup` — min_score=0.35 + title dedup verified

---

### `test_evaluation_benchmark.py`
Tests the evaluation framework correctness (not production code).

- `test_evaluation_dataset_splits_correctly` — train/test split is stable
- `test_freeze_manifest_idempotent` — sealed manifest doesn't change

---

## 3. Running the Tests

```bash
cd "/Users/nileshlalwani/Desktop/FINAL YEAR PROJECT/academic-search"
backend/venv/bin/python -m pytest backend/tests/ -v
```

**Run a single file**:
```bash
backend/venv/bin/python -m pytest backend/tests/test_author_resolution_service.py -v
```

**With coverage**:
```bash
backend/venv/bin/python -m pytest backend/tests/ --cov=backend --cov-report=term-missing
```

---

## 4. Test Configuration (`conftest.py`)

```python
@pytest.fixture
async def db():
    # Creates in-memory SQLite database
    # Runs all migrations
    # Yields session
    # Tears down after test
    ...

@pytest.fixture
def app():
    # Returns test FastAPI app with override database
    ...
```

All tests use an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`) that is fresh for each test function. No production database is touched.

