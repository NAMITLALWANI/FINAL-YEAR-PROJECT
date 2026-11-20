"""T008: tests of the blinded dossier packet builder and leak scanner (Decision B). Synthetic fixtures, plus an in-memory check against the shape of the real
smoke payloads. Nothing is written to a reviewer location, no packet is saved, and no ORCID value is printed."""
import copy
import csv
import json
import re
from pathlib import Path

import pytest

from hammer_pilot import dossier as d
from hammer_pilot.capture import classify_author_response
from hammer_pilot.dossier import DossierError, LeakFound
from hammer_pilot.replay import load_index

ROOT = Path(__file__).resolve().parents[2] / "research_data" / "lagos_and_v2"
SMOKE, GOLD = ROOT / "smoke_v1", ROOT / "seed_v1" / "gold_identity_register.csv"
ORCID = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]")
FAKE_ORCID = "0000-0002-1825-0097"


def paper(i, **extra):
    return {"title": f"Paper {i}", "doi": f"10.9999/p{i}", "year": 2010 + i, "venue": "Journal", "author_names": ["A. Name", "B. Other"], "affiliation": "Example University",
            "coauthor_names": ["B. Other"], "orcid": FAKE_ORCID, "pid": "2000000001", "block_fullname": "name, a", "train1_test0_val2": "0", "source_row": 99, **extra}


def candidate(i, **extra):
    return {"id": f"https://openalex.org/A50000000{i:02d}", "orcid": f"https://orcid.org/{FAKE_ORCID}", "observed_orcids": [FAKE_ORCID], "display_name": f"Alex Name {i}",
            "raw_author_names": ["alex name"], "full_name": "alex name", "relevance_score": 100.0 - i, "works_count": 10 + i, "cited_by_count": 5,
            "ids": {"openalex": "https://openalex.org/A1", "orcid": f"https://orcid.org/{FAKE_ORCID}"}, "block_key": "name, a",
            "works_api_url": "https://api.openalex.org/works?filter=author.id:A1", "display_name_alternatives": ["A. Name", "Alex N."],
            "affiliations": [{"institution": {"id": "https://openalex.org/I1", "ror": "https://ror.org/x", "display_name": "Example University", "country_code": "US"}, "years": [2012, 2013]}],
            "last_known_institutions": [{"id": "https://openalex.org/I1", "display_name": "Example University"}],
            "topics": [{"id": "https://openalex.org/T1", "display_name": "Genetics", "count": 4, "field": {"id": "f", "display_name": "Biology"}}],
            "counts_by_year": [{"year": 2012, "works_count": 2, "oa_works_count": 1, "cited_by_count": 0}], "unknown_future_field": "anything", **extra}


# ---------------------------------------------------------------- Stage A
def test_stage_a_includes_the_designated_paper_caps_at_k_and_is_deterministic():
    papers = [paper(i) for i in range(30)]
    a = d.build_stage_a_packet("c1", "A. Name", papers, seed=7, k=10, designated_doi="10.9999/p17")
    b = d.build_stage_a_packet("c1", "A. Name", list(reversed(papers)), seed=7, k=10, designated_doi="10.9999/P17")
    assert a == b and a["paper_count_shown"] == 10 == len(a["papers"]) and "10.9999/p17" in {p["doi"] for p in a["papers"]}
    assert d.build_stage_a_packet("c1", "A. Name", papers, seed=8, k=10, designated_doi="10.9999/p17") != a
    few = d.build_stage_a_packet("c1", "A. Name", papers[:3], seed=7, k=10, designated_doi="10.9999/p1")
    assert few["paper_count_shown"] == 3


def test_stage_a_copies_only_allow_listed_fields_and_never_the_benchmark_identity():
    p = d.build_stage_a_packet("c1", "A. Name", [paper(i) for i in range(5)], seed=1, k=5, designated_doi="10.9999/p2")
    assert set(p) == {"packet_type", "packet_id", "query_name", "paper_count_shown", "papers"}
    assert all(set(x) == set(d.STAGE_A_PAPER_FIELDS) for x in p["papers"])
    text = json.dumps(p)
    assert FAKE_ORCID not in text and "2000000001" not in text and "name, a" not in text and "train1" not in text
    assert d.leak_scan(p)["released"]


def test_stage_a_input_validation():
    with pytest.raises(DossierError):
        d.build_stage_a_packet("c", "n", [paper(1)], seed=1, k=0, designated_doi="10.9999/p1")
    with pytest.raises(DossierError, match="designated"):
        d.build_stage_a_packet("c", "n", [paper(1)], seed=1, k=3, designated_doi="10.9999/zzz")
    with pytest.raises(DossierError, match="designated"):
        d.build_stage_a_packet("c", "n", [paper(1), paper(1)], seed=1, k=3, designated_doi="10.9999/p1")
    with pytest.raises(DossierError):
        d.build_stage_a_packet("c", "n", [paper(1)], seed=1, k=True, designated_doi="10.9999/p1")


# ---------------------------------------------------------------- Stage B: allow-list, shuffle, opaque ids, crosswalk
def test_candidate_allow_list_drops_every_identifier_orcid_rank_and_unknown_field():
    out = d.allowlisted_candidate(candidate(1))
    assert set(out) == {"display_name", "name_variants", "affiliations", "last_known_institutions", "topics", "works_count", "works_per_year"}
    text = json.dumps(out).lower()
    for forbidden in (FAKE_ORCID, "orcid", "openalex", "relevance", "block_key", "works_api_url", "unknown_future_field", "raw_author_names", "ror.org", "a5000000"):
        assert forbidden not in text, forbidden
    assert out["affiliations"] == [{"institution": "Example University", "country": "US", "years": [2012, 2013]}] and out["works_count"] == 11
    assert d.leak_scan({"packet_id": "x", "c": out})["released"]


def test_stage_b_order_is_independent_of_provider_order_and_rank_and_depends_on_seed():
    cands = [candidate(i) for i in range(1, 8)]
    a, cw_a = d.build_stage_b_packet("c1", cands, seed=3, works_cap=5)
    b, cw_b = d.build_stage_b_packet("c1", list(reversed(cands)), seed=3, works_cap=5)
    assert [e["candidate"] for e in a["candidates"]] == [e["candidate"] for e in b["candidates"]] and cw_a == cw_b
    reranked = [candidate(i, relevance_score=float(i)) for i in range(1, 8)]
    c, _ = d.build_stage_b_packet("c1", reranked, seed=3, works_cap=5)
    assert [e["candidate"] for e in c["candidates"]] == [e["candidate"] for e in a["candidates"]]
    other, _ = d.build_stage_b_packet("c1", cands, seed=4, works_cap=5)
    assert [e["candidate"] for e in other["candidates"]] != [e["candidate"] for e in a["candidates"]]
    assert [e["position"] for e in a["candidates"]] == list(range(1, 8))


def test_opaque_ids_and_crosswalk_map_back_without_appearing_in_the_packet():
    cands = [candidate(i) for i in range(1, 5)]
    pkt, cw = d.build_stage_b_packet("c1", cands, seed=3, works_cap=0)
    assert set(cw) == {e["candidate"] for e in pkt["candidates"]} and sorted(cw.values()) == sorted(c["id"].rsplit("/", 1)[-1] for c in cands)
    assert not any(v in json.dumps(pkt) for v in cw.values())
    with pytest.raises(DossierError, match="unique"):
        d.build_stage_b_packet("c1", [candidate(1), candidate(1)], seed=3, works_cap=1)
    with pytest.raises(DossierError):
        d.build_stage_b_packet("c1", [candidate(1)], seed=3, works_cap=-1)


def test_works_are_capped_allow_listed_and_ordered_independent_of_provider_order():
    works = [{"title": f"W{i}", "doi": f"10.9999/w{i}", "publication_year": 2000 + i, "primary_location": {"source": {"display_name": "J"}},
              "authorships": [{"author": {"display_name": "A. Name", "orcid": f"https://orcid.org/{FAKE_ORCID}", "id": "https://openalex.org/A9"}}], "id": "W1"} for i in range(12)]
    cands = [candidate(1)]
    pkt, _ = d.build_stage_b_packet("c1", cands, seed=1, works_cap=5, works_by_candidate={"A5000000001": works})
    shown = pkt["candidates"][0]["works_shown"]
    assert len(shown) == 5 and [w["year"] for w in shown] == sorted((w["year"] for w in shown), reverse=True)
    assert all(set(w) == set(d.STAGE_B_WORK_FIELDS) and w["author_names"] == ["A. Name"] for w in shown)
    again, _ = d.build_stage_b_packet("c1", cands, seed=1, works_cap=5, works_by_candidate={"A5000000001": list(reversed(works))})
    assert again == pkt and d.leak_scan(pkt)["released"]


# ---------------------------------------------------------------- leak scan: positive and negative controls, release gate
CLEAN = {"packet_id": "B-x", "candidates": [{"candidate": "K-1", "display_name": "Alex Name", "affiliations": [], "works_shown": []}]}


@pytest.mark.parametrize("mutate,kind", [
    (lambda p: p["candidates"][0].update(note=f"see {FAKE_ORCID}"), "orcid_pattern"),
    (lambda p: p["candidates"][0].update(note="https://orcid.org/abc"), "orcid_url"),
    (lambda p: p["candidates"][0].update(note="https://openalex.org/A1"), "openalex_url"),
    (lambda p: p["candidates"][0].update(note="A5057791417"), "openalex_id"),
    (lambda p: p["candidates"][0].update(orcid="x"), "forbidden_key"),
    (lambda p: p["candidates"][0].update(relevance_score=1.0), "forbidden_key"),
    (lambda p: p["candidates"][0].update(works_api_url="u"), "forbidden_key"),
    (lambda p: p["candidates"][0].update(hammer_rank=1), "forbidden_key"),
    (lambda p: p["candidates"][0].update(selected=True), "forbidden_key"),
    (lambda p: p["candidates"][0].update(policy="v2"), "forbidden_key"),
])
def test_leak_scan_positive_controls(mutate, kind):
    pkt = copy.deepcopy(CLEAN)
    mutate(pkt)
    rep = d.leak_scan(pkt)
    assert not rep["released"] and kind in {f["type"] for f in rep["findings"]}
    with pytest.raises(LeakFound):
        d.release(pkt)


def test_leak_scan_negative_control_gold_values_and_report_contents():
    assert d.leak_scan(CLEAN)["released"] and d.leak_scan(CLEAN)["scanner"] == d.SCANNER_VERSION
    gold = "0000-0001-2345-6789"
    pkt = copy.deepcopy(CLEAN)
    pkt["candidates"][0]["display_name"] = f"Alex {gold}"
    types = {f["type"] for f in d.leak_scan(pkt, gold_values=[gold])["findings"]}
    assert {"gold_value", "orcid_pattern"} <= types
    rep = d.leak_scan(CLEAN)
    assert rep["packet_sha256"] == d.sha256_text(d.canonical(CLEAN)) and rep["packet_id"] == "B-x"


def test_release_gate_and_hand_edit_detection():
    pkt, rep = d.release(copy.deepcopy(CLEAN))
    assert d.verify_packet(pkt, rep)
    edited = copy.deepcopy(pkt)
    edited["candidates"][0]["display_name"] = "Someone Else"
    assert not d.verify_packet(edited, rep) and not d.verify_packet(pkt, {**rep, "released": False})


def test_an_adversarial_display_name_is_caught_by_the_scan_even_though_the_field_is_allow_listed():
    bad = candidate(1, display_name=f"Alex {FAKE_ORCID}")
    pkt, _ = d.build_stage_b_packet("c1", [bad], seed=1, works_cap=0)
    with pytest.raises(LeakFound):
        d.release(pkt)


def test_a_deny_list_would_leak_but_the_allow_list_does_not():
    raw = candidate(1)
    naive = {k: v for k, v in raw.items() if k not in ("orcid", "ids")}                       # a plausible deny-list: drops the obvious fields
    assert not d.leak_scan({"packet_id": "n", **naive})["released"]                            # observed_orcids and urls still leak
    assert d.leak_scan({"packet_id": "a", **d.allowlisted_candidate(raw)})["released"]


# ---------------------------------------------------------------- queue and release layout
def test_automatic_and_audited_cases_have_the_same_packet_form_and_a_flag_independent_queue():
    pa, _ = d.build_stage_b_packet("auto-case", [candidate(i) for i in range(1, 4)], seed=2, works_cap=2)
    pb, _ = d.build_stage_b_packet("audit-case", [candidate(i) for i in range(1, 4)], seed=2, works_cap=2)
    assert set(pa) == set(pb) and set(pa["candidates"][0]) == set(pb["candidates"][0])
    sa = d.build_stage_a_packet("auto-case", "A. Name", [paper(i) for i in range(4)], seed=2, k=3, designated_doi="10.9999/p1")
    assert set(sa) == set(d.build_stage_a_packet("audit-case", "A. Name", [paper(i) for i in range(4)], seed=2, k=3, designated_doi="10.9999/p1"))
    packets = [pa, pb, sa]
    q1 = d.build_queue(packets, seed=2)
    assert q1 == d.build_queue(list(reversed(packets)), seed=2) and sorted(q1) == sorted(p["packet_id"] for p in packets)
    assert d.build_queue(packets, seed=3) != q1


def test_release_layout_separates_the_crosswalk_and_refuses_unsafe_use(tmp_path):
    pkt, cw = d.build_stage_b_packet("c1", [candidate(i) for i in range(1, 4)], seed=2, works_cap=1)
    released = [d.release(pkt)]
    reviewer, protected = tmp_path / "reviewer", tmp_path / "protected"
    hashes = d.write_release(reviewer, protected, released, cw, {"c1": "audit"})
    files = {p.name for p in reviewer.iterdir()}
    assert files == {f"{pkt['packet_id']}.json", f"{pkt['packet_id']}.scan.json"} and hashes == {pkt["packet_id"]: released[0][1]["packet_sha256"]}
    assert {p.name for p in protected.iterdir()} == {"crosswalk.json", "case_flags.json"}
    assert not any(ORCID.search(p.read_text()) for p in reviewer.iterdir()) and not any("A50000" in p.read_text() for p in reviewer.iterdir())
    with pytest.raises(DossierError, match="nested"):
        d.write_release(tmp_path / "r2", tmp_path / "r2" / "inner", released, cw, {})
    with pytest.raises(FileExistsError):
        d.write_release(reviewer, tmp_path / "p3", released, cw, {})
    tampered = copy.deepcopy(pkt)
    tampered["candidates"][0]["display_name"] = "Changed"
    with pytest.raises(DossierError, match="unmodified"):
        d.write_release(tmp_path / "r4", tmp_path / "p4", [(tampered, released[0][1])], cw, {})


# ---------------------------------------------------------------- real payload shape (in memory only)
@pytest.mark.skipif(not (SMOKE / "captures" / "capture_index.jsonl").is_file() or not GOLD.is_file(), reason="smoke artifacts not present")
def test_allow_list_removes_every_gold_orcid_from_real_smoke_payloads_in_memory():
    cap = SMOKE / "captures"
    index = {e["seq"]: e for e in load_index(cap)}
    gold = {r["case_id"]: r["gold_orcid"] for r in csv.DictReader(open(GOLD, encoding="utf-8"))}
    raw_hits = packet_hits = n_candidates = 0
    for case in gold:
        summary = json.loads((cap / "cases" / f"{case}.json").read_text(encoding="utf-8"))
        parts = [summary["R2_primary"]] + ([summary["R2_fallback"]] if summary["R2_fallback"] else [])
        items, seen = [], set()
        for part in parts:
            e = index[part["seq"]]
            body = (cap / e["body_file"]).read_bytes() if e.get("body_file") else None
            for it in classify_author_response(e.get("status"), body, e.get("error"))[2]:
                if it.get("id") and it["id"] not in seen:
                    seen.add(it["id"])
                    items.append(it)
        if not items:
            continue
        raw_hits += sum(json.dumps(it).count(gold[case]) for it in items)
        pkt, cw = d.build_stage_b_packet(case, items, seed=1, works_cap=0)
        report = d.leak_scan(pkt, gold_values=list(gold.values()))
        packet_hits += len(report["findings"])
        n_candidates += pkt["candidate_count"]
        assert report["released"], (case, report["findings"][:3])
    pool_total = sum(int(r["pool_size"]) for r in csv.DictReader(open(SMOKE / "replay" / "retrieval.csv", encoding="utf-8")) if r["arm"] == "R2")
    assert raw_hits > 0 and packet_hits == 0 and n_candidates == pool_total                           # raw payloads leak the gold ORCID; the packets never do


def test_the_module_has_no_network_dependency_and_no_orcid_field_access():
    src = Path(d.__file__).read_text(encoding="utf-8")
    assert not re.search(r"^\s*(import|from)\s+(httpx|requests|urllib|socket|aiohttp)", src, re.M)
    assert not re.search(r"""\.get\(["'](orcid|observed_orcids)["']\)|\[["']orcid["']\]""", src)
