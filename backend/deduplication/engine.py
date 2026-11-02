"""Architectural Role: Core Deduplication Engine Subsystem (V1 Baseline & V2 Safeguards).

This module determines whether two bibliographic records from disparate providers represent
the same underlying scholarly publication.

Key Architectural Principles & Distinctions:
1. Publication Deduplication != Author Entity Resolution:
   - Publication deduplication establishes document equivalence (whether two records describe the same paper).
   - Author entity resolution establishes personhood equivalence (which real human researcher authored the paper).
2. Deterministic Veto Rules Overrule Statistical Similarity:
   - High string similarity alone is insufficient for merging.
   - V2 incorporates 5 explicit deterministic safeguards to prevent catastrophic false merges:
     a) Hard DOI Conflict Veto: Differing valid DOIs immediately forbid merging.
     b) Edition Conflict Detection: Distinct textbook editions (e.g. 1st vs 2nd edition) are protected.
     c) Multi-Year Divergence Guard: >= 4 year divergence without identical DOI vetoes merge.
     d) Title Distinctness Floor: String similarity < 0.82 prevents merging distinct works sharing keywords.
     e) Prefix-Aware Title Matching: Recovers true duplicates lost to subtitle additions/truncations.
3. Asymmetric Cost of Errors:
   - In citation indexes, false positive merges (corrupting distinct works into one) are far more damaging
     than false negative splits (leaving duplicates unmerged). V2 prioritizes precision and safety.
"""
import re
import json
from dataclasses import dataclass, field
from typing import Optional
from rapidfuzz import fuzz
from deduplication.normalize import (
    CanonicalRecord,
    author_key_set,
    normalized_title_for_compare,
)
from config import (
    SOURCE_PRIORITY,
    DEDUP_DEFAULT_THRESHOLD,
    DEDUP_LENIENT_THRESHOLD,
    DEDUP_STRICT_THRESHOLD,
    DEDUP_LOG_THRESHOLD,
)


@dataclass
class MergedPublication:
    canonical_id: str
    title: str
    authors: list[str]
    year: Optional[int]
    abstract: str
    abstract_source: str
    doi: str
    doi_source: str
    venue: str
    venue_source: str
    citations: int
    citations_source: str
    best_source: str
    confidence_score: float
    source_count: int
    source_list: list[str]
    source_record_ids: list[int]   # indices into original records list


@dataclass
class SimilarityEntry:
    record1_idx: int
    record2_idx: int
    title_sim: float
    author_sim: float
    year_match: bool
    score: float
    decision: str   # "MERGED" | "SEPARATE"


# ── Threshold selection ───────────────────────────────────────────

def _threshold(src_a: str, src_b: str) -> float:
    pair = frozenset([src_a, src_b])
    if pair == frozenset(["scholar", "crossref"]):
        return 0.95
    if pair == frozenset(["scholar", "openalex"]):
        return 0.93
    if pair == frozenset(["openalex", "crossref"]):
        return DEDUP_LENIENT_THRESHOLD
    if "scholar" in pair or "faculty_page" in pair:
        return DEDUP_STRICT_THRESHOLD
    return DEDUP_DEFAULT_THRESHOLD


# ── Edition and Conflict Detection Helpers ─────────────────────────

_EDITION_RE = re.compile(
    r"(?:(\d+)(?:st|nd|rd|th)?\s+ed(?:ition)?|(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+ed(?:ition)?)",
    re.IGNORECASE,
)
_WORD_TO_EDITION = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
}


def _extract_edition(title: str) -> Optional[int]:
    """Extract edition number from title string (e.g., '1st Edition' -> 1)."""
    m = _EDITION_RE.search(title)
    if not m:
        return None
    num_str, word_str = m.groups()
    if num_str:
        return int(num_str)
    if word_str:
        return _WORD_TO_EDITION.get(word_str.lower())
    return None


def _has_edition_conflict(t1: str, t2: str) -> bool:
    """True if both titles have explicit, conflicting edition markers."""
    e1 = _extract_edition(t1)
    e2 = _extract_edition(t2)
    return e1 is not None and e2 is not None and e1 != e2


def _has_doi_conflict(d1: str, d2: str) -> bool:
    """True if both records have non-empty, conflicting registered DOIs."""
    if d1 and d2:
        return d1.strip().lower() != d2.strip().lower()
    return False


def _has_year_contradiction(
    y1: Optional[int], y2: Optional[int], d1: str, d2: str
) -> bool:
    """True if publication years differ by >= 4 years without an exact DOI match."""
    if y1 is not None and y2 is not None:
        if abs(y1 - y2) >= 4:
            if not (d1 and d2 and d1.strip().lower() == d2.strip().lower()):
                return True
    return False


def _is_shortened_prefix(n1: str, n2: str) -> bool:
    """Check if one normalized title is an exact leading prefix of another (>= 3 words, >= 15 chars)."""
    short, long_ = (n1, n2) if len(n1) <= len(n2) else (n2, n1)
    words = short.split()
    return len(words) >= 3 and len(short) >= 15 and long_.startswith(short)


# ── Scoring helpers ───────────────────────────────────────────────

def _title_sim(t1: str, t2: str) -> float:
    if not t1 or not t2:
        return 0.0
    n1 = normalized_title_for_compare(t1)
    n2 = normalized_title_for_compare(t2)
    if n1 == n2:
        return 1.0
    sort_sim = fuzz.token_sort_ratio(n1, n2) / 100.0
    if _is_shortened_prefix(n1, n2):
        set_sim = fuzz.token_set_ratio(n1, n2) / 100.0
        return max(sort_sim, set_sim * 0.95)
    return sort_sim


def _author_sim(a1: list[str], a2: list[str]) -> float:
    s1, s2 = author_key_set(a1), author_key_set(a2)
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / min(len(s1), len(s2))


def _year_match(y1: Optional[int], y2: Optional[int]) -> bool:
    if y1 is None or y2 is None:
        return False
    return abs(y1 - y2) <= 1


def _blocking_pass(r1: CanonicalRecord, r2: CanonicalRecord) -> bool:
    """At least one cheap condition must hold before fuzzy scoring runs."""
    if r1.doi and r1.doi == r2.doi:
        return True
    if _year_match(r1.year, r2.year):
        return True
    if author_key_set(r1.authors) & author_key_set(r2.authors):
        return True
    t1 = normalized_title_for_compare(r1.title)
    t2 = normalized_title_for_compare(r2.title)
    if t1[:5] and t1[:5] == t2[:5]:
        return True
    if _is_shortened_prefix(t1, t2):
        return True
    return False


def _fuzzy_score(r1: CanonicalRecord, r2: CanonicalRecord) -> tuple[float, float, bool, float]:
    ts = _title_sim(r1.title, r2.title)
    as_ = _author_sim(r1.authors, r2.authors)
    ym = _year_match(r1.year, r2.year)
    score = 0.6 * ts + 0.3 * as_ + 0.1 * (1.0 if ym else 0.0)
    return ts, as_, ym, score


# ── Field merging (by source priority) ───────────────────────────

def _best_field(records: list[CanonicalRecord], attr: str):
    """Return (value, source_name) from the highest-priority record that has the field."""
    sorted_recs = sorted(records, key=lambda r: SOURCE_PRIORITY.get(r.source, 99))
    for rec in sorted_recs:
        val = getattr(rec, attr, None)
        if val:
            return val, rec.source
    return "", sorted_recs[0].source if sorted_recs else ""


def _merge_group(records: list[CanonicalRecord], record_ids: list[int]) -> MergedPublication:
    """Merge a group of duplicate CanonicalRecords into one MergedPublication."""
    sorted_recs = sorted(records, key=lambda r: SOURCE_PRIORITY.get(r.source, 99))
    best = sorted_recs[0]

    title,    _         = _best_field(records, "title")
    abstract, abs_src   = _best_field(records, "abstract")
    doi,      doi_src   = _best_field(records, "doi")
    venue,    venue_src = _best_field(records, "venue")

    # Authors from best source
    authors = best.authors or []

    # Citations: max across sources
    all_citations = [(r.citations, r.source) for r in records if r.citations]
    if all_citations:
        citations, citations_src = max(all_citations, key=lambda x: x[0])
    else:
        citations, citations_src = 0, best.source

    # Canonical ID: prefer DOI-based
    canonical_id = best.canonical_id
    for r in sorted_recs:
        if r.canonical_id.startswith("doi_"):
            canonical_id = r.canonical_id
            break

    source_list = list(dict.fromkeys(r.source for r in records))  # deduped, ordered

    return MergedPublication(
        canonical_id      = canonical_id,
        title             = title or best.title,
        authors           = authors,
        year              = best.year,
        abstract          = abstract,
        abstract_source   = abs_src,
        doi               = doi,
        doi_source        = doi_src,
        venue             = venue,
        venue_source      = venue_src,
        citations         = citations,
        citations_source  = citations_src,
        best_source       = best.source,
        confidence_score  = 1.0 if len(records) == 1 else 0.9,
        source_count      = len(records),
        source_list       = source_list,
        source_record_ids = record_ids,
    )


# ── Main deduplication entry points ─────────────────────────────

def deduplicate_v1(
    records: list[CanonicalRecord],
    exclusions: dict | None = None,
) -> tuple[list[MergedPublication], list[SimilarityEntry]]:
    """Preserved Historical V1 Baseline deduplication algorithm."""
    exclusions = exclusions or {}
    bad_merges   = {frozenset(p) for p in exclusions.get("bad_merges", [])}
    force_merges = [frozenset(p) for p in exclusions.get("force_merges", [])]

    n = len(records)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    sim_log: list[SimilarityEntry] = []

    for i in range(n):
        for j in range(i + 1, n):
            r1, r2 = records[i], records[j]

            pair_key = frozenset([r1.source_id or str(i), r2.source_id or str(j)])
            if pair_key in bad_merges:
                continue

            merged = False

            if r1.doi and r1.doi == r2.doi:
                union(i, j)
                merged = True
            elif (normalized_title_for_compare(r1.title) ==
                  normalized_title_for_compare(r2.title) and r1.title):
                union(i, j)
                merged = True
            else:
                # Raw V1 blocking (ignoring prefix helper)
                t1 = normalized_title_for_compare(r1.title)
                t2 = normalized_title_for_compare(r2.title)
                v1_blocking = (
                    (r1.doi and r1.doi == r2.doi)
                    or _year_match(r1.year, r2.year)
                    or bool(author_key_set(r1.authors) & author_key_set(r2.authors))
                    or (bool(t1[:5]) and t1[:5] == t2[:5])
                )
                if v1_blocking:
                    ts = fuzz.token_sort_ratio(t1, t2) / 100.0
                    as_ = _author_sim(r1.authors, r2.authors)
                    ym = _year_match(r1.year, r2.year)
                    score = 0.6 * ts + 0.3 * as_ + 0.1 * (1.0 if ym else 0.0)
                    threshold = _threshold(r1.source, r2.source)
                    decision = "MERGED" if score >= threshold else "SEPARATE"

                    if score >= DEDUP_LOG_THRESHOLD:
                        sim_log.append(SimilarityEntry(
                            record1_idx = i,
                            record2_idx = j,
                            title_sim   = round(ts, 4),
                            author_sim  = round(as_, 4),
                            year_match  = ym,
                            score       = round(score, 4),
                            decision    = decision,
                        ))
                    if decision == "MERGED":
                        union(i, j)
                        merged = True

    for fp in force_merges:
        ids = list(fp)
        if len(ids) == 2:
            idx_map = {(r.source_id or str(k)): k for k, r in enumerate(records)}
            a, b = idx_map.get(ids[0]), idx_map.get(ids[1])
            if a is not None and b is not None:
                union(a, b)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(i)

    publications = [
        _merge_group([records[i] for i in idxs], idxs)
        for idxs in groups.values()
    ]

    return publications, sim_log


def deduplicate(
    records: list[CanonicalRecord],
    exclusions: dict | None = None,
) -> tuple[list[MergedPublication], list[SimilarityEntry]]:
    """
    Audited Conservative V2 Deduplication.
    
    Incorporates minimal, high-precision safeguards:
      1. Conflicting DOI veto (different registered DOIs cannot merge).
      2. Exact DOI match.
      3. Explicit edition conflict veto (e.g. 1st vs 2nd edition).
      4. Strong publication year contradiction veto (gap >= 4 years without DOI match).
      5. Exact normalized title match.
      6. Blocking pass -> fuzzy scoring with prefix subtitle awareness and title distinctness guard.
      7. Manual exclusions/inclusions.
    """
    exclusions = exclusions or {}
    bad_merges   = {frozenset(p) for p in exclusions.get("bad_merges", [])}
    force_merges = [frozenset(p) for p in exclusions.get("force_merges", [])]

    n = len(records)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    sim_log: list[SimilarityEntry] = []

    for i in range(n):
        for j in range(i + 1, n):
            r1, r2 = records[i], records[j]

            # Manual veto
            pair_key = frozenset([r1.source_id or str(i), r2.source_id or str(j)])
            if pair_key in bad_merges:
                continue

            # Safeguard 1: DOI Conflict Veto
            if _has_doi_conflict(r1.doi, r2.doi):
                continue

            merged = False

            # Step 1: exact DOI match
            if r1.doi and r1.doi == r2.doi:
                union(i, j)
                merged = True
            # Safeguard 2: Edition Conflict Veto (e.g. 1st vs 2nd edition)
            elif _has_edition_conflict(r1.title, r2.title):
                continue
            # Safeguard 3: Publication Year Contradiction (gap >= 4 years without DOI match)
            elif _has_year_contradiction(r1.year, r2.year, r1.doi, r2.doi):
                continue
            # Step 2: exact normalised title match
            elif (normalized_title_for_compare(r1.title) ==
                  normalized_title_for_compare(r2.title) and r1.title):
                union(i, j)
                merged = True
            else:
                # Step 3: blocking + fuzzy scoring
                if _blocking_pass(r1, r2):
                    ts, as_, ym, score = _fuzzy_score(r1, r2)
                    threshold = _threshold(r1.source, r2.source)
                    
                    n1 = normalized_title_for_compare(r1.title)
                    n2 = normalized_title_for_compare(r2.title)
                    is_prefix = _is_shortened_prefix(n1, n2)

                    # Conservative Guard: prevent title differences below 0.82 from merging
                    # solely because authors and publication year match closely.
                    can_merge = (score >= threshold)
                    if not is_prefix and ts < 0.82:
                        can_merge = False

                    decision = "MERGED" if can_merge else "SEPARATE"

                    if score >= DEDUP_LOG_THRESHOLD:
                        sim_log.append(SimilarityEntry(
                            record1_idx = i,
                            record2_idx = j,
                            title_sim   = round(ts, 4),
                            author_sim  = round(as_, 4),
                            year_match  = ym,
                            score       = round(score, 4),
                            decision    = decision,
                        ))
                    if decision == "MERGED":
                        union(i, j)
                        merged = True

            _ = merged

    # Manual force-merges
    for fp in force_merges:
        ids = list(fp)
        if len(ids) == 2:
            idx_map = {(r.source_id or str(k)): k for k, r in enumerate(records)}
            a, b = idx_map.get(ids[0]), idx_map.get(ids[1])
            if a is not None and b is not None:
                union(a, b)

    # Group by root
    groups: dict[int, list[int]] = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(i)

    publications = [
        _merge_group([records[i] for i in idxs], idxs)
        for idxs in groups.values()
    ]

    return publications, sim_log
