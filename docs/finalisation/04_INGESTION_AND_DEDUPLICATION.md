# HAMMER — Ingestion, Normalisation & Deduplication

## 1. Multi-Source Ingestion Architecture

HAMMER fans out search requests to up to 6 scholarly data sources in parallel using `asyncio.gather`. Each connector inherits from `BaseConnector` (`connectors/base.py`) which implements a cache-first fetch-and-store template.

### Active Sources (Default Configuration)

| Source | Type | Auth Required | Notes |
|--------|------|---------------|-------|
| OpenAlex | Free REST API | No (polite pool mailto) | Primary source for author metadata |
| DBLP | Free REST API | No | Computer science bibliography |
| ArXiv | Atom feed | No | Preprints; 3s delay between requests |
| Crossref | Free REST API | No (polite pool mailto) | DOI-authoritative, highest field trust |
| Scholar | Scraper | No | Disabled by default (rate-limited) |
| Faculty Scraper | HTML scraper | No | Disabled by default |

### Connector Interface

Each connector implements:
```python
class BaseConnector:
    async def fetch(self, author_name: str, **kwargs) -> tuple[list[dict], dict]:
        # 1. Check cache (CacheEntry table)
        # 2. If cache miss: call _fetch_impl()
        # 3. Store result to cache
        # 4. Return (records, status_dict)
    
    async def _fetch_impl(self, author_name: str, **kwargs) -> list[dict]:
        # Source-specific implementation
        ...
```

All raw records are returned as `dict` with a standard set of fields:
`source`, `source_id`, `title`, `authors`, `year`, `doi`, `abstract`, `venue`, `citations`, `url`, `raw_json`

---

## 2. Normalisation Pipeline

**Module**: `backend/pipeline/normalize.py`

Every raw record passes through `normalize(raw: dict) → CanonicalRecord`.

### Field-by-field normalisation

| Field | Raw Input Handling | Output |
|-------|--------------------|--------|
| `title` | Strip HTML tags, collapse whitespace | `str` |
| `abstract` | Strip HTML tags, collapse whitespace | `str` |
| `authors` | Accept `list[str]` or comma-separated `str` | `list[str]` |
| `year` | Integer or string with regex `\b(19|20)\d{2}\b` | `Optional[int]` |
| `doi` | Lowercased, stripped | `str` (empty string if missing) |
| `venue` | Strip HTML | `str` |
| `citations` | Cast to `int`, default 0 on failure | `int` |

### Canonical ID Generation

```python
def _make_canonical_id(doi, source_id, title) -> str:
    if doi:
        return "doi_" + sha256(doi.lower().strip().encode()).hexdigest()[:16]
    if source_id:
        return "sid_" + sha256(source_id.encode()).hexdigest()[:16]
    norm = _normalize_title(title)
    return "ttl_" + sha256(norm.encode()).hexdigest()[:16]
```

The canonical ID is **stable across ingestion runs** for the same logical publication. DOI-based IDs are preferred as DOIs are globally unique.

### Author Key Normalisation

For deduplication, authors are reduced to `FIRST_INITIAL_LASTNAME` format:
```python
def normalize_author_key(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0].upper()}_{parts[-1].upper()}"
    return name.upper().replace(" ", "_")
```

"Geoffrey E. Hinton" → "G_HINTON", "Yann LeCun" → "Y_LECUN"

This prevents false positives on common surnames while being robust to middle-name variations.

---

## 3. Deduplication Algorithm

**Module**: `backend/pipeline/deduplicate.py`

### Algorithm Overview

```
Input:  list[CanonicalRecord]
Output: (list[MergedPublication], list[SimilarityEntry])

1. Exact DOI match         → immediate merge
2. Exact normalised title  → immediate merge
3. Blocking pass           → candidate pair selection
4. Fuzzy scoring           → source-pair threshold comparison
5. Union-Find grouping     → connected components
6. Field merging           → _merge_group() per component
```

### Blocking Pass

Before fuzzy scoring (O(n²) in worst case), a blocking pass pre-filters candidate pairs:

```python
def _blocking_pass(r1, r2) -> bool:
    if r1.doi and r1.doi == r2.doi: return True
    if _year_match(r1.year, r2.year): return True           # |y1-y2| <= 1
    if author_key_set(r1.authors) & author_key_set(r2.authors): return True
    if t1[:5] and t1[:5] == t2[:5]: return True             # title 5-char prefix
    return False
```

Blocking ensures the expensive `fuzz.token_sort_ratio` is only called on pairs that share at least one cheap anchor.

### Fuzzy Score Composition

```
score = 0.60 × title_sim + 0.30 × author_sim + 0.10 × year_match
```

- **title_sim**: `rapidfuzz.fuzz.token_sort_ratio` on normalised titles (word-order invariant)
- **author_sim**: Jaccard overlap on `author_key_set` (INITIAL_LASTNAME keys)
- **year_match**: 1.0 if `|year1 - year2| ≤ 1`, else 0.0

### Source-Pair Thresholds

| Source Pair | Threshold | Rationale |
|-------------|-----------|-----------|
| `scholar` + `crossref` | 0.95 | Scholar is noisy; very high confidence required |
| `scholar` + `openalex` | 0.93 | Same rationale |
| `openalex` + `crossref` | 0.80 | Both high-quality; lenient threshold acceptable |
| Any + `scholar`/`faculty_page` | 0.92 | Scholar/scraper data quality concern |
| Default | 0.85 | Conservative baseline |

### Field Merging Strategy

When records are merged into a `MergedPublication`, fields are selected by **source priority** (Crossref=1, OpenAlex=2, DBLP=3, ArXiv=4):

```python
def _best_field(records, attr):
    sorted_recs = sorted(records, key=lambda r: SOURCE_PRIORITY.get(r.source, 99))
    for rec in sorted_recs:
        val = getattr(rec, attr, None)
        if val:
            return val, rec.source
    return "", ...
```

Exception: **citations** use `max()` across all sources (a paper's citation count is authoritative at its maximum known value).

### Confidence Score

- Single-source record: `confidence_score = 1.0`
- Multi-source merged: `confidence_score = 0.9`

This conservative assignment acknowledges that automatic merging carries inherent uncertainty.

---

## 4. Ingestion Idempotency

`search_service._persist_publications()` implements a three-tier idempotency guard to prevent duplicate records on repeated searches:

```python
# Tier 1: exact canonical_id match
existing = await db.execute(select(Publication).where(
    Publication.canonical_id == pub.canonical_id
))
if existing: continue (update if richer)

# Tier 2: DOI fallback (different canonical_id, same DOI)
if pub.doi:
    existing = await db.execute(select(Publication).where(
        Publication.doi == pub.doi
    ))

# Tier 3: normalised title fallback
norm_title = normalized_title_for_compare(pub.title)
existing = await db.execute(select(Publication).where(
    Publication.norm_title == norm_title
))
```

This ensures that running the same author search twice does not double the database.

---

## 5. Current Database State

| Metric | Value |
|--------|-------|
| `source_records` | 2,053 raw ingested records |
| `publications` | 454 merged canonical publications |
| `similarity_log` | entries for all MERGED + near-miss pairs |
| `duplicate_groups` | grouping log for audit |
| Dedup compression ratio | 2053 raw → 454 merged ≈ 4.5× reduction |

