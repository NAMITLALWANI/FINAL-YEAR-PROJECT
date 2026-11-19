import json
import pytest

from author_resolution.context import QueryContext
from author_resolution.evidence import extract_evidence
from author_resolution.policy import AUTO_RESOLVED, MANUAL_REVIEW, UNRESOLVED
from author_resolution.resolver import decide, rank_candidates
from author_resolution.scoring import score_evidence
from config import AUTHOR_SCORE_WEIGHTS
from author_test_helpers import by_signal, cand, co, with_co, with_pub


def ev(candidate, ctx):
    return by_signal(extract_evidence(candidate, ctx))


FULL = {"institution_hints": ["Example Institute"], "publications": ["10.1000/a"], "coauthors": [{"openalex_id": "A7"}],
        "active_year_start": 2020, "active_year_end": 2023}


def full_candidate(ctx):
    return with_co(with_pub(cand("A1"), ctx, matched=["W1"]), [co("A7", "Bob Jones")])


def test_approved_weights_are_unchanged():
    assert AUTHOR_SCORE_WEIGHTS == {"name_similarity": 0.35, "institution_similarity": 0.25, "publication_overlap": 0.20,
                                    "coauthor_overlap": 0.10, "temporal_compatibility": 0.10}


def test_all_five_signals_available_from_genuine_inputs():
    ctx = QueryContext.from_any(FULL)
    e = ev(full_candidate(ctx), ctx)
    assert {k: v.status for k, v in e.items()} == {k: "observed" for k in AUTHOR_SCORE_WEIGHTS}
    assert all(v.normalized_score == 1.0 for v in e.values())
    score = score_evidence(list(e.values()))
    assert score.signal_set == tuple(AUTHOR_SCORE_WEIGHTS) and score.available_signals == 5
    assert score.effective_weights == pytest.approx(dict(AUTHOR_SCORE_WEIGHTS))


def test_name_only_has_one_signal_and_others_are_explicitly_unavailable():
    e = ev(cand("A1"), None)
    assert e["name_similarity"].normalized_score == 1.0
    assert [k for k, v in e.items() if v.status == "unavailable_query_input_absent"] == [
        "institution_similarity", "publication_overlap", "coauthor_overlap", "temporal_compatibility"]
    assert score_evidence(list(e.values())).available_signals == 1


def test_name_plus_institution_and_name_plus_temporal_renormalise_correctly():
    s = score_evidence(list(ev(cand("A1"), {"institution_hints": ["Example Institute"]}).values()))
    assert round(s.effective_weights["name_similarity"], 4) == round(0.35 / 0.60, 4) and s.signal_set == ("name_similarity", "institution_similarity")
    t = score_evidence(list(ev(cand("A1"), {"active_year_start": 2020, "active_year_end": 2023}).values()))
    assert t.signal_set == ("name_similarity", "temporal_compatibility") and round(t.effective_weights["temporal_compatibility"], 4) == round(0.10 / 0.45, 4)


def test_publication_and_coauthor_are_unavailable_without_retrieved_evidence():
    ctx = QueryContext.from_any(FULL)
    e = ev(cand("A1"), ctx)                                     # live candidate, never enriched
    assert e["publication_overlap"].status == "unavailable_not_retrieved" and e["publication_overlap"].normalized_score is None
    assert e["coauthor_overlap"].status == "unavailable_not_retrieved" and e["coauthor_overlap"].normalized_score is None


def test_failed_and_empty_retrieval_never_count_as_agreement_or_conflict():
    ctx = QueryContext.from_any(FULL)
    failed = ev(with_co(with_pub(cand("A1"), ctx, status="failed", error="timeout"), status="failed", error="timeout"), ctx)
    assert failed["publication_overlap"].status == "unavailable_retrieval_failed" and failed["publication_overlap"].normalized_score is None
    assert failed["coauthor_overlap"].status == "unavailable_retrieval_failed"
    empty = ev(with_pub(cand("A1"), ctx, status="empty", comparable=()), ctx)
    assert empty["publication_overlap"].status == "unavailable_inconclusive"


def test_publication_overlap_is_a_real_ratio_and_zero_is_observed_non_support():
    ctx = QueryContext.from_any({"publications": ["10.1000/a", "10.1000/b"]})
    half = ev(with_pub(cand("A1"), ctx, matched=["W1"], comparable=["W1", "W2"]), ctx)["publication_overlap"]
    assert half.normalized_score == 0.5
    none = ev(with_pub(cand("A1"), ctx, matched=[], comparable=["W1", "W2"]), ctx)["publication_overlap"]
    assert none.status == "observed" and none.normalized_score == 0.0


def test_publication_evidence_from_a_different_context_is_not_reused():
    ctx_a = QueryContext.from_any({"publications": ["10.1000/a"]})
    ctx_b = QueryContext.from_any({"publications": ["10.1000/zzz"]})
    stale = with_pub(cand("A1"), ctx_a, matched=["W1"])
    assert ev(stale, ctx_b)["publication_overlap"].status == "unavailable_not_retrieved"


def test_title_only_publications_are_never_compared():
    ctx = QueryContext.from_any({"publications": [{"title": "A Paper"}]})
    e = ev(cand("A1"), ctx)["publication_overlap"]
    assert e.status == "unavailable_query_input_absent"


def test_only_openalex_ids_score_coauthors_and_names_never_do():
    by_id = QueryContext.from_any({"coauthors": [{"openalex_id": "A7"}]})
    hit = ev(with_co(cand("A1"), [co("A7", "Someone Else")]), by_id)["coauthor_overlap"]
    assert hit.normalized_score == 1.0 and hit.raw_value["matches"][0]["basis"] == "openalex_id"
    names = QueryContext.from_any({"coauthors": ["Bob Jones"]})
    out = ev(with_co(cand("A1"), [co("A7", "Bob Jones")]), names)["coauthor_overlap"]       # exact name present in sample
    assert out.status == "unavailable_input_unresolvable" and out.normalized_score is None
    diag = out.raw_value["name_only_diagnostics"]
    assert diag["name_only_used_for_scoring"] is False and diag["name_only_unique_exact_name_in_sample"] == 1
    assert "Bob" not in json.dumps(out.raw_value) and "A7" not in json.dumps(out.raw_value)       # no names, no resolved IDs leaked


def test_homonyms_and_ambiguous_names_are_diagnostics_only():
    names = QueryContext.from_any({"coauthors": ["Bob Jones", "Carol White"]})
    out = ev(with_co(cand("A1"), [co("A7", "Bob Jones"), co("A8", "Bob Jones")]), names)["coauthor_overlap"]
    d = out.raw_value["name_only_diagnostics"]
    assert out.normalized_score is None and d["name_only_ambiguous_exact_name_in_sample"] == 1 and d["name_only_no_name_in_sample"] == 1


def test_mixed_id_and_name_input_scores_only_the_id():
    mixed = QueryContext.from_any({"coauthors": [{"openalex_id": "A7"}, "Bob Jones"]})
    out = ev(with_co(cand("A1"), [co("A7", "X Y"), co("A8", "Bob Jones")]), mixed)["coauthor_overlap"]
    assert out.normalized_score == 1.0 and len(out.raw_value["matches"]) == 1
    assert out.raw_value["name_only_diagnostics"]["name_only_supplied"] == 1


def test_missing_ids_and_empty_sets():
    assert ev(cand("A1"), {})["coauthor_overlap"].status == "unavailable_query_input_absent"
    ids = QueryContext.from_any({"coauthors": [{"openalex_id": "A7"}]})
    assert ev(cand("A1"), ids)["coauthor_overlap"].status == "unavailable_not_retrieved"
    assert ev(with_co(cand("A1"), [], status="empty"), ids)["coauthor_overlap"].status == "unavailable_inconclusive"


def test_coauthor_zero_overlap_is_conclusive_only_for_a_complete_sample():
    ctx = QueryContext.from_any({"coauthors": [{"openalex_id": "A7"}]})
    incomplete = ev(with_co(cand("A1"), [co("A9", "Carol White")], complete=False), ctx)["coauthor_overlap"]
    assert incomplete.status == "unavailable_inconclusive" and incomplete.normalized_score is None
    complete = ev(with_co(cand("A1"), [co("A9", "Carol White")], complete=True), ctx)["coauthor_overlap"]
    assert complete.status == "observed" and complete.normalized_score == 0.0
    assert ev(with_co(cand("A1"), [co("A7", "X Y")], complete=False), ctx)["coauthor_overlap"].normalized_score == 1.0   # positive evidence survives truncation


def test_institution_subset_names_no_longer_score_perfectly():
    subset = ev(cand("A1", inst="Example Institute of Technology"), {"institution_hints": ["Example Institute"]})["institution_similarity"]
    exact = ev(cand("A1", inst="Example Institute"), {"institution_hints": ["Example Institute"]})["institution_similarity"]
    assert exact.normalized_score == 1.0 and subset.normalized_score < 1.0


def test_institution_identifiers_and_missing_affiliations():
    c = cand("A1", inst="Example Institute", inst_id="I100", ror="03yrm5c26")
    same = ev(c, {"institutions": [{"openalex_id": "I100"}]})["institution_similarity"]
    other = ev(c, {"institutions": [{"openalex_id": "I999", "name": "Example Institute"}]})["institution_similarity"]
    ror = ev(c, {"institutions": [{"ror": "03yrm5c26"}]})["institution_similarity"]
    assert same.normalized_score == 1.0 and ror.normalized_score == 1.0
    assert other.normalized_score == 0.0 and other.raw_value["basis"] == "openalex_id_different"   # different entity: name does not rescue it
    missing = ev(cand("A1", inst=None), {"institution_hints": ["Example Institute"]})["institution_similarity"]
    assert missing.status == "unavailable_candidate_data_absent" and missing.normalized_score is None   # absent is not a mismatch


def test_temporal_rules():
    c = cand("A1", years=(2019, 2023))
    ok = ev(c, {"active_year_start": 2020, "active_year_end": 2022})["temporal_compatibility"]
    assert ok.normalized_score == 1.0
    before = ev(c, {"active_year_start": 2000, "active_year_end": 2005})["temporal_compatibility"]
    assert before.status == "unavailable_inconclusive" and before.normalized_score is None
    after = ev(c, {"active_year_start": 2025, "active_year_end": 2026})["temporal_compatibility"]
    assert after.status == "observed" and after.normalized_score == 0.0
    assert ev(cand("A1", years=()), {"active_year_start": 2020, "active_year_end": 2021})["temporal_compatibility"].status == "unavailable_candidate_data_absent"


def test_scoring_is_deterministic_and_missing_metadata_stays_unknown():
    ctx = QueryContext.from_any(FULL)
    c = full_candidate(ctx)
    first = [(e.signal_name, e.normalized_score, e.status) for e in extract_evidence(c, ctx)]
    second = [(e.signal_name, e.normalized_score, e.status) for e in extract_evidence(c, ctx)]
    assert first == second
    bare = ev(cand("A1", inst=None, years=()), {})
    assert all(bare[s].normalized_score is None for s in ("institution_similarity", "publication_overlap", "coauthor_overlap", "temporal_compatibility"))


def test_scoring_and_decision_are_separate_and_conservative():
    ctx = QueryContext.from_any({"institution_hints": ["Example Institute"]})
    strong = rank_candidates([cand("A1")], ctx)
    assert decide(strong)[0] == AUTO_RESOLVED                   # exact name + institution, single candidate
    weak = rank_candidates([cand("A1", name="Other Person", inst="Elsewhere University")], ctx)
    assert decide(weak)[0] in (UNRESOLVED, MANUAL_REVIEW) and decide(weak)[0] != AUTO_RESOLVED
    close = rank_candidates([cand("A1"), cand("A2")], ctx)
    assert decide(close)[0] == MANUAL_REVIEW


def test_institution_regressions_containment_shared_tokens_abbreviations_and_aliases():
    def score(candidate_inst, hint):
        return ev(cand("A1", inst=candidate_inst, inst_id="I100"), {"institution_hints": [hint]})["institution_similarity"].normalized_score
    assert score("Example Institute", "Example Institute") == 1.0
    assert score("Example Institute of Technology", "Example Institute") < 1.0       # containment is not a full match
    assert score("Mila - Quebec AI Institute", "Mila") < 0.5                          # alias/short form: known false mismatch
    assert score("Massachusetts Institute of Technology", "MIT") < 0.5                # abbreviation: known false mismatch
    assert score("University of California, Los Angeles", "University of California, Berkeley") < 1.0
    assert score("University of Toronto", "University of Technology") < 0.9          # shared tokens do not give a match
    assert score("Stanford University", "Stanford Univeristy") > 0.9                  # minor spelling variation survives
    ids = ev(cand("A1", inst="Mila - Quebec AI Institute", inst_id="I100"), {"institutions": [{"name": "Mila", "openalex_id": "I100"}]})["institution_similarity"]
    assert ids.normalized_score == 1.0 and ids.raw_value["basis"] == "openalex_id_equal"        # an identifier resolves an alias
