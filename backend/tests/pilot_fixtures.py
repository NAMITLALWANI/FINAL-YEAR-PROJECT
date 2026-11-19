"""Synthetic fixtures for the pilot toolkit tests. No provider is ever contacted."""
from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path

import httpx

from author_test_helpers import payload, work
from hammer_pilot.capture import run_capture
from hammer_pilot.common import sha256_file

SEED_FIELDS = ["case_id", "query_text", "identity_group_id", "planned_status", "context_c1_json", "context_c1x_json", "context_modified_after_candidates_seen"]
REG_FIELDS = ["case_id", "doi", "purpose", "registered_by", "justification_if_both"]


def seed(case, query, *, c1=None, c1x=None, planned="resolved", group=None):
    return {"case_id": case, "query_text": query, "identity_group_id": group or f"G-{case}", "planned_status": planned,
            "context_c1_json": json.dumps(c1 or {}), "context_c1x_json": json.dumps(c1x or {}), "context_modified_after_candidates_seen": "false"}


def write_csv(path: Path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_pilot(root: Path, seeds, register=(), frozen_at="2020-01-01T00:00:00Z") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    write_csv(root / "seeds.csv", SEED_FIELDS, seeds)
    write_csv(root / "doi_register.csv", REG_FIELDS, list(register))
    (root / "seed_freeze.json").write_text(json.dumps({
        "frozen_at": frozen_at, "dataset_version": "synthetic-v1", "seeds_sha256": sha256_file(root / "seeds.csv"),
        "doi_register_sha256": sha256_file(root / "doi_register.csv")}))
    return root


def make_handler(authors=None, search=None, doi_works=None, author_works=None, calls=None):
    authors, search, doi_works, author_works = authors or {}, search or {}, doi_works or [], author_works or {}

    def reply(value):
        if isinstance(value, Exception):
            raise value
        if isinstance(value, int):
            return httpx.Response(value, json={})
        if isinstance(value, str):
            return httpx.Response(200, text=value)
        return httpx.Response(200, json={"results": value, "meta": {"count": len(value)}})

    def handler(request):
        if calls is not None:
            calls.append(str(request.url.path) + "?" + str(request.url.query, "utf-8") if isinstance(request.url.query, bytes) else str(request.url))
        p, path = request.url.params, request.url.path
        if path == "/authors":
            if p.get("filter"):
                return reply(authors.get(p["filter"].split("display_name.search:", 1)[1], []))
            return reply(search.get(p.get("search"), []))
        f = p.get("filter", "")
        if f.startswith("doi:"):
            if isinstance(doi_works, dict):
                wanted = [d.replace("https://doi.org/", "") for d in f[4:].split("|")]
                return reply([w for d, w in doi_works.items() if d in wanted])
            return reply(doi_works)
        if f.startswith("author.id:"):
            return reply(author_works.get(f.split(":", 1)[1], []))
        return httpx.Response(404, json={})
    return handler


def capture(pilot: Path, handler, *, budget=200, resume=False, mailto="synthetic-pool", api_key="synthetic-key"):
    return asyncio.run(run_capture(pilot, inner_transport=httpx.MockTransport(handler), budget=budget, resume=resume, mailto=mailto, api_key=api_key))


def one(aid="A1", name="Alice Smith", **kw):
    return payload(aid, name, **kw)


REVIEW_FIELDS = ["case_id", "reviewer_id", "status", "confidence", "rationale", "evidence_refs_json", "gold_dois_json", "submitted_at"]
STAGE_A_FIELDS = ["case_id", "final_status", "gold_person_id", "adjudication_status", "adjudicator_id", "rationale"]
STAGE_B_FIELDS = ["case_id", "candidate_author_id", "reviewer_a_judgment", "reviewer_b_judgment", "final_judgment", "adjudication_status", "submitted_at"]


def write_annotation(pilot: Path, cases, *, reviewer_a="rev-A", reviewer_b="rev-B", adjudicator="adj-C", submitted="2025-12-30T10:00:00Z"):
    """cases: [{case, a, b, final, person, gold_dois}] -> review_a.csv, review_b.csv, stage_a.csv, development_exclusions.csv"""
    for tag, rid in (("a", reviewer_a), ("b", reviewer_b)):
        write_csv(pilot / f"review_{tag}.csv", REVIEW_FIELDS, [
            {"case_id": c["case"], "reviewer_id": rid, "status": c[tag], "confidence": "4", "rationale": "independent public evidence",
             "evidence_refs_json": json.dumps([f"https://example.org/staff/{c['case']}"]), "gold_dois_json": json.dumps(c.get("gold_dois", [])),
             "submitted_at": submitted} for c in cases])
    write_csv(pilot / "stage_a.csv", STAGE_A_FIELDS, [
        {"case_id": c["case"], "final_status": c["final"], "gold_person_id": c.get("person", ""),
         "adjudication_status": "agreed" if c["a"] == c["b"] else "adjudicated", "adjudicator_id": "" if c["a"] == c["b"] else adjudicator,
         "rationale": "final"} for c in cases])
    write_csv(pilot / "development_exclusions.csv", ["kind", "value"], [{"kind": "name", "value": "development person"}])


def write_stage_b(pilot: Path, rows, submitted="2099-01-01T00:00:00Z"):
    write_csv(pilot / "stage_b.csv", STAGE_B_FIELDS, [
        {"case_id": c, "candidate_author_id": a, "reviewer_a_judgment": j, "reviewer_b_judgment": j, "final_judgment": j, "adjudication_status": "agreed", "submitted_at": submitted}
        for c, a, j in rows])


def build_synthetic_pilot(root: Path) -> Path:
    """15 fabricated cases (10 resolved + 5 unresolved) with fabricated OpenAlex-like responses. Nobody real."""
    inst = lambda n: n
    specs = [
        # case, query, kind, c1, authors(list of (id,name,institution)), mapping, extra
        ("P01", "Avel Marchetti", "resolved", {"institution_hints": ["Alpha Institute"]}, [("A101", "Avel Marchetti", "Alpha Institute")], {"A101": "same"}),
        ("P02", "Brenna  Okafor", "resolved", {"institution_hints": ["Beta Institute"]}, [("A201", "Brenna Okafor", "Beta Institute"), ("A202", "Brenna Okafor", "Beta Institute")], {"A201": "same", "A202": "same"}),
        ("P03", "Corwin Delacroix", "resolved", {"institution_hints": ["Gamma Institute"]}, [("A301", "Corwin Delacroix", "Gamma Institute"), ("A302", "Zed Different", "Other University")], {"A301": "same", "A302": "not_same"}),
        ("P04", "Dalia Ferenc", "resolved", {"institution_hints": ["Delta Institute"]}, [], {}),
        ("P05", "Evander Holt", "resolved", {"institution_hints": ["Eps Institute"]}, 500, {}),
        ("P06", "Fenwick Gale", "resolved", {"institution_hints": ["Delta Institute"], "coauthors": [{"openalex_id": "A9001"}]}, [("A601", "Fenwick Gale", "Delta Institute")], {"A601": "same"}),
        ("P07", "Galina Ivers", "resolved", {"institution_hints": ["Epsilon Institute"], "publications": ["10.9999/ctx07"]}, [("A701", "Galina Ivers", "Epsilon Institute")], {"A701": "same"}),
        ("P08", "Hollis Quade", "resolved", {"institution_hints": ["Zeta Institute"], "publications": ["10.9999/both08"]}, [("A801", "Hollis Quade", "Zeta Institute")], {"A801": "same"}),
        ("P09", "Ilsa Brandt", "resolved", {"coauthors": ["Some Coauthor"]}, [("A901", "Ilsa Brandt", "Eta Institute")], {"A901": "same"}),
        ("P10", "Joran Whitlock", "resolved", {"institution_hints": ["Theta Institute"]}, [("A1001", "Joran Whitlock", "Theta Institute")], {"A1001": "not_same"}),
        ("P11", "Kestrel Moon", "unresolved", {"institution_hints": ["Iota Institute"]}, [("A1101", "Kestrel Moon", "Iota Institute"), ("A1102", "Kestrel Moon", "Iota Institute")], {"A1101": "not_same", "A1102": "not_same"}),
        ("P12", "Lorcan Pike", "unresolved", {"institution_hints": ["Kappa Institute"]}, [("A1201", "Lorcan Pike", "Kappa Institute")], {"A1201": "not_same"}),
        ("P13", "Marisol Vance", "unresolved", {"institution_hints": ["Lambda Institute"]}, [], {}),
        ("P14", "Nell Archer", "unresolved", {"institution_hints": ["Mu Institute"]}, [("A1401", "Quentin Zacharias", "Unrelated College")], {"A1401": "not_same"}),
        ("P15", "Osric Pell", "unresolved", {"institution_hints": ["Nu Institute"]}, [("A1501", "Osric Pell", "Nu Institute"), ("A1502", "Osric Pell", "Nu Institute")], {"A1501": "not_same", "A1502": "not_same"}),
    ]
    seeds, register, authors, author_works, doi_works = [], [], {}, {}, {}
    review_cases, stage_b = [], []
    for n, (case, query, kind, c1, cands, mapping) in enumerate(specs, 1):
        seeds.append(seed(case, query, c1=c1, planned=kind))
        cleaned = " ".join(query.split())
        if isinstance(cands, int):
            authors[query.strip()] = cands
            authors[cleaned] = cands
        else:
            payloads = [one(a, nm, inst=i) for a, nm, i in cands]
            authors[cleaned] = payloads
            authors[query.strip()] = [] if query.strip() != cleaned else payloads      # R0 raw query misses on the double-space case
        gold = []
        if kind == "resolved":
            gold = ["10.9999/both08"] if case == "P08" else [f"10.9999/gold{n:02d}"]
            for d in gold:
                register.append({"case_id": case, "doi": d, "purpose": "both" if case == "P08" else "gold_evidence", "registered_by": "reviewer_a",
                                 "justification_if_both": "synthetic justification: DOI is public context chosen before review" if case == "P08" else ""})
        if case == "P07":
            register.append({"case_id": case, "doi": "10.9999/ctx07", "purpose": "query_context", "registered_by": "frame_preparer", "justification_if_both": ""})
            doi_works["10.9999/ctx07"] = work("W7", "10.9999/ctx07", ["A701"])
        if case == "P08":
            doi_works["10.9999/both08"] = work("W8", "10.9999/both08", ["A801"])
        if case == "P06":
            author_works["A601"] = 500
        review_cases.append({"case": case, "a": "unresolved" if kind == "unresolved" else "resolved",
                             "b": "uncertain" if case == "P14" else ("unresolved" if kind == "unresolved" else "resolved"),
                             "final": kind, "person": f"person-{n:02d}" if kind == "resolved" else "", "gold_dois": gold})
        stage_b += [(case, a, j) for a, j in mapping.items()]
    pilot = write_pilot(root, seeds, register, frozen_at="2026-01-02T00:00:00Z")
    write_annotation(pilot, review_cases)
    capture(pilot, make_handler(authors=authors, doi_works=doi_works, author_works=author_works))
    write_stage_b(pilot, stage_b)
    return pilot
