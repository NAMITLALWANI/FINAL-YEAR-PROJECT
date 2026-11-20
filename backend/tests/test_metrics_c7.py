"""Synthetic-fixture tests of the Decision C7 metrics module. No benchmark data, no captures, no network."""
import json
import math
import re
from pathlib import Path

import pytest

from hammer_pilot import metrics_c7 as m
from hammer_pilot.metrics import clopper_pearson, zero_event_upper_bound
from hammer_pilot.metrics_c7 import C7Error, Case, InferenceSettings


def mk(cid, stratum="S", outcome="manual", pool=("a", "b"), mapped=(), selected="", g=1, block=None, **kw):
    pool = () if outcome in ("empty_pool", "provider_failed") else tuple(pool)
    return Case(case_id=cid, block_id=block or f"B-{cid}", stratum=stratum, outcome=outcome, pool_ids=pool, mapped_ids=frozenset(mapped),
                selected_id=selected, group_count=g, **kw)


def auto(cid, state=None, judgments=None, selected="a", **kw):
    return mk(cid, outcome="auto", selected=selected, label_state=state, pool_judgments=judgments, **kw)


def est(report_section, name, estimand="E1"):
    return report_section[name]["pooled"][estimand]


# ---------------------------------------------------------------- input validation
@pytest.mark.parametrize("kwargs", [
    dict(outcome="bogus"),
    dict(outcome="empty_pool", pool_ids=("a",)),
    dict(outcome="manual", pool_ids=()),
    dict(outcome="auto", pool_ids=("a",), selected_id=""),
    dict(outcome="manual", pool_ids=("a",), selected_id="a"),
    dict(outcome="manual", pool_ids=("a", "a")),
    dict(outcome="manual", pool_ids=("a",), label_state="maybe"),
    dict(outcome="manual", pool_ids=("a",), selected_judgment="probably"),
    dict(outcome="manual", pool_ids=("a",), group_count=0),
    dict(outcome="manual", pool_ids=("a",), audit_subset="automatic"),
    dict(outcome="auto", pool_ids=("a",), selected_id="a", audit_subset="audit_sample"),
    dict(outcome="manual", pool_ids=("a",), pool_judgments={"z": "same"}),
])
def test_inconsistent_cases_are_rejected(kwargs):
    base = dict(case_id="c", block_id="b", stratum="S")
    with pytest.raises(C7Error):
        Case(**{**base, **kwargs})


def test_sample_validation_one_primary_per_block_known_strata_and_frame_size():
    with pytest.raises(C7Error, match="more than one primary case in a block"):
        m.evaluate_primary([mk("1", block="X"), mk("2", block="X")], {"S": 10})
    with pytest.raises(C7Error, match="missing from the frame"):
        m.evaluate_primary([mk("1", stratum="Q")], {"S": 10})
    with pytest.raises(C7Error, match="exceed the frame size"):
        m.evaluate_primary([mk("1"), mk("2"), mk("3")], {"S": 2})
    with pytest.raises(C7Error, match="duplicate case_id"):
        m.evaluate_primary([mk("1", block="X"), mk("1", block="Y")], {"S": 10})
    with pytest.raises(C7Error, match="no primary cases"):
        m.evaluate_primary([mk("1", is_primary=False)], {"S": 10})


def test_secondary_cases_are_excluded_from_every_estimate_and_counted():
    cases = [mk("p1", outcome="auto", selected="a"), mk("p2"), mk("s1", block="B-p1", outcome="auto", selected="a", is_primary=False)]
    rep = m.evaluate_primary(cases, {"S": 100})
    assert rep["case_accounting"]["n_primary"] == 2 and rep["case_accounting"]["n_secondary_excluded"] == 1
    assert rep["label_free"]["rate_auto"]["per_stratum"]["S"]["denominator"] == 2


# ---------------------------------------------------------------- label-free rates: all N, six categories
def test_six_outcome_categories_partition_all_primary_cases_and_use_all_N():
    cases = [auto("1"), auto("2"), mk("3"), mk("4"), mk("5", outcome="unresolved"), mk("6", outcome="empty_pool"),
             mk("7", outcome="provider_failed"), mk("8", outcome="no_score")]
    rep = m.evaluate_primary(cases, {"S": 1000})
    acc = rep["case_accounting"]
    assert acc["n_primary"] == 8 and sum(acc["outcome_counts"].values()) == 8
    assert acc["outcome_counts"] == {"auto": 2, "manual": 2, "unresolved": 1, "empty_pool": 1, "provider_failed": 1, "no_score": 1}
    nums = {o: rep["label_free"][f"rate_{o}"]["per_stratum"]["S"] for o in m.OUTCOMES}
    assert all(v["denominator"] == 8 for v in nums.values())                    # failures and empties stay in the denominator
    assert sum(v["numerator"] for v in nums.values()) == 8
    assert nums["auto"]["value"] == 0.25
    assert rep["label_free"]["rate_auto"]["label_basis"] == "label_free"


# ---------------------------------------------------------------- retrieval: end-to-end versus conditional
def retrieval_cases():
    return [mk("1", pool=("a", "b"), mapped={"a"}),                  # first mapped rank 1
            mk("2", pool=("a", "b", "c"), mapped={"c"}),              # rank 3
            mk("3", pool=("a", "b"), mapped={"z"}),                   # successful pool, no mapped profile
            mk("4", outcome="provider_failed", mapped={"z"})]         # failure counts as a miss end-to-end


def test_end_to_end_and_conditional_retrieval_have_the_right_denominators():
    rep = m.evaluate_primary(retrieval_cases(), {"S": 1000})["retrieval_benchmark_derived"]
    cell = lambda name: rep[name]["per_stratum"]["S"]
    assert (cell("pool_mapping_rate")["numerator"], cell("pool_mapping_rate")["denominator"]) == (2, 4)
    assert (cell("end_to_end_success_at_1")["numerator"], cell("end_to_end_success_at_1")["denominator"]) == (1, 4)
    assert (cell("end_to_end_success_at_5")["numerator"], cell("end_to_end_success_at_5")["denominator"]) == (2, 4)
    assert (cell("conditional_recall_at_1")["numerator"], cell("conditional_recall_at_1")["denominator"]) == (1, 2)
    assert (cell("conditional_recall_at_5")["numerator"], cell("conditional_recall_at_5")["denominator"]) == (2, 2)
    assert cell("end_to_end_mrr")["value"] == pytest.approx((1 + 1 / 3) / 4)
    assert cell("conditional_mrr")["value"] == pytest.approx((1 + 1 / 3) / 2)
    assert cell("end_to_end_mrr")["denominator"] == 4 and cell("conditional_mrr")["denominator"] == 2


def test_mapping_uses_only_the_given_r2_pool():
    c = mk("1", pool=("a", "b"), mapped={"x"})                       # the mapped candidate exists only outside this pool (e.g. an R0-only hit)
    assert m.first_rank(c) is None
    rep = m.evaluate_primary([c], {"S": 100})["retrieval_benchmark_derived"]
    assert rep["pool_mapping_rate"]["per_stratum"]["S"]["numerator"] == 0


# ---------------------------------------------------------------- verified scoring table
@pytest.mark.parametrize("state,judgments,expected", [
    ("resolved", {"a": "same", "b": "different"}, ("correct", "resolved_same")),
    ("resolved", {"a": "different", "b": "same"}, ("incorrect", "resolved_different")),
    ("resolved", {"a": "different", "b": "different"}, ("incorrect", "resolved_no_matching_candidate")),
    ("resolved", {"a": "cannot_tell", "b": "different"}, ("uncertain", "selected_cannot_tell")),
    ("unresolved", None, ("incorrect", "unresolved")),
    ("uncertain", None, ("uncertain", "case_uncertain")),
    ("unverifiable", None, ("unverifiable", "case_unverifiable")),
    (None, None, ("unverified", "not_verified")),
])
def test_verified_scoring_table(state, judgments, expected):
    assert m.score_automatic(auto("1", state, judgments)) == expected


def test_scoring_requires_a_selected_judgment_for_resolved_cases_and_only_automatic_cases():
    with pytest.raises(C7Error, match="needs a judgment"):
        m.score_automatic(auto("1", "resolved", None))
    with pytest.raises(C7Error, match="only automatic"):
        m.score_automatic(mk("2"))


def verified_set():
    return [auto("A1", "resolved", {"a": "same", "b": "different"}),
            auto("A2", "resolved", {"a": "same", "b": "different"}),
            auto("A3", "resolved", {"a": "different", "b": "same"}),
            auto("A4", "resolved", {"a": "different", "b": "different"}),   # definite identity, no matching candidate
            auto("A5", "unresolved"),                                        # no unique intended person
            auto("A6", "uncertain"),
            auto("A7", "unverifiable")]


def test_precision_denominator_keeps_unresolved_and_no_match_and_drops_only_uncertain():
    rep = m.evaluate_primary(verified_set(), {"S": 1000})["selective_verified"]
    cell = lambda name: rep["estimates"][name]["per_stratum"]["S"]
    p = cell("verified_automatic_precision")
    assert (p["numerator"], p["denominator"]) == (2, 5)                      # A3, A4, A5 are incorrect but stay in
    r = cell("verified_selective_risk")
    assert (r["numerator"], r["denominator"]) == (3, 5)
    assert rep["scoring"]["status_counts"] == {"correct": 2, "incorrect": 3, "uncertain": 1, "unverifiable": 1, "unverified": 0}
    assert rep["scoring"]["reason_counts"]["resolved_no_matching_candidate"] == 1 and rep["scoring"]["reason_counts"]["unresolved"] == 1
    assert rep["scoring"]["verification_complete"] is True


def test_all_wrong_and_all_right_brackets():
    est_ = m.evaluate_primary(verified_set(), {"S": 1000})["selective_verified"]["estimates"]
    lo = est_["verified_precision_all_wrong"]["per_stratum"]["S"]
    hi = est_["verified_precision_all_right"]["per_stratum"]["S"]
    assert (lo["numerator"], lo["denominator"]) == (2, 7)                    # uncertain and unverifiable counted as wrong
    assert (hi["numerator"], hi["denominator"]) == (4, 7)                    # counted as right
    assert lo["value"] < 2 / 5 < hi["value"]


def test_unverified_automatic_assignments_are_flagged_not_dropped():
    rep = m.evaluate_primary([auto("1", "resolved", {"a": "same", "b": "different"}), auto("2")], {"S": 100})["selective_verified"]
    assert rep["scoring"]["verification_complete"] is False and rep["scoring"]["status_counts"]["unverified"] == 1


def test_benchmark_precision_counts_unmapped_selection_as_incorrect():
    cases = [auto("1", mapped={"a"}), auto("2", mapped={"z"}), mk("3")]
    cell = m.evaluate_primary(cases, {"S": 100})["selective_benchmark_derived"]["benchmark_automatic_precision"]["per_stratum"]["S"]
    assert (cell["numerator"], cell["denominator"]) == (1, 2)


# ---------------------------------------------------------------- reporting classes
def test_every_case_has_exactly_one_reporting_class():
    cases = [mk("1"),                                                                               # benchmark-derived
             mk("2", label_state="resolved", audit_subset="audit_sample", group_purity="pure", pool_judgments={"a": "different", "b": "different"}),
             mk("3", label_state="uncertain", audit_subset="audit_sample"),
             mk("4", label_state="unverifiable", audit_subset="audit_sample"),
             auto("5", "resolved", {"a": "same", "b": "different"}, audit_subset="automatic"),
             auto("6", "resolved", {"a": "cannot_tell", "b": "different"}, audit_subset="automatic")]  # cannot tell for the selected candidate
    acc = m.evaluate_primary(cases, {"S": 100})["case_accounting"]
    assert acc["reporting_class_counts"] == {"verified": 2, "uncertain": 2, "unverifiable": 1, "benchmark_derived": 1}
    assert sum(acc["reporting_class_counts"].values()) == 6
    assert m.reporting_class(cases[1]) == "verified"                                               # an audited case is never benchmark-derived


# ---------------------------------------------------------------- strata, weights, census
def test_weights_and_pooled_estimates_for_e1_and_e2():
    frame = {"S": 100, "M": 40, "XL": 2}
    cases = [auto("s1", g=3), mk("s2"), mk("s3"), mk("s4"),
             auto("m1", stratum="M", g=2), auto("m2", stratum="M", g=2),
             mk("x1", stratum="XL"), mk("x2", stratum="XL")]
    rep = m.evaluate_primary(cases, frame, InferenceSettings(bootstrap_min_stratum_n=2, bootstrap_resamples=20), seed=1)
    pooled = rep["label_free"]["rate_auto"]["pooled"]
    assert pooled["E1"]["point"] == pytest.approx((25 * 1 + 20 * 2 + 1 * 0) / (25 * 4 + 20 * 2 + 1 * 2))     # N_h/n_h: S 25, M 20, XL 1
    assert pooled["E2"]["point"] == pytest.approx((25 * 3 + 20 * 2 + 20 * 2) / (25 * (3 + 1 + 1 + 1) + 20 * (2 + 2) + 1 * (1 + 1)))
    assert pooled["E1"]["weighted_denominator"] == pytest.approx(142)


def test_census_strata_have_no_interval_and_are_flagged():
    cases = [mk("x1", stratum="XL", outcome="auto", selected="a"), mk("x2", stratum="XL")]
    cell = m.evaluate_primary(cases, {"XL": 2})["label_free"]["rate_auto"]["per_stratum"]["XL"]
    assert cell["census"] is True and cell["interval"] is None and "census" in cell["interval_status"]
    assert cell["sampling_fraction"] == 1.0 and cell["value"] == 0.5


def test_per_stratum_interval_is_clopper_pearson_and_sampling_fraction_is_flagged():
    cases = [auto(f"a{i}") for i in range(3)] + [mk(f"m{i}") for i in range(7)]
    cell = m.evaluate_primary(cases, {"S": 50})["label_free"]["rate_auto"]["per_stratum"]["S"]
    lo, hi = clopper_pearson(3, 10)
    assert cell["interval"] == [round(lo, 6), round(hi, 6)]
    assert cell["sampling_fraction"] == 0.2 and cell["sampling_fraction_flag"] is True            # above the provisional 0.10 trigger
    assert "conservative superpopulation approximation" in cell["interval_status"]


def test_unsampled_and_negligible_strata_are_dropped_and_the_estimand_is_relabelled():
    frame = {"S": 1000, "M": 1000, "XL": 1}
    cases = [auto("1"), mk("2"), mk("3", stratum="M", outcome="auto", selected="a"), mk("4", stratum="M")]
    rep = m.evaluate_primary(cases, frame, InferenceSettings(negligible_weight=0.01))
    pooled = rep["label_free"]["rate_auto"]["pooled"]["E1"]
    assert pooled["pooled_over"] == ["S", "M"] and "XL" in pooled["dropped_strata"] and "unsampled" in pooled["dropped_strata"]["XL"]
    assert rep["label_free"]["rate_auto"]["per_stratum"]["XL"]["interval_status"] == "unsampled stratum"
    cases2 = cases + [mk("5", stratum="XL")]
    pooled2 = m.evaluate_primary(cases2, frame, InferenceSettings(negligible_weight=0.01))["label_free"]["rate_auto"]["pooled"]["E1"]
    assert "negligible_weight" in pooled2["dropped_strata"]["XL"] and pooled2["pooled_over"] == ["S", "M"]
    pooled3 = m.evaluate_primary(cases2, frame)["label_free"]["rate_auto"]["pooled"]["E1"]          # no rule given: nothing is dropped silently
    assert pooled3["pooled_over"] == ["S", "M", "XL"] and pooled3["dropped_strata"] == {}


# ---------------------------------------------------------------- bootstrap and sparse handling
def hits_sample(n=50, hits=20, stratum="S"):
    return [mk(f"{stratum}{i}", stratum=stratum, outcome="auto" if i < hits else "manual", selected="a" if i < hits else "") for i in range(n)]


def test_bootstrap_is_reproducible_seeded_and_plausible():
    cases = hits_sample()
    settings = InferenceSettings(bootstrap_min_stratum_n=10, bootstrap_resamples=400)
    a = m.evaluate_primary(cases, {"S": 5000}, settings, seed=11)
    b = m.evaluate_primary(cases, {"S": 5000}, settings, seed=11)
    c = m.evaluate_primary(cases, {"S": 5000}, settings, seed=12)
    assert m.to_json(a) == m.to_json(b)
    assert m.to_json(a) != m.to_json(c)
    p = est(a["label_free"], "rate_auto")
    lo, hi = p["interval"]
    assert p["interval_status"] == "bootstrap" and p["regime"] == "R2" and p["point"] == pytest.approx(0.4)
    assert lo < 0.4 < hi and 0.2 < hi - lo < 0.35
    assert p["bootstrap"]["resamples_used"] == 400


def test_bootstrap_withheld_when_minimum_stratum_size_is_unspecified_or_not_met():
    cases = hits_sample(30, 10)
    p = est(m.evaluate_primary(cases, {"S": 5000}, seed=1)["label_free"], "rate_auto")
    assert p["interval"] is None and "unspecified" in p["interval_status"]
    p = est(m.evaluate_primary(cases, {"S": 5000}, InferenceSettings(bootstrap_min_stratum_n=40), seed=1)["label_free"], "rate_auto")
    assert p["interval"] is None and "too small to resample" in p["interval_status"] and p["point"] is not None
    with pytest.raises(C7Error, match="seed"):
        m.evaluate_primary(cases, {"S": 5000}, InferenceSettings(bootstrap_min_stratum_n=10))


def test_a_too_small_stratum_is_withheld_unless_the_negligible_weight_rule_drops_it():
    frame = {"S": 5000, "XL": 400}
    cases = hits_sample(30, 10) + [mk(f"x{i}", stratum="XL", outcome="manual") for i in range(3)]
    base = InferenceSettings(bootstrap_min_stratum_n=10, bootstrap_resamples=50)
    assert est(m.evaluate_primary(cases, frame, base, seed=2)["label_free"], "rate_auto")["interval"] is None
    dropped = InferenceSettings(bootstrap_min_stratum_n=10, bootstrap_resamples=50, negligible_weight=0.1)
    p = est(m.evaluate_primary(cases, frame, dropped, seed=2)["label_free"], "rate_auto")
    assert p["interval"] is not None and p["pooled_over"] == ["S"] and "XL" in p["dropped_strata"]


def test_all_census_strata_give_no_interval_and_no_bootstrap():
    cases = [mk("a", stratum="XL", outcome="auto", selected="a"), mk("b", stratum="XL")]
    p = est(m.evaluate_primary(cases, {"XL": 2}, InferenceSettings(bootstrap_min_stratum_n=1), seed=1)["label_free"], "rate_auto")
    assert p["interval"] is None and "census" in p["interval_status"] and p["point"] == 0.5


def test_census_strata_are_held_fixed_in_the_bootstrap():
    cases = hits_sample(40, 8) + [mk("x1", stratum="XL", outcome="auto", selected="a"), mk("x2", stratum="XL")]
    rep = m.evaluate_primary(cases, {"S": 4000, "XL": 2}, InferenceSettings(bootstrap_min_stratum_n=10, bootstrap_resamples=100), seed=3)
    assert est(rep["label_free"], "rate_auto")["interval"] is not None
    assert rep["label_free"]["rate_auto"]["per_stratum"]["XL"]["interval"] is None


def test_zero_errors_never_produce_a_bootstrap_interval():
    cases = [auto(f"c{i}", "resolved", {"a": "same", "b": "different"}) for i in range(12)] + [mk("m")]
    p = est(m.evaluate_primary(cases, {"S": 5000}, InferenceSettings(bootstrap_min_stratum_n=5, bootstrap_resamples=50), seed=1)["selective_verified"]["estimates"],
            "verified_automatic_precision")
    assert p["regime"] == "R3" and p["interval"] is None and "bootstrap" not in p
    assert p["zero_event_one_sided_95_upper_bound"] == pytest.approx(round(zero_event_upper_bound(12), 6))
    assert p["unweighted_counts"]["ci95_exact"] == [round(x, 6) for x in clopper_pearson(12, 12)]


def test_adequate_counts_use_the_bootstrap_for_automatic_precision():
    cases = [mk(f"c{i}", outcome="auto", selected="a", mapped={"a"} if i < 30 else {"z"}) for i in range(40)] + [mk(f"m{i}") for i in range(20)]
    rep = m.evaluate_primary(cases, {"S": 5000}, InferenceSettings(bootstrap_min_stratum_n=20, bootstrap_resamples=200), seed=5)
    p = est(rep["selective_benchmark_derived"], "benchmark_automatic_precision")
    assert p["regime"] == "R2" and p["interval"] is not None and p["point"] == pytest.approx(0.75)
    assert p["unweighted_counts"]["numerator"] == 30 and p["unweighted_counts"]["denominator"] == 40


def test_sparse_warning_thresholds_are_provisional_parameters_and_reported_as_such():
    cases = [mk(f"c{i}", outcome="auto", selected="a", mapped={"a"} if i < 30 else {"z"}) for i in range(40)]
    settings = InferenceSettings(bootstrap_min_stratum_n=20, bootstrap_resamples=50, sparse_automatic_warn=100)
    p = est(m.evaluate_primary(cases, {"S": 5000}, settings, seed=1)["selective_benchmark_derived"], "benchmark_automatic_precision")
    assert p["regime"] == "R3" and p["sparse_warning"]["status"] == "provisional thresholds"
    params = m.evaluate_primary(cases, {"S": 5000}, seed=1)["parameters"]
    assert params["bootstrap_min_stratum_n"]["status"] == "unspecified" and params["negligible_weight"]["status"] == "unspecified"
    assert params["sparse_automatic_warn"]["status"] == "provisional" and params["sampling_fraction_flag"]["status"] == "provisional"


# ---------------------------------------------------------------- verified retrieval and audit
def test_verified_retrieval_brackets_cannot_tell_and_never_pools_subsets():
    cases = [mk("1", outcome="manual", pool=("a", "b"), label_state="resolved", audit_subset="audit_sample", group_purity="pure", pool_judgments={"a": "different", "b": "same"}),
             mk("2", outcome="manual", pool=("a", "b"), label_state="resolved", audit_subset="audit_sample", group_purity="pure", pool_judgments={"a": "cannot_tell", "b": "different"}),
             mk("3", outcome="provider_failed", label_state="resolved", audit_subset="audit_sample", group_purity="pure"),
             mk("4", outcome="manual", pool=("a",), label_state="unresolved", audit_subset="audit_sample", group_purity="pure"),
             mk("5", outcome="manual", pool=("a",), label_state="uncertain", audit_subset="audit_sample"),
             mk("6", outcome="manual", pool=("a", "b"), label_state="resolved", audit_subset="audit_sample", group_purity="pure", pool_judgments={"a": "same"}),
             auto("7", "resolved", {"a": "same", "b": "different"}, audit_subset="automatic")]
    rep = m.evaluate_primary(cases, {"S": 1000})["verified_retrieval"]
    s = rep["audit_sample"]
    assert s["case_counts"]["ground_truth_unresolved"] == 1 and s["case_counts"]["uncertain_case"] == 1 and s["case_counts"]["incomplete_stage_b"] == 1
    assert s["resolved_cases_used"] == 3                                       # cases 1, 2 and 3; the provider failure counts as a miss
    assert s["end_to_end_success_at_1"]["lower"]["numerator"] == 0 and s["end_to_end_success_at_1"]["upper"]["numerator"] == 1
    assert s["end_to_end_success_at_5"]["lower"]["numerator"] == 1 and s["end_to_end_success_at_5"]["upper"]["numerator"] == 2
    assert s["end_to_end_success_at_5"]["indefinite_cases"] == 1
    assert s["end_to_end_mrr"]["lower"] == pytest.approx((1 / 2) / 3) and s["end_to_end_mrr"]["upper"] == pytest.approx((1 / 2 + 1) / 3)
    a = rep["automatic"]
    assert a["resolved_cases_used"] == 1 and a["mapping_rate"]["lower"]["numerator"] == 1
    assert "never pooled" in a["weighting"]


def test_audit_label_error_rate_and_bracket():
    judged = lambda **kw: mk(kw.pop("cid"), label_state=kw.pop("state", "resolved"), audit_subset="audit_sample", mapped={"a"}, **kw)
    cases = [judged(cid="1", group_purity="pure", pool_judgments={"a": "same", "b": "different"}),         # consistent
             judged(cid="2", group_purity="impure", pool_judgments={"a": "same", "b": "different"}),       # impure group
             judged(cid="3", group_purity="pure", pool_judgments={"a": "different", "b": "different"}),    # false mapping
             judged(cid="4", group_purity="pure", pool_judgments={"a": "same", "b": "same"}),              # missed mapping
             judged(cid="5", state="uncertain")]                                                            # indeterminate
    a = m.evaluate_primary(cases, {"S": 100})["audit_label_error"]
    assert (a["definite"], a["label_errors"], a["indeterminate"]) == (4, 3, 1)
    assert a["error_rate"]["value"] == 0.75
    assert a["bracket"]["all_right"]["value"] == pytest.approx(3 / 5) and a["bracket"]["all_wrong"]["value"] == pytest.approx(4 / 5)
    assert "not a correction factor" in a["population"]
    with pytest.raises(C7Error, match="group-purity"):
        m.evaluate_primary([mk("9", label_state="resolved", audit_subset="audit_sample")], {"S": 100})


# ---------------------------------------------------------------- whole report
def full_dataset():
    cases = []
    for i in range(6):
        cases.append(mk(f"s{i}", stratum="S", outcome="auto" if i < 2 else "manual", selected="a" if i < 2 else "", mapped={"a"} if i % 2 == 0 else {"z"},
                        label_state="resolved" if i < 2 else None, pool_judgments={"a": "same", "b": "different"} if i == 0 else ({"a": "different", "b": "different"} if i == 1 else None),
                        audit_subset="automatic" if i < 2 else None))
    for i in range(4):
        cases.append(mk(f"m{i}", stratum="M", outcome="manual", mapped={"b"}, label_state="resolved" if i == 0 else None,
                        audit_subset="audit_sample" if i == 0 else None, pool_judgments={"a": "different", "b": "same"} if i == 0 else None,
                        group_purity="pure" if i == 0 else None))
    cases += [mk("x0", stratum="XL", outcome="empty_pool"), mk("x1", stratum="XL", outcome="provider_failed"), mk("x2", stratum="XL", outcome="no_score")]
    return cases


def test_full_report_is_complete_deterministic_json_and_consistent():
    frame = {"S": 4000, "M": 3000, "XL": 3}
    settings = InferenceSettings(bootstrap_min_stratum_n=4, bootstrap_resamples=30)
    a = m.to_json(m.evaluate_primary(full_dataset(), frame, settings, seed=9))
    b = m.to_json(m.evaluate_primary(full_dataset(), frame, settings, seed=9))
    assert a == b
    rep = json.loads(a)
    assert set(rep) >= {"scope", "parameters", "case_accounting", "label_free", "retrieval_benchmark_derived", "selective_benchmark_derived",
                        "selective_verified", "verified_retrieval", "audit_label_error"}
    acc = rep["case_accounting"]
    assert acc["n_primary"] == 13 and sum(acc["outcome_counts"].values()) == 13 and sum(acc["reporting_class_counts"].values()) == 13
    assert acc["strata"]["XL"]["census"] is True
    assert not re.search(r"NaN|Infinity", a)
    for section in ("label_free", "retrieval_benchmark_derived"):
        assert all(v["label_basis"] in ("label_free", "benchmark_derived") for v in rep[section].values())
    assert all(v["label_basis"] == "verified" for v in rep["selective_verified"]["estimates"].values())


def test_cases_from_replay_builds_primary_cases_without_orcid_handling():
    preds = [{"case_id": "C1", "condition": "C1", "policy": "selective_policy_v2", "outcome": "auto", "selected_author_id": "A1"},
             {"case_id": "C2", "condition": "C1", "policy": "selective_policy_v2", "outcome": "manual", "selected_author_id": ""},
             {"case_id": "C1", "condition": "C0", "policy": "selective_policy_v2", "outcome": "manual", "selected_author_id": ""}]
    ret = [{"case_id": "C1", "arm": "R2", "ordered_candidate_ids": '["A1","A2"]'}, {"case_id": "C1", "arm": "R0", "ordered_candidate_ids": '["A9"]'},
           {"case_id": "C2", "arm": "R2", "ordered_candidate_ids": '["B1"]'}]
    cases = m.cases_from_replay(preds, ret, condition="C1", policy="selective_policy_v2", block_by_case={"C1": "b1", "C2": "b2"},
                                stratum_by_case={"C1": "S", "C2": "M"}, mapped_by_case={"C1": {"A2"}})
    assert [(c.case_id, c.outcome, c.pool_ids, c.selected_id) for c in cases] == [("C1", "auto", ("A1", "A2"), "A1"), ("C2", "manual", ("B1",), "")]
    assert cases[0].mapped_ids == frozenset({"A2"}) and cases[1].mapped_ids == frozenset()


def test_the_module_has_no_network_or_orcid_field_access():
    src = Path(m.__file__).read_text(encoding="utf-8")
    assert not re.search(r"^\s*(import|from)\s+(httpx|requests|urllib|socket|aiohttp)", src, re.M)
    assert not re.search(r"""["'](ids\.)?orcid["']|\.orcid\b""", src, re.I)               # prose may mention ORCID; no field is ever read


def test_estimates_use_exactly_the_c5_parameters_listed():
    p = InferenceSettings().describe()
    assert p["bootstrap_resamples"]["value"] == 10_000 and p["sampling_fraction_flag"]["value"] == 0.10
    assert math.isclose(p["sparse_automatic_warn"]["value"], 30) and p["sparse_error_warn"]["value"] == 5
