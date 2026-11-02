import asyncio
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import main
from database import AuthorResolution, Base, get_db
from services.author_candidates import AuthorCandidateInput, CandidateGenerationResult, OpenAlexCandidate
from services.scholarly_retrieval import RetrievalHit


def test_local_author_and_evidence_api_workflow_persists_only_valid_decisions(tmp_path, monkeypatch):
    async def scenario():
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'workflow.db'}")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        generation_calls = []
        search_calls = []
        candidates = [
            OpenAlexCandidate.from_openalex(
                {
                    "id": f"https://openalex.org/A{n}",
                    "display_name": "Ada Example",
                    "works_count": 12 + n,
                    "cited_by_count": 30 + n,
                    "last_known_institutions": [{"id": f"I{n}", "display_name": f"Example University {n}"}],
                    "counts_by_year": [{"year": 2021, "works_count": 1}],
                },
                AuthorCandidateInput("Ada Example"),
                datetime.now(timezone.utc).replace(tzinfo=None),
            )
            for n in (1, 2)
        ]

        async def generate(request):
            generation_calls.append(request.author_name)
            if request.author_name == "Failure Example":
                return CandidateGenerationResult(request, status="failed", error_code="network_error")
            return CandidateGenerationResult(request, status="ok", candidates=candidates)

        async def get_session():
            async with sessions() as session:
                yield session

        async def retrieve(query, top_k=5, filters=None):
            return [RetrievalHit(
                "doc-evidence", "doi:10.1000/demo", "Evidence for scholarly discovery",
                "A retrieved abstract.", "10.1000/demo", 2024, "Example Journal",
                ["Ada Example"], ["Example University"], ["crossref"], ["source-1"],
                {"crossref": ["R123"]}, "https://example.org/record", 0.74, 1, "hash-1",
            )]

        async def explain(query, hits):
            return {"status": "provider_not_configured", "summary": "Retrieved topical context; it does not establish identity.", "claims": []}

        async def search(**kwargs):
            search_calls.append(kwargs)
            return {"papers": [{"canonical_id": "doi:10.1000/demo", "title": "Evidence for scholarly discovery"}], "source_statuses": {}, "stats": {}}

        async def no_op():
            return None

        class BrowserStub:
            async def start(self): return None
            async def stop(self): return None

        monkeypatch.setattr(main.author_resolution_service.candidate_service, "generate", generate)
        monkeypatch.setattr(main, "retrieve", retrieve)
        monkeypatch.setattr(main, "generate_explanation", explain)
        monkeypatch.setattr(main, "run_search", search)
        # TestClient lifespan must not initialize or write the real configured DB.
        monkeypatch.setattr(main, "init_db", no_op)
        monkeypatch.setattr(main.BrowserManager, "get_instance", lambda: BrowserStub())
        main.app.dependency_overrides[get_db] = get_session
        try:
            with TestClient(main.app) as client:
                evidence_search = client.post("/evidence/search", json={"query": "scholarly discovery", "top_k": 3})
                assert evidence_search.status_code == 200
                assert evidence_search.json()["hits"][0]["document_id"] == "doc-evidence"
                assert evidence_search.json()["explanation"]["status"] == "provider_not_configured"

                candidate_response = client.post("/author-resolutions/candidates", json={"author_name": "Ada Example"})
                assert candidate_response.status_code == 200
                candidate_payload = candidate_response.json()
                assert len(candidate_payload["candidates"]) == 2
                assert candidate_payload["retrieval"]["hits"][0]["document_id"] == "doc-evidence"
                assert "does not change" in candidate_payload["note"]
                ids = [item["candidate_id"] for item in candidate_payload["candidates"]]

                selected = client.post("/author-resolutions", json={
                    "author_name": "Ada Example", "candidate_ids": ids,
                    "selected_candidate_id": ids[0],
                })
                assert selected.status_code == 200
                selected_payload = selected.json()
                assert selected_payload["status"] == "manual_selected"
                assert selected_payload["author_id"]

                details = client.get(f"/author-resolutions/{selected_payload['resolution_id']}")
                assert details.status_code == 200
                assert details.json()["status"] == "manual_selected"
                assert details.json()["evidence"]

                papers = client.get("/search", params={"name": "Ada Example", "resolution_id": selected_payload["resolution_id"]})
                assert papers.status_code == 200
                assert papers.json()["identity_context"]["status"] == "manual_selected"
                assert len(papers.json()["papers"]) == 1
                assert len(search_calls) == 1

                unresolved = client.post("/author-resolutions", json={
                    "author_name": "Ada Example", "candidate_ids": ids,
                    "mark_unresolved": True, "reason": "Insufficient source evidence.",
                })
                assert unresolved.status_code == 200
                unresolved_payload = unresolved.json()
                assert unresolved_payload["status"] == "unresolved"
                blocked_search = client.get("/search", params={"name": "Ada Example", "resolution_id": unresolved_payload["resolution_id"]})
                assert blocked_search.status_code == 200
                assert "no multi-source search was started" in blocked_search.json()["message"]
                assert len(search_calls) == 1

                failed_candidates = client.post("/author-resolutions/candidates", json={"author_name": "Failure Example"})
                assert failed_candidates.status_code == 503
                assert "no resolution decision was recorded" in failed_candidates.json()["error"]
                failed_resolution = client.post("/author-resolutions", json={"author_name": "Failure Example"})
                assert failed_resolution.status_code == 503
                async with sessions() as db:
                    count = await db.scalar(select(func.count()).select_from(AuthorResolution))
                    assert count == 2
                assert generation_calls == ["Ada Example", "Failure Example", "Failure Example"]
        finally:
            main.app.dependency_overrides.pop(get_db, None)
            await engine.dispose()

    asyncio.run(scenario())