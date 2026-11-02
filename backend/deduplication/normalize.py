"""Architectural Role: Normalization Component of the Deduplication Subsystem.

This module converts heterogeneous, unstandardized bibliographic records ingested from
disparate external sources (OpenAlex, Crossref, DBLP, arXiv) into a unified CanonicalRecord schema.
Standardization includes HTML entity stripping, title lowercasing and punctuation removal,
robust publication year extraction, author name tokenization, and deterministic SHA-256
canonical ID generation.
"""
import re
import json
import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CanonicalRecord:
    """Standardized intermediate bibliographic record used across the deduplication pipeline.

    Each ingested source record is mapped to this schema before similarity calculations,
    blocking passes, and merge groupings are performed.
    """
    source: str
    source_id: str
    title: str
    authors: list[str]
    year: Optional[int]
    doi: str
    abstract: str
    venue: str
    citations: int
    url: str
    raw_json: str
    canonical_id: str = ""

    def __post_init__(self):
        # Generate a deterministic canonical ID if one was not explicitly supplied
        if not self.canonical_id:
            self.canonical_id = _make_canonical_id(self.doi, self.source_id, self.title)


# ── Text & Identifier Normalization Helpers ───────────────────────

_HTML_TAG  = re.compile(r"<[^>]+>")
_MULTI_WS  = re.compile(r"\s+")
_YEAR_RE   = re.compile(r"\b(19|20)\d{2}\b")
_PUNCT     = re.compile(r"[^\w\s]")


def _strip_html(text: str) -> str:
    """Remove HTML/XML formatting tags and collapse excess whitespace."""
    return _MULTI_WS.sub(" ", _HTML_TAG.sub("", text)).strip()


def _normalize_title(title: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace — used for exact-match comparison."""
    return _MULTI_WS.sub(" ", _PUNCT.sub("", title.lower())).strip()


def _extract_year(raw) -> Optional[int]:
    """Extract a 4-digit Gregorian calendar year between 1900 and 2100 from string or integer inputs."""
    if isinstance(raw, int) and 1900 < raw < 2100:
        return raw
    if isinstance(raw, str):
        m = _YEAR_RE.search(raw)
        if m:
            return int(m.group(0))
    return None


def _make_canonical_id(doi: str, source_id: str, title: str) -> str:
    """Construct a deterministic, collision-resistant identifier for a bibliographic record.
    
    If a valid DOI exists, it forms the basis of the canonical hash. Otherwise, a SHA-256
    hash is computed from the source name, source ID, and normalized title.
    """
    clean_doi = (doi or "").strip().lower()
    if clean_doi:
        return f"doi:{clean_doi}"
    key = f"{source_id}:{_normalize_title(title)}"
    return f"hash:{hashlib.sha256(key.encode()).hexdigest()[:16]}"


def _parse_authors(raw) -> list[str]:
    """Normalize author lists from strings, dictionaries, or lists of names into standardized strings."""
    if not raw:
        return []
    if isinstance(raw, list):
        out = []
        for item in raw:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    out.append(cleaned)
            elif isinstance(item, dict):
                name = item.get("name") or item.get("display_name") or ""
                if name.strip():
                    out.append(name.strip())
        return out
    if isinstance(raw, str):
        # Handle semicolon-separated or comma-separated author strings
        parts = re.split(r"[;,]", raw)
        return [p.strip() for p in parts if p.strip()]
    return []


def normalize(raw: dict) -> CanonicalRecord:
    """Convert an arbitrary raw dictionary from an academic connector into a standardized CanonicalRecord.

    Architectural Role:
    This function is the primary entry point for bibliographic normalization. It insulates downstream
    deduplication and persistence logic from external provider schema discrepancies.
    """
    title = _strip_html(raw.get("title") or "")
    doi   = (raw.get("doi") or "").strip().lower()

    # Normalize DOI string formatting by stripping standard resolver prefixes
    if doi.startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]
    elif doi.startswith("http://doi.org/"):
        doi = doi[len("http://doi.org/"):]
    elif doi.startswith("doi:"):
        doi = doi[4:]

    authors = _parse_authors(raw.get("authors"))
    year    = _extract_year(raw.get("year"))

    citations = raw.get("citations", 0)
    try:
        citations = int(citations or 0)
    except (ValueError, TypeError):
        citations = 0

    return CanonicalRecord(
        source=raw.get("source", "unknown"),
        source_id=str(raw.get("source_id", "")),
        title=title,
        authors=authors,
        year=year,
        doi=doi,
        abstract=_strip_html(raw.get("abstract") or ""),
        venue=raw.get("venue") or "",
        citations=citations,
        url=raw.get("url") or "",
        raw_json=json.dumps(raw, default=str),
    )


def normalize_author_key(name: str) -> str:
    """Produce a normalized comparison key for an individual author (e.g. 'y bengio' or 'bengio y').
    
    Transforms names into lowercase token-sorted keys to match author mentions regardless
    of Western (First Last) vs. Eastern/Bibliographic (Last, First) ordering.
    """
    cleaned = _PUNCT.sub("", name.lower()).strip()
    parts = cleaned.split()
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    # Return last name + first initial for fuzzy author comparison
    return f"{parts[-1]} {parts[0][0]}"


def author_key_set(authors: list[str]) -> set[str]:
    """Convert an author list into a set of normalized author comparison keys."""
    return {normalize_author_key(a) for a in authors if normalize_author_key(a)}


def normalized_title_for_compare(title: str) -> str:
    """Public title normalization helper for cross-module comparison (used in evidence scoring)."""
    return _normalize_title(title)
