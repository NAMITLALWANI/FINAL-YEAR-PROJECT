"""T017: tests of the review driver (works capture, release). Synthetic data and mock transports; a read-only check on the smoke capture (skipped if absent)."""
import asyncio
import json
import re
from pathlib import Path

import httpx
import pytest

from hammer_pilot import dossier
from hammer_pilot import review_driver as rd
from hammer_pilot.capture import BudgetExhausted, ProviderStop
from hammer_pilot.guarded_transport import GuardStop, GuardedTransport

ROOT = Path(__file__).resolve().parents[2] / "research_data" / "lagos_and_v2" / "smoke_v1"
ORCID = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]")
GOLD = "0000-0001-2345-6789"


def preds(rows):
    return [{"case_id": c, "condition": "C1", "policy": "selective_policy_v2", "outcome": o} for c, o in rows.items()]


def test_plan_reviewed_automatic_plus_audit_with_flags():
    p = preds({"a": "auto", "b": "manual", "c": "auto", "d": "unresolved"})
    reviewed, flags = rd.plan_reviewed(["a", "b", "c", "d"], p, ["d", "b"])
    assert reviewed == ["a", "b", "c", "d"] and flags == {"a": "automatic", "c": "automatic", "b": "audit_sample", "d": "audit_sample"}


def test_plan_refuses_audit_of_automatic_non_primary_and_missing_predictions():
    p = preds({"a": "auto", "b": "manual"})
    with pytest.raises(rd.DriverError):
        rd.plan_reviewed(["a", "b"], p, ["a"])
    with pytest.raises(rd.DriverError):
        rd.plan_reviewed(["a", "b"], p, ["zz"])
    with pytest.raises(rd.DriverError):
        rd.plan_reviewed(["a", "b", "c"], p, [])


def test_works_params_validation():
    assert rd.works_params("A123", 25)["per-page"] == 25
    for bad in ("", "123", "Axyz", "W1"):
        with pytest.raises(rd.DriverError):
            rd.works_params(bad, 25)
    with pytest.raises(rd.DriverError):
        rd.works_params("A1", 0)


def works_handler(req):
    aid = req.url.params["filter"].split(":")[1]
    if aid == "A3":
        return httpx.Response(500, json={"error": "boom"})
    if aid == "A4":
        return httpx.Response(200, content=b"not json")
    return httpx.Response(200, json={"results": [{"id": f"https://openalex.org/W{aid}", "title": f"Work of {aid}", "doi": "https://doi.org/10.1/x", "publication_year": 2020,
                                                  "authorships": [{"author": {"display_name": "X Y", "orcid": f"https://orcid.org/{GOLD}"}}],
                                                  "primary_location": {"source": {"display_name": "J"}}}], "meta": {"cost_usd": 0.001}})


def test_capture_works_saves_hashes_and_marks_failures(tmp_path):
    out = asyncio.run(rd.capture_works(["A1", "A2", "A3", "A4", "A1"], tmp_path, inner_transport=httpx.MockTransport(works_handler), budget=20, cap=5, mailto="lab@x.org", api_key="SECRET"))
    assert {k: v["status"] for k, v in out.items()} == {"A1": "ok", "A2": "ok", "A3": "failed", "A4": "failed"}
    index = (tmp_path / "capture_index.jsonl").read_text()
    assert "SECRET" not in index and "lab@x.org" not in index and len(index.splitlines()) == 4
    assert all(v["sha256"] and (tmp_path / v["body_file"]).is_file() for v in out.values())
    loaded = rd.load_works(tmp_path, ["A1", "A2", "A3", "A4"], 5)
    assert set(loaded) == {"A1", "A2"}


def test_capture_works_budget_resume_and_provider_stop(tmp_path):
    t = httpx.MockTransport(works_handler)
    with pytest.raises(BudgetExhausted):
        asyncio.run(rd.capture_works(["A1", "A2", "A5"], tmp_path / "b", inner_transport=t, budget=2, cap=5))
    asyncio.run(rd.capture_works(["A1", "A2", "A5"], tmp_path / "b", inner_transport=t, budget=1, cap=5))     # resumes: two served from disk, one new request
    stop = httpx.MockTransport(lambda r: httpx.Response(429, json={}))
    with pytest.raises(ProviderStop):
        asyncio.run(rd.capture_works(["A1", "A2"], tmp_path / "c", inner_transport=stop, budget=5, cap=5))
    assert len((tmp_path / "c" / "capture_index.jsonl").read_text().splitlines()) == 1     # saved before stopping


def test_capture_works_guard_stop_propagates(tmp_path):
    g = GuardedTransport(httpx.MockTransport(lambda r: httpx.Response(503, json={})), cost_ceiling_usd=None, max_consecutive_failures=2)
    with pytest.raises(GuardStop):
        asyncio.run(rd.capture_works(["A1", "A2", "A5"], tmp_path, inner_transport=g, budget=9, cap=5))


def inputs(case, n_pool=2, leak=False):
    items = [{"id": f"https://openalex.org/A{100 + i}", "orcid": f"https://orcid.org/{GOLD}", "display_name": f"X Y {i}", "relevance_score": 9 - i, "works_count": 3,
              "affiliations": [], "topics": []} for i in range(n_pool)]
    papers = [{"title": f"T{i}", "doi": f"10.9/{case}-{i}", "year": 2010 + i, "venue": "J", "author_names": ["X Y"], "affiliation": "U", "coauthor_names": ["Z"]} for i in range(6)]
    if leak:
        papers[1]["title"] = f"see {GOLD}"
    return {"query_name": "X Y", "papers": papers, "designated_doi": f"10.9/{case}-0", "pool_items": items,
            "works_by_candidate": {"A100": [{"title": "W", "publication_year": 2021, "authorships": [{"author": {"display_name": "X Y"}}]}]}}


def test_release_writes_separate_directories_and_no_leak(tmp_path):
    ci = {"c1": inputs("c1"), "c2": inputs("c2", n_pool=0)}
    flags = {"c1": "automatic", "c2": "audit_sample"}
    res = rd.build_release(ci, flags, seed=7, k=4, works_cap=3, gold_values=[GOLD], reviewer_dir=tmp_path / "rev", protected_dir=tmp_path / "prot")
    assert res["cases"] == 2 and res["cases_with_stage_b"] == 1 and res["packets"] == 3 and res["queue_length"] == 3
    text = "".join(p.read_text() for p in (tmp_path / "rev").iterdir())
    assert not ORCID.search(text) and "openalex.org" not in text.lower() and "automatic" not in text and "audit_sample" not in text
    prot = {p.name for p in (tmp_path / "prot").iterdir()}
    assert prot == {"crosswalk.json", "case_flags.json"} and json.loads((tmp_path / "prot" / "case_flags.json").read_text()) == flags


def test_release_aborts_on_a_leak_and_writes_nothing(tmp_path):
    with pytest.raises(dossier.LeakFound):
        rd.build_release({"c1": inputs("c1", leak=True)}, {"c1": "automatic"}, seed=7, k=6, works_cap=3, gold_values=[GOLD], reviewer_dir=tmp_path / "r", protected_dir=tmp_path / "p")
    assert not (tmp_path / "r").exists()


def test_release_requires_matching_cases_and_flags(tmp_path):
    with pytest.raises(rd.DriverError):
        rd.build_release({"c1": inputs("c1")}, {"c2": "automatic"}, seed=7, k=4, works_cap=3, gold_values=[], reviewer_dir=tmp_path / "r", protected_dir=tmp_path / "p")


@pytest.mark.skipif(not (ROOT / "captures" / "capture_index.jsonl").is_file(), reason="smoke capture not present")
def test_pool_items_match_the_smoke_pools_in_provider_order():
    for case in ("LG001", "LG002", "LG003"):
        summary = json.loads((ROOT / "captures" / "cases" / f"{case}.json").read_text())
        ids = [str(i["id"]).rsplit("/", 1)[-1] for i in rd.pool_items(ROOT / "captures", case)]
        assert ids == summary["r2_pool_candidate_ids"][: len(ids)] and len(ids) == len(summary["r2_pool_candidate_ids"])


def test_plan_uses_only_the_primary_condition_and_policy():
    p = preds({"a": "auto", "b": "manual"}) + [
        {"case_id": "b", "condition": "C0", "policy": "selective_policy_v2", "outcome": "auto"},
        {"case_id": "a", "condition": "C1", "policy": "forced_top1", "outcome": "manual"},
        {"case_id": "b", "condition": "C1", "policy": "forced_top1", "outcome": "auto"}]
    reviewed, flags = rd.plan_reviewed(["a", "b"], p, [])
    assert reviewed == ["a"] and flags == {"a": "automatic"}


def test_failed_works_response_is_not_used_even_if_its_body_parses(tmp_path):
    def h(req):
        aid = req.url.params["filter"].split(":")[1]
        body = {"results": [{"id": "W1", "title": "t"}]}
        return httpx.Response(500 if aid == "A6" else 200, json=body)
    asyncio.run(rd.capture_works(["A6", "A7"], tmp_path, inner_transport=httpx.MockTransport(h), budget=9, cap=5))
    assert set(rd.load_works(tmp_path, ["A6", "A7"], 5)) == {"A7"}


def make_capture(tmp_path, primary, fallback):
    """A minimal capture directory with one case: R2 primary (and optionally fallback) responses."""
    cap = tmp_path / "cap"
    (cap / "bodies").mkdir(parents=True)
    (cap / "cases").mkdir()
    entries, summary = [], {}
    for seq, (name, items) in enumerate((("R2_primary", primary), ("R2_fallback", fallback)), 1):
        if items is None:
            summary[name] = None
            continue
        body = json.dumps({"results": items}).encode()
        (cap / "bodies" / f"{seq}.body").write_bytes(body)
        entries.append({"seq": seq, "key": f"k{seq}", "status": 200, "error": None, "body_file": f"bodies/{seq}.body", "sha256": "x", "label": name})
        summary[name] = {"seq": seq}
    (cap / "capture_index.jsonl").write_text("".join(json.dumps(e) + "\n" for e in entries))
    (cap / "cases" / "c1.json").write_text(json.dumps(summary))
    return cap


def item(n):
    return {"id": f"https://openalex.org/A{n}", "display_name": f"Name {n}"}


def test_pool_items_dedupe_and_cap_across_primary_and_fallback(tmp_path):
    cap = make_capture(tmp_path, [item(1), item(2)], [item(2), item(3)])
    assert [i["id"].rsplit("/", 1)[-1] for i in rd.pool_items(cap, "c1")] == ["A1", "A2", "A3"]
    big = make_capture(tmp_path / "x", [item(n) for n in range(1, 14)], None)
    assert len(rd.pool_items(big, "c1")) == 10
