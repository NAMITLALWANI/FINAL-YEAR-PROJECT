# HAMMER — Data Models

## 1. Database Overview

- **Engine**: SQLite (async via `aiosqlite`)
- **ORM**: SQLAlchemy 2.0 mapped columns
- **File**: `backend/academic_search.db`
- **Tables**: 16 (7 legacy + 9 author-resolution)
- **Migration**: Alembic (`alembic/versions/20260907_01_author_resolution_foundation.py`)

### Current Row Counts

| Table | Rows | Notes |
|-------|------|-------|
| `publications` | 454 | Merged canonical records |
| `source_records` | 2,053 | Raw ingested records |
| `duplicate_groups` | 960 | Merge group audit log |
| `similarity_logs` | 133 | Pairs with score ≥ 0.70 |
| `cache_entries` | 18 | HTTP response cache |
| `scholar_cache` | 2 | Scholar-specific cache |
| `circuit_breaker_state` | 4 | Per-source breaker state |
| `author_candidates` | 15 | OpenAlex candidates fetched |
| `author_resolutions` | 2 | Resolution decisions |
| `author_resolution_evidence` | 75 | Signal-level evidence |
| `authors` | 1 | Resolved author entities |
| `author_external_ids` | 1 | Source ID links |
| `author_affiliations` | 0 | (populated on resolution) |
| `author_aliases` | 0 | (populated on resolution) |
| `publication_authorships` | 0 | (populated on resolution) |
| `alembic_version` | 1 | Migration state |

---

## 2. Core Tables — Legacy (Created by `init_db`)

### `source_records`
Raw ingested record from any connector.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `source` | TEXT | `openalex`, `dblp`, `arxiv`, `crossref`, `scholar`, `faculty_page` |
| `source_id` | TEXT | Source-specific ID |
| `title` | TEXT | Normalised title |
| `authors_json` | TEXT | JSON list of author strings |
| `year` | INTEGER | Publication year |
| `doi` | TEXT | Lowercased DOI |
| `abstract` | TEXT | Cleaned abstract |
| `venue` | TEXT | Journal/conference name |
| `citations` | INTEGER | Citation count at ingestion |
| `url` | TEXT | Source URL |
| `raw_json` | TEXT | Complete raw API response |
| `canonical_id` | TEXT | Deterministic hash ID |
| `created_at` | DATETIME | Ingestion timestamp |

**Unique constraint**: `(source, source_id)`

---

### `publications`
Merged canonical publication after deduplication.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `canonical_id` | TEXT UNIQUE | DOI-hash or title-hash |
| `title` | TEXT | Best available title |
| `authors` | TEXT | JSON list (from best source) |
| `year` | INTEGER | |
| `abstract` | TEXT | From highest-priority source |
| `abstract_source` | TEXT | Which source provided abstract |
| `doi` | TEXT | Unified DOI |
| `doi_source` | TEXT | Which source provided DOI |
| `venue` | TEXT | |
| `venue_source` | TEXT | |
| `citations` | INTEGER | Maximum across sources |
| `citations_source` | TEXT | |
| `best_source` | TEXT | Highest-priority source in group |
| `confidence_score` | FLOAT | 1.0 (single-source) or 0.9 (merged) |
| `source_count` | INTEGER | Number of contributing sources |
| `source_list` | TEXT | JSON list of source names |
| `norm_title` | TEXT | Normalised title for dedup |
| `created_at` | DATETIME | |

---

### `duplicate_groups`
Audit log linking source records to merged publications.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `publication_id` | INTEGER FK → publications | |
| `source_record_ids` | TEXT | JSON list of `source_records.id` |
| `created_at` | DATETIME | |

---

### `similarity_logs`
Pairwise similarity scores for all record pairs with score ≥ 0.70.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `record1_id` | TEXT | source_records.id |
| `record2_id` | TEXT | source_records.id |
| `title_sim` | FLOAT | token_sort_ratio / 100 |
| `author_sim` | FLOAT | Jaccard on author keys |
| `year_match` | BOOLEAN | |year1-year2| ≤ 1 |
| `score` | FLOAT | 0.6×title + 0.3×author + 0.1×year |
| `decision` | TEXT | `MERGED` or `SEPARATE` |

---

### `cache_entries`
HTTP response cache for connector API calls.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `source` | TEXT | Connector name |
| `query_hash` | TEXT | SHA-256 of normalised query |
| `response_json` | TEXT | Serialised connector response |
| `expires_at` | DATETIME | TTL from `CACHE_TTL_HOURS` |

**Unique constraint**: `(source, query_hash)`

---

### `circuit_breaker_state`
Per-source failure tracking.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `source` | TEXT UNIQUE | Connector name |
| `failure_count` | INTEGER | Consecutive failures |
| `last_failure_at` | DATETIME | |
| `state` | TEXT | `closed`, `open`, `half_open` |
| `reset_at` | DATETIME | When to retry |

---

## 3. Author Resolution Tables (Created by Alembic)

### `authors`
Resolved author entity (one per unique real person).

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PK | UUID |
| `display_name` | TEXT | |
| `normalized_name` | TEXT | |
| `resolution_state` | TEXT | `resolved`, `unresolved`, `pending` |
| `created_at` | DATETIME | |

---

### `author_external_ids`
Links an `Author` to a source-specific profile ID.

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PK | UUID |
| `author_id` | TEXT FK → authors | |
| `source` | TEXT | e.g. `openalex` |
| `external_id` | TEXT | e.g. `A5000000123` |
| `provenance_json` | TEXT | Identity strength and notes |
| `created_at` | DATETIME | |

**Unique constraint**: `(source, external_id)`

---

### `author_candidates`
OpenAlex author profiles retrieved during candidate generation.

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PK | UUID |
| `source` | TEXT | `openalex` |
| `source_author_id` | TEXT | OpenAlex author ID |
| `query_original` | TEXT | Input query string |
| `query_normalized` | TEXT | casefolded |
| `display_name` | TEXT | |
| `normalized_name` | TEXT | |
| `works_count` | INTEGER | |
| `affiliation_json` | TEXT | JSON list of affiliation dicts |
| `aliases_json` | TEXT | JSON list of alternative names |
| `raw_payload_json` | TEXT | Complete OpenAlex author response |
| `retrieved_at` | DATETIME | |

---

### `author_resolutions`
A resolution decision record for one (query, institution_hint) pair.

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PK | UUID |
| `query_original` | TEXT | |
| `query_normalized` | TEXT | |
| `institution_hint` | TEXT | Optional |
| `status` | TEXT | `auto_selected`, `manual_selected`, `manual_selection_required`, `unresolved`, `expired` |
| `selected_candidate_id` | TEXT FK → author_candidates | Null if unresolved |
| `author_id` | TEXT FK → authors | Created on auto/manual select |
| `top_score` | FLOAT | [0, 1] |
| `second_score` | FLOAT | [0, 1] |
| `dominance_ratio` | FLOAT | top/second |
| `score_margin` | FLOAT | top - second |
| `confidence_level` | TEXT | `engineering_heuristic` |
| `decision_reason` | TEXT | Human-readable explanation |
| `resolver_version` | TEXT | `v1` |
| `scoring_version` | TEXT | `v1` |
| `threshold_version` | TEXT | `v1` |
| `created_at` | DATETIME | |
| `resolved_at` | DATETIME | |
| `expires_at` | DATETIME | |

**CheckConstraints**: status enum, top/second score in [0,1]  
**Indexes**: `(query_normalized, status)`, `author_id`, `expires_at`

---

### `author_resolution_evidence`
One row per signal × candidate for a resolution. Full audit trail.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `resolution_id` | TEXT FK | |
| `candidate_id` | TEXT FK | |
| `signal_name` | TEXT | One of the 5 evidence signals |
| `raw_value_json` | TEXT | Exact inputs to the scoring function |
| `normalized_score` | FLOAT | [0, 1] or NULL if unavailable |
| `weight` | FLOAT | (unused in v1 — stored as NULL) |
| `weighted_contribution` | FLOAT | signal weight × score / total_weight |
| `availability` | TEXT | `available`, `unavailable`, `not_applicable` |
| `explanation` | TEXT | Human-readable signal explanation |
| `source_provenance_json` | TEXT | Which API fields were used |
| `created_at` | DATETIME | |

**Unique constraint**: `(resolution_id, candidate_id, signal_name)`

---

## 4. Entity Relationship Summary

```
authors ──< author_external_ids
       ──< author_resolutions
       ──< publication_authorships

author_resolutions ──< author_resolution_evidence >── author_candidates
                   ──> author_candidates (selected_candidate)

publications ──< duplicate_groups
            ──< publication_authorships
            ──< source_records (via duplicate_groups)
```

