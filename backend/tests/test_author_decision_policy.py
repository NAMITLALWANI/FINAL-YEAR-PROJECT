from author_resolution.context import QueryContext
from author_resolution.policy import (
    AUTO_RESOLVED, MANUAL_REVIEW, S1_UNSCORED_COMPETITOR, S2_NO_CORROBORATION, S3_HARD_CONFLICT,
    S4_INCOMPARABLE, S5_INCOMPLETE, UNRESOLVED, evaluate_decision,
)
from author_resolution.resolver import RankedCandidate
from author_resolution.scoring import CandidateScore
import config
from author_test_helpers import cand, rank, with_pub

INST = QueryContext.from_any({"institution_hints": ["Example Institute"]})


def test_approved_thresholds_are_unchanged():
    assert (config.AUTHOR_AUTO_SCORE_THRESHOLD, config.AUTHOR_AUTO_MARGIN_THRESHOLD, config.AUTHOR_AUTO_DOMINANCE_THRESHOLD,
            config.AUTHOR_MANUAL_SCORE_THRESHOLD, config.AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO) == (0.75, 0.15, 1.35, 0.45, 2)


def test_empty_pool_is_unresolved_with_no_scores():
    out = evaluate_decision([])
    assert out.status == UNRESOLVED and out.top_score is None


def test_single_candidate_with_name_only_is_manual_review():
    out = evaluate_decision(rank([cand("A1")], None))
    assert out.status == MANUAL_REVIEW and out.top_score == 1.0         # name alone never auto-assigns


def test_single_candidate_with_sufficient_corroborated_evidence_can_be_auto():
    out = evaluate_decision(rank([cand("A1")], INST))
    assert out.status == AUTO_RESOLVED and out.auto_blockers == ()
    assert "name_similarity" in out.reason and "institution_similarity" in out.reason     # evidence set is explained


def test_name_plus_temporal_only_is_not_enough():
    ctx = QueryContext.from_any({"active_year_start": 2020, "active_year_end": 2022})
    out = evaluate_decision(rank([cand("A1")], ctx))
    assert out.status == MANUAL_REVIEW and S2_NO_CORROBORATION in out.auto_blockers and out.threshold_gates_passed


def test_observed_zero_signal_blocks_automation_even_with_strong_name():
    ctx = QueryContext.from_any({"institution_hints": ["Example Institute"], "active_year_start": 2025, "active_year_end": 2026})
    out = evaluate_decision(rank([cand("A1")], ctx))
    assert out.status == MANUAL_REVIEW and S3_HARD_CONFLICT in out.auto_blockers
    assert "zero support" in out.reason


def test_multiple_candidates_with_comparable_evidence_and_clear_margin_can_be_auto():
    ranked = rank([cand("A1"), cand("A2", name="Zed Qwerty", inst="Example Institute")], INST)
    out = evaluate_decision(ranked)
    assert ranked[0].candidate.source_author_id == "A1"
    assert out.status == AUTO_RESOLVED and out.margin >= 0.15 and out.dominance >= 1.35


def test_exact_tie_goes_to_manual_review():
    out = evaluate_decision(rank([cand("A1"), cand("A2")], INST))
    assert out.status == MANUAL_REVIEW and out.margin == 0.0 and not out.threshold_gates_passed


def test_margin_failure_and_dominance_failure():
    close = rank([cand("A1"), cand("A2", name="Alice Smyth")], INST)          # similar name, same institution
    out = evaluate_decision(close)
    assert out.status == MANUAL_REVIEW and not out.threshold_gates_passed


def test_incomparable_evidence_sets_block_automation_but_ranking_is_unchanged():
    # A2 has no affiliation data: it is scored on the name alone (1.0) and outranks the institution-checked A1 (0.73).
    pool = rank([cand("A1", inst="Other University"), cand("A2", inst=None)], INST)
    assert [r.candidate.source_author_id for r in pool] == ["A2", "A1"]            # ranking order preserved
    out = evaluate_decision(pool)
    assert out.status == MANUAL_REVIEW
    # Make the top candidate pass every numeric gate and confirm incomparability alone withholds automation.
    top = rank([cand("A1")], INST)[0]
    weak_other = rank([cand("A2", name="Zed Qwerty", inst=None)], INST)[0]
    assert tuple(top.score.signal_set) != tuple(weak_other.score.signal_set)
    out2 = evaluate_decision([top, weak_other])
    assert out2.threshold_gates_passed and S4_INCOMPARABLE in out2.auto_blockers and out2.status == MANUAL_REVIEW


def test_unscored_competitor_fails_closed_and_is_distinct_from_a_single_candidate_pool():
    top = rank([cand("A1")], INST)[0]
    unscored = RankedCandidate(cand("A2"), [], CandidateScore(None, 0, {}))
    multi = evaluate_decision([top, unscored])
    single = evaluate_decision([top])
    assert single.status == AUTO_RESOLVED                                      # genuine single-candidate pool
    assert multi.status == MANUAL_REVIEW and S1_UNSCORED_COMPETITOR in multi.auto_blockers and not multi.threshold_gates_passed


def test_enrichment_failure_or_unreadable_candidate_blocks_automation():
    ctx = QueryContext.from_any({"institution_hints": ["Example Institute"], "publications": ["10.1000/a"]})
    failed = with_pub(cand("A1"), ctx, status="failed", error="timeout")
    out = evaluate_decision(rank([failed], ctx))
    assert out.status == MANUAL_REVIEW and S5_INCOMPLETE in out.auto_blockers
    unreadable = evaluate_decision(rank([cand("A1")], INST), incomplete_pool=True)
    assert unreadable.status == MANUAL_REVIEW and S5_INCOMPLETE in unreadable.auto_blockers


def test_publication_support_supplies_corroboration_and_all_signals_are_listed():
    ctx = QueryContext.from_any({"publications": ["10.1000/a"]})
    out = evaluate_decision(rank([with_pub(cand("A1"), ctx, matched=["W1"])], ctx))
    assert out.status == AUTO_RESOLVED
    assert dict(out.signal_sets)["A1"] == ("name_similarity", "publication_overlap")
    assert out.assessment()["auto_blockers"] == []


def test_low_score_without_evidence_is_unresolved():
    out = evaluate_decision(rank([cand("A1", name="Completely Different")], None))
    assert out.status == UNRESOLVED and not out.threshold_gates_passed
