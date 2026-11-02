"""OpenAlex author candidate generation.

This module deliberately generates hypotheses only.  A returned OpenAlex ID
identifies a source profile; it does not establish that the profile represents
the person intended by a user query, nor does it establish identity in any
other source.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import OPENALEX_API_KEY, OPENALEX_MAILTO, SOURCE_TIMEOUT
from database import AuthorCandidate
from log_config import get_logger


logger = get_logger(__name__)

OPENALEX_AUTHORS_URL = "https://api.openalex.org/authors"
SOURCE_NAME = "openalex"


def normalize_name(value: str) -> str:
    """Normalize a display/query name for storage and exact lookup only."""
    return re.sub(r"\s+", " ", value.strip().casefold())


# ── Day 5 Integration: narrowly scoped query normalization ───────

# Surname particles that must never be concatenated with the following token.
# These are legitimate Dutch, German, French, Italian, and Spanish particles.
_PRESERVED_PARTICLES = frozenset({
    "von", "van", "de", "du", "der", "den", "das", "dos", "di", "del",
    "al", "el", "bin", "ibn", "ben", "mac", "mc",
})


def clean_query_name(raw_name: str) -> str:
    """Conservative query normalization applied before sending to OpenAlex.

    Operations (in order):
    1. Unicode NFC normalization — merges decomposed diacritics.
    2. Whitespace collapsing — removes leading/trailing and multiple internal spaces.
    3. Narrow compound-name spacing — collapses 'Le Cun' → 'LeCun' only when the
       first token is NOT a preserved surname particle (e.g. 'von', 'van', 'de').

    This function never deletes particles, never lowercases, and never truncates.
    """
    if not raw_name:
        return ""
    name = unicodedata.normalize("NFC", raw_name)
    name = re.sub(r"\s+", " ", name).strip()
    if not name:
        return ""

    parts = name.split()
    if len(parts) < 2:
        return name

    merged: list[str] = []
    i = 0
    while i < len(parts):
        token = parts[i]
        # Only attempt merge when the token is a capitalised short prefix
        # that is NOT a protected particle and the next token starts uppercase
        # and has length > 2 (avoids merging initials).
        if (
            i + 1 < len(parts)
            and token.lower() in {"le", "la"}
            and parts[i + 1][0].isupper()
            and len(parts[i + 1]) > 2
            and parts[i + 1].isalpha()
        ):
            merged.append(token + parts[i + 1])
            i += 2
        else:
            merged.append(token)
            i += 1
    return " ".join(merged)


# Institutional input patterns — these are administrative entities, not people.
_INSTITUTIONAL_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bdepartment of\b", r"\bdept\.? of\b", r"\bdivision of\b",
        r"\bfaculty of\b", r"\bschool of\b", r"\binstitute of\b",
        r"\binstitute for\b", r"\bcenter for\b", r"\bcentre for\b",
        r"\blaboratory\b", r"\blabs?\b",
    ]
]


def is_institutional_input(text: str) -> bool:
    """Return True if the input resembles an institution or department name.

    When True, HAMMER should refuse to query the OpenAlex author endpoint
    because searching for department strings produces spurious candidates
    (e.g. searching for 'Department of Statistics' returns people named
    'Department' or 'Statistics').
    """
    if not text or not text.strip():
        return False
    return any(pat.search(text) for pat in _INSTITUTIONAL_PATTERNS)


def _has_initial_token(name: str) -> bool:
    """Return True if the name contains a single-letter initial (e.g. 'Y. LeCun')."""
    return bool(re.search(r"\b[A-Za-z]\.", name))


def _source_identifier(value: Any) -> str | None:
    """Extract an OpenAlex author ID from either a bare value or API URL."""
    if not isinstance(value, str) or not value.strip():
        return None
    return value.rstrip("/").rsplit("/", 1)[-1] or None


def _as_nonnegative_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _normalise_institution(item: Any) -> dict[str, Any] | None:
    """Keep source metadata while exposing a consistent affiliation shape."""
    if not isinstance(item, dict):
        return None
    institution = item.get("institution") if isinstance(item.get("institution"), dict) else item
    name = institution.get("display_name") or institution.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    return {
        "name": name.strip(),
        "normalized_name": normalize_name(name),
        "source_institution_id": _source_identifier(institution.get("id")),
        "country_code": institution.get("country_code"),
        "type": institution.get("type"),
        "years": item.get("years") if isinstance(item.get("years"), list) else None,
        "source": SOURCE_NAME,
    }


def _affiliations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Combine currently exposed OpenAlex affiliation shapes without duplicates."""
    raw_items: list[Any] = []
    for key in ("last_known_institutions", "affiliations"):
        value = payload.get(key)
        if isinstance(value, list):
            raw_items.extend(value)

    affiliations: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None]] = set()
    for item in raw_items:
        normalised = _normalise_institution(item)
        if not normalised:
            continue
        key = (normalised["normalized_name"], normalised["source_institution_id"])
        if key not in seen:
            seen.add(key)
            affiliations.append(normalised)
    return affiliations


def _aliases(payload: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("display_name_alternatives", "alternate_names", "aliases"):
        raw = payload.get(key)
        if isinstance(raw, list):
            values.extend(item.strip() for item in raw if isinstance(item, str) and item.strip())

    aliases: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = normalize_name(value)
        if key not in seen:
            seen.add(key)
            aliases.append(value)
    return aliases


def _active_years(payload: dict[str, Any]) -> tuple[int | None, int | None]:
    years: list[int] = []
    counts = payload.get("counts_by_year")
    if isinstance(counts, list):
        for row in counts:
            if isinstance(row, dict):
                year = _as_nonnegative_int(row.get("year"))
                if year and 1800 <= year <= 2200:
                    years.append(year)
    return (min(years), max(years)) if years else (None, None)


@dataclass(frozen=True)
class AuthorCandidateInput:
    author_name: str
    institution_hint: str | None = None
    query_context: dict[str, Any] | None = None


@dataclass(frozen=True)
class OpenAlexCandidate:
    """A source-derived candidate, not a resolved author identity."""
    query_original: str
    query_normalized: str
    source: str
    source_author_id: str
    source_author_url: str | None
    display_name: str
    normalized_name: str
    aliases: list[str]
    institution_summary: str | None
    affiliations: list[dict[str, Any]]
    works_count: int | None
    citation_count: int | None
    sample_publications: list[dict[str, Any]] | None
    topics: list[dict[str, Any]] | None
    coauthor_summary: list[dict[str, Any]] | None
    years_active_start: int | None
    years_active_end: int | None
    retrieved_at: datetime
    raw_payload: dict[str, Any]

    @classmethod
    def from_openalex(
        cls, payload: dict[str, Any], request: AuthorCandidateInput, retrieved_at: datetime
    ) -> "OpenAlexCandidate | None":
        source_id = _source_identifier(payload.get("id"))
        display_name = payload.get("display_name")
        if not source_id or not isinstance(display_name, str) or not display_name.strip():
            return None

        affiliations = _affiliations(payload)
        start_year, end_year = _active_years(payload)
        topics = payload.get("topics") or payload.get("x_concepts")
        if not isinstance(topics, list):
            topics = None

        return cls(
            query_original=request.author_name,
            query_normalized=normalize_name(request.author_name),
            source=SOURCE_NAME,
            source_author_id=source_id,
            source_author_url=payload.get("id") if isinstance(payload.get("id"), str) else None,
            display_name=display_name.strip(),
            normalized_name=normalize_name(display_name),
            aliases=_aliases(payload),
            institution_summary=affiliations[0]["name"] if affiliations else None,
            affiliations=affiliations,
            works_count=_as_nonnegative_int(payload.get("works_count")),
            citation_count=_as_nonnegative_int(payload.get("cited_by_count")),
            # The OpenAlex author endpoint does not guarantee these values.  They
            # remain absent until a later evidence-collection stage retrieves them.
            sample_publications=None,
            topics=topics,
            coauthor_summary=None,
            years_active_start=start_year,
            years_active_end=end_year,
            retrieved_at=retrieved_at,
            raw_payload=payload,
        )

    def to_persistence_values(self) -> dict[str, Any]:
        """Map a source candidate to the Stage 1 AuthorCandidate schema."""
        return {
            "query_original": self.query_original,
            "query_normalized": self.query_normalized,
            "source": self.source,
            "source_author_id": self.source_author_id,
            "display_name": self.display_name,
            "normalized_name": self.normalized_name,
            "aliases_json": json.dumps(self.aliases),
            "institution_summary": self.institution_summary,
            "affiliations_json": json.dumps(self.affiliations),
            "works_count": self.works_count,
            "citation_count": self.citation_count,
            "sample_publications_json": json.dumps(self.sample_publications)
            if self.sample_publications is not None
            else None,
            "topics_json": json.dumps(self.topics) if self.topics is not None else None,
            "coauthor_summary_json": json.dumps(self.coauthor_summary)
            if self.coauthor_summary is not None
            else None,
            "years_active_start": self.years_active_start,
            "years_active_end": self.years_active_end,
            "raw_payload_json": json.dumps(
                {
                    "source": self.source,
                    "source_author_url": self.source_author_url,
                    "payload": self.raw_payload,
                }
            ),
            "retrieved_at": self.retrieved_at,
        }

    @classmethod
    def from_persisted(cls, row: Any) -> "OpenAlexCandidate":
        payload = json.loads(row.raw_payload_json or "{}")
        return cls(
            query_original=row.query_original,
            query_normalized=row.query_normalized,
            source=row.source,
            source_author_id=row.source_author_id,
            source_author_url=payload.get("source_author_url"),
            display_name=row.display_name,
            normalized_name=row.normalized_name,
            aliases=json.loads(row.aliases_json or "[]"),
            institution_summary=row.institution_summary,
            affiliations=json.loads(row.affiliations_json or "[]"),
            works_count=row.works_count,
            citation_count=row.citation_count,
            sample_publications=json.loads(row.sample_publications_json) if row.sample_publications_json else None,
            topics=json.loads(row.topics_json) if row.topics_json else None,
            coauthor_summary=json.loads(row.coauthor_summary_json) if row.coauthor_summary_json else None,
            years_active_start=row.years_active_start,
            years_active_end=row.years_active_end,
            retrieved_at=row.retrieved_at,
            raw_payload=payload.get("payload", payload),
        )


@dataclass(frozen=True)
class CandidateGenerationResult:
    request: AuthorCandidateInput
    status: str
    candidates: list[OpenAlexCandidate] = field(default_factory=list)
    source: str = SOURCE_NAME
    error_code: str | None = None
    error_message: str | None = None
    retrieved_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.request.author_name,
            "institution_hint": self.request.institution_hint,
            "query_context": self.request.query_context,
            "status": self.status,
            "source": self.source,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "retrieved_at": self.retrieved_at.isoformat(),
            "candidates": [asdict(candidate) for candidate in self.candidates],
        }


class OpenAlexCandidateService:
    """Fetch and normalize OpenAlex profiles as author candidates only."""

    def __init__(
        self,
        *,
        timeout_seconds: float = SOURCE_TIMEOUT,
        transport: httpx.AsyncBaseTransport | None = None,
        max_candidates: int = 10,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.transport = transport
        self.max_candidates = max_candidates

    async def generate(self, request: AuthorCandidateInput) -> CandidateGenerationResult:
        author_name = request.author_name.strip()
        retrieved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if not author_name:
            return CandidateGenerationResult(
                request=request,
                status="failed",
                error_code="invalid_query",
                error_message="Author name cannot be empty.",
                retrieved_at=retrieved_at,
            )

        # Day 5: reject institutional strings before querying the author endpoint
        if is_institutional_input(author_name):
            logger.info("Rejected institutional input from author query: %r", author_name)
            return CandidateGenerationResult(
                request=request,
                status="failed",
                error_code="unsupported_input",
                error_message="Input appears to be an institution or department, not a person name.",
                retrieved_at=retrieved_at,
            )

        # Day 5: apply conservative query normalization (NFC + whitespace + compound-name)
        query_name = clean_query_name(author_name)
        if not query_name:
            query_name = author_name  # defensive: never send empty

        params = {
            "mailto": OPENALEX_MAILTO,
            "filter": f"display_name.search:{query_name}",
            "per-page": self.max_candidates,
        }
        if OPENALEX_API_KEY:
            params["api_key"] = OPENALEX_API_KEY

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds, transport=self.transport
            ) as client:
                response = await client.get(OPENALEX_AUTHORS_URL, params=params)
        except httpx.TimeoutException:
            logger.warning("OpenAlex candidate lookup timed out for query=%r", author_name)
            return CandidateGenerationResult(
                request=request,
                status="failed",
                error_code="timeout",
                error_message="OpenAlex did not respond before the request timeout.",
                retrieved_at=retrieved_at,
            )
        except httpx.HTTPError as exc:
            logger.warning("OpenAlex candidate lookup request failed for query=%r: %s", author_name, exc)
            return CandidateGenerationResult(
                request=request,
                status="failed",
                error_code="request_failed",
                error_message="OpenAlex request failed.",
                retrieved_at=retrieved_at,
            )

        if response.status_code == 429:
            return CandidateGenerationResult(
                request=request,
                status="failed",
                error_code="rate_limited",
                error_message="OpenAlex rate-limited the candidate request.",
                retrieved_at=retrieved_at,
            )
        if response.is_error:
            logger.warning(
                "OpenAlex candidate lookup returned status=%s for query=%r",
                response.status_code,
                author_name,
            )
            return CandidateGenerationResult(
                request=request,
                status="failed",
                error_code="http_error",
                error_message=f"OpenAlex returned HTTP {response.status_code}.",
                retrieved_at=retrieved_at,
            )

        try:
            body = response.json()
        except ValueError:
            return CandidateGenerationResult(
                request=request,
                status="failed",
                error_code="malformed_response",
                error_message="OpenAlex returned invalid JSON.",
                retrieved_at=retrieved_at,
            )

        results = body.get("results") if isinstance(body, dict) else None
        if not isinstance(results, list):
            return CandidateGenerationResult(
                request=request,
                status="failed",
                error_code="malformed_response",
                error_message="OpenAlex response did not contain an author results list.",
                retrieved_at=retrieved_at,
            )

        candidates: list[OpenAlexCandidate] = []
        seen_source_ids: set[str] = set()
        for item in results:
            if not isinstance(item, dict):
                continue
            candidate = OpenAlexCandidate.from_openalex(item, request, retrieved_at)
            if candidate and candidate.source_author_id not in seen_source_ids:
                seen_source_ids.add(candidate.source_author_id)
                candidates.append(candidate)

        # Day 5: initial-only fallback — if zero candidates were returned and
        # the query contains an abbreviated initial (e.g. "Y. LeCun"), retry
        # using OpenAlex's broader `search:` parameter instead of the strict
        # `filter=display_name.search:` endpoint.  This is restricted to
        # initial-containing queries to avoid inflating candidate volume on
        # common full names.
        if not candidates and _has_initial_token(query_name):
            logger.info(
                "Zero candidates for initial-containing query=%r; attempting search fallback",
                query_name,
            )
            fallback_params = {
                "mailto": OPENALEX_MAILTO,
                "search": query_name,
                "per-page": self.max_candidates,
            }
            if OPENALEX_API_KEY:
                fallback_params["api_key"] = OPENALEX_API_KEY
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout_seconds, transport=self.transport
                ) as fb_client:
                    fb_response = await fb_client.get(OPENALEX_AUTHORS_URL, params=fallback_params)
                if fb_response.is_success:
                    try:
                        fb_body = fb_response.json()
                    except ValueError:
                        fb_body = None
                    fb_results = fb_body.get("results") if isinstance(fb_body, dict) else None
                    if isinstance(fb_results, list):
                        for item in fb_results:
                            if not isinstance(item, dict):
                                continue
                            candidate = OpenAlexCandidate.from_openalex(item, request, retrieved_at)
                            if candidate and candidate.source_author_id not in seen_source_ids:
                                seen_source_ids.add(candidate.source_author_id)
                                candidates.append(candidate)
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                logger.warning("Initial-only search fallback failed for query=%r: %s", query_name, exc)

        return CandidateGenerationResult(
            request=request,
            status="ok" if candidates else "empty",
            candidates=candidates,
            retrieved_at=retrieved_at,
        )

    async def persist_candidates(
        self, result: CandidateGenerationResult, db: AsyncSession
    ) -> list[AuthorCandidate]:
        """Persist candidates idempotently without creating an Author identity.

        This method intentionally does not commit.  The caller controls the
        transaction, and must apply the Stage 1 migration before invoking it.
        """
        persisted: list[AuthorCandidate] = []
        for candidate in result.candidates:
            existing = await db.scalar(
                select(AuthorCandidate).where(
                    AuthorCandidate.query_normalized == candidate.query_normalized,
                    AuthorCandidate.source == candidate.source,
                    AuthorCandidate.source_author_id == candidate.source_author_id,
                )
            )
            if existing is not None:
                persisted.append(existing)
                continue

            row = AuthorCandidate(**candidate.to_persistence_values())
            db.add(row)
            await db.flush()
            persisted.append(row)
        return persisted