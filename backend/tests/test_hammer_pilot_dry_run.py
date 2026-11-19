"""Synthetic end-to-end dry run, per-gate policy checks, shared-response provenance, validator hardening, output integrity."""
import asyncio
import json

import pytest

from author_resolution.candidates import AuthorCandidateInput, OpenAlexCandidate
from author_resolution.context import QueryContext
from author_resolution.policy import (
    S1_UNSCORED_COMPETITOR, S2_NO_CORROBORATION, S3_HARD_CONFLICT, S4_INCOMPARABLE, S5_INCOMPLETE,
)
from author_resolution.resolver import RankedCandidate, rank_candidates
from author_resolution.scoring import CandidateScore
from hammer_pilot.common import read_csv, sha256_file
from hammer_pilot.pipeline import run_pipeline
from hammer_pilot.replay import evaluate_policies
from hammer_pilot.reproducibility import RUN_ID, verify_reproducibility
from hammer_pilot.validation import validate_pilot
from author_test_helpers import cand, payload, work
from pilot_fixtures import (
    build_synthetic_pilot, capture, make_handler, one, seed, write_annotation, write_csv, write_pilot, write_stage_b,
)

INST = {"institution_hints": ["Example Institute"]}
BASE = {"run_id": "t", "case_id": "P1", "condition": "C1", "pool_status": "ok", "pool_size": 1, "fallback_status": ""}


def rows_for(tmp_path, c1, authors, **handler_kw):
    pilot = write_pilot(tmp_path / "p", [seed("P1", "Alice Smith", c1=c1)])
    capture(pilot, make_handler(authors={"Alice Smith": authors}, **handler_kw))
    asyncio.run(run_pipeline(pilot, tmp_path / "out"))
    preds = read_csv(tmp_path / "out" / "predictions.csv", {"case_id", "condition", "policy", "outcome"})
    return {(r["condition"], r["policy"]): r for r in preds}


def fake(aid, score, signals, sig_set, ctx=INST, name="Alice Smith"):
    c = cand(aid, name)
    ev = rank_candidates([c], QueryContext.from_any(ctx))[0].evidence
    return RankedCandidate(c, ev, CandidateScore(score, signals, {}, signal_set=tuple(sig_set)))


def policies(ranked):
    return {r["policy"]: r for r in evaluate_policies(BASE, "ok", ranked)}


NI = ("name_similarity", "institution_similarity")


# ------------------------------------------------------------------ Task 2: each gate on its own
def test_p0_null_top_score_is_no_score_in_every_policy():
    out = policies([RankedCandidate(cand("A1"), [], CandidateScore(None, 0, {}))])
    assert {p: r["outcome"] for p, r in out.items()} == {"forced_top1": "no_score", "selective_policy_v2": "no_score", "legacy_gates_plus_p3": "no_score"}


def test_p1_two_signal_minimum_is_enforced_by_both_selective_policies():
    out = policies([fake("A1", 0.95, 1, ("name_similarity",))])
    assert out["selective_policy_v2"]["outcome"] == "manual" and out["legacy_gates_plus_p3"]["outcome"] == "manual"


def test_p2_margin_and_dominance_apply_to_both_selective_policies():
    top = fake("A9", 0.9, 2, NI)
    margin_fail = policies([top, fake("A1", 0.8, 2, NI)])                    # margin 0.1
    dominance_fail = policies([top, fake("A1", 0.7, 2, NI)])                 # margin 0.2 but dominance 1.286
    clear = policies([top, fake("A1", 0.5, 2, NI)])                          # margin 0.4, dominance 1.8
    for out in (margin_fail, dominance_fail):
        assert out["selective_policy_v2"]["outcome"] == "manual" and out["legacy_gates_plus_p3"]["outcome"] == "manual"
    assert clear["selective_policy_v2"]["outcome"] == "auto" and clear["legacy_gates_plus_p3"]["outcome"] == "auto"


def test_p3_relaxes_only_margin_and_dominance_for_a_single_candidate():
    single = policies([fake("A1", 0.8, 2, NI)])
    assert single["selective_policy_v2"]["outcome"] == "auto" and single["legacy_gates_plus_p3"]["outcome"] == "auto"
    with_close_competitor = policies([fake("A1", 0.8, 2, NI), fake("A2", 0.75, 2, NI)])
    assert with_close_competitor["selective_policy_v2"]["outcome"] == "manual" and with_close_competitor["legacy_gates_plus_p3"]["outcome"] == "manual"
    assert policies([fake("A1", 0.8, 1, ("name_similarity",))])["legacy_gates_plus_p3"]["outcome"] == "manual"      # P1 not bypassed
    assert policies([fake("A1", 0.7, 2, NI)])["legacy_gates_plus_p3"]["outcome"] == "manual"                        # score gate not bypassed


def test_p9_manual_and_p10_unresolved_boundaries():
    assert policies([fake("A1", 0.5, 2, NI)])["selective_policy_v2"]["outcome"] == "manual"
    assert policies([fake("A1", 0.5, 2, NI)])["legacy_gates_plus_p3"]["outcome"] == "manual"
    assert policies([fake("A1", 0.3, 2, NI)])["selective_policy_v2"]["outcome"] == "unresolved"
    assert policies([fake("A1", 0.3, 2, NI)])["legacy_gates_plus_p3"]["outcome"] == "unresolved"


def test_p4_unscored_competitor_blocks_v2_but_cannot_arise_from_a_replay_snapshot():
    top = fake("A1", 0.95, 2, NI)
    unscored = RankedCandidate(cand("A2"), [], CandidateScore(None, 0, {}))
    out = policies([top, unscored])
    assert out["selective_policy_v2"]["outcome"] == "manual" and S1_UNSCORED_COMPETITOR in json.loads(out["selective_policy_v2"]["auto_blockers"])
    assert out["legacy_gates_plus_p3"]["outcome"] == "manual"          # P2 cannot be evaluated without a competitor score
    # Reconstruction limit: a captured response cannot yield an unscored candidate, because the parser drops profiles without a name.
    assert OpenAlexCandidate.from_openalex({"id": "https://openalex.org/A5", "display_name": ""}, AuthorCandidateInput("x"), None) is None


def test_p5_corroboration_blocks_name_plus_temporal_only(tmp_path):
    rows = rows_for(tmp_path, {"active_year_start": 2020, "active_year_end": 2022}, [one()])
    v2, legacy = rows[("C1", "selective_policy_v2")], rows[("C1", "legacy_gates_plus_p3")]
    assert v2["outcome"] == "manual" and S2_NO_CORROBORATION in json.loads(v2["auto_blockers"]) and legacy["outcome"] == "auto"


def test_p6_zero_signal_blocks_v2_only(tmp_path):
    rows = rows_for(tmp_path, {**INST, "active_year_start": 2030, "active_year_end": 2031}, [one()])
    assert S3_HARD_CONFLICT in json.loads(rows[("C1", "selective_policy_v2")]["auto_blockers"])
    assert rows[("C1", "selective_policy_v2")]["outcome"] == "manual" and rows[("C1", "legacy_gates_plus_p3")]["outcome"] == "auto"


def test_p7_incomparable_signal_sets_block_v2_only(tmp_path):
    rows = rows_for(tmp_path, INST, [one("A1"), one("A2", "Zed Different", inst=None)])
    v2 = rows[("C1", "selective_policy_v2")]
    assert S4_INCOMPARABLE in json.loads(v2["auto_blockers"]) and v2["outcome"] == "manual"
    assert rows[("C1", "legacy_gates_plus_p3")]["outcome"] == "auto" and v2["different_signal_sets_in_pool"] == "True"


def test_p8_failed_enrichment_blocks_v2_only(tmp_path):
    rows = rows_for(tmp_path, {**INST, "coauthors": [{"openalex_id": "A7"}]}, [one()], author_works={"A1": 500})
    v2 = rows[("C1", "selective_policy_v2")]
    assert S5_INCOMPLETE in json.loads(v2["auto_blockers"]) and v2["outcome"] == "manual"
    assert rows[("C1", "legacy_gates_plus_p3")]["outcome"] == "auto"


def test_only_the_disabled_gate_changes_the_legacy_result(tmp_path):
    """Where no P4-P8 safeguard fires, v2 and legacy agree."""
    rows = rows_for(tmp_path, INST, [one()])
    assert rows[("C1", "selective_policy_v2")]["outcome"] == rows[("C1", "legacy_gates_plus_p3")]["outcome"] == "auto"
    assert json.loads(rows[("C1", "selective_policy_v2")]["auto_blockers"]) == []


# ------------------------------------------------------------------ Tasks 1, 3, 5: the full synthetic pipeline
@pytest.fixture(scope="module")
def synthetic(tmp_path_factory):
    root = tmp_path_factory.mktemp("synthetic")
    pilot = build_synthetic_pilot(root / "pilot")
    out = root / "out"
    asyncio.run(run_pipeline(pilot, out))
    return pilot, out


def preds(out):
    return {(r["case_id"], r["condition"], r["policy"]): r for r in read_csv(out / "predictions.csv", {"case_id", "condition", "policy", "outcome"})}


def test_synthetic_dataset_validates_and_has_the_requested_composition(synthetic):
    pilot, _ = synthetic
    rep = validate_pilot(pilot)
    assert rep.ok, rep.errors
    assert rep.info["final_composition"] == {"resolved": 10, "unresolved": 5, "uncertain": 0}
    assert rep.info["doi_overlap_cases"] == {"P08": ["10.9999/both08"]}


def test_synthetic_outcomes_cover_every_requested_situation(synthetic):
    _, out = synthetic
    p = preds(out)
    v2 = lambda c, cond="C1": p[(c, cond, "selective_policy_v2")]["outcome"]
    assert v2("P01") == "auto" and v2("P03") == "auto"                         # automatic assignment (single, and with a competitor)
    assert v2("P02") == "manual" and v2("P09") == "manual"                     # abstention (tie of two fragments; no usable coauthor IDs)
    assert v2("P04") == "empty_pool" and v2("P05") == "provider_failed"        # empty pool and provider failure stay distinct
    assert p[("P06", "C1", "selective_policy_v2")]["outcome"] == "manual" and p[("P06", "C1", "legacy_gates_plus_p3")]["outcome"] == "auto"   # partial enrichment
    assert v2("P07") == "auto" and v2("P08") == "auto"
    assert v2("P10") == "auto" and v2("P12") == "auto"                         # an incorrect automatic assignment and a false acceptance exist
    assert all(p[(c, "C0", "selective_policy_v2")]["outcome"] not in ("auto",) for c in (f"P{i:02d}" for i in range(1, 16)))


def test_doi_disjoint_and_both_cases(synthetic):
    _, out = synthetic
    snap = [json.loads(l) for l in (out / "evidence_snapshot.jsonl").read_text().splitlines()]
    sig = lambda case, cond: {e["signal"]: e["status"] for e in next(s for s in snap if s["case_id"] == case and s["condition"] == cond)["candidates"][0]["evidence"]}
    assert sig("P07", "C1")["publication_overlap"] == "observed"               # disjoint DOI: eligible primary evidence
    assert sig("P08", "C1")["publication_overlap"] == "unavailable_query_input_absent"    # 'both' DOI: never primary
    assert sig("P08", "C1x")["publication_overlap"] == "observed"                         # exploratory only
    assert sig("P09", "C1")["coauthor_overlap"] == "unavailable_input_unresolvable"       # names only: no eligible coauthor IDs


def test_metrics_counts_denominators_and_c0_label(synthetic):
    _, out = synthetic
    metrics = json.loads((out / "metrics.json").read_text())

    def walk(node, path=""):
        if isinstance(node, dict):
            if "numerator" in node:
                assert "denominator" in node, path
            for k, v in node.items():
                walk(v, f"{path}/{k}")
    walk(metrics)
    for key, m in metrics["selective_RQ2b"].items():
        assert "eligible_cases" in m and m["eligible_cases"] == 15, key
        if key.startswith("C0/") and not key.endswith("forced_top1"):
            assert m["automatic_coverage_zero_by_design"] is True and "BY DESIGN" in m["structural_note"] and m["automatic_coverage"]["numerator"] == 0
        if key.startswith("C1/") and not key.endswith("forced_top1"):
            assert "automatic_coverage_zero_by_design" not in m
    c1 = metrics["selective_RQ2b"]["C1/selective_policy_v2"]
    assert c1["incorrect_automatic"] == 2 and c1["false_acceptances_on_unresolved_controls"] == 1
    assert c1["outcome_counts"]["provider_failed"] == 1 and c1["outcome_counts"]["empty_pool"] == 2    # kept separate from unresolved/manual
    assert metrics["retrieval_RQ2a"]["arms"]["R2"]["recall_at_1"]["numerator"] > metrics["retrieval_RQ2a"]["arms"]["R0"]["recall_at_1"]["numerator"]
    assert metrics["trace"]["frozen_inputs_sha256"]["stage_b.csv"] and metrics["trace"]["run_id"].startswith("run-")


def test_shared_r0_r2_response_is_one_physical_observation(synthetic):
    pilot, out = synthetic
    manifest = json.loads((out / "run_manifest.json").read_text())
    recs = [r for r in manifest["logical_requests"] if r["case_id"] == "P01"]
    r0 = next(r for r in recs if r["arm"] == "R0")
    r2 = next(r for r in recs if r["role"] == "R2_primary")
    assert r0["body_file"] == r2["body_file"] and r0["sha256"] == r2["sha256"] and r0["seq"] == r2["seq"]
    assert r0["shares_response_with"] == ["R2_primary"] and r2["shares_response_with"] == ["R0"]
    p02 = [r for r in manifest["logical_requests"] if r["case_id"] == "P02"]
    assert next(r for r in p02 if r["arm"] == "R0")["sha256"] != next(r for r in p02 if r["role"] == "R2_primary")["sha256"]   # separate requests, separate responses
    assert manifest["physical_response_count"] < manifest["logical_request_count"]
    index = [json.loads(l) for l in (pilot / "captures" / "capture_index.jsonl").read_text().splitlines()]
    bodies = {f.name for f in (pilot / "captures" / "bodies").iterdir()}
    assert bodies == {e["body_file"].split("/")[-1] for e in index if e["body_file"]}          # one physical file per captured response
    assert len([e for e in index if e["key"] == next(x for x in index if x["seq"] == r0["seq"])["key"]]) == 1   # the shared request was issued once
    retr = read_csv(out / "retrieval.csv", {"case_id", "arm", "response_sha256", "shares_response_with_other_arm"})
    assert {r["arm"] for r in retr if r["case_id"] == "P01" and r["shares_response_with_other_arm"] == "True"} == {"R0", "R2"}
    prov = json.loads((out / "metrics.json").read_text())["retrieval_RQ2a"]["response_provenance"]
    assert prov["cases_where_R0_and_R2_share_one_physical_response"] >= 1 and "not two independent observations" in prov["note"]
    paired = json.loads((out / "metrics.json").read_text())["retrieval_RQ2a"]["paired_r0_vs_r2_discordant"]["independent_comparison_cases"]
    assert paired["n"] + paired["shared_response_cases_excluded"] == 10


def test_manifest_hashes_every_scoring_evidence_context_enrichment_policy_and_replay_file(synthetic):
    _, out = synthetic
    m = json.loads((out / "run_manifest.json").read_text())
    needed = {"author_resolution/scoring.py", "author_resolution/evidence.py", "author_resolution/context.py", "author_resolution/enrichment.py",
              "author_resolution/enrichment_types.py", "author_resolution/policy.py", "author_resolution/resolver.py", "author_resolution/candidates.py"}
    assert needed <= set(m["author_resolution_source_hashes"])
    assert {"hammer_pilot/replay.py", "hammer_pilot/capture.py", "hammer_pilot/metrics.py", "hammer_pilot/validation.py", "hammer_pilot/context_rules.py", "hammer_pilot/pipeline.py"} <= set(m["evaluator_source_hashes"])
    assert m["config_hash"] and m["run_id"] and m["input_hashes"]["review_a.csv"] and m["input_hashes"]["development_exclusions.csv"]


def test_reproducibility_compares_every_artifact_with_a_fixed_run_id(synthetic, tmp_path):
    pilot, _ = synthetic
    result = asyncio.run(verify_reproducibility(pilot, tmp_path / "w"))
    assert result["identical"] and result["run_id"] == RUN_ID and result["bytes_compared"] > 0
    assert set(result["files"]) == {"predictions.csv", "retrieval.csv", "evidence_snapshot.jsonl", "metrics.json", "run_manifest.json"}
    for run in ("run_a", "run_b"):
        assert {r["run_id"] for r in read_csv(tmp_path / "w" / run / "predictions.csv", {"run_id"})} == {RUN_ID}
        assert json.loads((tmp_path / "w" / run / "run_manifest.json").read_text())["run_id"] == RUN_ID


# ------------------------------------------------------------------ Task 4: validator hardening
def fresh(tmp_path):
    return build_synthetic_pilot(tmp_path / "pilot")


def errors(p):
    return validate_pilot(p).errors


def edit(path, old, new, count=1):
    text = path.read_text()
    assert old in text, old
    path.write_text(text.replace(old, new, count))


def test_validator_never_modifies_input(tmp_path):
    p = fresh(tmp_path)
    before = {f: sha256_file(f) for f in sorted(p.rglob("*")) if f.is_file()}
    validate_pilot(p)
    assert {f: sha256_file(f) for f in before} == before


def test_cross_case_duplicate_doi_is_an_error(tmp_path):
    p = fresh(tmp_path)
    edit(p / "doi_register.csv", "10.9999/gold02", "10.9999/gold01")
    assert any("used by several cases" in e for e in errors(p))


def test_development_exclusions_manifest_is_mandatory(tmp_path):
    p = fresh(tmp_path)
    (p / "development_exclusions.csv").unlink()
    assert any("development_exclusions.csv is mandatory" in e for e in errors(p))


def test_two_distinct_reviewer_ids_and_separate_records(tmp_path):
    p = fresh(tmp_path)
    edit(p / "review_b.csv", "rev-B", "rev-A", count=99)
    assert any("two distinct reviewer IDs" in e for e in errors(p))
    p2 = fresh(tmp_path / "x")
    (p2 / "review_b.csv").unlink()
    assert any("review_b.csv" in e for e in errors(p2))


def test_adjudication_requires_a_third_person(tmp_path):
    p = fresh(tmp_path)
    edit(p / "stage_a.csv", "adj-C", "rev-A")
    assert any("adjudicator distinct from both reviewers" in e for e in errors(p))


def test_reviewer_submissions_must_be_blind(tmp_path):
    p = fresh(tmp_path)
    edit(p / "review_a.csv", "case_id,", "score,case_id,")
    assert any("forbidden columns" in e for e in errors(p))
    p2 = fresh(tmp_path / "y")
    edit(p2 / "review_a.csv", "independent public evidence", "HAMMER ranked this person first", count=1)
    assert any("mentions HAMMER output" in e for e in errors(p2))
    p3 = fresh(tmp_path / "z")
    edit(p3 / "review_b.csv", "independent public evidence", "matches profile A101", count=1)
    assert any("captured candidate ID" in e for e in errors(p3))


def test_timestamp_consistency(tmp_path):
    p = fresh(tmp_path)
    edit(p / "review_a.csv", "2025-12-30T10:00:00Z", "2099-01-01T00:00:00Z", count=1)
    assert any("review was submitted after candidate capture began" in e for e in errors(p))
    p2 = fresh(tmp_path / "x")
    edit(p2 / "stage_b.csv", "2099-01-01T00:00:00Z", "2000-01-01T00:00:00Z", count=1)
    assert any("before the last candidate capture" in e for e in errors(p2))


def test_one_gold_person_cannot_be_assigned_to_two_cases(tmp_path):
    p = fresh(tmp_path)
    edit(p / "stage_a.csv", "person-02", "person-01")
    assert any("assigned to several cases" in e for e in errors(p))


def test_reviewer_disagreement_must_not_be_recorded_as_agreed(tmp_path):
    p = fresh(tmp_path)
    edit(p / "stage_a.csv", "adjudicated", "agreed")
    assert any("P14: reviewers disagree; adjudication_status must be" in e for e in errors(p))


def test_both_doi_needs_justification_and_is_c1x_only(tmp_path):
    seeds = [seed("P1", "Alice Smith", c1={"publications": ["10.9999/b1"]})]
    no_just = [{"case_id": "P1", "doi": "10.9999/b1", "purpose": "both", "registered_by": "reviewer_a", "justification_if_both": ""}]
    assert any("needs a justification" in e for e in errors(write_pilot(tmp_path / "a", seeds, no_just)))
    ok = [{**no_just[0], "justification_if_both": "documented"}]
    from hammer_pilot.context_rules import derive_contexts, register_by_case
    ctx = derive_contexts(seeds[0], register_by_case(ok)["P1"])
    assert "publications" not in ctx["C1"] and ctx["C1x"]["publications"] == ["10.9999/b1"]       # C1x only
