from datetime import datetime

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from database import (
    Author,
    AuthorAlias,
    AuthorCandidate,
    AuthorExternalId,
    AuthorResolution,
    AuthorResolutionEvidence,
    Base,
    Publication,
    PublicationAuthorship,
    SourceRecord,
)


def test_existing_and_author_resolution_tables_create_together():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    table_names = set(inspect(engine).get_table_names())
    assert {"publications", "source_records", "duplicate_groups", "similarity_logs"} <= table_names
    assert {
        "authors",
        "author_external_ids",
        "author_aliases",
        "author_affiliations",
        "author_candidates",
        "author_resolutions",
        "author_resolution_evidence",
        "publication_authorships",
    } <= table_names


def test_author_resolution_relationships_and_provenance_persist():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        publication = Publication(
            canonical_id="doi_test",
            title="A test publication",
            source_count=1,
            merged_at=datetime.utcnow(),
        )
        source_record = SourceRecord(source="openalex", title="A test publication")
        author = Author(display_name="Test Author", normalized_name="test author")
        candidate = AuthorCandidate(
            query_original="Test Author",
            query_normalized="test author",
            source="openalex",
            source_author_id="A123",
            display_name="Test Author",
            normalized_name="test author",
        )
        session.add_all([publication, source_record, author, candidate])
        session.flush()

        external_id = AuthorExternalId(
            author=author,
            source="openalex",
            external_id="A123",
            provenance_json='{"retrieved_from":"fixture"}',
        )
        alias = AuthorAlias(
            author=author,
            alias="T. Author",
            normalized_alias="t author",
            source="openalex",
        )
        resolution = AuthorResolution(
            query_original="Test Author",
            query_normalized="test author",
            status="manual_selected",
            selected_candidate=candidate,
            author=author,
            resolver_version="v1",
            scoring_version="v1",
            threshold_version="v1",
        )
        session.add_all([external_id, alias, resolution])
        session.flush()

        evidence = AuthorResolutionEvidence(
            resolution=resolution,
            candidate=candidate,
            signal_name="name_similarity",
            normalized_score=1.0,
            weight=0.2,
            weighted_contribution=0.2,
            availability="available",
            explanation="Exact normalized-name match.",
        )
        authorship = PublicationAuthorship(
            publication_id=publication.id,
            source_record_id=source_record.id,
            author=author,
            author_candidate=candidate,
            author_position=0,
            author_name_raw="Test Author",
            normalized_author_name="test author",
            source="openalex",
            source_author_id="A123",
            identity_strength="source_identified",
            confidence=1.0,
        )
        session.add_all([evidence, authorship])
        session.commit()

        persisted = session.get(Author, author.id)
        assert persisted is not None
        assert persisted.external_ids[0].external_id == "A123"
        assert persisted.aliases[0].normalized_alias == "t author"
        assert persisted.resolutions[0].selected_candidate_id == candidate.id
        assert persisted.resolutions[0].evidence_rows[0].signal_name == "name_similarity"
        assert persisted.publication_authorships[0].identity_strength == "source_identified"