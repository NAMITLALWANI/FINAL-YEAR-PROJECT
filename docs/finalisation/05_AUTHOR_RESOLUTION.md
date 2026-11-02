# HAMMER — Author Resolution V1

## 1. Problem Statement

Academic name disambiguation is a well-known challenge: "J. Lee" may refer to dozens of distinct researchers. Without resolution, a publication search returns a mix of papers from multiple real individuals.

HAMMER implements a conservative, explainable author identity resolution system that:
1. Generates structured candidate profiles from OpenAlex
2. Extracts five deterministic evidence signals per candidate
3. Applies a weighted scoring model
4. Makes an auto-resolution decision only when evidence is unambiguous
5. Falls back to human-in-the-loop when the evidence is insufficient
6. Records full evidence provenance for audit

---

## 2. Candidate Generation

**Module**: `services/author_candidates.py`  
**API Used**: OpenAlex `/authors` search endpoint

```python
class OpenAlexCandidateService:
    async def generate(self, input: AuthorCandidateInput) -> CandidateResult:
        url = f"https://api.openalex.org/authors?search={query}&per_page=10"
        ...
        return CandidateResult(candidates=[OpenAlexCandidate.from_openalex(r, input) for r in raw])
```

### OpenAlexCandidate Fields

| Field | Source | Used By |
|-------|--------|---------|
| `display_name` | `display_name` | name_similarity |
| `aliases` | `display_name_alternatives` | name_similarity |
| `affiliations` | `affiliations[].institution.display_name` | institution_similarity |
| `sample_publications` | `works` (sampled) | publication_overlap |
| `coauthor_summary` | aggregated from works | coauthor_overlap |
| `years_active_start/end` | `counts_by_year` | temporal_compatibility |
| `works_count` | `works_count` | ranking heuristic |
| `source_author_id` | `id` (OpenAlex ID) | resolution foreign key |

---

## 3. Five Evidence Signals

All signals are computed deterministically and return a normalised score in [0, 1] or `None` if unavailable.

### Signal 1: Name Similarity (weight 0.35)

```python
def name_similarity(candidate, context=None):
    variants = [candidate.display_name, *candidate.aliases]
    scores = [fuzz.token_sort_ratio(normalize_name(query), normalize_name(v)) / 100
              for v in variants]
    score = max(scores)
```

Uses `rapidfuzz.fuzz.token_sort_ratio` which is word-order invariant. Compares the query name against the OpenAlex display name AND all aliases.

**Example**: Query "G Hinton" vs candidate "Geoffrey Hinton" + aliases ["G.E. Hinton", "G Hinton"] → score 1.0 (exact alias match)

### Signal 2: Institution Similarity (weight 0.25)

```python
def institution_similarity(candidate, context=None):
    hints = _values(context, "institution_hints")   # from request
    institutions = [item["name"] for item in candidate.affiliations]
    score = max(fuzz.token_set_ratio(normalize_name(h), normalize_name(i)) / 100
                for h in hints for i in institutions)
```

`token_set_ratio` is robust to abbreviations: "University of Toronto" vs "U of T" scores high.

Availability: `UNAVAILABLE` if no institution hint was provided in the request.

### Signal 3: Publication Overlap (weight 0.20)

```python
def publication_overlap(candidate, context=None):
    # Intersection of DOIs + normalised titles
    doi_matches = query_dois & candidate_dois
    title_matches = query_titles & candidate_titles
    matched = len(doi_matches | title_matches)
    score = min(1.0, matched / comparable)
```

Requires the request context to include `publications` (list of known papers with DOI/title).

### Signal 4: Coauthor Overlap (weight 0.10)

```python
def coauthor_overlap(candidate, context=None):
    query_coauthors = {normalize_name(v) for v in _values(context, "coauthors")}
    candidate_coauthors = {normalize_name(item.get("name", item)) for item in candidate.coauthor_summary}
    overlap = query_coauthors & candidate_coauthors
    score = len(overlap) / min(len(query_coauthors), len(candidate_coauthors))
```

### Signal 5: Temporal Compatibility (weight 0.10)

```python
def temporal_compatibility(candidate, context=None):
    overlap = max(0, min(end, c_end) - max(start, c_start) + 1)
    span = max(1, min(end - start + 1, c_end - c_start + 1))
    score = min(1.0, overlap / span)
```

Compares the requested active-year range with the candidate's OpenAlex `counts_by_year` range.

---

## 4. Weighted Scoring

**Module**: `services/author_scoring.py`

```python
def score_evidence(evidence, weights=None):
    # Only available signals contribute
    available = [e for e in evidence if e.normalized_score is not None and e.signal_name in configured]
    total_weight = sum(configured[e.signal_name] for e in available)
    contributions = {
        e.signal_name: (configured[e.signal_name] * e.normalized_score) / total_weight
        for e in available
    }
    return CandidateScore(round(sum(contributions.values()), 6), len(available), contributions)
```

**Key property**: Weights are re-normalised over *available* signals only. If institution hint is absent, its 0.25 weight is distributed proportionally to the other available signals. This prevents artificially low scores due to missing context.

---

## 5. Decision Logic

**Module**: `services/author_resolution.py::decide()`

```
Three gates for AUTO_RESOLVED:
  Gate 1: top_score >= 0.75          (absolute quality threshold)
  Gate 2: margin >= 0.15             (separation from second candidate)
  Gate 3: dominance_ratio >= 1.35    (top/second score ratio)
  Gate 4: available_signals >= 2     (minimum evidence coverage)

All four must pass → AUTO_RESOLVED (selected_candidate = top candidate)
Gate 1+2+3 pass but Gate 4 fails → MANUAL_SELECTION_REQUIRED
top_score >= 0.45 but gates fail → MANUAL_SELECTION_REQUIRED
top_score < 0.45 → UNRESOLVED
```

The conservative design deliberately errs toward `MANUAL_SELECTION_REQUIRED` to avoid false disambiguation — an incorrect auto-resolution would silently contaminate all downstream publication results.

---

## 6. Resolution Outcomes and Human-in-the-Loop

| Status | Meaning | Next Action |
|--------|---------|-------------|
| `auto_selected` | High-confidence automatic resolution | Search proceeds with selected candidate |
| `manual_selection_required` | Evidence insufficient for auto-resolve | UI presents candidate list for human selection |
| `unresolved` | No viable candidate | Search returns empty with explanation |
| `manual_selected` | Human chose a specific candidate | Search proceeds with chosen candidate |
| `expired` | Resolution exceeded TTL | Re-resolve required |

### Manual Selection API

```http
PATCH /author-resolutions/{resolution_id}
{
  "selected_candidate_id": "A5000000123",
  "reason": "Matched faculty page profile"
}
```

### Mark Unresolved API

```http
PATCH /author-resolutions/{resolution_id}
{
  "mark_unresolved": true,
  "reason": "All candidates are incorrect"
}
```

---

## 7. Evidence Audit Trail

For every resolution, the database stores:

- `author_resolutions` — resolution record with scores, decision, versions
- `author_resolution_evidence` — one row per signal × candidate with:
  - `signal_name`, `availability`, `normalized_score`, `weight`, `weighted_contribution`
  - `raw_value_json` — exact inputs used
  - `explanation` — human-readable description
  - `source_provenance_json` — which API field was used

This makes every resolution **fully auditable and reproducible**.

---

## 8. Version Pinning

All resolution records are stamped with:

| Field | Default | Purpose |
|-------|---------|---------|
| `resolver_version` | `v1` | Algorithm version |
| `scoring_version` | `v1` | Weight schema version |
| `threshold_version` | `v1` | Threshold set version |

Changing any of these constants in `config.py` creates a new version namespace without invalidating historical records.

