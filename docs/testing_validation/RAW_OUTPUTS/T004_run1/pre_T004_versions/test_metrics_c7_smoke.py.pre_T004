"""Cross-checks of the C7 metrics module on the existing 50-case smoke capture (read-only, offline, no provider requests).

The smoke sample is NOT a probability sample (complete blocks, round-robin over size bands). These tests validate the tooling's arithmetic by comparing it
with independently produced artifacts. They are not performance results. Benchmark ORCID values are read into memory only to build the benchmark mapping
and are never written anywhere.
"""
import csv
import json
import re
from collections import Counter
from pathlib import Path

import pytest

from hammer_pilot import metrics_c7 as m
from hammer_pilot.capture import classify_author_response
from hammer_pilot.metrics import selective_metrics
from hammer_pilot.replay import load_index

ROOT = Path(__file__).resolve().parents[2] / "research_data" / "lagos_and_v2"
SMOKE, GOLD = ROOT / "smoke_v1", ROOT / "seed_v1" / "gold_identity_register.csv"
ORCID = re.compile(r"(\d{4}-\d{4}-\d{4}-\d{3}[\dX])")

pytestmark = pytest.mark.skipif(not (SMOKE / "replay" / "predictions.csv").is_file() or not GOLD.is_file(), reason="smoke artifacts not present")


def _csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


@pytest.fixture(scope="module")
def smoke():
    seeds = {r["case_id"]: r for r in _csv(SMOKE / "seeds.csv")}
    gold = {r["case_id"]: r["gold_orcid"] for r in _csv(GOLD)}
    cap = SMOKE / "captures"
    index = {e["seq"]: e for e in load_index(cap)}
    mapped = {}
    for case in seeds:
        summary = json.loads((cap / "cases" / f"{case}.json").read_text(encoding="utf-8"))
        parts = [summary["R2_primary"]] + ([summary["R2_fallback"]] if summary["R2_fallback"] else [])
        ids = set()
        for part in parts:
            e = index[part["seq"]]
            body = (cap / e["body_file"]).read_bytes() if e.get("body_file") else None
            for item in classify_author_response(e.get("status"), body, e.get("error"))[2]:
                found = ORCID.search(item["orcid"]) if isinstance(item.get("orcid"), str) else None
                if found and found.group(1) == gold[case]:
                    ids.add(item["id"].rsplit("/", 1)[-1])
        mapped[case] = ids
    return {"seeds": seeds, "gold": gold, "mapped": mapped, "preds": _csv(SMOKE / "replay" / "predictions.csv"), "ret": _csv(SMOKE / "replay" / "retrieval.csv"),
            "diag": _csv(SMOKE / "diagnostics" / "orcid_diagnostics.csv"), "diag_summary": json.loads((SMOKE / "diagnostics" / "orcid_diagnostics_summary.json").read_text())}


def build(smoke, primary_rule="all"):
    s = smoke["seeds"]
    blocks = {c: (c if primary_rule == "all" else s[c]["source_block_id"]) for c in s}
    cases = m.cases_from_replay(smoke["preds"], smoke["ret"], condition="C1", policy="selective_policy_v2", block_by_case=blocks,
                                stratum_by_case={c: s[c]["sampling_stratum"] for c in s}, mapped_by_case=smoke["mapped"])
    if primary_rule == "first_per_block":
        seen, out = set(), []
        for c in sorted(cases, key=lambda x: x.case_id):
            first = c.block_id not in seen
            seen.add(c.block_id)
            out.append(c if first else m.Case(**{**c.__dict__, "is_primary": False}))
        cases = out
    return cases


def census_frame(cases):
    return dict(Counter(c.stratum for c in cases if c.is_primary))      # stand-in frame (N_h = n_h) so only the arithmetic is exercised


def test_label_free_counts_match_the_replay_predictions_exactly(smoke):
    cases = build(smoke)
    rep = m.evaluate_primary(cases, census_frame(cases))
    expected = Counter(r["outcome"] for r in smoke["preds"] if r["condition"] == "C1" and r["policy"] == "selective_policy_v2")
    got = rep["case_accounting"]["outcome_counts"]
    assert {k: v for k, v in got.items() if v} == dict(expected) == {"auto": 4, "manual": 46}
    assert rep["case_accounting"]["n_primary"] == 50 and sum(got.values()) == 50
    assert rep["case_accounting"]["reporting_class_counts"] == {"verified": 0, "uncertain": 0, "unverifiable": 0, "benchmark_derived": 50}


def test_retrieval_metrics_match_the_independent_orcid_diagnostics(smoke):
    cases = build(smoke)
    rep = m.evaluate_primary(cases, census_frame(cases))["retrieval_benchmark_derived"]
    total = lambda name: sum(v["numerator"] for v in rep[name]["per_stratum"].values())
    den = lambda name: sum(v["denominator"] for v in rep[name]["per_stratum"].values())
    r2 = [r for r in smoke["diag"] if r["arm"] == "R2"]
    found = smoke["diag_summary"]["by_arm_classification"]["R2"]["expected_orcid_found"]
    assert (total("pool_mapping_rate"), den("pool_mapping_rate")) == (found, 50) == (38, 50)
    for k in (1, 5, 10):
        assert total(f"end_to_end_success_at_{k}") == sum(1 for r in r2 if r[f"hit_at_{k}"] == "True")
        assert den(f"end_to_end_success_at_{k}") == 50                                  # all N
        assert total(f"conditional_recall_at_{k}") == total(f"end_to_end_success_at_{k}") and den(f"conditional_recall_at_{k}") == found
    diag_rank = {r["case_id"]: (int(r["first_rank_of_expected"]) if r["first_rank_of_expected"] else None) for r in r2}
    assert {c.case_id: m.first_rank(c) for c in cases} == diag_rank                    # per-case agreement, not only totals


def test_benchmark_selective_numbers_match_the_existing_metrics_module(smoke):
    cases = build(smoke)
    rep = m.evaluate_primary(cases, census_frame(cases))
    rows = [r for r in smoke["preds"] if r["condition"] == "C1" and r["policy"] == "selective_policy_v2"]
    gold = {c: {"status": "resolved", "mapped": smoke["mapped"][c]} for c in smoke["seeds"]}
    old = selective_metrics(rows, gold, "C1", "selective_policy_v2")
    p = rep["selective_benchmark_derived"]["benchmark_automatic_precision"]["per_stratum"]
    assert (sum(v["numerator"] for v in p.values()), sum(v["denominator"] for v in p.values())) == (old["automatic_precision"]["numerator"], old["automatic_precision"]["denominator"])
    cov = rep["label_free"]["rate_auto"]["per_stratum"]
    assert sum(v["numerator"] for v in cov.values()) == old["automatic_coverage"]["numerator"] == 4
    assert sum(v["denominator"] for v in cov.values()) == old["automatic_coverage"]["denominator"] == 50


def test_one_primary_case_per_block_rule_on_the_real_block_structure(smoke):
    cases = build(smoke, "first_per_block")
    rep = m.evaluate_primary(cases, census_frame(cases))
    acc = rep["case_accounting"]
    assert acc["n_primary"] == 23 and acc["n_secondary_excluded"] == 27                # 50 cases in 23 blocks
    assert sum(acc["outcome_counts"].values()) == 23
    with pytest.raises(m.C7Error, match="more than one primary case in a block"):
        m.evaluate_primary(build(smoke, "block"), {"S": 99, "M": 99, "L": 99, "XL": 99})


def test_report_is_deterministic_and_contains_no_benchmark_orcid(smoke):
    cases = build(smoke)
    frame = census_frame(cases)
    a = m.to_json(m.evaluate_primary(cases, frame, seed=1))
    assert a == m.to_json(m.evaluate_primary(cases, frame, seed=1))
    assert not ORCID.search(a)
    assert not any(g in a for g in smoke["gold"].values())
    unverified = json.loads(a)["selective_verified"]["scoring"]
    assert unverified["verification_complete"] is False and unverified["status_counts"]["unverified"] == 4   # no independent labels exist for the smoke cases
