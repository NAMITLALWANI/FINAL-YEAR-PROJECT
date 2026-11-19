"""Candidate enrichment: the only place that contacts OpenAlex for works-derived evidence.

Evidence extraction and scoring never call this module and never touch the network.
Two bounded retrievals, each performed only when the query supplied the input that
makes it useful:

1. Query-works lookup (one request per query, only if publication identifiers were
   supplied): resolve the query's own DOIs / OpenAlex work IDs and read their
   authorships. A candidate "links" to a work when its OpenAlex author ID is among
   that work's authors.
2. Coauthor sample (per candidate, only if at least one OpenAlex coauthor ID was supplied): up to
   ``max_pages`` x ``per_page`` of the candidate's works, basic paging, authorships
   only. Coauthors are stable OpenAlex author IDs; the candidate's own ID is excluded.

A failed or empty retrieval never becomes evidence of agreement. Failures are
recorded per signal and never raise out of the pool.

The works filters and ``select`` fields follow the OpenAlex documentation; they have
not been exercised against the live service in this repository's tests (mocked only).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any

import httpx

from author_resolution.candidates import OpenAlexCandidate
from author_resolution.context import QueryContext, normalize_doi, normalize_openalex_id
from author_resolution.enrichment_types import (
    EMPTY, FAILED, OK, CoauthorEvidence, PublicationLinkEvidence,
)
from config import (
    AUTHOR_ENRICHMENT_MAX_PAGES, AUTHOR_ENRICHMENT_WORKS_PER_PAGE, ENABLE_AUTHOR_ENRICHMENT,
    OPENALEX_API_KEY, OPENALEX_MAILTO, SOURCE_TIMEOUT,
)
from log_config import get_logger

logger = get_logger(__name__)

OPENALEX_WORKS_URL = "https://api.openalex.org/works"
WORKS_SELECT = "id,doi,publication_year,authorships,is_authors_truncated"
SKIPPED_AFTER_RATE_LIMIT = "skipped_after_rate_limit"
# Explicit, documented sort (help.openalex.org: ascending by default, ":desc" descending, comma-separated keys).
# Recent works are favoured by design; tie order between equal keys is not documented by OpenAlex.
WORKS_SORT = "publication_date:desc,cited_by_count:desc"


@dataclass(frozen=True)
class EnrichmentReport:
    candidates: list[OpenAlexCandidate]
    query_works_status: str | None = None            # None = not requested
    candidate_status: dict[str, dict[str, str | None]] = field(default_factory=dict)
    request_count: int = 0

    @property
    def any_failed(self) -> bool:
        if self.query_works_status == FAILED:
            return True
        return any(FAILED in (v.get("publications"), v.get("coauthors")) for v in self.candidate_status.values())

    def summary(self) -> dict[str, Any]:
        return {
            "query_works_status": self.query_works_status,
            "candidates": self.candidate_status,
            "request_count": self.request_count,
            "any_failed": self.any_failed,
        }


@dataclass
class _QueryWorks:
    status: str
    works: list[dict[str, Any]] = field(default_factory=list)   # {"work_id","doi","authors","truncated"}
    unresolved: list[str] = field(default_factory=list)
    error_code: str | None = None
    retrieved_at: str | None = None
    requests: int = 0


def _now() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


def _author_ids(work: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for authorship in work.get("authorships") or []:
        author = authorship.get("author") if isinstance(authorship, dict) else None
        aid = normalize_openalex_id(author.get("id"), "author") if isinstance(author, dict) else None
        if aid:
            ids.add(aid)
    return ids


class CandidateEnrichmentService:
    def __init__(
        self,
        *,
        timeout_seconds: float = SOURCE_TIMEOUT,
        transport: httpx.AsyncBaseTransport | None = None,
        per_page: int = AUTHOR_ENRICHMENT_WORKS_PER_PAGE,
        max_pages: int = AUTHOR_ENRICHMENT_MAX_PAGES,
        enabled: bool = ENABLE_AUTHOR_ENRICHMENT,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.transport = transport
        self.per_page = max(1, min(per_page, 100))   # 100 is OpenAlex's documented maximum
        self.max_pages = max(1, max_pages)
        self.enabled = enabled
        self._requests = 0

    # ------------------------------------------------------------------ HTTP
    def _params(self, **extra: Any) -> dict[str, Any]:
        params: dict[str, Any] = {"mailto": OPENALEX_MAILTO, **extra}
        if OPENALEX_API_KEY:
            params["api_key"] = OPENALEX_API_KEY
        return params

    async def _get(self, client: httpx.AsyncClient, params: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
        """Return (body, error_code). Exactly one of the two is None."""
        self._requests += 1
        try:
            response = await client.get(OPENALEX_WORKS_URL, params=params)
        except httpx.TimeoutException:
            return None, "timeout"
        except httpx.HTTPError:
            return None, "request_failed"
        if response.status_code == 429:
            return None, "rate_limited"
        if response.is_error:
            return None, "http_error"
        try:
            body = response.json()
        except ValueError:
            return None, "malformed_response"
        if not isinstance(body, dict) or not isinstance(body.get("results"), list):
            return None, "malformed_response"
        return body, None

    # ------------------------------------------------------------ query works
    async def _lookup_query_works(self, client: httpx.AsyncClient, ctx: QueryContext) -> _QueryWorks:
        found: dict[str, dict[str, Any]] = {}
        requests: list[dict[str, str]] = []
        if ctx.publication_dois:
            requests.append({"filter": "doi:" + "|".join(f"https://doi.org/{d}" for d in ctx.publication_dois)})
        if ctx.publication_work_ids:
            requests.append({"filter": "openalex:" + "|".join(ctx.publication_work_ids)})
        start = self._requests
        for extra in requests:
            body, error = await self._get(client, self._params(**extra, **{"per-page": 100, "select": WORKS_SELECT}))
            if error:
                return _QueryWorks(FAILED, error_code=error, retrieved_at=_now(), requests=self._requests - start)
            for work in body["results"]:
                if not isinstance(work, dict):
                    continue
                wid = normalize_openalex_id(work.get("id"), "work")
                if not wid:
                    continue
                found[wid] = {
                    "work_id": wid, "doi": normalize_doi(work.get("doi")), "authors": _author_ids(work),
                    "truncated": bool(work.get("is_authors_truncated")),
                }
        resolved_dois = {w["doi"] for w in found.values() if w["doi"]}
        unresolved = [d for d in ctx.publication_dois if d not in resolved_dois]
        unresolved += [w for w in ctx.publication_work_ids if w not in found]
        status = OK if found else EMPTY
        return _QueryWorks(status, works=list(found.values()), unresolved=unresolved, retrieved_at=_now(), requests=self._requests - start)

    @staticmethod
    def _publication_evidence(candidate_id: str, lookup: _QueryWorks, ctx: QueryContext) -> PublicationLinkEvidence:
        base = {"provider": "openalex", "endpoint": "works", "method": "query_works_lookup",
                "identifiers_requested": len(ctx.publication_dois) + len(ctx.publication_work_ids)}
        fingerprint = ctx.publication_fingerprint()
        if lookup.status == FAILED:
            return PublicationLinkEvidence(FAILED, fingerprint, retrieved_at=lookup.retrieved_at, provenance=base, error_code=lookup.error_code)
        comparable: list[str] = []
        matched: list[str] = []
        matched_dois: list[str] = []
        truncated: list[str] = []
        for work in lookup.works:
            linked = candidate_id in work["authors"]
            if linked:
                matched.append(work["work_id"])
                comparable.append(work["work_id"])
                if work["doi"]:
                    matched_dois.append(work["doi"])
            elif work["truncated"]:
                truncated.append(work["work_id"])      # author list incomplete: cannot call this a non-match
            else:
                comparable.append(work["work_id"])
        return PublicationLinkEvidence(
            lookup.status, fingerprint, tuple(sorted(comparable)), tuple(sorted(matched)), tuple(sorted(matched_dois)),
            tuple(lookup.unresolved), tuple(sorted(truncated)), lookup.retrieved_at, base,
        )

    # ------------------------------------------------------------- coauthors
    async def _coauthor_sample(self, client: httpx.AsyncClient, candidate: OpenAlexCandidate) -> CoauthorEvidence:
        own = normalize_openalex_id(candidate.source_author_id, "author")
        provenance = {"provider": "openalex", "endpoint": "works", "method": "author_works_sample",
                      "per_page": self.per_page, "max_pages": self.max_pages, "paging": "basic", "sort": WORKS_SORT}
        if not own:     # never issue a filter such as author.id:None
            return CoauthorEvidence(FAILED, retrieved_at=_now(), provenance=provenance, error_code="invalid_candidate_id")
        pages_requested = pages_succeeded = 0
        coauthors: dict[str, dict[str, Any]] = {}
        examined = 0
        total: int | None = None
        partial_error: str | None = None
        for page in range(1, self.max_pages + 1):
            body, error = await self._get(client, self._params(**{
                "filter": f"author.id:{own}", "per-page": self.per_page, "page": page, "sort": WORKS_SORT, "select": WORKS_SELECT}))
            pages_requested += 1
            if error:
                if page == 1:
                    return CoauthorEvidence(FAILED, retrieved_at=_now(), provenance=provenance, error_code=error)
                partial_error = error
                break
            pages_succeeded += 1
            meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
            if isinstance(meta.get("count"), int):
                total = meta["count"]
            works = [w for w in body["results"] if isinstance(w, dict)]
            for work in works:
                examined += 1
                wid = normalize_openalex_id(work.get("id"), "work")
                for authorship in work.get("authorships") or []:
                    author = authorship.get("author") if isinstance(authorship, dict) else None
                    aid = normalize_openalex_id(author.get("id"), "author") if isinstance(author, dict) else None
                    if not aid or aid == own:
                        continue
                    entry = coauthors.setdefault(aid, {"openalex_id": aid, "display_name": None, "work_ids": []})
                    if not entry["display_name"] and isinstance(author.get("display_name"), str):
                        entry["display_name"] = author["display_name"].strip() or None
                    if wid and wid not in entry["work_ids"] and len(entry["work_ids"]) < 3:
                        entry["work_ids"].append(wid)
            if len(works) < self.per_page or (total is not None and examined >= total):
                break
        complete = total is not None and examined >= total and partial_error is None
        provenance = {**provenance, "pages_requested": pages_requested, "pages_succeeded": pages_succeeded,
                      "works_examined": examined, "works_total": total, "truncated": not complete,
                      "partial": partial_error is not None}
        if partial_error:
            provenance["partial_error_code"] = partial_error
        ordered = tuple(coauthors[k] for k in sorted(coauthors))
        status = OK if ordered else EMPTY
        return CoauthorEvidence(status, ordered, examined, total, complete, _now(), provenance)

    # ------------------------------------------------------------------ main
    async def enrich(self, candidates: list[OpenAlexCandidate], ctx: QueryContext) -> EnrichmentReport:
        needs_publications = ctx.has_publications
        needs_coauthors = ctx.has_coauthor_ids     # names alone cannot be scored, so nothing is retrieved for them
        if not self.enabled or not candidates or not (needs_publications or needs_coauthors):
            return EnrichmentReport(list(candidates))
        self._requests = 0
        enriched: list[OpenAlexCandidate] = []
        status: dict[str, dict[str, str | None]] = {}
        query_status: str | None = None
        rate_limited = False
        async with httpx.AsyncClient(timeout=self.timeout_seconds, transport=self.transport) as client:
            lookup: _QueryWorks | None = None
            if needs_publications:
                lookup = await self._lookup_query_works(client, ctx)
                query_status = lookup.status
                rate_limited = lookup.error_code == "rate_limited"
            for candidate in candidates:
                updates: dict[str, Any] = {}
                entry: dict[str, str | None] = {"publications": None, "coauthors": None}
                if lookup is not None:
                    pub = self._publication_evidence(normalize_openalex_id(candidate.source_author_id, "author") or "", lookup, ctx)
                    updates["publication_evidence"] = pub
                    updates["sample_publications"] = (
                        [{"openalex_work_id": w, "doi": None} for w in pub.matched_work_ids] if pub.status == OK else None)
                    entry["publications"] = pub.status
                if needs_coauthors:
                    if rate_limited:
                        co = CoauthorEvidence(FAILED, retrieved_at=_now(), error_code=SKIPPED_AFTER_RATE_LIMIT,
                                              provenance={"provider": "openalex", "endpoint": "works"})
                    else:
                        co = await self._coauthor_sample(client, candidate)
                        rate_limited = co.error_code == "rate_limited"
                    updates["coauthor_evidence"] = co
                    updates["coauthor_summary"] = [dict(c) for c in co.coauthors] if co.status in (OK, EMPTY) else None
                    entry["coauthors"] = co.status
                status[candidate.source_author_id] = entry
                enriched.append(replace(candidate, **updates))
        failed = sum(1 for v in status.values() if FAILED in v.values())
        logger.info("Author enrichment finished: candidates=%d failed=%d requests=%d", len(enriched), failed, self._requests)
        return EnrichmentReport(enriched, query_status, status, self._requests)
