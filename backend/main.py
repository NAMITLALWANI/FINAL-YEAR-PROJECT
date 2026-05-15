import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from database import (
    init_db, get_db, Publication, SourceRecord,
    SimilarityLog, DuplicateGroup,
)
from services.search_service import search as run_search, get_author_candidates
from circuit_breaker import get_all_statuses
from rate_limiter import limiter
from slowapi.errors import RateLimitExceeded
from log_config import configure_root, get_logger
from config import LOG_LEVEL
from connectors.scrapers.scholar.browser import BrowserManager

logger = get_logger(__name__)

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
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests. Max 10/minute per IP.", "detail": str(exc)},
    )


# ── Routes ────────────────────────────────────────────────────────

@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    cb_status = await get_all_statuses(db)
    return {
        "status": "ok",
        "circuit_breakers": cb_status,
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
    candidate_id: str | None = Query(None, description="Explicit candidate ID from /search/candidates"),
    candidate_source: str | None = Query(None, description="Source of the explicit candidate ID"),
    sources: str | None = Query(None, description="Comma-separated source list e.g. openalex,dblp"),
    use_cache: bool = Query(True),
    disable_dedup: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
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
    # Get source_record IDs for this publication
    grp_res = await db.execute(
        select(DuplicateGroup).where(DuplicateGroup.publication_id == pub_id)
    )
    group = grp_res.scalar_one_or_none()
    if not group:
        return {"pub_id": pub_id, "logs": []}

    record_ids = json.loads(group.source_record_ids or "[]")
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

    # Per-source record counts
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
    """Debug endpoint to see raw responses from connectors without DB involvement."""
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
        # Bypassing BaseConnector circuit breakers for direct debug
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
