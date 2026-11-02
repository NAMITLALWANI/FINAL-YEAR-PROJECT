import asyncio
import httpx
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database import Base, AuthorExternalId, AuthorResolutionEvidence
from services.author_candidates import OpenAlexCandidateService
from services.author_resolution import AuthorResolutionService, MANUAL_SELECTED, UNRESOLVED


def run(value): return asyncio.run(value)


def test_manual_selection_and_unresolved_are_auditable():
    async def scenario():
        def handler(request):
            return httpx.Response(200, json={"results": [
                {"id": "https://openalex.org/A1", "display_name": "Rajesh Kumar", "works_count": 1, "cited_by_count": 1, "last_known_institutions": []},
                {"id": "https://openalex.org/A2", "display_name": "Rajesh Kumar", "works_count": 1, "cited_by_count": 1, "last_known_institutions": []},
            ]})
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection: await connection.run_sync(Base.metadata.create_all)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        service = AuthorResolutionService(OpenAlexCandidateService(transport=httpx.MockTransport(handler)))
        async with sessions() as db:
            rows, _, _ = await service.generate_and_rank("Rajesh Kumar", None, None, db)
            manual = await service.create_resolution("Rajesh Kumar", None, None, db, selected_candidate_id=rows[1].id, reason="Reviewer selected institutional profile.")
            repeated_manual = await service.create_resolution("Rajesh Kumar", None, None, db, selected_candidate_id=rows[1].id, reason="Reviewer confirmed the same source profile.")
            unresolved = await service.create_resolution("Unknown Person", None, None, db, mark_unresolved=True, reason="Reviewer found no supported match.")
            evidence = (await db.execute(__import__('sqlalchemy').select(AuthorResolutionEvidence).where(AuthorResolutionEvidence.resolution_id == manual.id))).scalars().all()
            external_ids = (await db.execute(__import__('sqlalchemy').select(AuthorExternalId).where(AuthorExternalId.external_id == "A2"))).scalars().all()
            assert manual.status == MANUAL_SELECTED
            assert manual.selected_candidate_id == rows[1].id
            assert manual.author_id is not None
            assert repeated_manual.author_id == manual.author_id
            assert len(external_ids) == 1
            assert evidence
            assert unresolved.status == UNRESOLVED
            assert "Reviewer" in unresolved.decision_reason
        await engine.dispose()
    run(scenario())


def test_explicit_empty_candidate_list_does_not_repeat_source_request():
    async def scenario():
        class CandidateService:
            async def generate(self, request):
                raise AssertionError("An explicit empty cached result must not fetch candidates again")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        service = AuthorResolutionService(CandidateService())
        async with sessions() as db:
            result = await service.create_resolution(
                "Unknown Person", None, None, db, mark_unresolved=True,
                reason="No candidates were returned.", candidate_ids=[],
            )
            assert result.status == UNRESOLVED
            assert result.decision_reason == "No candidates were returned."
        await engine.dispose()

    run(scenario())