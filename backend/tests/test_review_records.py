"""T009: tests of the review records, validation, agreement statistics and conversion to C7 case fields (Decision B5 to B7). Synthetic records only."""
import math

import pytest

from hammer_pilot import metrics_c7 as m
from hammer_pilot import review_records as rr
from hammer_pilot.review_records import ReviewError

CANDS = ["K-1", "K-2", "K-3"]
CROSS = {"K-1": "A100", "K-2": "A200", "K-3": "A300"}


def a_row(reviewer, status="resolved", purity="pure", case="c1", **kw):
    return {"case_id": case, "reviewer_id": reviewer, "status": status, "group_purity": purity, "confidence": 4, "rationale": "r", "evidence_refs": "e", "searches": "s",
            "orcid_encountered": "false", "minutes": 12, **kw}


def b_rows(reviewer, judg, case="c1", minutes=3, **kw):
    return [{"case_id": case, "reviewer_id": reviewer, "candidate": c, "judgment": j, "confidence": 3, "evidence_refs": "e", "orcid_encountered": "false", "minutes": minutes, **kw}
            for c, j in judg.items()]


SAME = {"K-1": "same", "K-2": "different", "K-3": "different"}


def agreeing():
    return [a_row("r1"), a_row("r2")], b_rows("r1", SAME) + b_rows("r2", SAME)


def resolve(a, b, final=None, builder="builder", cands=CANDS):
    return rr.resolve_case("c1", a, b, final, candidates=cands, builder_id=builder)


# ---------------------------------------------------------------- validation of single rows
@pytest.mark.parametrize("bad", [dict(status="maybe"), dict(group_purity="cannot_tell"), dict(confidence=0), dict(confidence=6), dict(confidence="x"),
                                 dict(orcid_encountered="perhaps"), dict(minutes=-1), dict(minutes="nan"), dict(reviewer_id="")])
def test_invalid_stage_a_rows_are_rejected(bad):
    with pytest.raises(ReviewError):
        rr.validate_stage_a({**a_row("r1"), **bad})


@pytest.mark.parametrize("bad", [dict(judgment="probably"), dict(confidence=9), dict(candidate=""), dict(minutes=-5)])
def test_invalid_stage_b_rows_are_rejected(bad):
    with pytest.raises(ReviewError):
        rr.validate_stage_b({**b_rows("r1", SAME)[0], **bad})


def test_purity_vocabulary_matches_c7_and_judgment_parsing():
    assert rr.PURITY == m.PURITY and rr.STATUSES == m.LABEL_STATES and rr.JUDGMENTS == m.JUDGMENTS
    assert rr.parse_judgments("K-1:same; K-2:different;") == {"K-1": "same", "K-2": "different"}
    with pytest.raises(ReviewError):
        rr.parse_judgments("K-1:maybe")


# ---------------------------------------------------------------- one case: independence, completeness, adjudication
def test_agreeing_reviewers_give_the_final_label_by_agreement_and_raw_rows_are_untouched():
    a, b = agreeing()
    before = (list(map(dict, a)), list(map(dict, b)))
    out = resolve(a, b)
    assert out["source"] == "agreement" and out["status"] == "resolved" and out["candidate_judgments"] == SAME and out["adjudicator_id"] is None
    assert (a, b) == before


def test_exactly_two_distinct_reviewers_are_required():
    a, b = agreeing()
    with pytest.raises(ReviewError, match="two distinct reviewers"):
        resolve([a[0]], b[:3])
    with pytest.raises(ReviewError, match="two distinct reviewers"):
        resolve([a_row("r1"), a_row("r1")], b)
    with pytest.raises(ReviewError, match="packet builder is a reviewer"):
        resolve(a, b, builder="r2")


def test_every_candidate_must_be_judged_by_each_reviewer():
    a, b = agreeing()
    with pytest.raises(ReviewError, match="did not judge every candidate"):
        resolve(a, b[:-1])
    with pytest.raises(ReviewError, match="not in the packet"):
        resolve(a, b + b_rows("r1", {"K-9": "same"}))
    with pytest.raises(ReviewError, match="more than once"):
        resolve(a, b + b_rows("r1", {"K-1": "same"}))
    assert resolve(a, [], cands=[])["candidate_judgments"] == {}                                         # no pool: Stage A only


def test_disagreement_requires_an_independent_adjudicator_and_keeps_both_reviewer_rows():
    a = [a_row("r1"), a_row("r2", status="uncertain")]
    b = b_rows("r1", SAME) + b_rows("r2", {**SAME, "K-2": "same"})
    with pytest.raises(ReviewError, match="no adjudication"):
        resolve(a, b)
    final = {"case_id": "c1", "adjudicator_id": "judge", "final_status": "resolved", "final_group_purity": "pure", "candidate_judgments": "K-1:same;K-2:different;K-3:different", "rationale": "x"}
    out = resolve(a, b, final)
    assert out["source"] == "adjudication" and out["adjudicator_id"] == "judge" and out["candidate_judgments"] == SAME
    assert a[1]["status"] == "uncertain"                                                                  # the original reviewer row is not overwritten
    for who in ("r1", "r2", "builder"):
        with pytest.raises(ReviewError, match="third person"):
            resolve(a, b, {**final, "adjudicator_id": who})
    with pytest.raises(ReviewError, match="every candidate"):
        resolve(a, b, {**final, "candidate_judgments": "K-1:same"})


def test_purity_and_candidate_disagreements_also_require_adjudication():
    a = [a_row("r1"), a_row("r2", purity="impure")]
    with pytest.raises(ReviewError, match="no adjudication"):
        resolve(a, b_rows("r1", SAME) + b_rows("r2", SAME))
    a2, _ = agreeing()
    with pytest.raises(ReviewError, match="no adjudication"):
        resolve(a2, b_rows("r1", SAME) + b_rows("r2", {**SAME, "K-3": "cannot_tell"}))


def test_a_non_resolved_adjudication_need_not_judge_candidates():
    a = [a_row("r1", status="unverifiable", purity="unresolved"), a_row("r2", status="uncertain", purity="unresolved")]
    b = []
    final = {"case_id": "c1", "adjudicator_id": "judge", "final_status": "unverifiable", "final_group_purity": "unresolved", "candidate_judgments": "", "rationale": "x"}
    out = resolve(a, b, final, cands=[])
    assert out["status"] == "unverifiable" and out["candidate_judgments"] == {}


# ---------------------------------------------------------------- conversion to C7
def test_conversion_applies_the_crosswalk_and_feeds_the_c7_module():
    a, b = agreeing()
    label = resolve(a, b)
    fields = rr.to_c7_fields(label, CROSS, audit_subset="audit_sample", selected_candidate="A100")
    assert fields == {"label_state": "resolved", "group_purity": "pure", "audit_subset": "audit_sample", "pool_judgments": {"A100": "same", "A200": "different", "A300": "different"},
                      "selected_judgment": "same"}
    case = m.Case(case_id="c1", block_id="b1", stratum="S", outcome="manual", pool_ids=("A100", "A200", "A300"), mapped_ids=frozenset({"A100"}), **fields | {"selected_judgment": None})
    assert m.audit_status(case) == ("consistent", [], None)                                               # the reviewers agree with the benchmark mapping
    wrong = m.Case(case_id="c2", block_id="b2", stratum="S", outcome="manual", pool_ids=("A100", "A200", "A300"), mapped_ids=frozenset({"A200"}),
                   **rr.to_c7_fields(label, CROSS, audit_subset="audit_sample"))
    assert m.audit_status(wrong)[:2] == ("contradicted", ["false_mapping", "missed_mapping"])


def test_conversion_for_an_automatic_case_gives_the_selected_judgment_for_the_c7_scoring_table():
    a, b = agreeing()
    fields = rr.to_c7_fields(resolve(a, b), CROSS, audit_subset="automatic", selected_candidate="A200")
    case = m.Case(case_id="c1", block_id="b1", stratum="S", outcome="auto", pool_ids=("A100", "A200", "A300"), selected_id="A200", **fields)
    assert m.score_automatic(case) == ("incorrect", "resolved_different")
    ok = m.Case(case_id="c2", block_id="b2", stratum="S", outcome="auto", pool_ids=("A100", "A200", "A300"), selected_id="A100",
                **rr.to_c7_fields(resolve(a, b), CROSS, audit_subset="automatic", selected_candidate="A100"))
    assert m.score_automatic(ok) == ("correct", "resolved_same")


def test_conversion_without_candidates_gives_no_pool_judgments():
    label = {"status": "unresolved", "group_purity": "pure", "candidate_judgments": {}}
    assert rr.to_c7_fields(label, {}, audit_subset="audit_sample")["pool_judgments"] is None


# ---------------------------------------------------------------- agreement statistics
def test_cohens_kappa_matches_hand_computed_values():
    pairs = [("y", "y")] * 20 + [("y", "n")] * 5 + [("n", "y")] * 10 + [("n", "n")] * 15
    r = rr.cohens_kappa(pairs)
    assert r["n"] == 50 and r["agreements"] == 35 and r["raw_agreement"] == pytest.approx(0.7) and r["chance_agreement"] == pytest.approx(0.5) and r["kappa"] == pytest.approx(0.4)
    assert r["categories"]["y"] == {"rater1": 25, "rater2": 30}
    three = [("a", "a")] * 6 + [("b", "b")] * 3 + [("c", "c")] * 1 + [("a", "b")] * 2 + [("b", "c")] * 1 + [("c", "a")] * 1                         # n = 14
    r3 = rr.cohens_kappa(three)
    po = 10 / 14
    pe = (9 / 14) * (8 / 14) + (4 / 14) * (5 / 14) + (2 / 14) * (2 / 14) * 0 + (1 / 14) * 0 + 0
    ca, cb = {"a": 8 + 0, "b": 4, "c": 2}, {"a": 7, "b": 5, "c": 2}
    pe = sum(ca[k] * cb[k] for k in "abc") / 14 ** 2
    assert r3["raw_agreement"] == pytest.approx(po) and r3["kappa"] == pytest.approx((po - pe) / (1 - pe))
    assert "unstable at small n" in r3["note"]


def test_kappa_edge_cases_are_reported_not_hidden():
    assert rr.cohens_kappa([])["kappa"] is None
    same = rr.cohens_kappa([("y", "y")] * 5)
    assert same["raw_agreement"] == 1.0 and same["kappa"] is None and "undefined" in same["note"]
    perfect = rr.cohens_kappa([("y", "y")] * 3 + [("n", "n")] * 3)
    assert perfect["kappa"] == pytest.approx(1.0)
    opposite = rr.cohens_kappa([("y", "n")] * 3 + [("n", "y")] * 3)
    assert opposite["kappa"] == pytest.approx(-1.0)


def test_agreement_report_pairs_the_two_reviewers_per_case_and_candidate():
    a = [a_row("r1", case="c1"), a_row("r2", case="c1"), a_row("r1", case="c2", status="uncertain"), a_row("r2", case="c2")]
    b = b_rows("r1", SAME, "c1") + b_rows("r2", SAME, "c1") + b_rows("r1", SAME, "c2") + b_rows("r2", {**SAME, "K-3": "same"}, "c2")
    rep = rr.agreement_report(a, b)
    assert rep["stage_a_status"]["n"] == 2 and rep["stage_a_status"]["agreements"] == 1 and rep["stage_a_purity"]["raw_agreement"] == 1.0
    assert rep["stage_b_judgment"]["n"] == 6 and rep["stage_b_judgment"]["agreements"] == 5


def test_orcid_encounters_and_reviewer_time_summary():
    a = [a_row("r1", orcid_encountered="true"), a_row("r2", minutes=18, case="c1")]
    b = b_rows("r1", SAME, minutes=2) + b_rows("r2", SAME, minutes=4)
    enc = rr.orcid_encounter_summary(a, b)
    assert enc["cases_with_an_orcid_encounter"] == 1 and enc["case_ids"] == ["c1"] and "separately" in enc["note"]
    t = rr.reviewer_time_summary(a, b, hours_available=10)
    assert t["t_A_minutes_mean"] == pytest.approx(15) and t["t_B_minutes_mean"] == pytest.approx(3) and t["mean_candidates_per_case"] == 3
    assert t["affordable_cases_per_reviewer"] == math.floor(60 * 10 / (15 + 3 * 3)) == 25
    with pytest.raises(ReviewError):
        rr.reviewer_time_summary(a, b, hours_available=-1)
    with pytest.raises(ReviewError):
        rr.reviewer_time_summary([], b, hours_available=5)


def test_an_orcid_encounter_recorded_only_in_stage_b_is_counted():
    a = [a_row("r1", case="c1"), a_row("r2", case="c1")]
    b = b_rows("r1", SAME, case="c1") + b_rows("r2", SAME, case="c1", orcid_encountered="true")
    enc = rr.orcid_encounter_summary(a, b)
    assert enc["cases_with_an_orcid_encounter"] == 1 and enc["case_ids"] == ["c1"] and enc["cases"] == 1


def test_the_time_helper_requires_explicit_hours():
    import inspect
    assert inspect.signature(rr.reviewer_time_summary).parameters["hours_available"].default is inspect.Parameter.empty


# ---------------------------------------------------------------- CSV templates and round trip
def test_templates_have_exact_headers_and_no_data_and_refuse_overwrite(tmp_path):
    names = rr.write_templates(tmp_path / "t")
    assert names == ["final_labels.csv", "stage_a_reviews.csv", "stage_b_reviews.csv"]
    assert rr.read_csv(tmp_path / "t" / "stage_a_reviews.csv", rr.STAGE_A_FIELDS) == []
    with pytest.raises(FileExistsError):
        rr.write_templates(tmp_path / "t")
    with pytest.raises(ReviewError, match="header"):
        rr.read_csv(tmp_path / "t" / "stage_a_reviews.csv", rr.STAGE_B_FIELDS)


def test_csv_round_trip_and_the_pipeline_from_csv_to_a_final_label(tmp_path):
    a, b = agreeing()
    rr.write_csv(tmp_path / "a.csv", rr.STAGE_A_FIELDS, a)
    rr.write_csv(tmp_path / "b.csv", rr.STAGE_B_FIELDS, b)
    with pytest.raises(FileExistsError):
        rr.write_csv(tmp_path / "a.csv", rr.STAGE_A_FIELDS, a)
    ra, rb = rr.read_csv(tmp_path / "a.csv", rr.STAGE_A_FIELDS), rr.read_csv(tmp_path / "b.csv", rr.STAGE_B_FIELDS)
    out = resolve(ra, rb)
    assert out["status"] == "resolved" and out["candidate_judgments"] == SAME and len(ra) == 2 and len(rb) == 6
