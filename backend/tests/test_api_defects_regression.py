import asyncio
import json
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import main
from database import Base, Publication, DuplicateGroup, SimilarityLog, get_db
from services.author_candidates import AuthorCandidateInput, CandidateGenerationResult, OpenAlexCandidate


def test_author_candidates_whitespace_and_empty_validation():
    with TestClient(main.app) as client:
        # Empty string
        resp_empty = client.post("/author-resolutions/candidates", json={"author_name": ""})
        assert resp_empty.status_code == 422
        assert "cannot be empty" in resp_empty.text

        # Whitespace only
        resp_ws = client.post("/author-resolutions/candidates", json={"author_name": "   "})
        assert resp_ws.status_code == 422
        assert "cannot be empty" in resp_ws.text

        # Single character
        resp_short = client.post("/author-resolutions/candidates", json={"author_name": "a"})
        assert resp_short.status_code == 422
        assert "at least 2 non-whitespace characters" in resp_short.text


def test_get_similarity_log_handles_multiple_duplicate_groups(tmp_path):
    async def scenario():
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'sim_test.db'}")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        sessions = async_sessionmaker(engine, expire_on_commit=False)

        async with sessions() as session:
            pub = Publication(
                canonical_id="doi_test_multi_1",
                title="Test Publication for Multi Groups",
                authors="['Ada Author']",
                year=2024,
            )
            session.add(pub)
            await session.flush()
            pub_id = pub.id

            # Add MULTIPLE duplicate group rows for the same publication
            grp1 = DuplicateGroup(publication_id=pub_id, source_record_ids=json.dumps(["rec_1", "rec_2"]))
            grp2 = DuplicateGroup(publication_id=pub_id, source_record_ids=json.dumps(["rec_3"]))
            session.add_all([grp1, grp2])

            # Add similarity log for rec_1 and rec_2
            sim = SimilarityLog(
                record1_id="rec_1",
                record2_id="rec_2",
                title_sim=0.95,
                author_sim=1.0,
                year_match=True,
                score=0.96,
                decision="MERGED",
            )
            session.add(sim)
            await session.commit()

        async def get_session():
            async with sessions() as session:
                yield session

        main.app.dependency_overrides[get_db] = get_session
        try:
            with TestClient(main.app) as client:
                resp = client.get(f"/similarity-log/{pub_id}")
                assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
                data = resp.json()
                assert data["pub_id"] == pub_id
                assert len(data["logs"]) == 1
                assert data["logs"][0]["decision"] == "MERGED"
                assert data["logs"][0]["score"] == 0.96
        finally:
            main.app.dependency_overrides.pop(get_db, None)
            await engine.dispose()

    asyncio.run(scenario())


def test_get_search_candidates_query_parameter_contract():
    with TestClient(main.app) as client:
        # Omitting 'name' query parameter returns 422
        resp_missing = client.get("/search/candidates")
        assert resp_missing.status_code == 422
        assert "Field required" in resp_missing.text
        assert "name" in resp_missing.text
