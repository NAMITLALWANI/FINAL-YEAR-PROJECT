"""T004: tests for the five director rulings of 20 November 2026 on the C7 metrics module. Synthetic fixtures only; no data files, no network."""
import pytest

from hammer_pilot import metrics_c7 as m
from hammer_pilot.metrics_c7 import C7Error, Case


def mk(cid, stratum="S", outcome="manual", pool=("a", "b"), mapped=(), selected="", **kw):
    pool = () if outcome in ("empty_pool", "provider_failed") else tuple(pool)
    return Case(case_id=cid, block_id=f"B-{cid}", stratum=stratum, outcome=outcome, pool_ids=pool, mapped_ids=frozenset(mapped), selected_id=selected, **kw)


def audited(cid, purity="pure", state="resolved", judgments=None, mapped=("a",), **kw):
    return mk(cid, label_state=state, group_purity=purity, pool_judgments=judgments, mapped=mapped, audit_subset="audit_sample", **kw)


FRAME = {"S": 1000}


def audit(cases):
    return m.evaluate_primary(cases, FRAME)["audit_label_error"]


# ================================================================ ruling 1: derived audit-label error
def test_the_manual_contradiction_flag_no_longer_exists():
    with pytest.raises(TypeError):
        Case(case_id="c", block_id="b", stratum="S", outcome="manual", pool_ids=("a",), label_contradicted=True)


@pytest.mark.parametrize("kwargs,status,reasons,why", [
    (dict(purity="pure", judgments={"a": "same", "b": "different"}), "consistent", [], None),
    (dict(purity="impure", judgments={"a": "same", "b": "different"}), "contradicted", ["impure_group"], None),
    (dict(purity="pure", judgments={"a": "different", "b": "different"}), "contradicted", ["false_mapping"], None),
    (dict(purity="pure", judgments={"a": "same", "b": "same"}), "contradicted", ["missed_mapping"], None),
    (dict(purity="pure", judgments={"a": "cannot_tell", "b": "different"}), "indeterminate", [], "mapped_candidate_cannot_tell"),
    (dict(purity="pure", judgments={"a": "same", "b": "cannot_tell"}), "consistent", [], None),          # cannot-tell on an unmapped candidate is not an error
    (dict(purity="unresolved", judgments={"a": "same", "b": "different"}), "indeterminate", [], "purity_unresolved"),
    (dict(purity="pure", judgments={"a": "same"}), "indeterminate", [], "incomplete_stage_b"),           # consistency needs every candidate judged
    (dict(purity="pure", judgments={"a": "different"}), "contradicted", ["false_mapping"], None),        # a definite reason does not need completeness
    (dict(purity="impure", state="uncertain", judgments=None), "indeterminate", [], "label_uncertain"),   # T005: outside the definite-label denominator; impurity reported separately
    (dict(purity=None, state="uncertain", judgments=None), "indeterminate", [], "label_uncertain"),
    (dict(purity=None, state="unverifiable", judgments=None), "indeterminate", [], "label_unverifiable"),
])
def test_audit_status_is_derived_from_the_adjudicated_record(kwargs, status, reasons, why):
    assert m.audit_status(audited("1", **kwargs)) == (status, reasons, why)


def test_impure_group_is_distinct_from_an_unresolved_group_and_only_impurity_is_automatic():
    pure_unresolved = audited("1", purity="pure", state="unresolved")
    impure_unresolved = audited("2", purity="impure", state="unresolved")
    assert m.audit_status(pure_unresolved) == ("indeterminate", [], "label_unresolved_pure_group")   # T005: not automatically a contradiction, and no longer consistent
    assert m.audit_status(impure_unresolved) == ("contradicted", ["impure_group"], None)
    a = audit([pure_unresolved, impure_unresolved])
    assert (a["label_errors"], a["indeterminate"]) == (1, 1)


def test_an_unresolved_case_can_still_be_contradicted_by_stage_b_reasons():
    c = audited("1", purity="pure", state="unresolved", judgments={"a": "different", "b": "different"})
    assert m.audit_status(c)[:2] == ("contradicted", ["false_mapping"])


def test_a_definite_audited_case_needs_a_group_purity_judgment():
    with pytest.raises(C7Error, match="group-purity"):
        audit([audited("1", purity=None, state="resolved")])
    with pytest.raises(C7Error, match="group-purity"):
        audit([audited("1", purity=None, state="unresolved")])


def test_purity_belongs_to_a_verified_case_and_must_be_valid():
    with pytest.raises(C7Error):
        Case(case_id="c", block_id="b", stratum="S", outcome="manual", pool_ids=("a",), group_purity="pure")
    with pytest.raises(C7Error):
        Case(case_id="c", block_id="b", stratum="S", outcome="manual", pool_ids=("a",), label_state="resolved", group_purity="maybe")


def test_each_case_counts_once_in_the_numerator_and_reasons_are_reported_separately():
    both = audited("1", purity="impure", judgments={"a": "different", "b": "same"})                    # impure + false mapping + missed mapping
    only_false = audited("2", judgments={"a": "different", "b": "different"})
    only_missed = audited("3", judgments={"a": "same", "b": "same"})
    clean = audited("4", judgments={"a": "same", "b": "different"})
    a = audit([both, only_false, only_missed, clean])
    assert a["label_errors"] == 3 and a["definite"] == 4 and a["error_rate"]["numerator"] == 3        # counted once each, not once per reason
    assert a["reason_counts"] == {"impure_group": 1, "false_mapping": 2, "missed_mapping": 2}         # reason counts overlap
    assert sum(a["reason_counts"].values()) == 5 > a["label_errors"]
    assert a["cases_with_more_than_one_reason"] == 1
    assert "more than one reason" in a["reason_counts_note"]


def test_indeterminate_cases_are_bracketed_not_counted_as_errors():
    cases = [audited("1", judgments={"a": "same", "b": "different"}), audited("2", judgments={"a": "different", "b": "different"}),
             audited("3", judgments={"a": "cannot_tell", "b": "different"}), audited("4", purity=None, state="unverifiable")]
    a = audit(cases)
    assert (a["contradicted"], a["consistent"], a["indeterminate"]) == (1, 1, 2)
    assert a["indeterminate_reasons"] == {"label_unverifiable": 1, "mapped_candidate_cannot_tell": 1}
    assert a["bracket"]["all_right"]["value"] == pytest.approx(1 / 4) and a["bracket"]["all_wrong"]["value"] == pytest.approx(3 / 4)


def test_empty_pool_audited_case_is_consistent_when_the_group_is_pure():
    c = mk("1", outcome="provider_failed", label_state="resolved", group_purity="pure", audit_subset="audit_sample")
    assert m.audit_status(c) == ("consistent", [], None)


# ================================================================ ruling 2: cannot-verify automatic cases stay Uncertain
def test_an_automatic_case_where_reviewers_cannot_verify_the_selected_candidate_stays_uncertain():
    c = mk("1", outcome="auto", selected="a", label_state="resolved", pool_judgments={"a": "cannot_tell", "b": "different"}, audit_subset="automatic")
    assert m.score_automatic(c) == ("uncertain", "selected_cannot_tell")
    assert m.reporting_class(c) == "uncertain"                                                         # not verified, not benchmark-derived
    rep = m.evaluate_primary([c, mk("2")], FRAME)
    assert rep["case_accounting"]["reporting_class_counts"] == {"verified": 0, "uncertain": 1, "unverifiable": 0, "benchmark_derived": 1}
    cell = rep["selective_verified"]["estimates"]["verified_automatic_precision"]["per_stratum"]["S"]
    assert cell["denominator"] == 0                                                                     # leaves the primary denominator, stays in the bracket
    assert rep["selective_verified"]["estimates"]["verified_precision_all_wrong"]["per_stratum"]["S"]["denominator"] == 1


# ================================================================ ruling 3: ground-truth unresolved versus HAMMER abstention
def test_a_hammer_abstention_never_removes_an_adjudicable_case_from_verified_retrieval():
    judged = {"a": "different", "b": "same"}
    cases = [mk("1", outcome="manual", label_state="resolved", audit_subset="audit_sample", pool_judgments=judged, group_purity="pure"),
             mk("2", outcome="unresolved", label_state="resolved", audit_subset="audit_sample", pool_judgments=judged, group_purity="pure"),
             mk("3", outcome="no_score", label_state="resolved", audit_subset="audit_sample", pool_judgments=judged, group_purity="pure")]
    r = m.evaluate_primary(cases, FRAME)["verified_retrieval"]["audit_sample"]
    assert r["resolved_cases_used"] == 3 and r["case_counts"]["hammer_abstentions_included"] == 3
    assert r["outcomes_of_cases_used"] == {"manual": 1, "no_score": 1, "unresolved": 1}
    assert r["case_counts"]["ground_truth_unresolved"] == 0
    assert "never an exclusion" in r["exclusions"]


def test_only_ground_truth_unresolved_cases_are_excluded_and_are_counted_separately():
    judged = {"a": "same", "b": "different"}
    cases = [mk("1", outcome="manual", label_state="resolved", audit_subset="audit_sample", pool_judgments=judged, group_purity="pure"),
             mk("2", outcome="manual", label_state="unresolved", audit_subset="audit_sample", pool_judgments=judged, group_purity="pure"),
             mk("3", outcome="unresolved", label_state="unresolved", audit_subset="audit_sample", group_purity="pure")]    # HAMMER and ground truth both unresolved
    r = m.evaluate_primary(cases, FRAME)["verified_retrieval"]["audit_sample"]
    assert r["resolved_cases_used"] == 1 and r["case_counts"]["ground_truth_unresolved"] == 2
    assert r["conditional_recall_at_1"]["denominator"] == 1


def test_a_ground_truth_unresolved_case_is_excluded_even_when_hammer_assigned_automatically():
    c = mk("1", outcome="auto", selected="a", label_state="unresolved", audit_subset="automatic")
    r = m.evaluate_primary([c], FRAME)["verified_retrieval"]["automatic"]
    assert r["resolved_cases_used"] == 0 and r["case_counts"]["ground_truth_unresolved"] == 1
    assert m.score_automatic(c) == ("incorrect", "unresolved")                                          # but it is a false automatic assignment


def test_hammer_unresolved_outcome_and_ground_truth_unresolved_are_separate_counts():
    cases = [mk("1", outcome="unresolved", label_state="resolved"), mk("2", outcome="manual", label_state="unresolved"), mk("3", outcome="manual")]
    rep = m.evaluate_primary(cases, FRAME)
    assert rep["label_free"]["rate_unresolved"]["per_stratum"]["S"]["numerator"] == 1                  # HAMMER outcome only; label_state is not read
    assert rep["case_accounting"]["outcome_counts"]["unresolved"] == 1


def test_conditional_verified_retrieval_uses_cases_with_a_verified_mapped_profile_only():
    cases = [mk("A", outcome="manual", pool=("a", "b"), label_state="resolved", audit_subset="audit_sample", group_purity="pure", pool_judgments={"a": "different", "b": "same"}),
             mk("B", outcome="unresolved", pool=("a", "b"), label_state="resolved", audit_subset="audit_sample", group_purity="pure", pool_judgments={"a": "same", "b": "different"}),
             mk("C", outcome="provider_failed", label_state="resolved", audit_subset="audit_sample", group_purity="pure"),                      # no pool: a miss end-to-end, outside M
             mk("D", outcome="manual", label_state="unresolved", audit_subset="audit_sample", group_purity="pure", pool_judgments={"a": "same", "b": "different"}),
             mk("E", outcome="manual", pool=("a", "b"), label_state="resolved", audit_subset="audit_sample", group_purity="pure", pool_judgments={"a": "cannot_tell", "b": "different"})]
    r = m.evaluate_primary(cases, FRAME)["verified_retrieval"]["audit_sample"]
    assert r["resolved_cases_used"] == 4 and r["case_counts"]["ground_truth_unresolved"] == 1          # A, B, C, E used; D excluded
    assert r["case_counts"]["indefinite_mapped_cases"] == 1                                              # E: only a cannot-tell candidate; outside M, visible
    assert r["conditional_recall_at_1"]["denominator"] == 2
    assert (r["conditional_recall_at_1"]["lower"]["numerator"], r["conditional_recall_at_1"]["upper"]["numerator"]) == (1, 1)    # only B hits at rank 1
    assert r["conditional_recall_at_5"]["lower"]["numerator"] == 2
    assert r["conditional_mrr"]["lower"] == pytest.approx((1 / 2 + 1) / 2) and r["conditional_mrr"]["denominator"] == 2
    assert r["end_to_end_success_at_1"]["lower"]["denominator"] == 4                                    # end-to-end keeps C (a miss) and E
    assert r["end_to_end_success_at_5"]["lower"]["numerator"] == 2 and r["end_to_end_success_at_5"]["upper"]["numerator"] == 3


# ================================================================ ruling 4: the R2 pool is the primary pool
def test_the_report_states_that_the_r2_pool_is_primary_and_r0_is_descriptive():
    rep = m.evaluate_primary([mk("1")], FRAME)
    assert "R2" in rep["scope"]["pool"] and "R0 is descriptive only" in rep["scope"]["pool"]
    assert rep["verified_retrieval"]["automatic"]["pool"] == "captured R2 (name-only) pool"


def test_replay_builder_uses_the_r2_pool_and_ignores_r0():
    preds = [{"case_id": "C1", "condition": "C1", "policy": "selective_policy_v2", "outcome": "manual", "selected_author_id": ""}]
    ret = [{"case_id": "C1", "arm": "R0", "ordered_candidate_ids": '["TARGET","X"]'}, {"case_id": "C1", "arm": "R2", "ordered_candidate_ids": '["X","Y"]'}]
    (case,) = m.cases_from_replay(preds, ret, condition="C1", policy="selective_policy_v2", block_by_case={"C1": "b"}, stratum_by_case={"C1": "S"},
                                  mapped_by_case={"C1": {"TARGET"}})
    assert case.pool_ids == ("X", "Y") and m.first_rank(case) is None                                  # the R0-only hit does not count
    rep = m.evaluate_primary([case], FRAME)["retrieval_benchmark_derived"]
    assert rep["pool_mapping_rate"]["per_stratum"]["S"]["numerator"] == 0
    assert rep["end_to_end_success_at_10"]["per_stratum"]["S"]["numerator"] == 0


# ================================================================ ruling 5: every candidate judged before "no matching candidate"
def auto_resolved(judgments, selected="a", pool=("a", "b", "c")):
    return mk("1", outcome="auto", pool=pool, selected=selected, label_state="resolved", pool_judgments=judgments)


@pytest.mark.parametrize("judgments,reason", [
    ({"a": "different", "b": "different", "c": "different"}, "resolved_no_matching_candidate"),     # complete and all different
    ({"a": "different", "b": "different"}, "resolved_different"),                                    # candidate c never judged: no claim
    ({"a": "different"}, "resolved_different"),
    ({"a": "different", "b": "cannot_tell", "c": "different"}, "resolved_different"),               # complete but one cannot tell: no claim
    ({"a": "different", "b": "same", "c": "different"}, "resolved_different"),                       # someone else is the person
])
def test_no_matching_candidate_is_claimed_only_when_every_candidate_is_judged_different(judgments, reason):
    assert m.score_automatic(auto_resolved(judgments)) == ("incorrect", reason)                        # both reasons are incorrect


def test_both_reasons_stay_in_the_precision_denominator():
    for judgments in ({"a": "different", "b": "different", "c": "different"}, {"a": "different"}):
        c = auto_resolved(judgments)
        cell = m.evaluate_primary([c], FRAME)["selective_verified"]["estimates"]["verified_automatic_precision"]["per_stratum"]["S"]
        assert (cell["numerator"], cell["denominator"]) == (0, 1)


def test_verified_retrieval_claims_a_miss_only_when_every_candidate_was_judged():
    base = dict(outcome="manual", label_state="resolved", audit_subset="audit_sample", group_purity="pure")
    cases = [mk("1", pool=("a", "b"), pool_judgments={"a": "different", "b": "different"}, **base),     # complete: a verified miss
             mk("2", pool=("a", "b"), pool_judgments={"a": "different"}, **base),                         # incomplete: not claimed, excluded and counted
             mk("3", pool=("a", "b"), **base)]                                                           # no judgments at all
    r = m.evaluate_primary(cases, FRAME)["verified_retrieval"]["audit_sample"]
    assert r["resolved_cases_used"] == 1 and r["case_counts"]["incomplete_stage_b"] == 2
    assert r["end_to_end_success_at_5"]["lower"]["numerator"] == 0 and r["end_to_end_success_at_5"]["lower"]["denominator"] == 1


def test_an_empty_pool_has_nothing_to_judge_and_is_a_verified_miss():
    c = mk("1", outcome="provider_failed", label_state="resolved", audit_subset="audit_sample", group_purity="pure")
    r = m.evaluate_primary([c], FRAME)["verified_retrieval"]["audit_sample"]
    assert r["resolved_cases_used"] == 1 and r["case_counts"]["incomplete_stage_b"] == 0
    assert r["mapping_rate"]["lower"]["numerator"] == 0
