"""Deterministic, provenance-preserving author candidate evidence extractors."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from rapidfuzz import fuzz

from pipeline.normalize import normalized_title_for_compare
from services.author_candidates import OpenAlexCandidate, normalize_name


AVAILABLE = "available"
UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class Evidence:
    signal_name: str
    availability: str
    normalized_score: float | None
    raw_value: dict[str, Any]
    explanation: str
    provenance: dict[str, Any]

    def as_db_values(self) -> dict[str, Any]:
        return {
            "signal_name": self.signal_name,
            "availability": self.availability,
            "normalized_score": self.normalized_score,
            "raw_value_json": json.dumps(self.raw_value),
            "explanation": self.explanation,
            "source_provenance_json": json.dumps(self.provenance),
        }


def _values(context: dict[str, Any] | None, key: str) -> list[str]:
    raw = (context or {}).get(key)
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    return [str(value) for value in raw if isinstance(value, (str, int, float))]


def name_similarity(candidate: OpenAlexCandidate, context: dict[str, Any] | None = None) -> Evidence:
    variants = [candidate.display_name, *candidate.aliases]
    query = candidate.query_original
    if not query.strip() or not variants:
        return Evidence("name_similarity", UNAVAILABLE, None, {}, "No comparable name data.", {"source": "openalex"})
    scores = [fuzz.token_sort_ratio(normalize_name(query), normalize_name(value)) / 100 for value in variants]
    score = max(scores)
    return Evidence(
        "name_similarity", AVAILABLE, score,
        {"query": query, "candidate_names": variants, "best_score": score},
        f"Best normalized name similarity against OpenAlex profile: {score:.2f}.",
        {"candidate_source": "openalex", "fields": ["display_name", "aliases"]},
    )


def institution_similarity(candidate: OpenAlexCandidate, context: dict[str, Any] | None = None) -> Evidence:
    hints = _values(context, "institution_hints")
    if not hints:
        return Evidence("institution_similarity", UNAVAILABLE, None, {}, "No institution hint was provided.", {"source": "request"})
    institutions = [item["name"] for item in candidate.affiliations if item.get("name")]
    if not institutions:
        return Evidence("institution_similarity", UNAVAILABLE, None, {"hints": hints}, "Candidate has no OpenAlex affiliation data.", {"source": "openalex"})
    score = max(fuzz.token_set_ratio(normalize_name(hint), normalize_name(inst)) / 100 for hint in hints for inst in institutions)
    return Evidence(
        "institution_similarity", AVAILABLE, score,
        {"hints": hints, "candidate_affiliations": institutions, "best_score": score},
        f"Best institution/affiliation similarity: {score:.2f}.",
        {"request_source": "institution_hints", "candidate_source": "openalex.affiliations"},
    )


def publication_overlap(candidate: OpenAlexCandidate, context: dict[str, Any] | None = None) -> Evidence:
    query_publications = (context or {}).get("publications")
    candidate_publications = candidate.sample_publications
    if not isinstance(query_publications, list) or not isinstance(candidate_publications, list):
        return Evidence("publication_overlap", UNAVAILABLE, None, {}, "Publication metadata is unavailable for comparison.", {"source": "request/openalex"})
    query_dois = {str(p.get("doi", "")).lower().strip() for p in query_publications if isinstance(p, dict) and p.get("doi")}
    candidate_dois = {str(p.get("doi", "")).lower().strip() for p in candidate_publications if isinstance(p, dict) and p.get("doi")}
    doi_matches = query_dois & candidate_dois
    query_titles = {normalized_title_for_compare(str(p.get("title", ""))) for p in query_publications if isinstance(p, dict) and p.get("title")}
    candidate_titles = {normalized_title_for_compare(str(p.get("title", ""))) for p in candidate_publications if isinstance(p, dict) and p.get("title")}
    title_matches = query_titles & candidate_titles
    comparable = max(1, min(len(query_dois | query_titles), len(candidate_dois | candidate_titles)))
    matched = len(doi_matches | title_matches)
    score = min(1.0, matched / comparable)
    return Evidence("publication_overlap", AVAILABLE, score, {"doi_matches": sorted(doi_matches), "title_matches": sorted(title_matches), "matched": matched, "comparable": comparable}, f"Publication overlap: {matched} matching DOI/title record(s).", {"request_source": "publications", "candidate_source": "openalex.sample_publications"})


def coauthor_overlap(candidate: OpenAlexCandidate, context: dict[str, Any] | None = None) -> Evidence:
    query_coauthors = {normalize_name(value) for value in _values(context, "coauthors")}
    candidate_coauthors = {normalize_name(str(item.get("name", item))) for item in (candidate.coauthor_summary or []) if isinstance(item, (str, dict)) and str(item.get("name", item) if isinstance(item, dict) else item).strip()}
    if not query_coauthors or not candidate_coauthors:
        return Evidence("coauthor_overlap", UNAVAILABLE, None, {}, "Coauthor metadata is unavailable for comparison.", {"source": "request/openalex"})
    overlap = query_coauthors & candidate_coauthors
    score = len(overlap) / min(len(query_coauthors), len(candidate_coauthors))
    return Evidence("coauthor_overlap", AVAILABLE, score, {"overlap": sorted(overlap), "request_count": len(query_coauthors), "candidate_count": len(candidate_coauthors)}, f"Coauthor overlap: {len(overlap)} shared normalized name(s).", {"request_source": "coauthors", "candidate_source": "openalex.coauthors"})


def temporal_compatibility(candidate: OpenAlexCandidate, context: dict[str, Any] | None = None) -> Evidence:
    requested_start = (context or {}).get("active_year_start")
    requested_end = (context or {}).get("active_year_end")
    if requested_start is None or requested_end is None or candidate.years_active_start is None or candidate.years_active_end is None:
        return Evidence("temporal_compatibility", UNAVAILABLE, None, {}, "Active-year range is unavailable for comparison.", {"source": "request/openalex"})
    start, end = int(requested_start), int(requested_end)
    c_start, c_end = candidate.years_active_start, candidate.years_active_end
    overlap = max(0, min(end, c_end) - max(start, c_start) + 1)
    span = max(1, min(end - start + 1, c_end - c_start + 1))
    score = min(1.0, overlap / span)
    return Evidence("temporal_compatibility", AVAILABLE, score, {"request_range": [start, end], "candidate_range": [c_start, c_end], "overlap_years": overlap}, f"Active-year compatibility: {score:.2f}.", {"request_source": "active_years", "candidate_source": "openalex.counts_by_year"})


def extract_evidence(candidate: OpenAlexCandidate, context: dict[str, Any] | None = None) -> list[Evidence]:
    return [
        name_similarity(candidate, context), institution_similarity(candidate, context),
        publication_overlap(candidate, context), coauthor_overlap(candidate, context),
        temporal_compatibility(candidate, context),
    ]