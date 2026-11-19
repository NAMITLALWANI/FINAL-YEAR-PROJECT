"""Empty retrieval vs provider failure vs partial enrichment, at service and API level. Offline only."""
import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import main
from author_resolution.candidates import OpenAlexCandidateService
from author_resolution.enrichment import CandidateEnrichmentService
from author_resolution.resolver import AuthorResolutionService, CandidateSourceUnavailable
from database import AuthorCandidate, AuthorResolution, AuthorResolutionEvidence, Base, get_db
from author_test_helpers import json_response, payload, work


def run(coro):
    return asyncio.run(coro)


def authors_handler(results=None, status=200, raises=None, text=None):
    def handler(request):
        if raises:
            raise raises
        if text is not None:
            return httpx.Response(status, text=text)
        return httpx.Response(status, json={"results": results or []})
    return handler


def make_service(authors, works=None):
    works_handler = works or (lambda request: httpx.Response(200, json={"results": [], "meta": {"count": 0}}))
    return AuthorResolutionService(
        OpenAlexCandidateService(transport=httpx.MockTransport(authors)),
        CandidateEnrichmentService(transport=httpx.MockTransport(works_handler)),
    )


async def counts(db):
    return {
        "candidates": await db.scalar(select(func.count()).select_from(AuthorCandidate)),
        "resolutions": await db.scalar(select(func.count()).select_from(AuthorResolution)),
        "evidence": await db.scalar(select(func.count()).select_from(AuthorResolutionEvidence)),
    }


async def memory_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def test_successful_empty_response_is_an_unresolved_decision_not_a_provider_failure():
    async def scenario():
        engine, sessions = await memory_db()
        service = make_service(authors_handler([]))
        async with sessions() as db:
            outcome = await service.create_resolution_detailed("Nobody Known", None, None, db)
            assert outcome.retrieval_status == "empty" and outcome.resolution.status == "unresolved"
            assert "successful empty response" in outcome.resolution.decision_reason
            assert await counts(db) == {"candidates": 0, "resolutions": 1, "evidence": 0}      # no fake candidate rows
        await engine.dispose()
    run(scenario())


@pytest.mark.parametrize("handler,code", [
    (authors_handler(status=500), "http_error"),
    (authors_handler(status=429), "rate_limited"),
    (authors_handler(raises=httpx.ReadTimeout("slow")), "timeout"),
    (authors_handler(text="not json"), "malformed_response"),
])
def test_provider_failures_raise_with_a_code_and_record_nothing(handler, code):
    async def scenario():
        engine, sessions = await memory_db()
        service = make_service(handler)
        async with sessions() as db:
            with pytest.raises(CandidateSourceUnavailable) as caught:
                await service.create_resolution_detailed("Alice Smith", None, None, db)
            assert caught.value.error_code == code
            assert await counts(db) == {"candidates": 0, "resolutions": 0, "evidence": 0}
        await engine.dispose()
    run(scenario())


def test_malformed_candidate_items_are_dropped_but_the_pool_survives():
    async def scenario():
        engine, sessions = await memory_db()
        service = make_service(authors_handler([payload("A1"), {"id": None, "display_name": ""}, "junk"]))
        async with sessions() as db:
            pool = await service.generate_pool("Alice Smith", None, None, db)
            assert pool.status == "ok" and [r.source_author_id for r in pool.rows] == ["A1"]
        await engine.dispose()
    run(scenario())


def test_partial_enrichment_failure_is_reported_and_withholds_automatic_assignment():
    async def scenario():
        engine, sessions = await memory_db()
        service = make_service(authors_handler([payload("A1")]), works=lambda r: httpx.Response(500, json={}))
        ctx = {"coauthors": [{"openalex_id": "A7"}]}
        async with sessions() as db:
            outcome = await service.create_resolution_detailed("Alice Smith", "Example Institute", ctx, db)
            assert outcome.enrichment["any_failed"] is True
            assert outcome.resolution.status == "manual_selection_required"        # would be auto on name+institution alone
            assert "evidence retrieval failed" in outcome.resolution.decision_reason
            rows = (await db.execute(select(AuthorResolutionEvidence).where(AuthorResolutionEvidence.signal_name == "coauthor_overlap"))).scalars().all()
            assert rows[0].availability == "unavailable" and rows[0].normalized_score is None
            assert json.loads(rows[0].source_provenance_json)["status"] == "unavailable_retrieval_failed"
        await engine.dispose()
    run(scenario())


def test_enrichment_is_persisted_and_only_reused_for_the_same_context():
    async def scenario():
        engine, sessions = await memory_db()
        works = lambda r: httpx.Response(200, json={"results": [work("W1", "10.1000/a", ["A1"])], "meta": {"count": 1}})
        service = make_service(authors_handler([payload("A1")]), works=works)
        ctx = {"publications": ["10.1000/a"]}
        async with sessions() as db:
            pool = await service.generate_pool("Alice Smith", "Example Institute", ctx, db)
            ids = [r.id for r in pool.rows]
            same = await service.create_resolution_detailed("Alice Smith", "Example Institute", ctx, db, candidate_ids=ids)
            ev = {e.signal_name: e for e in (await db.execute(select(AuthorResolutionEvidence).where(AuthorResolutionEvidence.resolution_id == same.resolution.id))).scalars()}
            assert ev["publication_overlap"].availability == "available" and ev["publication_overlap"].normalized_score == 1.0
            assert ev["publication_overlap"].weight == pytest.approx(0.2 / 0.8)        # effective (renormalised) weight is stored
            other = await service.create_resolution_detailed("Alice Smith", "Example Institute", {"publications": ["10.1000/other"]}, db, candidate_ids=ids)
            ev2 = {e.signal_name: e for e in (await db.execute(select(AuthorResolutionEvidence).where(AuthorResolutionEvidence.resolution_id == other.resolution.id))).scalars()}
            assert ev2["publication_overlap"].availability == "unavailable"
            assert json.loads(ev2["publication_overlap"].source_provenance_json)["status"] == "unavailable_not_retrieved"
        await engine.dispose()
    run(scenario())


def test_manual_selection_records_the_algorithmic_assessment_separately():
    async def scenario():
        engine, sessions = await memory_db()
        service = make_service(authors_handler([payload("A1"), payload("A2")]))
        async with sessions() as db:
            rows, _, _ = await service.generate_and_rank("Alice Smith", None, None, db)
            outcome = await service.create_resolution_detailed("Alice Smith", None, None, db, selected_candidate_id=rows[0].id,
                                                               candidate_ids=[r.id for r in rows], reason="Reviewer picked.")
            assert outcome.resolution.status == "manual_selected"
            assert outcome.resolution.decision_reason.startswith("Reviewer picked.")
            assert "Algorithmic assessment: manual_selection_required" in outcome.resolution.decision_reason
        await engine.dispose()
    run(scenario())


def test_algorithmic_automatic_decision_is_persisted_only_when_policy_permits():
    async def scenario():
        engine, sessions = await memory_db()
        async with sessions() as db:
            sufficient = make_service(authors_handler([payload("A1")]))
            auto = await sufficient.create_resolution_detailed("Alice Smith", "Example Institute", None, db)
            assert auto.resolution.status == "auto_selected" and auto.resolution.selected_candidate_id and auto.resolution.confidence_level == "engineering_heuristic"
            name_only = make_service(authors_handler([payload("A2", name="Alice Smith")]))
            held = await name_only.create_resolution_detailed("Alice Smith", None, None, db)
            assert held.resolution.status == "manual_selection_required" and held.resolution.selected_candidate_id is None
        await engine.dispose()
    run(scenario())


# ----------------------------------------------------------------------------- API
def api_client(tmp_path, monkeypatch, authors, works=None):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'api.db'}")

    async def prepare():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    asyncio.run(prepare())
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def get_session():
        async with sessions() as session:
            yield session

    async def no_op():
        return None

    async def retrieve(query, top_k=5, filters=None):
        return []

    async def explain(query, hits):
        return {"status": "abstained", "summary": "none", "claims": []}

    class BrowserStub:
        async def start(self): return None
        async def stop(self): return None

    service = make_service(authors, works)
    monkeypatch.setattr(main, "author_resolution_service", service)
    monkeypatch.setattr(main, "retrieve", retrieve)
    monkeypatch.setattr(main, "generate_explanation", explain)
    monkeypatch.setattr(main, "init_db", no_op)
    monkeypatch.setattr(main.BrowserManager, "get_instance", lambda: BrowserStub())
    main.app.dependency_overrides[get_db] = get_session
    return engine


def test_api_distinguishes_empty_from_failed_and_validates_context(tmp_path, monkeypatch):
    engine = api_client(tmp_path, monkeypatch, authors_handler([]))
    try:
        with TestClient(main.app) as client:
            empty = client.post("/author-resolutions/candidates", json={"author_name": "Nobody Known"})
            assert empty.status_code == 200
            assert empty.json()["candidate_retrieval_status"] == "empty" and empty.json()["candidates"] == []
            created = client.post("/author-resolutions", json={"author_name": "Nobody Known"})
            assert created.status_code == 200 and created.json()["status"] == "unresolved"
            assert created.json()["candidate_retrieval_status"] == "empty" and created.json()["decision_source"] == "algorithm"
            bad = client.post("/author-resolutions/candidates", json={"author_name": "Alice Smith", "context": {"publications": ["nonsense"]}})
            assert bad.status_code == 422
            bad_years = client.post("/author-resolutions/candidates", json={"author_name": "Alice Smith", "context": {"active_year_start": 2030, "active_year_end": 2020}})
            assert bad_years.status_code == 422
    finally:
        main.app.dependency_overrides.clear()
        asyncio.run(engine.dispose())


def test_api_provider_failure_returns_503_with_code_and_records_nothing(tmp_path, monkeypatch):
    engine = api_client(tmp_path, monkeypatch, authors_handler(status=500))
    try:
        with TestClient(main.app) as client:
            for url, body in (("/author-resolutions/candidates", {"author_name": "Alice Smith"}), ("/author-resolutions", {"author_name": "Alice Smith"})):
                response = client.post(url, json=body)
                assert response.status_code == 503
                assert response.json()["error_code"] == "http_error" and response.json()["candidate_retrieval_status"] == "failed"

        async def totals():
            sessions = async_sessionmaker(engine, expire_on_commit=False)
            async with sessions() as db:
                return await counts(db)
        assert asyncio.run(totals()) == {"candidates": 0, "resolutions": 0, "evidence": 0}
    finally:
        main.app.dependency_overrides.clear()
        asyncio.run(engine.dispose())


def test_api_candidates_report_context_signal_status_and_algorithmic_assessment(tmp_path, monkeypatch):
    works = lambda r: httpx.Response(200, json={"results": [work("W1", "10.1000/a", ["A1"])], "meta": {"count": 1}})
    engine = api_client(tmp_path, monkeypatch, authors_handler([payload("A1")]), works)
    try:
        with TestClient(main.app) as client:
            body = client.post("/author-resolutions/candidates", json={
                "author_name": "Alice Smith", "institution_hint": "Example Institute",
                "context": {"publications": ["https://doi.org/10.1000/A"], "active_year_start": 2020, "active_year_end": 2022}}).json()
            assert body["context_received"]["institution"] and body["context_received"]["publications"] and not body["context_received"]["coauthors"]
            cand = body["candidates"][0]
            statuses = {e["signal_name"]: e["status"] for e in cand["evidence"]}
            assert statuses["publication_overlap"] == "observed" and statuses["coauthor_overlap"] == "unavailable_query_input_absent"
            assert cand["score_is_heuristic"] is True and "coauthor_overlap" not in cand["signal_set"]
            assert body["algorithmic_assessment"]["status"] == "auto_selected"
            ids = [cand["candidate_id"]]
            saved = client.post("/author-resolutions", json={
                "author_name": "Alice Smith", "institution_hint": "Example Institute", "candidate_ids": ids,
                "selected_candidate_id": ids[0], "context": {"publications": ["10.1000/a"], "active_year_start": 2020, "active_year_end": 2022}}).json()
            assert saved["status"] == "manual_selected" and saved["decision_source"] == "reviewer"
            assert saved["algorithmic_assessment"]["status"] == "auto_selected"
    finally:
        main.app.dependency_overrides.clear()
        asyncio.run(engine.dispose())
