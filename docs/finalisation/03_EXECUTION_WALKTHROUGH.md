# HAMMER — Execution Walkthrough

This document traces the complete lifecycle of the two primary workflows: a publication search and an author resolution. Each step maps directly to a function or class in the codebase.

---

## Walkthrough 1: `GET /search?name=Geoffrey+Hinton`

### Step 1 — Route entry (`main.py`)

```python
@app.get("/search")
@limiter.limit("10/minute")
async def search(
    request: Request,
    name: str = Query(..., min_length=2),
    resolution_id: str | None = Query(None),
    candidate_id: str | None = Query(None),
    candidate_source: str | None = Query(None),
    sources: str | None = Query(None),
    use_cache: bool = Query(True),
    disable_dedup: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    result = await run_search(
        author_name=name, author_id=candidate_id,
        author_source=candidate_source, db=db,
        requested_sources=requested, use_cache=use_cache,
        disable_dedup=disable_dedup,
    )
    return result
```

**What happens**: Rate limit checked (10/min). If `resolution_id` is provided, the previously resolved `selected_candidate_id` is injected as `candidate_id`. `run_search()` is awaited.

---

### Step 2 — Connector fan-out (`search_service.py`)

```python
async def run_search(author_name, author_id, author_source, db, ...):
    connectors = _get_active_connectors(requested_sources)
    tasks = [_fetch_from_connector(c, author_name, author_id, db) for c in connectors]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Active connectors** (by default): OpenAlex, DBLP, ArXiv, Crossref (Scholar and Faculty Page are disabled by flag).

Each `_fetch_from_connector()` call:
1. Checks circuit breaker state for the source
2. Calls `connector.fetch(author_name, db=db)`
3. Records success or failure into `CircuitBreakerState` table

---

### Step 3 — Normalisation (`pipeline/normalize.py`)

```python
def normalize(raw: dict) -> CanonicalRecord:
    title    = _strip_html(str(raw.get("title") or ""))
    abstract = _strip_html(str(raw.get("abstract") or ""))
    authors  = _parse_authors(raw.get("authors") or raw.get("authors_raw") or [])
    year     = _extract_year(raw.get("year") or raw.get("publication_year"))
    doi      = str(raw.get("doi") or "").strip().lower()
    ...
    return CanonicalRecord(source=..., source_id=..., ...)
```

The `canonical_id` is assigned deterministically:
- DOI present → `doi_` + SHA-256[:16] of lowercased DOI
- Otherwise → `sid_` + SHA-256[:16] of source_id  
- Otherwise → `ttl_` + SHA-256[:16] of normalised title

---

### Step 4 — Deduplication (`pipeline/deduplicate.py`)

```python
def deduplicate(records, exclusions=None):
    # union-find over n records
    for i in range(n):
        for j in range(i+1, n):
            if _blocking_pass(r1, r2):
                ts, as_, ym, score = _fuzzy_score(r1, r2)
                threshold = _threshold(r1.source, r2.source)
                if score >= threshold:
                    union(i, j)
    # group by root → _merge_group()
```

**Fuzzy score formula**: `0.6 × title_sim + 0.3 × author_sim + 0.1 × year_match`

**Source-pair thresholds**:
- scholar + crossref: 0.95
- scholar + openalex: 0.93
- openalex + crossref: 0.80 (lenient — both high-quality sources)
- any with scholar/faculty_page: 0.92
- default: 0.85

---

### Step 5 — Persistence (`search_service.py`)

```python
async def _persist_publications(merged_pubs, records, record_id_map, db):
    for pub in merged_pubs:
        # Idempotency guard: match by canonical_id, then DOI, then norm_title
        existing = await db.execute(
            select(Publication).where(Publication.canonical_id == pub.canonical_id)
        )
        if not existing.scalar_one_or_none():
            # check DOI fallback, then norm_title fallback
            ...
            db.add(new_publication)
```

The idempotency guard prevents duplicate database entries on repeated searches for the same author.

---

### Step 6 — Response assembly

The final response includes:
- `papers` — list of deduplicated, merged publications
- `source_statuses` — per-source success/fail/circuit_open
- `stats` — total raw records fetched, merged count, dedup savings

---

## Walkthrough 2: `POST /author-resolutions`

### Step 1 — Route entry

```python
@app.post("/author-resolutions", response_model=AuthorResolutionResponse)
async def create_author_resolution(body: AuthorResolutionRequest, db=Depends(get_db)):
    resolution = await author_resolution_service.create_resolution(
        author_name=body.author_name,
        institution_hint=body.institution_hint,
        context=body.context,
        db=db,
    )
    return format_resolution_response(resolution, ranked_candidates)
```

---

### Step 2 — Candidate generation (OpenAlex `/authors`)

```python
async def generate_and_rank(self, author_name, institution_hint, context, db):
    result = await self.candidate_service.generate(
        AuthorCandidateInput(author_name, institution_hint, context)
    )
    rows = await self.candidate_service.persist_candidates(result, db)
    return rows, rank_candidates(result.candidates, context), result.status
```

Candidates are fetched from the OpenAlex Author search API and stored in `author_candidates`.

---

### Step 3 — Evidence extraction (5 signals)

For each candidate:

```python
def extract_evidence(candidate, context=None) -> list[Evidence]:
    return [
        name_similarity(candidate, context),         # rapidfuzz token_sort_ratio
        institution_similarity(candidate, context),  # affiliation token_set_ratio
        publication_overlap(candidate, context),     # DOI + title set intersection
        coauthor_overlap(candidate, context),        # normalised name intersection
        temporal_compatibility(candidate, context),  # year-range overlap fraction
    ]
```

Each `Evidence` dataclass carries: `signal_name`, `availability`, `normalized_score`, `raw_value`, `explanation`, `provenance`.

---

### Step 4 — Weighted scoring

```python
# config.py weights
AUTHOR_SCORE_WEIGHTS = {
    "name_similarity":        0.35,
    "institution_similarity": 0.25,
    "publication_overlap":    0.20,
    "coauthor_overlap":       0.10,
    "temporal_compatibility": 0.10,
}

def score_evidence(evidence, weights=None):
    available = [e for e in evidence if e.normalized_score is not None and e.signal_name in configured]
    total_weight = sum(configured[e.signal_name] for e in available)
    contributions = {e.signal_name: (configured[e.signal_name] * e.normalized_score) / total_weight for e in available}
    return CandidateScore(round(sum(contributions.values()), 6), len(available), contributions)
```

Scores are re-normalised over only the *available* signals — if an institution hint is missing, the institution weight is redistributed proportionally.

---

### Step 5 — Decision logic (`decide()`)

```python
def decide(ranked: list[RankedCandidate]):
    if not ranked:
        return UNRESOLVED, None, None, None, None, "No candidates returned."
    top = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None
    
    margin = top.score.score - (second.score.score if second else 0.0)
    dominance = top.score.score / (second.score.score + 1e-9) if second else 999.0
    
    if (top.score.score >= 0.75 and margin >= 0.15
            and dominance >= 1.35
            and top.score.available_signals >= 2):
        return AUTO_RESOLVED, top.score.score, ...
    elif top.score.score >= 0.45:
        return MANUAL_SELECTION_REQUIRED, ...
    else:
        return UNRESOLVED, ...
```

The three-gate auto-resolution prevents false positives: high absolute score, clear separation from second candidate, and minimum signal coverage.

---

## Walkthrough 3: `POST /evidence/search`

### Request

```json
{"query": "deep learning neural networks attention mechanism", "top_k": 5}
```

### Step 1 — ChromaDB dense retrieval

```python
async def retrieve(query, top_k=5, filters=None, path=INDEX_PATH, min_score=0.35):
    return await asyncio.to_thread(_search, query.strip(), top_k, filters, path, min_score)
```

ChromaDB computes cosine similarity between the query embedding (all-MiniLM-L6-v2) and 449 stored document embeddings. Results with score < 0.35 are discarded.

Deduplication pass: if two results share `canonical_id`, `doi`, or normalised title, only the higher-scoring one is kept.

### Step 2 — Gemini explanation

```python
body = {
    "systemInstruction": {"parts": [{"text": system_prompt}]},
    "contents": [{"role": "user", "parts": [{"text": json.dumps(context)}]}],
    "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
}
response = await client.post(
    f"{base_url}/models/{model_path}:generateContent",
    headers={"x-goog-api-key": api_key},
    json=body,
)
```

`temperature=0` ensures deterministic outputs. `responseMimeType: application/json` forces structured output.

### Step 3 — Zero-trust citation validation

```python
valid_claims = []
for claim in claims:
    cited = claim.get("document_ids")
    if not isinstance(cited, list) or not cited:
        continue
    if any(doc_id not in hit_by_id for doc_id in cited):
        continue   # claim references a document that was NOT retrieved — rejected
    valid_claims.append({"text": claim["text"][:1000], "document_ids": cited})
```

Only claims that cite documents from the current retrieval set are included. The LLM cannot introduce hallucinated document references.

