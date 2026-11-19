import asyncio
import json

import httpx
import pytest

from hammer_pilot.capture import classify_author_response
from hammer_pilot.common import PilotDataError, sha256_file
from pilot_fixtures import capture, make_handler, one, seed, write_pilot
from author_test_helpers import work


def summary(pilot, case):
    return json.loads((pilot / "captures" / "cases" / f"{case}.json").read_text())


def test_r0_normal_capture_preserves_raw_body_hash_and_order(tmp_path):
    pilot = write_pilot(tmp_path / "p", [seed("P1", "  Alice Smith ")])
    r = capture(pilot, make_handler(authors={"Alice Smith": [one("A2"), one("A1")]}))
    s = summary(pilot, "P1")
    assert s["R0"]["status"] == "ok" and s["R0"]["candidate_ids"] == ["A2", "A1"]        # provider order preserved, query trimmed
    index = [json.loads(l) for l in (pilot / "captures" / "capture_index.jsonl").read_text().splitlines()]
    entry = next(e for e in index if e["seq"] == s["R0"]["seq"])
    assert sha256_file(pilot / "captures" / entry["body_file"]) == entry["sha256"] and entry["status"] == 200 and r.requests_made >= 1


def test_no_secret_is_written_anywhere(tmp_path):
    pilot = write_pilot(tmp_path / "p", [seed("P1", "Alice Smith")])
    capture(pilot, make_handler(authors={"Alice Smith": [one()]}), mailto="mailto-token-xyz", api_key="key-token-abc")
    blob = "".join(p.read_text(errors="ignore") for p in (pilot / "captures").rglob("*") if p.is_file())
    assert "mailto-token-xyz" not in blob and "key-token-abc" not in blob


def test_r2_successful_primary_issues_no_fallback(tmp_path):
    pilot = write_pilot(tmp_path / "p", [seed("P1", "Y. LeCun")])
    calls = []
    capture(pilot, make_handler(authors={"Y. LeCun": [one("A1", "Yann LeCun")]}, calls=calls))
    s = summary(pilot, "P1")
    assert s["R2_primary"]["status"] == "ok" and s["R2_fallback"] is None and s["r2_pool_status"] == "ok"


def test_r2_fallback_after_successful_empty_primary_is_recorded_separately(tmp_path):
    pilot = write_pilot(tmp_path / "p", [seed("P1", "Y. LeCun")])
    capture(pilot, make_handler(authors={"Y. LeCun": []}, search={"Y. LeCun": [one("A9", "Yann LeCun")]}))
    s = summary(pilot, "P1")
    assert s["R0"]["status"] == "empty" and s["R0"]["seq"] == s["R2_primary"]["seq"]       # identical request captured once
    assert s["R2_primary"]["status"] == "empty" and s["R2_fallback"]["status"] == "ok" and s["r2_pool_candidate_ids"] == ["A9"]
    assert s["R2_fallback"]["seq"] != s["R2_primary"]["seq"]


def test_no_fallback_without_an_initial(tmp_path):
    pilot = write_pilot(tmp_path / "p", [seed("P1", "Nobody Known")])
    capture(pilot, make_handler())
    assert summary(pilot, "P1")["R2_fallback"] is None and summary(pilot, "P1")["r2_pool_status"] == "empty"


def test_r2_fallback_failure_is_not_a_plain_empty(tmp_path):
    pilot = write_pilot(tmp_path / "p", [seed("P1", "Y. LeCun")])
    capture(pilot, make_handler(authors={"Y. LeCun": []}, search={"Y. LeCun": 500}))
    s = summary(pilot, "P1")
    assert s["R2_fallback"]["status"] == "provider_failed" and s["r2_pool_status"] == "provider_failed"


def test_provider_failure_versus_successful_empty(tmp_path):
    pilot = write_pilot(tmp_path / "p", [seed("P1", "Failing Name"), seed("P2", "Empty Name")])
    capture(pilot, make_handler(authors={"Failing Name": 500, "Empty Name": []}))
    assert summary(pilot, "P1")["r2_pool_status"] == "provider_failed" and summary(pilot, "P1")["R0"]["error_code"] == "http_error"
    assert summary(pilot, "P2")["r2_pool_status"] == "empty" and summary(pilot, "P2")["R0"]["error_code"] is None


def test_timeout_and_malformed_responses_are_preserved(tmp_path):
    pilot = write_pilot(tmp_path / "p", [seed("P1", "Slow Name"), seed("P2", "Bad Body")])
    capture(pilot, make_handler(authors={"Slow Name": httpx.ReadTimeout("t"), "Bad Body": "not json at all"}))
    assert summary(pilot, "P1")["R0"]["error_code"] == "ReadTimeout" and summary(pilot, "P1")["r2_pool_status"] == "provider_failed"
    s2 = summary(pilot, "P2")
    assert s2["R0"]["status"] == "malformed" and s2["r2_pool_status"] == "provider_failed"
    index = [json.loads(l) for l in (pilot / "captures" / "capture_index.jsonl").read_text().splitlines()]
    bad = next(e for e in index if e["seq"] == s2["R0"]["seq"])
    assert (pilot / "captures" / bad["body_file"]).read_bytes() == b"not json at all" and bad["json_valid"] is False
    assert classify_author_response(200, b'{"results": 5}', None)[0] == "malformed"


def test_partial_enrichment_is_captured_per_signal(tmp_path):
    c1 = {"institution_hints": ["Example Institute"], "coauthors": [{"openalex_id": "A7"}]}
    pilot = write_pilot(tmp_path / "p", [seed("P1", "Alice Smith", c1=c1)])
    handler = make_handler(authors={"Alice Smith": [one("A1"), one("A2")]}, author_works={"A1": [work("W1", None, ["A1", "A7"])], "A2": 500})
    capture(pilot, handler)
    enr = summary(pilot, "P1")["enrichment"]["C1"]
    assert enr["A1"]["coauthors"] == "ok" and enr["A2"]["coauthors"] == "failed"


def test_budget_exhaustion_stops_safely_and_blocks_resume(tmp_path):
    pilot = write_pilot(tmp_path / "p", [seed("P1", "Alice Smith"), seed("P2", "Bob Jones")])
    r = capture(pilot, make_handler(authors={"Alice Smith": [one()], "Bob Jones": [one("A2", "Bob Jones")]}), budget=1)
    assert r.budget_exhausted and r.requests_made == 1 and r.completed_cases == ["P1"]    # R0 and R2 primary share one request; P2 hit the budget
    with pytest.raises(PilotDataError):
        capture(pilot, make_handler(), resume=True)


def test_existing_captures_are_never_overwritten_or_mixed(tmp_path):
    pilot = write_pilot(tmp_path / "p", [seed("P1", "Alice Smith")])
    capture(pilot, make_handler(authors={"Alice Smith": [one()]}))
    with pytest.raises(PilotDataError):
        capture(pilot, make_handler(authors={"Alice Smith": [one()]}))
    r = capture(pilot, make_handler(), resume=True)                         # nothing left to do; nothing overwritten
    assert r.completed_cases == [] and r.requests_made == 0


def test_capture_requires_an_unchanged_seed_freeze(tmp_path):
    pilot = write_pilot(tmp_path / "p", [seed("P1", "Alice Smith")])
    (pilot / "seeds.csv").write_text((pilot / "seeds.csv").read_text().replace("Alice Smith", "Alice Smyth"))
    with pytest.raises(PilotDataError):
        capture(pilot, make_handler())
    (pilot / "seed_freeze.json").unlink()
    with pytest.raises(PilotDataError):
        capture(pilot, make_handler())


def test_authentication_or_rate_limit_response_stops_the_capture_immediately(tmp_path):
    for status in (401, 403, 429):
        pilot = write_pilot(tmp_path / f"p{status}", [seed("P1", "Alice Smith"), seed("P2", "Bob Jones")])
        calls = []
        r = capture(pilot, make_handler(authors={"Alice Smith": status, "Bob Jones": [one()]}, calls=calls))
        assert r.provider_stop_status == status and r.completed_cases == [] and r.requests_made == 1 and len(calls) == 1      # no second request
        index = [json.loads(line) for line in (pilot / "captures" / "capture_index.jsonl").read_text().splitlines()]
        assert len(index) == 1 and index[0]["status"] == status and sha256_file(pilot / "captures" / index[0]["body_file"]) == index[0]["sha256"]
        with pytest.raises(PilotDataError):
            capture(pilot, make_handler(), resume=True)
