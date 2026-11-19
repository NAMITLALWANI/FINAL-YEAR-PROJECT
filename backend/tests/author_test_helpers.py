"""Shared offline helpers for author-resolution tests. No network, no real database."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime

import httpx

from author_resolution.candidates import AuthorCandidateInput, OpenAlexCandidate
from author_resolution.context import QueryContext
from author_resolution.enrichment_types import CoauthorEvidence, PublicationLinkEvidence
from author_resolution.resolver import RankedCandidate, rank_candidates

NOW = datetime(2026, 1, 1)


def payload(aid="A1", name="Alice Smith", inst="Example Institute", inst_id="I100", ror=None, years=(2019, 2023), alts=()):
    institutions = []
    if inst:
        institutions = [{"id": f"https://openalex.org/{inst_id}", "display_name": inst, "country_code": "US",
                         **({"ror": f"https://ror.org/{ror}"} if ror else {})}]
    return {
        "id": f"https://openalex.org/{aid}", "display_name": name, "works_count": 10, "cited_by_count": 5,
        "display_name_alternatives": list(alts), "last_known_institutions": institutions,
        "counts_by_year": [{"year": y, "works_count": 1} for y in years] if years else [],
    }


def cand(aid="A1", name="Alice Smith", query="Alice Smith", **kw) -> OpenAlexCandidate:
    return OpenAlexCandidate.from_openalex(payload(aid, name, **kw), AuthorCandidateInput(query), NOW)


def with_pub(candidate: OpenAlexCandidate, ctx: QueryContext, matched=(), comparable=None, status="ok", unresolved=(), truncated=(), error=None):
    comparable = tuple(matched) if comparable is None else tuple(comparable)
    return replace(candidate, publication_evidence=PublicationLinkEvidence(
        status, ctx.publication_fingerprint(), comparable, tuple(matched), (), tuple(unresolved), tuple(truncated),
        "2026-01-01T00:00:00", {"provider": "openalex"}, error))


def with_co(candidate: OpenAlexCandidate, coauthors=(), status="ok", complete=True, error=None):
    return replace(candidate, coauthor_evidence=CoauthorEvidence(
        status, tuple(coauthors), 10, 10 if complete else 500, complete, "2026-01-01T00:00:00", {"provider": "openalex"}, error))


def co(aid, name, works=("W1",)):
    return {"openalex_id": aid, "display_name": name, "work_ids": list(works)}


def rank(candidates, ctx):
    return rank_candidates(candidates, ctx)


def by_signal(evidence):
    return {e.signal_name: e for e in evidence}


def json_response(body, status=200):
    return httpx.Response(status, json=body)


def work(wid, doi, author_ids, truncated=False, year=2020):
    return {
        "id": f"https://openalex.org/{wid}", "doi": f"https://doi.org/{doi}" if doi else None, "publication_year": year,
        "is_authors_truncated": truncated,
        "authorships": [{"author": {"id": f"https://openalex.org/{a}", "display_name": f"Name {a}"}} for a in author_ids],
    }
