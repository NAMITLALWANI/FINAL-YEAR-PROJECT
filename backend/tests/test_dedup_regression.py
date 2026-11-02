from pipeline.deduplicate import deduplicate, deduplicate_v1
from pipeline.normalize import normalize


def test_existing_deduplication_still_merges_exact_doi_records():
    records = [
        normalize(
            {
                "source": "openalex",
                "source_id": "W1",
                "title": "A Reproducible Paper",
                "authors": ["Ada Lovelace"],
                "year": 2024,
                "doi": "10.1000/example",
            }
        ),
        normalize(
            {
                "source": "crossref",
                "source_id": "10.1000/example",
                "title": "A reproducible paper",
                "authors": ["A. Lovelace"],
                "year": 2024,
                "doi": "10.1000/example",
            }
        ),
    ]

    publications, similarity_logs = deduplicate(records)

    assert len(publications) == 1
    assert publications[0].source_count == 2
    assert similarity_logs == []


def test_edition_conflict_prevents_merge_sutton_barto():
    """Regression test for FP1: Distinct textbook editions must not merge."""
    records = [
        normalize(
            {
                "source": "crossref",
                "source_id": "s1",
                "title": "Reinforcement Learning: An Introduction (1st Edition)",
                "authors": ["R. Sutton", "A. Barto"],
                "year": 1998,
                "doi": "",
            }
        ),
        normalize(
            {
                "source": "crossref",
                "source_id": "s2",
                "title": "Reinforcement Learning: An Introduction (2nd Edition)",
                "authors": ["R. Sutton", "A. Barto"],
                "year": 2018,
                "doi": "",
            }
        ),
    ]

    # V1 erroneously merged these
    pubs_v1, _ = deduplicate_v1(records)
    assert len(pubs_v1) == 1

    # Audited V2 correctly keeps them separate
    pubs_v2, _ = deduplicate(records)
    assert len(pubs_v2) == 2


def test_semantic_title_distinctness_prevents_merge_hinton_deng():
    """Regression test for FP2: High author overlap must not merge distinct papers."""
    records = [
        normalize(
            {
                "source": "crossref",
                "source_id": "s3",
                "title": "Deep Neural Networks for Acoustic Modeling in Speech Recognition",
                "authors": ["G. Hinton", "L. Deng"],
                "year": 2012,
                "doi": "",
            }
        ),
        normalize(
            {
                "source": "crossref",
                "source_id": "s4",
                "title": "New Types of Deep Neural Network Learning for Acoustic Modeling",
                "authors": ["G. Hinton", "L. Deng"],
                "year": 2013,
                "doi": "",
            }
        ),
    ]

    # V1 erroneously merged these
    pubs_v1, _ = deduplicate_v1(records)
    assert len(pubs_v1) == 1

    # Audited V2 correctly keeps them separate
    pubs_v2, _ = deduplicate(records)
    assert len(pubs_v2) == 2


def test_shortened_prefix_title_merges_silver_go():
    """Regression test for FN1: Shortened title matching prefix merges correctly."""
    records = [
        normalize(
            {
                "source": "crossref",
                "source_id": "s5",
                "title": "Mastering the Game of Go with Deep Neural Networks and Tree Search",
                "authors": ["D. Silver"],
                "year": 2016,
                "doi": "",
            }
        ),
        normalize(
            {
                "source": "openalex",
                "source_id": "s6",
                "title": "Mastering the Game of Go",
                "authors": ["David Silver"],
                "year": 2016,
                "doi": "",
            }
        ),
    ]

    # V1 erroneously failed to merge
    pubs_v1, _ = deduplicate_v1(records)
    assert len(pubs_v1) == 2

    # Audited V2 correctly merges them
    pubs_v2, _ = deduplicate(records)
    assert len(pubs_v2) == 1
    assert pubs_v2[0].source_count == 2


def test_doi_conflict_vetoes_merge():
    """Regression test: Records with conflicting DOIs must never merge."""
    records = [
        normalize(
            {
                "source": "arxiv",
                "source_id": "a1",
                "title": "Attention Is All You Need",
                "authors": ["A. Vaswani"],
                "year": 2017,
                "doi": "10.1000/1",
            }
        ),
        normalize(
            {
                "source": "arxiv",
                "source_id": "a2",
                "title": "Attention Is All You Need",
                "authors": ["A. Vaswani"],
                "year": 2017,
                "doi": "10.1000/2",
            }
        ),
    ]

    pubs, _ = deduplicate(records)
    assert len(pubs) == 2
