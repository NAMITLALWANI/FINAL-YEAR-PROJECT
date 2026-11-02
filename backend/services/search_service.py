import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import Publication, SourceRecord, SimilarityLog, DuplicateGroup, CacheEntry
from pipeline.normalize import normalize
from pipeline.deduplicate import deduplicate, MergedPublication
from config import ENABLE_OPENALEX, ENABLE_DBLP, ENABLE_ARXIV, ENABLE_CROSSREF, ENABLE_FACULTY, ENABLE_SCHOLAR

from connectors.openalex import OpenAlexConnector
from connectors.dblp import DBLPConnector
from connectors.arxiv import ArXivConnector
from connectors.crossref import CrossrefConnector
from connectors.scholar import ScholarConnector
from connectors.faculty_scraper import FacultyScraper
from log_config import get_logger

logger = get_logger(__name__)


def _get_active_connectors(requested_sources: list[str] = None):
    all_connectors = [
        OpenAlexConnector(),
        DBLPConnector(),
        ArXivConnector(),
        CrossrefConnector(),
        ScholarConnector(),
        FacultyScraper("kjsomaiya"),
    ]
    if requested_sources:
        return [c for c in all_connectors if c.source_name in requested_sources]
    
    def _source_enabled(name):
        return {
            "openalex": ENABLE_OPENALEX,
            "dblp": ENABLE_DBLP,
            "arxiv": ENABLE_ARXIV,
            "crossref": ENABLE_CROSSREF,
            "faculty_page": ENABLE_FACULTY,
            "scholar": ENABLE_SCHOLAR,
        }.get(name, False)
        
    return [c for c in all_connectors if _source_enabled(c.source_name)]


async def get_author_candidates(author_name: str, institution_hint: str = None) -> dict:
    if not ENABLE_OPENALEX:
        return {"multiple_candidates": False, "candidates": []}
    
    openalex = OpenAlexConnector()
    cands = await openalex.search_authors(author_name, institution_hint)
    
    if not cands:
        return {"multiple_candidates": False, "candidates": []}

    for c in cands:
        if c["score"] >= 0.8:
            c["confidence"] = "High"
        elif c["score"] >= 0.4:
            c["confidence"] = "Medium"
        else:
            c["confidence"] = "Low"
    
    cands = _boost_candidates_by_institution(cands, institution_hint)
    cands.sort(key=lambda x: x["score"], reverse=True)

    if not cands:
        return {"candidates": [], "multiple_candidates": False, "auto_selected": False}

    top = cands[0]
    top_score = top["score"]
    top_works = top.get("works_count", 0)

    dominance_ratio = 1.0
    if len(cands) > 1:
        second_works = cands[1].get("works_count", 0)
        dominance_ratio = top_works / (second_works + 1)
    else:
        dominance_ratio = 999.0

    auto_select = False
    if top_score > 0.60 and dominance_ratio > 3:
        auto_select = True

    logger.info(json.dumps({
        "top_candidate": top.get("display_name"),
        "candidate_score": top_score,
        "dominance_ratio": round(dominance_ratio, 2),
        "auto_selected": auto_select
    }))

    if auto_select:
        return {"candidates": [top], "multiple_candidates": False, "auto_selected": True}

    return {"candidates": cands, "multiple_candidates": True, "auto_selected": False}


async def _fetch_from_connector(connector, author_name: str, author_id: str, db: AsyncSession) -> tuple[list[dict], dict]:
    source = connector.source_name
    from circuit_breaker import is_source_available, record_failure, record_success
    if not await is_source_available(source, db):
        logger.warning(f"Circuit breaker OPEN for {source}, skipping.")
        return [], {"status": "circuit_open"}

    kwargs = {"db": db}
    if author_id and getattr(connector, "source_name", "") == "openalex":
        kwargs["author_id"] = author_id

    records, status = await connector.fetch(author_name, **kwargs)

    if status.get("status") == "failed":
        await record_failure(source, db)
    else:
        await record_success(source, db)

    return records, status


async def search(
    author_name: str,
    db: AsyncSession,
    author_id: str = None,
    author_source: str = None,
    requested_sources: list[str] = None,
    use_cache: bool = True,
    disable_dedup: bool = False,
) -> dict:
    t_start = time.monotonic()
    
    query_key = f"{author_name.lower().strip()}_{author_id or 'none'}_{disable_dedup}"
    
    if use_cache:
        res = await db.execute(select(CacheEntry).where(CacheEntry.query_key == query_key))
        cached = res.scalar_one_or_none()
        if cached and cached.expires_at:
            now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
            expires = cached.expires_at.replace(tzinfo=None) if cached.expires_at.tzinfo else cached.expires_at
            if expires > now_naive:
                logger.info(f"Cache HIT for {query_key}")
                data = json.loads(cached.result_json)
                data["cache_hit"] = True
                return data

    if not author_id and requested_sources is None:
        cand_res = await get_author_candidates(author_name)
        if cand_res.get("multiple_candidates"):
            return cand_res

    logger.info(f"Cache MISS for {query_key}, triggering fan-out.")

    connectors = _get_active_connectors(requested_sources)
    tasks = [_fetch_from_connector(c, author_name, author_id, db) for c in connectors]
    results = await asyncio.gather(*tasks)

    all_raw = []
    source_statuses = {}

    for conn, (records, status) in zip(connectors, results):
        source = conn.source_name
        source_statuses[source] = status
        
        for r in records:
            all_raw.append(r)
            db.add(SourceRecord(
                source=r["source"],
                source_id=r.get("source_id"),
                title=r.get("title"),
                authors_raw=json.dumps(r.get("authors", [])),
                year=r.get("year"),
                venue=r.get("venue"),
                doi=r.get("doi"),
                abstract=r.get("abstract"),
                citations=r.get("citations"),
                url=r.get("url"),
                raw_json=json.dumps(r)
            ))
    
    await db.commit()

    normalized_records = [normalize(r) for r in all_raw if r]

    if disable_dedup:
        papers = []
        for i, rec in enumerate(normalized_records):
            mp = MergedPublication(
                canonical_id=f"raw_{i}",
                title=rec.title,
                authors=rec.authors,
                year=rec.year,
                abstract=rec.abstract,
                abstract_source=rec.source,
                doi=rec.doi,
                doi_source=rec.source,
                venue=rec.venue,
                venue_source=rec.source,
                citations=rec.citations,
                citations_source=rec.source,
                best_source=rec.source,
                confidence_score=1.0,
                source_count=1,
                source_list=[rec.source],
                source_record_ids=[i]
            )
            papers.append(mp)
        merge_logs = []
    else:
        papers, merge_logs = deduplicate(normalized_records)

    # Persist
    await _persist_publications(papers, merge_logs, normalized_records, db)

    # Convert to dict for response
    import dataclasses
    papers_dict = []
    for p in papers:
        if dataclasses.is_dataclass(p):
            papers_dict.append(dataclasses.asdict(p))
        else:
            papers_dict.append(p)

    response = {
        "query":          author_name,
        "candidate_id":   author_id,
        "total":          len(papers),
        "raw_records":    len(all_raw),
        "merged_count":   len(all_raw) - len(papers),
        "time_ms":        round((time.monotonic() - t_start) * 1000),
        "cache_hit":      False,
        "source_statuses": source_statuses,
        "papers":         papers_dict,
    }

    # Use merge to avoid UNIQUE constraint errors
    await db.merge(CacheEntry(
        query_key=query_key,
        result_json=json.dumps(response),
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=12)).replace(tzinfo=None)
    ))
    await db.commit()

    return response


async def _persist_publications(papers, merge_logs, normalized_records, db: AsyncSession):
    for pub in papers:
        res = await db.execute(select(Publication).where(Publication.canonical_id == pub.canonical_id))
        existing = res.scalar_one_or_none()
        if not existing and pub.doi:
            res_doi = await db.execute(select(Publication).where(Publication.doi == pub.doi))
            existing = res_doi.scalars().first()
        if not existing and pub.title:
            res_title = await db.execute(select(Publication).where(func.lower(Publication.title) == pub.title.strip().lower()))
            existing = res_title.scalars().first()

        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

        if existing:
            existing.citations = max(existing.citations or 0, pub.citations or 0)
            existing.source_count = pub.source_count
            existing.source_list = json.dumps(pub.source_list)
            if pub.abstract: existing.abstract = pub.abstract
            pub_id = existing.id
        else:
            row = Publication(
                canonical_id      = pub.canonical_id,
                title             = pub.title,
                authors           = json.dumps(pub.authors),
                year              = pub.year,
                abstract          = pub.abstract,
                abstract_source   = pub.abstract_source,
                doi               = pub.doi,
                doi_source        = pub.doi_source,
                venue             = pub.venue,
                venue_source      = pub.venue_source,
                citations         = pub.citations,
                citations_source  = pub.citations_source,
                best_source       = pub.best_source,
                confidence_score  = pub.confidence_score,
                source_count      = pub.source_count,
                source_list       = json.dumps(pub.source_list),
                scholar_scraped_at=now_naive if "scholar" in pub.source_list else None,
                merged_at         = now_naive
            )
            db.add(row)
            await db.flush()
            pub_id = row.id

        source_ids = [normalized_records[idx].source_id for idx in pub.source_record_ids if normalized_records[idx].source_id]
        if source_ids:
            grp_res = await db.execute(select(DuplicateGroup).where(DuplicateGroup.publication_id == pub_id))
            grp = grp_res.scalars().first()
            if grp:
                grp.source_record_ids = json.dumps(source_ids)
            else:
                db.add(DuplicateGroup(publication_id=pub_id, source_record_ids=json.dumps(source_ids)))

    for log in merge_logs:
        s1 = normalized_records[log.record1_idx].source_id or f"idx_{log.record1_idx}"
        s2 = normalized_records[log.record2_idx].source_id or f"idx_{log.record2_idx}"
        
        db.add(SimilarityLog(
            record1_id=s1,
            record2_id=s2,
            title_sim=log.title_sim,
            author_sim=log.author_sim,
            year_match=log.year_match,
            score=log.score,
            decision=log.decision,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        ))
    
    await db.commit()


def _boost_candidates_by_institution(cands: list[dict], hint: str) -> list[dict]:
    if not hint:
        return cands
    hint_lower = hint.lower()
    for c in cands:
        inst = c.get("institution", "").lower()
        if hint_lower in inst or inst in hint_lower:
            c["score"] += 0.2
            c["confidence"] = "High"
    return cands
