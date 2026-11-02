from datetime import datetime

from services.author_candidates import AuthorCandidateInput, OpenAlexCandidate
from services.author_evidence import extract_evidence, publication_overlap, coauthor_overlap, temporal_compatibility
from services.author_resolution import AUTO_RESOLVED, MANUAL_REVIEW, UNRESOLVED, RankedCandidate, decide
from services.author_scoring import score_evidence


def candidate(**changes):
    values = dict(query_original="A. Smith", query_normalized="a. smith", source="openalex", source_author_id="A1", source_author_url="https://openalex.org/A1", display_name="Alice Smith", normalized_name="alice smith", aliases=["A. Smith"], institution_summary="Example Institute", affiliations=[{"name": "Example Institute"}], works_count=1, citation_count=1, sample_publications=[{"doi": "10.1/x", "title": "A Paper"}], topics=None, coauthor_summary=[{"name": "Bob Jones"}], years_active_start=2018, years_active_end=2024, retrieved_at=datetime.now(), raw_payload={})
    values.update(changes)
    return OpenAlexCandidate(**values)


def by_signal(items): return {item.signal_name: item for item in items}


def test_evidence_extractors_keep_missing_metadata_unknown():
    evidence = by_signal(extract_evidence(candidate(), {"institution_hints": ["Example Institute"], "publications": [{"doi": "10.1/x"}], "coauthors": ["Bob Jones"], "active_year_start": 2020, "active_year_end": 2023}))
    assert evidence["name_similarity"].normalized_score > 0.8
    assert evidence["institution_similarity"].normalized_score == 1.0
    assert evidence["publication_overlap"].normalized_score == 1.0
    assert evidence["coauthor_overlap"].normalized_score == 1.0
    assert evidence["temporal_compatibility"].normalized_score == 1.0
    missing = by_signal(extract_evidence(candidate(affiliations=[], sample_publications=None, coauthor_summary=None, years_active_start=None), {}))
    assert missing["institution_similarity"].normalized_score is None
    assert missing["publication_overlap"].normalized_score is None
    assert missing["coauthor_overlap"].normalized_score is None
    assert missing["temporal_compatibility"].normalized_score is None


def test_publication_doi_and_title_overlap_and_absence():
    c = candidate()
    assert publication_overlap(c, {"publications": [{"doi": "10.1/x"}]}).normalized_score == 1.0
    assert publication_overlap(c, {"publications": [{"title": "A Paper"}]}).normalized_score == 1.0
    assert publication_overlap(c, {"publications": [{"title": "Different"}]}).normalized_score == 0.0


def test_coauthor_and_time_evidence():
    c = candidate()
    assert coauthor_overlap(c, {"coauthors": ["Bob Jones"]}).normalized_score == 1.0
    assert coauthor_overlap(c, {"coauthors": ["Other"]}).normalized_score == 0.0
    assert temporal_compatibility(c, {"active_year_start": 2019, "active_year_end": 2021}).normalized_score == 1.0
    assert temporal_compatibility(c, {"active_year_start": 2000, "active_year_end": 2005}).normalized_score == 0.0


def test_scoring_and_decision_are_separate_and_conservative():
    ev = extract_evidence(candidate(), {"institution_hints": ["Example Institute"], "publications": [{"doi": "10.1/x"}], "coauthors": ["Bob Jones"], "active_year_start": 2020, "active_year_end": 2023})
    strong = RankedCandidate(candidate(), ev, score_evidence(ev))
    status, *_ = decide([strong])
    assert status == AUTO_RESOLVED
    weak_ev = extract_evidence(candidate(display_name="Other", aliases=[]), {})
    weak = RankedCandidate(candidate(display_name="Other", aliases=[]), weak_ev, score_evidence(weak_ev))
    assert decide([weak])[0] == UNRESOLVED
    close = RankedCandidate(candidate(source_author_id="A2"), ev, score_evidence(ev))
    assert decide([strong, close])[0] == MANUAL_REVIEW