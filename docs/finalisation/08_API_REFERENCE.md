# HAMMER — REST API Reference

**Base URL**: `http://localhost:8000`  
**Rate limits**: 10/minute on `/search`, 20/minute on `/search/candidates`  
**Auth**: None (local deployment)  
**Format**: All responses are `application/json`

---

## 1. Publication Search

### `GET /search`

Search for publications by author name. Fans out to all enabled connectors, normalises, deduplicates, and persists results.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | ✓ | Author name (min 2 chars) |
| `resolution_id` | string | | Use a prior resolution to filter by candidate |
| `candidate_id` | string | | Explicit source author ID |
| `candidate_source` | string | | Source of candidate_id (e.g. `openalex`) |
| `sources` | string | | Comma-separated source list (e.g. `openalex,dblp`) |
| `use_cache` | bool | | Default `true` — use cached responses |
| `disable_dedup` | bool | | Default `false` — skip deduplication |

**Example Request**
```http
GET /search?name=Geoffrey+Hinton&sources=openalex,crossref
```

**Example Response**
```json
{
  "papers": [
    {
      "canonical_id": "doi_a1b2c3d4e5f6a7b8",
      "title": "Deep Learning",
      "authors": ["Yann LeCun", "Yoshua Bengio", "Geoffrey Hinton"],
      "year": 2015,
      "doi": "10.1038/nature14539",
      "venue": "Nature",
      "citations": 60420,
      "best_source": "crossref",
      "source_count": 3,
      "source_list": ["crossref", "openalex", "dblp"],
      "confidence_score": 0.9
    }
  ],
  "source_statuses": {
    "openalex": {"status": "ok", "count": 47},
    "crossref": {"status": "ok", "count": 31}
  },
  "stats": {
    "total_raw": 78,
    "total_merged": 45,
    "dedup_savings": 33
  }
}
```

---

## 2. Author Candidate Selection

### `GET /search/candidates`

Returns OpenAlex author candidates for a name. Used to resolve ambiguous authors before a search.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | ✓ | Author name (min 2 chars) |
| `institution` | string | | Optional institution hint |

**Example Request**
```http
GET /search/candidates?name=Y+LeCun&institution=NYU
```

**Example Response**
```json
{
  "multiple_candidates": true,
  "auto_selected": false,
  "candidates": [
    {
      "source_author_id": "A2208157607",
      "display_name": "Yann LeCun",
      "institution": "New York University",
      "works_count": 402,
      "score": 0.97,
      "confidence": "High"
    }
  ]
}
```

---

## 3. Evidence Search

### `POST /evidence/search`

Semantic retrieval from the ChromaDB index + Gemini explanation.

**Request Body**
```json
{
  "query": "convolutional neural networks image recognition",
  "top_k": 5,
  "filters": {}
}
```

**Example Response**
```json
{
  "query": "convolutional neural networks image recognition",
  "hits": [
    {
      "document_id": "chroma_abc123",
      "canonical_id": "doi_a1b2c3d4",
      "title": "ImageNet Classification with Deep CNNs",
      "score": 0.82,
      "rank": 1,
      "year": 2012,
      "doi": "10.1145/3065386",
      "authors": ["Alex Krizhevsky", "Ilya Sutskever", "Geoffrey Hinton"]
    }
  ],
  "explanation": {
    "status": "generated",
    "provider": "gemini",
    "model": "gemini-3.5-flash",
    "summary": "Retrieved publication: ImageNet Classification...",
    "claims": [
      {
        "text": "The paper introduced AlexNet, a deep CNN architecture...",
        "document_ids": ["chroma_abc123"]
      }
    ],
    "latency_ms": 2100,
    "token_usage": {"promptTokenCount": 3200, "candidatesTokenCount": 601}
  }
}
```

---

## 4. Author Resolution

### `POST /author-resolutions`

Create a new author resolution, scoring OpenAlex candidates and making an auto/manual decision.

**Request Body**
```json
{
  "author_name": "Geoffrey Hinton",
  "institution_hint": "University of Toronto",
  "context": {
    "institution_hints": ["University of Toronto", "Google Brain"],
    "coauthors": ["Yann LeCun", "Yoshua Bengio"],
    "active_year_start": 1980,
    "active_year_end": 2023
  }
}
```

**Response**
```json
{
  "resolution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "auto_selected",
  "author_name": "Geoffrey Hinton",
  "top_score": 0.91,
  "second_score": 0.43,
  "score_margin": 0.48,
  "dominance_ratio": 2.12,
  "confidence_level": "engineering_heuristic",
  "decision_reason": "Auto-resolved: margin=0.48 exceeds 0.15, dominance=2.12 exceeds 1.35",
  "selected_candidate": {
    "source_author_id": "A2208157607",
    "display_name": "Geoffrey Hinton",
    "institution": "University of Toronto"
  },
  "candidates": [...],
  "evidence_summary": {
    "name_similarity": {"score": 1.0, "availability": "available"},
    "institution_similarity": {"score": 0.87, "availability": "available"},
    "publication_overlap": {"score": 0.0, "availability": "unavailable"},
    "coauthor_overlap": {"score": 0.5, "availability": "available"},
    "temporal_compatibility": {"score": 0.95, "availability": "available"}
  }
}
```

---

### `GET /author-resolutions/{resolution_id}`

Retrieve a stored resolution with full evidence.

---

### `PATCH /author-resolutions/{resolution_id}`

Update a resolution (manual selection or mark unresolved).

**Request Body (manual select)**
```json
{"selected_candidate_id": "uuid-here", "reason": "Matched faculty profile"}
```

**Request Body (mark unresolved)**
```json
{"mark_unresolved": true, "reason": "No candidates match the target person"}
```

---

### `GET /author-resolutions/{resolution_id}/evidence`

Returns full signal-level evidence for each candidate in a resolution.

---

## 5. Utility Endpoints

### `GET /publications/{pub_id}`

Returns a single publication by database ID.

---

### `GET /similarity-log/{pub_id}`

Returns all pairwise similarity scores for source records that were merged into a publication.

---

### `GET /metrics`

System-wide counts: publications, raw records, merges, source breakdown, circuit breaker states.

**Response**
```json
{
  "total_publications": 454,
  "total_raw_records": 2053,
  "total_merges": 133,
  "source_record_counts": {
    "openalex": 712,
    "dblp": 489,
    "crossref": 601,
    "arxiv": 251
  },
  "circuit_breakers": {
    "openalex": "closed",
    "dblp": "closed"
  }
}
```

---

### `GET /debug/raw-response`

Fetches raw unprocessed response from a single connector. Debug only.

**Query Parameters**: `source` (e.g. `openalex`), `query`

---

## 6. HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 404 | Resolution or publication not found |
| 422 | Validation error (missing required field or type mismatch) |
| 429 | Rate limit exceeded |
| 500 | Internal server error (see logs) |

