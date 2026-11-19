from __future__ import annotations
"""Deterministic, provenance-preserving author candidate evidence extractors.

Pure functions: they read only the candidate (including its stored enrichment) and the
query context. They never touch the network, the database or the vector index.

Every signal ends in one of these ``status`` values (``availability`` keeps the stored
'available' / 'unavailable' pair):

  observed                          a score exists; 0.0 means observed non-support
  unavailable_query_input_absent    the caller supplied nothing to compare
  unavailable_candidate_data_absent the candidate profile has nothing to compare
  unavailable_not_retrieved         enrichment was not performed for this context
  unavailable_retrieval_failed      enrichment was attempted and failed
  unavailable_inconclusive          retrieved, but the data cannot support a score
  unavailable_input_unresolvable    supplied input cannot be compared reliably

An unavailable signal is omitted from scoring; it is never treated as zero or as agreement.
"""

import json
from dataclasses import dataclass
from typing import Any

from rapidfuzz import fuzz

from author_resolution.candidates import OpenAlexCandidate, normalize_name
from author_resolution.context import (
    QueryContext, normalize_openalex_id, normalize_ror,
)
from author_resolution.enrichment_types import EMPTY, FAILED, OK

AVAILABLE = "available"
UNAVAILABLE = "unavailable"

OBSERVED = "observed"
QUERY_ABSENT = "unavailable_query_input_absent"
CANDIDATE_ABSENT = "unavailable_candidate_data_absent"
NOT_RETRIEVED = "unavailable_not_retrieved"
RETRIEVAL_FAILED = "unavailable_retrieval_failed"
INCONCLUSIVE = "unavailable_inconclusive"
UNRESOLVABLE = "unavailable_input_unresolvable"

SIGNAL_ORDER = (
    "name_similarity", "institution_similarity", "publication_overlap", "coauthor_overlap", "temporal_compatibility",
)
IDENTITY_BEARING = ("institution_similarity", "publication_overlap", "coauthor_overlap")


@dataclass(frozen=True)
class Evidence:
    signal_name: str
    availability: str
    normalized_score: float | None
    raw_value: dict[str, Any]
    explanation: str
    provenance: dict[str, Any]
    status: str = ""

    @property
    def observed(self) -> bool:
        return self.normalized_score is not None

    def as_db_values(self) -> dict[str, Any]:
        return {
            "signal_name": self.signal_name,
            "availability": self.availability,
            "normalized_score": self.normalized_score,
            "raw_value_json": json.dumps(self.raw_value),
            "explanation": self.explanation,
            "source_provenance_json": json.dumps({**self.provenance, "status": self.status}),
        }


def _unavailable(signal: str, status: str, explanation: str, raw: dict[str, Any] | None = None, provenance: dict[str, Any] | None = None) -> Evidence:
    return Evidence(signal, UNAVAILABLE, None, raw or {}, explanation, provenance or {}, status)


def _observed(signal: str, score: float, raw: dict[str, Any], explanation: str, provenance: dict[str, Any]) -> Evidence:
    return Evidence(signal, AVAILABLE, score, raw, explanation, provenance, OBSERVED)


def _ctx(context: Any) -> QueryContext:
    return QueryContext.from_any(context)


def name_similarity(candidate: OpenAlexCandidate, context: Any = None) -> Evidence:
    ctx = _ctx(context)
    variants = [candidate.display_name, *candidate.aliases]
    queries = [q for q in [candidate.query_original, *ctx.aliases] if q and q.strip()]
    if not queries:
        return _unavailable("name_similarity", QUERY_ABSENT, "No query name to compare.", provenance={"source": "request"})
    if not variants:
        return _unavailable("name_similarity", CANDIDATE_ABSENT, "No comparable name data.", provenance={"source": "openalex"})
    best = max(
        ((fuzz.token_sort_ratio(normalize_name(q), normalize_name(v)) / 100, q, v) for q in queries for v in variants),
        key=lambda item: item[0],
    )
    score = best[0]
    return _observed(
        "name_similarity", score,
        {"query": candidate.query_original, "query_names_compared": queries, "candidate_names": variants,
         "best_score": score, "best_query_name": best[1], "best_candidate_name": best[2]},
        f"Best normalized name similarity against OpenAlex profile: {score:.2f}.",
        {"candidate_source": "openalex", "fields": ["display_name", "aliases"]},
    )


def _institution_pair(q, aff: dict[str, Any]) -> tuple[float | None, str]:
    """Score one (query institution, candidate affiliation) pair. None = not comparable."""
    c_id = normalize_openalex_id(aff.get("source_institution_id"), "institution")
    c_ror = normalize_ror(aff.get("ror"))
    if q.ror and c_ror:
        return (1.0, "ror_equal") if q.ror == c_ror else (0.0, "ror_different")
    if q.openalex_id and c_id:
        return (1.0, "openalex_id_equal") if q.openalex_id == c_id else (0.0, "openalex_id_different")
    if q.name and aff.get("name"):
        # token_sort_ratio, not token_set_ratio: a token subset must not score 1.0.
        return fuzz.token_sort_ratio(normalize_name(q.name), normalize_name(aff["name"])) / 100, "name_token_sort"
    return None, "not_comparable"


def institution_similarity(candidate: OpenAlexCandidate, context: Any = None) -> Evidence:
    ctx = _ctx(context)
    if not ctx.institutions:
        return _unavailable("institution_similarity", QUERY_ABSENT, "No institution context was provided.", provenance={"source": "request"})
    affiliations = [a for a in candidate.affiliations if a.get("name")]
    if not affiliations:
        return _unavailable("institution_similarity", CANDIDATE_ABSENT, "Candidate has no OpenAlex affiliation data.",
                            {"query_institutions": [i.name or i.openalex_id or i.ror for i in ctx.institutions]}, {"source": "openalex"})
    results = [(score, basis, q, a) for q in ctx.institutions for a in affiliations for score, basis in [_institution_pair(q, a)] if score is not None]
    if not results:
        return _unavailable("institution_similarity", UNRESOLVABLE,
                            "Institution identifiers could not be compared with the candidate's affiliation records.",
                            provenance={"request_source": "institutions", "candidate_source": "openalex.affiliations"})
    score, basis, q, a = max(results, key=lambda item: item[0])
    return _observed(
        "institution_similarity", score,
        {"best_score": score, "basis": basis, "query_institution": {"name": q.name, "openalex_id": q.openalex_id, "ror": q.ror},
         "candidate_affiliation": {"name": a.get("name"), "openalex_id": a.get("source_institution_id"), "ror": a.get("ror")},
         "candidate_affiliations": [x["name"] for x in affiliations]},
        f"Best institution/affiliation similarity: {score:.2f} ({basis}).",
        {"request_source": "institutions", "candidate_source": "openalex.affiliations",
         "coverage_note": "last_known_institutions plus affiliations (OpenAlex documents ~10 years of affiliation years)"},
    )


def publication_overlap(candidate: OpenAlexCandidate, context: Any = None) -> Evidence:
    ctx = _ctx(context)
    signal = "publication_overlap"
    extra = {"ignored_title_only_entries": ctx.ignored_title_only} if ctx.ignored_title_only else {}
    if not ctx.has_publications:
        return _unavailable(signal, QUERY_ABSENT, "No publication identifiers (DOI or OpenAlex work ID) were provided.", extra, {"source": "request"})
    ev = candidate.publication_evidence
    if ev is None:
        return _unavailable(signal, NOT_RETRIEVED, "Publication links were not retrieved for this candidate.", extra, {"source": "openalex.works"})
    if ev.context_fingerprint != ctx.publication_fingerprint():
        return _unavailable(signal, NOT_RETRIEVED, "Stored publication links were retrieved for a different set of identifiers.", extra, {"source": "openalex.works"})
    prov = {"request_source": "publications", "candidate_source": "openalex.works", "retrieved_at": ev.retrieved_at, **ev.provenance}
    if ev.status == FAILED:
        return _unavailable(signal, RETRIEVAL_FAILED, f"Publication retrieval failed ({ev.error_code}).", {**extra, "error_code": ev.error_code}, prov)
    comparable = len(ev.comparable_work_ids)
    raw = {**extra, "comparable_works": comparable, "matched_work_ids": list(ev.matched_work_ids), "matched_dois": list(ev.matched_dois),
           "unresolved_identifiers": list(ev.unresolved_identifiers), "truncated_author_list_work_ids": list(ev.truncated_author_work_ids)}
    if ev.status == EMPTY or comparable == 0:
        return _unavailable(signal, INCONCLUSIVE, "None of the supplied publications could be compared (not found in OpenAlex or author lists truncated).", raw, prov)
    matched = len(ev.matched_work_ids)
    return _observed(signal, matched / comparable, raw, f"Publication overlap: {matched} of {comparable} supplied work(s) list this profile as an author.", prov)


def coauthor_overlap(candidate: OpenAlexCandidate, context: Any = None) -> Evidence:
    """Coauthor overlap from OpenAlex author IDs only.

    A name is not an identity: name-only query coauthors never contribute to the score. They are
    summarised as counts (no names, no candidate IDs) in ``raw_value["name_only_diagnostics"]``.
    """
    ctx = _ctx(context)
    signal = "coauthor_overlap"
    if not ctx.has_coauthors:
        return _unavailable(signal, QUERY_ABSENT, "No coauthors were provided.", provenance={"source": "request"})
    id_entries = [q for q in ctx.coauthors if q.openalex_id]
    name_only = [q for q in ctx.coauthors if not q.openalex_id and q.name]
    ev = candidate.coauthor_evidence
    by_id = {c["openalex_id"]: c for c in (ev.coauthors if ev else ()) if c.get("openalex_id")}
    diagnostics = {"supplied_total": len(ctx.coauthors), "supplied_with_openalex_id": len(id_entries), "name_only_supplied": len(name_only)}
    if ev is not None and name_only:
        by_name: dict[str, int] = {}
        for c in ev.coauthors:
            if c.get("display_name"):
                key = normalize_name(c["display_name"])
                by_name[key] = by_name.get(key, 0) + 1
        hits = [by_name.get(normalize_name(q.name), 0) for q in name_only]
        diagnostics.update({"name_only_unique_exact_name_in_sample": sum(1 for h in hits if h == 1),
                            "name_only_ambiguous_exact_name_in_sample": sum(1 for h in hits if h > 1),
                            "name_only_no_name_in_sample": sum(1 for h in hits if h == 0),
                            "name_only_used_for_scoring": False})
    raw = {"name_only_diagnostics": diagnostics}
    if not id_entries:
        return _unavailable(signal, UNRESOLVABLE, "Coauthors were supplied by name only; names are not identities and are not scored. Supply OpenAlex author IDs.", raw, {"source": "request"})
    if ev is None:
        return _unavailable(signal, NOT_RETRIEVED, "Candidate coauthors were not retrieved.", raw, {"source": "openalex.works"})
    prov = {"request_source": "coauthors", "candidate_source": "openalex.works", "retrieved_at": ev.retrieved_at, **ev.provenance}
    if ev.status == FAILED:
        return _unavailable(signal, RETRIEVAL_FAILED, f"Coauthor retrieval failed ({ev.error_code}).", {**raw, "error_code": ev.error_code}, prov)
    if ev.status == EMPTY or not ev.coauthors:
        return _unavailable(signal, INCONCLUSIVE, "No coauthors could be derived from the candidate's retrieved works.", {**raw, "works_examined": ev.works_examined}, prov)
    matches = [{"openalex_id": q.openalex_id, "basis": "openalex_id", "work_ids": by_id[q.openalex_id].get("work_ids", [])}
               for q in id_entries if q.openalex_id in by_id]
    raw.update({"query_ids_supplied": len(id_entries), "candidate_coauthors": len(by_id), "works_examined": ev.works_examined,
                "works_total": ev.works_total, "sample_complete": ev.complete, "matches": matches})
    if not matches and not ev.complete:
        return _unavailable(signal, INCONCLUSIVE, "No overlap in the bounded works sample; the sample does not cover all of the candidate's works.", raw, prov)
    score = min(1.0, len(matches) / min(len(id_entries), len(by_id)))
    return _observed(signal, score, raw, f"Coauthor overlap: {len(matches)} OpenAlex-ID match(es) from actual authorships.", prov)


def temporal_compatibility(candidate: OpenAlexCandidate, context: Any = None) -> Evidence:
    ctx = _ctx(context)
    signal = "temporal_compatibility"
    if not ctx.has_years:
        return _unavailable(signal, QUERY_ABSENT, "No active-year range was provided.", provenance={"source": "request"})
    c_start, c_end = candidate.years_active_start, candidate.years_active_end
    if c_start is None or c_end is None:
        return _unavailable(signal, CANDIDATE_ABSENT, "Candidate has no observed active-year range.", provenance={"source": "openalex"})
    start, end = ctx.active_year_start, ctx.active_year_end
    overlap = max(0, min(end, c_end) - max(start, c_start) + 1)
    raw = {"request_range": [start, end], "candidate_range": [c_start, c_end], "overlap_years": overlap}
    prov = {"request_source": "active_years", "candidate_source": "openalex.counts_by_year",
            "coverage_note": "candidate range is the min/max year present in counts_by_year; OpenAlex does not document that window"}
    if overlap == 0 and end < c_start:
        return _unavailable(signal, INCONCLUSIVE, "Requested years precede the candidate's observed range; earlier activity may fall outside the observed window.", raw, prov)
    span = max(1, min(end - start + 1, c_end - c_start + 1))
    score = min(1.0, overlap / span)
    return _observed(signal, score, raw, f"Active-year compatibility: {score:.2f}.", prov)


def extract_evidence(candidate: OpenAlexCandidate, context: Any = None) -> list[Evidence]:
    ctx = _ctx(context)
    return [
        name_similarity(candidate, ctx), institution_similarity(candidate, ctx),
        publication_overlap(candidate, ctx), coauthor_overlap(candidate, ctx),
        temporal_compatibility(candidate, ctx),
    ]
