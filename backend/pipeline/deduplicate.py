import json
from dataclasses import dataclass, field
from typing import Optional
from rapidfuzz import fuzz
from pipeline.normalize import (
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


# ── Scoring helpers ───────────────────────────────────────────────

def _title_sim(t1: str, t2: str) -> float:
    if not t1 or not t2:
        return 0.0
    return fuzz.token_sort_ratio(
        normalized_title_for_compare(t1),
        normalized_title_for_compare(t2),
    ) / 100.0


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


# ── Main deduplication entry point ───────────────────────────────

def deduplicate(
    records: list[CanonicalRecord],
    exclusions: dict | None = None,
) -> tuple[list[MergedPublication], list[SimilarityEntry]]:
    """
    Input : list of CanonicalRecord
    Output: (merged_publications, similarity_log_entries)

    Algorithm:
      1. Exact DOI match
      2. Exact normalised title match
      3. Blocking pass → fuzzy scoring with source-aware threshold
      4. Apply manual_exclusions overrides
    """
    exclusions = exclusions or {}
    bad_merges   = {frozenset(p) for p in exclusions.get("bad_merges", [])}
    force_merges = [frozenset(p) for p in exclusions.get("force_merges", [])]

    n = len(records)
    # Union-Find
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

            merged = False

            # Step 1 & 2: exact matches
            if r1.doi and r1.doi == r2.doi:
                union(i, j)
                merged = True
            elif (normalized_title_for_compare(r1.title) ==
                  normalized_title_for_compare(r2.title) and r1.title):
                union(i, j)
                merged = True
            else:
                # Step 3: blocking + fuzzy
                if _blocking_pass(r1, r2):
                    ts, as_, ym, score = _fuzzy_score(r1, r2)
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

            _ = merged  # suppress unused warning

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
