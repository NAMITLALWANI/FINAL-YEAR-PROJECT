import json
import asyncio
import time
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from database import (
    init_db, get_db, Publication, SourceRecord,
    SimilarityLog, DuplicateGroup,
    AuthorCandidate, AuthorResolution, AuthorResolutionEvidence,
)
from services.search_service import search as run_search, get_author_candidates
from services.scholarly_retrieval import retrieve, generate_explanation, index_status
from services.author_resolution import (
    AuthorResolutionService, CandidateSourceUnavailable,
    UNRESOLVED, MANUAL_SELECTED, AUTO_RESOLVED,
)
from circuit_breaker import get_all_statuses
from rate_limiter import limiter
from slowapi.errors import RateLimitExceeded
from log_config import configure_root, get_logger
from config import CORS_ORIGINS, LOG_LEVEL, RETRIEVAL_TIMEOUT_SECONDS
from connectors.scrapers.scholar.browser import BrowserManager

logger = get_logger(__name__)

# Global singleton service exposed on module
author_resolution_service = AuthorResolutionService()

# ── Lifespan ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_root(LOG_LEVEL)
    await init_db()
    logger.info("Database initialised")
    
    # Start singleton browser
    browser_manager = BrowserManager.get_instance()
    await browser_manager.start()
    
    yield
    
    logger.info("Shutting down")
    await browser_manager.stop()

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(
    title="Academic Metadata Aggregator",
    description="Phase 1 — hybrid academic paper search across OpenAlex, DBLP, Crossref, arXiv",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests. Max 10/minute per IP.", "detail": str(exc)},
    )


# ── Schemas ───────────────────────────────────────────────────────
class EvidenceSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None


class AuthorCandidateSearchRequest(BaseModel):
    author_name: str
    institution_hint: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    @field_validator("author_name")
    @classmethod
    def validate_author_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("author_name cannot be empty or whitespace")
        if len(v.strip()) < 2:
            raise ValueError("author_name must have at least 2 non-whitespace characters")
        return v.strip()


class CreateAuthorResolutionRequest(BaseModel):
    author_name: str
    institution_hint: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    candidate_ids: Optional[List[str]] = None
    selected_candidate_id: Optional[str] = None
    mark_unresolved: bool = False
    reason: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────

@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    cb_status = await get_all_statuses(db)
    return {
        "status": "ok",
        "circuit_breakers": cb_status,
        "retrieval_index": await asyncio.to_thread(index_status),
    }


@app.post("/evidence/search")
async def search_evidence(req: EvidenceSearchRequest):
    hits = await retrieve(req.query, top_k=req.top_k, filters=req.filters)
    explanation = await generate_explanation(req.query, hits)
    return {
        "hits": [h.as_dict() if hasattr(h, "as_dict") else h for h in hits],
        "explanation": explanation,
        "retrieval_status": "ok",
    }


@app.post("/author-resolutions/candidates")
async def resolve_author_candidates(
    req: AuthorCandidateSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    rows, ranked, status = await author_resolution_service.generate_and_rank(
        req.author_name, req.institution_hint, req.context, db
    )
    if status == "failed" or status not in {"ok", "empty"}:
        return JSONResponse(
            status_code=503,
            content={"error": "Candidate source unavailable: no resolution decision was recorded"},
        )

    hits = await retrieve(req.author_name, top_k=3)
    explanation = await generate_explanation(req.author_name, hits)

    row_by_source_id = {r.source_author_id: r for r in rows}
    candidates_data = []
    for item in ranked:
        c_row = row_by_source_id.get(item.candidate.source_author_id)
        cid = c_row.id if c_row else item.candidate.source_author_id
        candidates_data.append({
            "candidate_id": cid,
            "source_author_id": item.candidate.source_author_id,
            "source": item.candidate.source,
            "display_name": item.candidate.display_name,
            "normalized_name": item.candidate.normalized_name,
            "institution": item.candidate.institution_summary,
            "institution_summary": item.candidate.institution_summary,
            "works_count": item.candidate.works_count,
            "cited_by_count": item.candidate.citation_count,
            "score": item.score.score,
            "available_signals": item.score.available_signals,
            "confidence": "High" if item.score.score and item.score.score >= 0.75 else ("Medium" if item.score.score and item.score.score >= 0.45 else "Low"),
            "evidence": [
                {
                    "signal": e.signal_name,
                    "signal_name": e.signal_name,
                    "signal_value": e.normalized_score,
                    "normalized_score": e.normalized_score,
                    "score": item.score.contributions.get(e.signal_name),
                    "availability": e.availability,
                    "raw_value": e.raw_value,
                    "source": e.provenance.get("source", "") if isinstance(e.provenance, dict) else str(e.provenance),
                }
                for e in item.evidence
            ],
        })

    return {
        "candidates": candidates_data,
        "retrieval": {
            "hits": [h.as_dict() if hasattr(h, "as_dict") else h for h in hits],
            "explanation": explanation,
        },
        "note": "Retrieval context provides topical relevance; it does not change deterministic identity decisions.",
    }


@app.post("/author-resolutions")
async def create_author_resolution(
    req: CreateAuthorResolutionRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        resolution = await author_resolution_service.create_resolution(
            author_name=req.author_name,
            institution_hint=req.institution_hint,
            context=req.context,
            db=db,
            selected_candidate_id=req.selected_candidate_id,
            mark_unresolved=req.mark_unresolved,
            reason=req.reason,
            candidate_ids=req.candidate_ids,
        )
    except CandidateSourceUnavailable as exc:
        return JSONResponse(
            status_code=503,
            content={"error": str(exc)},
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"error": str(exc)},
        )

    return {
        "resolution_id": resolution.id,
        "status": resolution.status,
        "author_id": resolution.author_id,
        "selected_candidate_id": resolution.selected_candidate_id,
        "decision_reason": resolution.decision_reason,
        "top_score": resolution.top_score,
        "second_score": resolution.second_score,
        "score_margin": resolution.score_margin,
        "dominance_ratio": resolution.dominance_ratio,
        "resolved_at": resolution.resolved_at.isoformat() if resolution.resolved_at else None,
    }


@app.get("/author-resolutions/{resolution_id}")
async def get_author_resolution(
    resolution_id: str,
    db: AsyncSession = Depends(get_db),
):
    resolution = await author_resolution_service.get_resolution(resolution_id, db)
    if not resolution:
        raise HTTPException(status_code=404, detail="Resolution not found")

    ev_rows = (await db.execute(
        select(AuthorResolutionEvidence).where(AuthorResolutionEvidence.resolution_id == resolution_id)
    )).scalars().all()

    return {
        "resolution_id": resolution.id,
        "query_original": resolution.query_original,
        "query_normalized": resolution.query_normalized,
        "status": resolution.status,
        "author_id": resolution.author_id,
        "selected_candidate_id": resolution.selected_candidate_id,
        "decision_reason": resolution.decision_reason,
        "top_score": resolution.top_score,
        "second_score": resolution.second_score,
        "score_margin": resolution.score_margin,
        "dominance_ratio": resolution.dominance_ratio,
        "confidence_level": resolution.confidence_level,
        "evidence": [
            {
                "id": e.id,
                "candidate_id": e.candidate_id,
                "signal_name": e.signal_name,
                "normalized_score": e.normalized_score,
                "raw_value": json.loads(e.raw_value_json) if e.raw_value_json else {},
                "explanation": e.explanation,
                "source_provenance": json.loads(e.source_provenance_json) if e.source_provenance_json else {},
                "availability": e.availability,
                "weight": e.weight,
                "weighted_contribution": e.weighted_contribution,
            }
            for e in ev_rows
        ],
    }


@app.get("/search/candidates")
@limiter.limit("20/minute")
async def fetch_candidates(
    request: Request,
    name: str = Query(..., min_length=2, description="Author name to search"),
    institution: str | None = Query(None, description="Optional institution hint"),
    db: AsyncSession = Depends(get_db),
):
    return await get_author_candidates(author_name=name, institution_hint=institution)


@app.get("/search")
@limiter.limit("10/minute")
async def search(
    request: Request,
    name: str = Query(..., min_length=2, description="Author name to search"),
    resolution_id: str | None = Query(None, description="Author resolution ID"),
    candidate_id: str | None = Query(None, description="Explicit candidate ID from /search/candidates"),
    candidate_source: str | None = Query(None, description="Source of the explicit candidate ID"),
    sources: str | None = Query(None, description="Comma-separated source list e.g. openalex,dblp"),
    use_cache: bool = Query(True),
    disable_dedup: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    if resolution_id:
        res = await author_resolution_service.get_resolution(resolution_id, db)
        if not res:
            raise HTTPException(status_code=404, detail="Resolution not found")
        if res.status == UNRESOLVED:
            return {
                "papers": [],
                "message": "Resolution is marked unresolved; no multi-source search was started.",
                "identity_context": {
                    "status": UNRESOLVED,
                    "resolution_id": res.id,
                    "reason": res.decision_reason,
                },
                "source_statuses": {},
                "stats": {},
            }
        # If candidate was selected in resolution
        if res.selected_candidate_id:
            cand = await db.get(AuthorCandidate, res.selected_candidate_id)
            if cand:
                candidate_id = cand.source_author_id
                candidate_source = cand.source

    requested = [s.strip() for s in sources.split(",")] if sources else None
    result = await run_search(
        author_name=name,
        author_id=candidate_id,
        author_source=candidate_source,
        db=db,
        requested_sources=requested,
        use_cache=use_cache,
        disable_dedup=disable_dedup,
    )
    if resolution_id and isinstance(result, dict):
        result["identity_context"] = {
            "status": res.status,
            "resolution_id": res.id,
            "author_id": res.author_id,
        }
    return result


@app.get("/publications/{pub_id}")
async def get_publication(pub_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Publication).where(Publication.id == pub_id))
    pub = result.scalar_one_or_none()
    if not pub:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return {
        "id":               pub.id,
        "canonical_id":     pub.canonical_id,
        "title":            pub.title,
        "authors":          json.loads(pub.authors or "[]"),
        "year":             pub.year,
        "abstract":         pub.abstract,
        "abstract_source":  pub.abstract_source,
        "doi":              pub.doi,
        "doi_source":       pub.doi_source,
        "venue":            pub.venue,
        "venue_source":     pub.venue_source,
        "citations":        pub.citations,
        "citations_source": pub.citations_source,
        "best_source":      pub.best_source,
        "confidence_score": pub.confidence_score,
        "source_count":     pub.source_count,
        "source_list":      json.loads(pub.source_list or "[]"),
    }


@app.get("/similarity-log/{pub_id}")
async def get_similarity_log(pub_id: int, db: AsyncSession = Depends(get_db)):
    grp_res = await db.execute(
        select(DuplicateGroup).where(DuplicateGroup.publication_id == pub_id).order_by(DuplicateGroup.id.desc())
    )
    groups = grp_res.scalars().all()
    if not groups:
        return {"pub_id": pub_id, "logs": []}

    record_ids = []
    for g in groups:
        for rid in json.loads(g.source_record_ids or "[]"):
            if str(rid) not in record_ids:
                record_ids.append(str(rid))
    if not record_ids:
        return {"pub_id": pub_id, "logs": []}

    logs_res = await db.execute(
        select(SimilarityLog).where(
            (SimilarityLog.record1_id.in_(record_ids)) |
            (SimilarityLog.record2_id.in_(record_ids))
        )
    )
    logs = logs_res.scalars().all()
    return {
        "pub_id": pub_id,
        "logs": [
            {
                "record1_id": l.record1_id,
                "record2_id": l.record2_id,
                "title_sim":  l.title_sim,
                "author_sim": l.author_sim,
                "year_match": l.year_match,
                "score":      l.score,
                "decision":   l.decision,
            }
            for l in logs
        ],
    }


@app.get("/metrics")
async def metrics(db: AsyncSession = Depends(get_db)):
    total_pubs   = (await db.execute(select(func.count()).select_from(Publication))).scalar()
    total_raw    = (await db.execute(select(func.count()).select_from(SourceRecord))).scalar()
    total_merges = (await db.execute(
        select(func.count()).select_from(SimilarityLog)
        .where(SimilarityLog.decision == "MERGED")
    )).scalar()

    src_counts_res = await db.execute(
        select(SourceRecord.source, func.count().label("cnt"))
        .group_by(SourceRecord.source)
    )
    source_counts = {row.source: row.cnt for row in src_counts_res}

    cb_status = await get_all_statuses(db)

    return {
        "total_publications": total_pubs,
        "total_raw_records":  total_raw,
        "total_merges":       total_merges,
        "source_record_counts": source_counts,
        "circuit_breakers":   cb_status,
    }


@app.get("/debug/raw-response")
async def debug_raw_response(
    source: str = Query(..., description="Source name (e.g. openalex, dblp)"),
    query: str = Query(..., description="Search query"),
    db: AsyncSession = Depends(get_db),
):
    from connectors.openalex import OpenAlexConnector
    from connectors.dblp import DBLPConnector
    from connectors.arxiv import ArXivConnector
    from connectors.crossref import CrossrefConnector
    from connectors.scholar import ScholarConnector
    from connectors.faculty_scraper import FacultyScraper

    connector_map = {
        "openalex": OpenAlexConnector,
        "dblp": DBLPConnector,
        "arxiv": ArXivConnector,
        "crossref": CrossrefConnector,
        "scholar": ScholarConnector,
        "faculty_page": lambda: FacultyScraper("kjsomaiya"),
    }

    if source not in connector_map:
        return JSONResponse(status_code=400, content={"error": f"Invalid source {source}"})

    try:
        conn = connector_map[source]()
        records = await conn._fetch_impl(query, db=db)
        return {
            "source": source,
            "query": query,
            "count": len(records),
            "records": records
        }
    except Exception as e:
        logger.error(f"Debug Raw Response Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
