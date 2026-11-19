import asyncio
import json

import pytest

from author_resolution.policy import S1_UNSCORED_COMPETITOR
from author_resolution.resolver import RankedCandidate, rank_candidates
from author_resolution.scoring import CandidateScore
from author_resolution.context import QueryContext
from hammer_pilot.common import PilotDataError, read_csv
from hammer_pilot.pipeline import run_pipeline
from hammer_pilot.replay import evaluate_policies
from author_test_helpers import cand, work
from pilot_fixtures import REG_FIELDS, capture, make_handler, one, seed, write_csv, write_pilot


def replay(pilot, out):
    asyncio.run(run_pipeline(pilot, out))
    preds = read_csv(out / "predictions.csv", {"case_id", "condition", "policy", "outcome"})
    return {(r["case_id"], r["condition"], r["policy"]): r for r in preds}


def build(tmp_path, seeds, handler, register=()):
    pilot = write_pilot(tmp_path / "p", seeds, register)
    capture(pilot, handler)
    return pilot


C1_INST = {"institution_hints": ["Example Institute"]}


def test_c0_is_structurally_unable_to_assign_automatically(tmp_path):
    pilot = build(tmp_path, [seed("P1", "Alice Smith", c1=C1_INST)], make_handler(authors={"Alice Smith": [one()]}))
    p = replay(pilot, tmp_path / "out")
    assert p[("P1", "C0", "selective_policy_v2")]["outcome"] == "manual"
    assert p[("P1", "C0", "legacy_gates_plus_p3")]["outcome"] == "manual"          # still needs two signals
    assert p[("P1", "C0", "forced_top1")]["outcome"] == "auto"                      # forced top-1 selects rank 1 on the name alone
    assert p[("P1", "C0", "forced_top1")]["selected_author_id"] == "A1"


def test_c1_with_available_signals_can_assign_automatically(tmp_path):
    pilot = build(tmp_path, [seed("P1", "Alice Smith", c1=C1_INST)], make_handler(authors={"Alice Smith": [one()]}))
    p = replay(pilot, tmp_path / "out")
    row = p[("P1", "C1", "selective_policy_v2")]
    assert row["outcome"] == "auto" and json.loads(row["top_signal_set"]) == ["name_similarity", "institution_similarity"]
    snap = [json.loads(l) for l in (tmp_path / "out" / "evidence_snapshot.jsonl").read_text().splitlines()]
    c1 = next(s for s in snap if s["condition"] == "C1")
    sig = {e["signal"]: e["status"] for e in c1["candidates"][0]["evidence"]}
    assert sig["institution_similarity"] == "observed" and sig["publication_overlap"] == "unavailable_query_input_absent"
    assert c1["candidates"][0]["effective_weights"]["institution_similarity"] > 0


def test_c1x_doi_overlap_is_exploratory_and_never_in_primary_c1(tmp_path):
    reg = [{"case_id": "P1", "doi": "10.1000/gold", "purpose": "both", "registered_by": "reviewer_a", "justification_if_both": "documented"}]
    pilot = write_pilot(tmp_path / "p", [seed("P1", "Alice Smith", c1={**C1_INST, "publications": ["10.1000/gold"]})], reg)
    capture(pilot, make_handler(authors={"Alice Smith": [one()]}, doi_works=[work("W1", "10.1000/gold", ["A1"])]))
    asyncio.run(run_pipeline(pilot, tmp_path / "out"))
    snap = {s["condition"]: s for s in (json.loads(l) for l in (tmp_path / "out" / "evidence_snapshot.jsonl").read_text().splitlines())}
    status = lambda cond: {e["signal"]: e["status"] for e in snap[cond]["candidates"][0]["evidence"]}["publication_overlap"]
    assert status("C1") == "unavailable_query_input_absent"          # gold DOI removed from primary C1
    assert status("C1x") == "observed"
    assert snap["C1x"]["candidates"][0]["evidence"][2]["score"] == 1.0


def test_three_policies_on_a_tie(tmp_path):
    pilot = build(tmp_path, [seed("P1", "Alice Smith", c1=C1_INST)], make_handler(authors={"Alice Smith": [one("A1"), one("A2")]}))
    p = replay(pilot, tmp_path / "out")
    assert p[("P1", "C1", "selective_policy_v2")]["outcome"] == "manual" and p[("P1", "C1", "legacy_gates_plus_p3")]["outcome"] == "manual"
    assert p[("P1", "C1", "forced_top1")]["outcome"] == "auto" and p[("P1", "C1", "forced_top1")]["selected_author_id"] == "A2"   # descending-ID tie-break


def test_p3_single_candidate_relaxes_only_margin_and_dominance(tmp_path):
    ctx = {**C1_INST, "active_year_start": 2030, "active_year_end": 2031}        # years after the candidate's range: observed 0.0
    pilot = build(tmp_path, [seed("P1", "Alice Smith", c1=ctx)], make_handler(authors={"Alice Smith": [one()]}))
    p = replay(pilot, tmp_path / "out")
    v2, legacy = p[("P1", "C1", "selective_policy_v2")], p[("P1", "C1", "legacy_gates_plus_p3")]
    assert legacy["outcome"] == "auto"                                            # P0-P3 only: single candidate, gates pass
    assert v2["outcome"] == "manual" and "observed_zero_signal" in json.loads(v2["auto_blockers"])   # P6 still applies to P3


def test_p3_does_not_bypass_p1_two_signal_requirement(tmp_path):
    pilot = build(tmp_path, [seed("P1", "Alice Smith")], make_handler(authors={"Alice Smith": [one()]}))
    p = replay(pilot, tmp_path / "out")
    assert p[("P1", "C0", "legacy_gates_plus_p3")]["outcome"] == "manual"        # single candidate, score 1.0, but one signal


def test_unscored_competitor_fails_closed_and_forced_top1_still_selects():
    ctx = QueryContext.from_any(C1_INST)
    top = rank_candidates([cand("A1")], ctx)[0]
    unscored = RankedCandidate(cand("A2"), [], CandidateScore(None, 0, {}))
    rows = {r["policy"]: r for r in evaluate_policies({"case_id": "P1", "condition": "C1", "pool_status": "ok", "pool_size": 2, "fallback_status": ""}, "ok", [top, unscored])}
    assert rows["selective_policy_v2"]["outcome"] == "manual" and S1_UNSCORED_COMPETITOR in json.loads(rows["selective_policy_v2"]["auto_blockers"])
    assert rows["legacy_gates_plus_p3"]["outcome"] == "manual" and rows["forced_top1"]["outcome"] == "auto"


def test_different_signal_sets_are_recorded_and_withhold_automation(tmp_path):
    pilot = build(tmp_path, [seed("P1", "Alice Smith", c1=C1_INST)],
                  make_handler(authors={"Alice Smith": [one("A1", inst="Example Institute"), one("A2", inst=None)]}))
    p = replay(pilot, tmp_path / "out")
    row = p[("P1", "C1", "selective_policy_v2")]
    assert row["different_signal_sets_in_pool"] == "True" and row["outcome"] != "auto"
    assert len(json.loads(row["candidate_signal_sets"])) == 2


def test_distinct_outcome_categories_are_preserved(tmp_path):
    pilot = build(tmp_path, [seed("P1", "Failing Name"), seed("P2", "Empty Name"), seed("P3", "Alice Smith")],
                  make_handler(authors={"Failing Name": 500, "Empty Name": [], "Alice Smith": [one()]}))
    p = replay(pilot, tmp_path / "out")
    assert p[("P1", "C0", "selective_policy_v2")]["outcome"] == "provider_failed"
    assert p[("P2", "C0", "selective_policy_v2")]["outcome"] == "empty_pool"
    assert p[("P3", "C0", "selective_policy_v2")]["outcome"] == "manual"


def test_replay_never_invents_a_missing_capture(tmp_path):
    pilot = build(tmp_path, [seed("P1", "Alice Smith", c1={"coauthors": [{"openalex_id": "A7"}]})],
                  make_handler(authors={"Alice Smith": [one()]}, author_works={"A1": [work("W1", None, ["A1", "A7"])]}))
    index = pilot / "captures" / "capture_index.jsonl"
    lines = index.read_text().splitlines()
    index.write_text("\n".join(l for l in lines if "author.id" not in l) + "\n")
    with pytest.raises(PilotDataError):
        asyncio.run(run_pipeline(pilot, tmp_path / "out"))


def test_tampered_capture_is_detected(tmp_path):
    pilot = build(tmp_path, [seed("P1", "Alice Smith")], make_handler(authors={"Alice Smith": [one()]}))
    body = next((pilot / "captures" / "bodies").iterdir())
    body.write_bytes(body.read_bytes() + b" ")
    with pytest.raises(PilotDataError):
        asyncio.run(run_pipeline(pilot, tmp_path / "out"))


def test_replay_makes_no_network_calls(tmp_path, monkeypatch):
    import httpx
    pilot = build(tmp_path, [seed("P1", "Alice Smith", c1={"coauthors": [{"openalex_id": "A7"}]})],
                  make_handler(authors={"Alice Smith": [one()]}, author_works={"A1": [work("W1", None, ["A1", "A7"])]}))

    async def forbidden(self, *a, **k):
        raise AssertionError("network used during replay")
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)
    asyncio.run(run_pipeline(pilot, tmp_path / "out"))
