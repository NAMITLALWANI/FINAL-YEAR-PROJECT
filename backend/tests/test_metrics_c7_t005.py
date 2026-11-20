"""T005: tests for the four director clarifications of 20 November 2026 on the C7 metrics module. Synthetic fixtures only; no data files, no network."""
import json

import pytest

from hammer_pilot import metrics_c7 as m
from hammer_pilot.metrics_c7 import C7Error, Case

FRAME = {"S": 1000}


def mk(cid, outcome="manual", pool=("a", "b"), mapped=(), selected="", **kw):
    pool = () if outcome in ("empty_pool", "provider_failed") else tuple(pool)
    return Case(case_id=cid, block_id=f"B-{cid}", stratum="S", outcome=outcome, pool_ids=pool, mapped_ids=frozenset(mapped), selected_id=selected, **kw)


def aud(cid, purity="pure", state="resolved", judgments=None, mapped=("a",), **kw):
    return mk(cid, label_state=state, group_purity=purity, pool_judgments=judgments, mapped=mapped, audit_subset="audit_sample", **kw)


def audit(cases):
    return m.evaluate_primary(cases, FRAME)["audit_label_error"]


CLEAN = {"a": "same", "b": "different"}                  # consistent with mapped={"a"}


# ================================================================ clarification 1: pure / impure / unresolved, and pure-unresolved is indeterminate
def test_group_purity_states_are_pure_impure_and_unresolved_only():
    assert m.PURITY == ("pure", "impure", "unresolved")
    for state in m.PURITY:
        Case(case_id="c", block_id="b", stratum="S", outcome="manual", pool_ids=("a",), label_state="resolved", group_purity=state)
    with pytest.raises(C7Error):
        Case(case_id="c", block_id="b", stratum="S", outcome="manual", pool_ids=("a",), label_state="resolved", group_purity="cannot_tell")


def test_a_pure_group_with_an_unresolved_case_label_is_indeterminate_not_consistent():
    c = aud("1", purity="pure", state="unresolved")
    assert m.audit_status(c) == ("indeterminate", [], "label_unresolved_pure_group")
    a = audit([c, aud("2", judgments=CLEAN)])
    assert (a["consistent"], a["indeterminate"], a["contradicted"]) == (1, 1, 0)
    assert a["definite"] == 1 and a["error_rate"]["denominator"] == 1                    # the pure-unresolved case is outside the definite denominator
    assert a["indeterminate_reasons"] == {"label_unresolved_pure_group": 1}
    assert a["bracket"]["all_right"]["value"] == 0 and a["bracket"]["all_wrong"]["value"] == pytest.approx(1 / 2)    # preserved in the bracket


def test_an_unresolved_group_purity_is_its_own_state_and_is_indeterminate():
    c = aud("1", purity="unresolved", state="resolved", judgments=CLEAN)
    assert m.audit_status(c) == ("indeterminate", [], "purity_unresolved")
    a = audit([c, aud("2", purity="pure", judgments=CLEAN), aud("3", purity="impure", judgments=CLEAN)])
    assert a["group_validity"]["purity_counts"] == {"pure": 1, "impure": 1, "unresolved": 1, "not_recorded": 0}     # three separate states


def test_stage_b_contradictions_still_count_when_purity_or_label_is_unresolved():
    mapped_wrong = {"a": "different", "b": "different"}
    assert m.audit_status(aud("1", purity="unresolved", judgments=mapped_wrong))[:2] == ("contradicted", ["false_mapping"])
    assert m.audit_status(aud("2", purity="pure", state="unresolved", judgments=mapped_wrong))[:2] == ("contradicted", ["false_mapping"])
    assert m.audit_status(aud("3", purity="impure", state="unresolved"))[:2] == ("contradicted", ["impure_group"])


# ================================================================ clarification 2: group validity apart from case-level verification
@pytest.mark.parametrize("state", ["uncertain", "unverifiable"])
def test_an_uncertain_case_with_a_confirmed_impure_group_stays_outside_the_definite_denominator(state):
    c = aud("1", purity="impure", state=state)
    assert m.audit_status(c) == ("indeterminate", [], f"label_{state}")
    a = audit([c, aud("2", judgments=CLEAN), aud("3", purity="impure", judgments=CLEAN)])
    assert (a["label_errors"], a["definite"], a["indeterminate"]) == (1, 2, 1)           # only the resolved impure case is an error and in the denominator
    assert a["error_rate"]["numerator"] == 1 and a["error_rate"]["denominator"] == 2
    gv = a["group_validity"]
    assert gv["purity_counts"]["impure"] == 2                                              # both impurities are reported
    assert gv["impure_by_label_state"][state] == 1 and gv["impure_by_label_state"]["resolved"] == 1
    assert gv["impure_outside_definite_label_denominator"] == 1
    assert a["bracket"]["all_right"]["errors"] == 1 and a["bracket"]["all_wrong"]["errors"] == 2    # the uncertainty bracket is preserved


def test_a_confirmed_impure_group_in_a_definite_case_is_a_benchmark_contradiction():
    c = aud("1", purity="impure", state="resolved", judgments=CLEAN)
    assert m.audit_status(c) == ("contradicted", ["impure_group"], None)
    a = audit([c])
    assert a["label_errors"] == 1 and a["group_validity"]["impure_outside_definite_label_denominator"] == 0


def test_case_level_candidate_evidence_does_not_pull_an_uncertain_case_into_the_denominator():
    c = aud("1", purity="pure", state="uncertain", judgments={"a": "different", "b": "different"})    # would be a false mapping if the case were definite
    assert m.audit_status(c) == ("indeterminate", [], "label_uncertain")
    assert audit([c])["definite"] == 0


def test_impure_group_rate_uses_determinate_purity_only_and_reports_the_rest():
    cases = [aud("1", purity="pure", judgments=CLEAN), aud("2", purity="pure", judgments=CLEAN), aud("3", purity="impure", judgments=CLEAN),
             aud("4", purity="unresolved", judgments=CLEAN), aud("5", purity="impure", state="uncertain")]
    gv = audit(cases)["group_validity"]
    assert (gv["impure_group_rate"]["numerator"], gv["impure_group_rate"]["denominator"]) == (2, 4)    # unresolved purity is outside; shown in purity_counts
    assert gv["purity_counts"]["unresolved"] == 1 and "separately" in gv["scope"]


def test_group_validity_counts_cases_without_a_purity_record():
    gv = audit([aud("1", purity=None, state="uncertain"), mk("2", label_state=None, audit_subset="audit_sample")])["group_validity"]
    assert gv["purity_counts"]["not_recorded"] == 2 and gv["impure_group_rate"]["denominator"] == 0


# ================================================================ clarification 3: overall retrieval is never adjusted by verification
def retrieval_set(verified):
    pools = [("a", "b"), ("b", "a", "c"), ("c", "d"), ("a",), ("d", "e"), ("a", "b")]
    mapped = [{"a"}, {"c"}, {"x"}, {"a"}, {"z"}, {"b"}]
    cases = []
    for i, pool in enumerate(pools):
        extra = {}
        if verified:                                              # attach verified labels, purity, judgments and audit membership; nothing else changes
            extra = dict(label_state=("resolved", "uncertain", "unresolved")[i % 3], group_purity="impure" if i % 2 else "pure",
                         pool_judgments={x: "different" for x in pool}, audit_subset="audit_sample")
        cases.append(mk(f"r{i}", pool=pool, mapped=mapped[i], **extra))
    cases += [mk("f1", outcome="provider_failed", mapped={"q"}), mk("f2", outcome="empty_pool", mapped={"q"})]
    return cases


def test_overall_retrieval_keeps_all_N_and_is_identical_with_or_without_verification():
    plain = m.evaluate_primary(retrieval_set(False), FRAME)
    verified = m.evaluate_primary(retrieval_set(True), FRAME)
    for section in ("retrieval_benchmark_derived", "label_free", "selective_benchmark_derived"):
        assert json.dumps(plain[section], sort_keys=True) == json.dumps(verified[section], sort_keys=True)     # no audit or label touches these
    r = verified["retrieval_benchmark_derived"]
    n = verified["case_accounting"]["n_primary"]
    assert n == 8
    for name in ("pool_mapping_rate", "end_to_end_success_at_1", "end_to_end_success_at_5", "end_to_end_success_at_10", "end_to_end_mrr"):
        assert r[name]["per_stratum"]["S"]["denominator"] == n                                                 # all N, whatever the verified label


def test_verified_retrieval_uses_only_definite_cases_and_reports_excluded_categories_separately():
    cases = [aud("1", state="resolved", judgments={"a": "same", "b": "different"}),
             aud("2", state="resolved", judgments={"a": "different"}),                                         # incomplete
             aud("3", state="uncertain", purity="pure"), aud("4", state="unverifiable", purity=None),
             aud("5", state="unresolved", purity="pure"),
             mk("6", label_state=None, audit_subset="audit_sample")]
    rep = m.evaluate_primary(cases, FRAME)
    r = rep["verified_retrieval"]["audit_sample"]
    assert r["resolved_cases_used"] == 1
    assert r["case_counts"] == {"in_subset": 6, "unverified": 1, "uncertain_case": 1, "unverifiable_case": 1, "ground_truth_unresolved": 1,
                                "incomplete_stage_b": 1, "hammer_abstentions_included": 1, "indefinite_mapped_cases": 0}
    assert rep["retrieval_benchmark_derived"]["pool_mapping_rate"]["per_stratum"]["S"]["denominator"] == 6      # overall keeps all N


def test_the_report_states_that_overall_retrieval_is_never_adjusted():
    notes = " ".join(m.evaluate_primary([mk("1")], FRAME)["scope"]["notes"])
    assert "never adjusted by any audit or verified result" in notes and "reported separately from the definite-label audit error rate" in notes
    assert "not a correction factor" in audit([mk("1")])["population"]


# ================================================================ clarification 4: conditional verified retrieval and its separate categories
def category_cases():
    base = dict(label_state="resolved", group_purity="pure", audit_subset="audit_sample")
    return [mk("A", pool=("a", "b"), pool_judgments={"a": "same", "b": "different"}, **base),
            mk("B", pool=("a", "b", "c"), pool_judgments={"a": "cannot_tell", "b": "same", "c": "different"}, **base),
            mk("C", pool=("a", "b"), pool_judgments={"a": "cannot_tell", "b": "different"}, **base),
            mk("D", pool=("a", "b"), pool_judgments={"a": "different", "b": "different"}, **base),
            mk("E", outcome="provider_failed", **base),
            mk("X1", label_state=None, audit_subset="audit_sample"),
            aud("X2", state="uncertain", purity="pure"), aud("X3", state="unverifiable", purity=None),
            aud("X4", state="unresolved", purity="pure"),
            mk("X5", pool=("a", "b"), pool_judgments={"a": "different"}, **base)]


def test_conditional_verified_retrieval_denominator_is_the_verified_same_cases_only():
    r = m.evaluate_primary(category_cases(), FRAME)["verified_retrieval"]["audit_sample"]
    assert r["judgment_categories"] == {"verified_same_in_pool": 2, "cannot_tell_only": 1, "verified_no_match": 1, "empty_pool": 1,
                                        "verified_same_with_cannot_tell_candidates": 1}
    assert r["resolved_cases_used"] == 5                                                                       # A to E
    for k in (1, 5, 10):
        assert r[f"conditional_recall_at_{k}"]["denominator"] == 2                                            # A and B only
    assert r["conditional_mrr"]["denominator"] == 2
    assert "outside it" in r["judgment_categories_note"]


def test_conditional_bounds_use_cannot_tell_candidates_and_every_other_category_is_outside_the_denominator():
    r = m.evaluate_primary(category_cases(), FRAME)["verified_retrieval"]["audit_sample"]
    assert (r["conditional_recall_at_1"]["lower"]["numerator"], r["conditional_recall_at_1"]["upper"]["numerator"]) == (1, 2)     # B: same at 2, cannot-tell at 1
    assert (r["conditional_recall_at_5"]["lower"]["numerator"], r["conditional_recall_at_5"]["upper"]["numerator"]) == (2, 2)
    assert r["conditional_mrr"]["lower"] == pytest.approx((1 + 1 / 2) / 2) and r["conditional_mrr"]["upper"] == pytest.approx((1 + 1) / 2)
    assert r["end_to_end_success_at_1"]["lower"]["denominator"] == 5 and r["end_to_end_success_at_1"]["upper"]["numerator"] == 3   # A, B and C could hit at 1
    assert r["case_counts"]["indefinite_mapped_cases"] == 1


def test_the_conditional_definition_is_unchanged_for_cases_without_cannot_tell():
    base = dict(label_state="resolved", group_purity="pure", audit_subset="audit_sample")
    cases = [mk("1", pool=("a", "b"), pool_judgments={"a": "different", "b": "same"}, **base), mk("2", pool=("a", "b"), pool_judgments={"a": "different", "b": "different"}, **base)]
    r = m.evaluate_primary(cases, FRAME)["verified_retrieval"]["audit_sample"]
    assert r["conditional_recall_at_5"]["denominator"] == 1 and r["conditional_recall_at_1"]["lower"]["numerator"] == 0
    assert r["judgment_categories"]["verified_no_match"] == 1 and r["judgment_categories"]["verified_same_with_cannot_tell_candidates"] == 0
