import re
import json
import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CanonicalRecord:
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
        if not self.canonical_id:
            self.canonical_id = _make_canonical_id(self.doi, self.source_id, self.title)


# ── Helpers ──────────────────────────────────────────────────────

_HTML_TAG  = re.compile(r"<[^>]+>")
_MULTI_WS  = re.compile(r"\s+")
_YEAR_RE   = re.compile(r"\b(19|20)\d{2}\b")
_PUNCT     = re.compile(r"[^\w\s]")


def _strip_html(text: str) -> str:
    return _MULTI_WS.sub(" ", _HTML_TAG.sub("", text)).strip()


def _normalize_title(title: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace — used for exact-match comparison."""
    return _MULTI_WS.sub(" ", _PUNCT.sub("", title.lower())).strip()


def _extract_year(raw) -> Optional[int]:
    if isinstance(raw, int) and 1900 < raw < 2100:
        return raw
    if isinstance(raw, str):
        m = _YEAR_RE.search(raw)
        if m:
            return int(m.group())
    return None


def _make_canonical_id(doi: str, source_id: str, title: str) -> str:
    """Stable ID: DOI hash → source_id → normalized-title hash."""
    if doi:
        return "doi_" + hashlib.sha256(doi.lower().strip().encode()).hexdigest()[:16]
    if source_id:
        return "sid_" + hashlib.sha256(source_id.encode()).hexdigest()[:16]
    norm = _normalize_title(title)
    return "ttl_" + hashlib.sha256(norm.encode()).hexdigest()[:16]


def _parse_authors(raw) -> list[str]:
    """Accepts list[str] or a comma-separated string."""
    if isinstance(raw, list):
        return [str(a).strip() for a in raw if a]
    if isinstance(raw, str):
        return [a.strip() for a in raw.split(",") if a.strip()]
    return []


# ── Public API ───────────────────────────────────────────────────

def normalize(raw: dict) -> CanonicalRecord:
    """
    Convert a raw dict (from any connector) into a CanonicalRecord.
    All fields are cleaned and type-coerced here — downstream code
    never needs to handle None-vs-empty or type ambiguity.
    """
    title    = _strip_html(str(raw.get("title") or ""))
    abstract = _strip_html(str(raw.get("abstract") or ""))
    authors  = _parse_authors(raw.get("authors") or raw.get("authors_raw") or [])
    year     = _extract_year(raw.get("year") or raw.get("publication_year"))
    doi      = str(raw.get("doi") or "").strip().lower()
    venue    = _strip_html(str(raw.get("venue") or ""))

    citations_raw = raw.get("citations") or raw.get("cited_by_count") or 0
    try:
        citations = int(citations_raw)
    except (ValueError, TypeError):
        citations = 0

    return CanonicalRecord(
        source    = str(raw.get("source", "unknown")),
        source_id = str(raw.get("source_id") or ""),
        title     = title,
        authors   = authors,
        year      = year,
        doi       = doi,
        abstract  = abstract,
        venue     = venue,
        citations = citations,
        url       = str(raw.get("url") or ""),
        raw_json  = raw.get("raw_json") or json.dumps(raw),
    )


def normalize_author_key(name: str) -> str:
    """
    FIRST_INITIAL + LAST_NAME — safe against Patel/Wang false positives.
    'Geoffrey E. Hinton' → 'G_HINTON'
    """
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0].upper()}_{parts[-1].upper()}"
    return name.upper().replace(" ", "_")


def author_key_set(authors: list[str]) -> set[str]:
    return {normalize_author_key(a) for a in authors if a.strip()}


def normalized_title_for_compare(title: str) -> str:
    return _normalize_title(title)
