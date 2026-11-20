"""T016: tests of the C7 report assembly. Synthetic cases plus a read-only regression on the smoke capture (skipped if absent)."""
import csv
import json
from collections import Counter
from pathlib import Path

import pytest

from hammer_pilot import metrics_c7 as m
from hammer_pilot import report_assembly as ra

ROOT = Path(__file__).resolve().parents[2] / "research_data" / "lagos_and_v2"
SMOKE, GOLD = ROOT / "smoke_v1", ROOT / "seed_v1" / "gold_identity_register.csv"


def world():
    seeds = [{"case_id": f"C{i}", "source_block_id": f"B{i}", "sampling_stratum": "S" if i < 4 else "M"} for i in range(6)]
    manifest = {"manifest_sha256": "x", "frame_post_exclusion": {"S": 40, "M": 60, "L": 0, "XL": 0},
                "cases": [{"case_id": f"C{i}", "stratum": "S" if i < 4 else "M", "case_eligible_groups": 2, "is_primary": True} for i in range(6)],
                "secondary_cases": [{"case_id": "C9", "stratum": "S", "primary_case_id": "C0", "is_primary": False}]}
    outcomes = {"C0": "auto", "C1": "manual", "C2": "unresolved", "C3": "empty_pool", "C4": "auto", "C5": "provider_failed", "C9": "manual"}
    preds, ret = [], []
    for c, o in outcomes.items():
        pool = [] if o in ("empty_pool", "provider_failed") else [f"A{c}1", f"A{c}2"]
        sel = pool[0] if o == "auto" else ""
        preds.append({"case_id": c, "condition": "C1", "policy": "selective_policy_v2", "outcome": o, "selected_author_id": sel})
        preds.append({"case_id": c, "condition": "C0", "policy": "selective_policy_v2", "outcome": "manual", "selected_author_id": ""})
        ret.append({"case_id": c, "arm": "R2", "ordered_candidate_ids": json.dumps(pool)})
    mapped = {"C0": {"AC01"}, "C1": {"AC12"}, "C4": {"AC42"}}
    return seeds, manifest, preds, ret, mapped


def test_secondary_cases_are_marked_and_missing_primary_refused():
    seeds, manifest, preds, ret, mapped = world()
    seeds.append({"case_id": "C9", "source_block_id": "B0", "sampling_stratum": "S"})
    cases = ra.build_cases(seeds, manifest, preds, ret, mapped)
    assert Counter(c.is_primary for c in cases) == {True: 6, False: 1}
    with pytest.raises(ra.AssemblyError):
        ra.build_cases(seeds, manifest, [p for p in preds if p["case_id"] != "C2"], ret, mapped)


def test_unknown_prediction_cases_refused():
    seeds, manifest, preds, ret, mapped = world()
    preds.append({"case_id": "ZZ", "condition": "C1", "policy": "selective_policy_v2", "outcome": "manual", "selected_author_id": ""})
    ret.append({"case_id": "ZZ", "arm": "R2", "ordered_candidate_ids": '["x"]'})
    with pytest.raises(ra.AssemblyError):
        ra.build_cases(seeds, manifest, preds, ret, mapped)


def test_report_without_verification_is_pending_and_benchmark_derived():
    seeds, manifest, preds, ret, mapped = world()
    seeds.append({"case_id": "C9", "source_block_id": "B0", "sampling_stratum": "S"})
    cases = ra.build_cases(seeds, manifest, preds, ret, mapped)
    rep = ra.assemble_report(cases, manifest, m.InferenceSettings(bootstrap_resamples=20, bootstrap_min_stratum_n=2), 5, {"freeze_id": "F"})
    assert rep["verification_status"] == {"state": "pending", "n_primary": 6, "n_automatic": 2, "n_automatic_verified": 0, "n_audit_sample_verified": 0}
    acc = rep["case_accounting"]
    assert acc["n_primary"] == 6 and acc["reporting_class_counts"]["benchmark_derived"] == 6 and acc["reporting_class_counts"]["verified"] == 0
    assert {k: v for k, v in acc["outcome_counts"].items() if v} == {"auto": 2, "manual": 1, "unresolved": 1, "empty_pool": 1, "provider_failed": 1}
    assert rep["provenance"]["freeze_id"] == "F"


def test_verified_merge_complete_incomplete_and_bad_fields():
    seeds, manifest, preds, ret, mapped = world()
    ver = {"C0": {"label_state": "resolved", "selected_judgment": "same", "group_purity": "pure", "audit_subset": "automatic"}}
    cases = ra.build_cases(seeds, manifest, preds[:-2] if False else [p for p in preds if p["case_id"] != "C9"], [r for r in ret if r["case_id"] != "C9"], mapped, ver)
    assert ra.verification_status(cases)["state"] == "incomplete"
    ver["C4"] = {"label_state": "resolved", "selected_judgment": "different", "group_purity": "pure", "audit_subset": "automatic"}
    cases = ra.build_cases(seeds, manifest, [p for p in preds if p["case_id"] != "C9"], [r for r in ret if r["case_id"] != "C9"], mapped, ver)
    assert ra.verification_status(cases)["state"] == "complete"
    rep = ra.assemble_report(cases, manifest, m.InferenceSettings(bootstrap_resamples=20, bootstrap_min_stratum_n=2), 5, {})
    assert rep["selective_verified"]["scoring"]
    with pytest.raises(ra.AssemblyError):
        ra.build_cases(seeds, manifest, [p for p in preds if p["case_id"] != "C9"], [r for r in ret if r["case_id"] != "C9"], mapped, {"C0": {"gold_orcid": "x"}})


def test_labels_for_secondary_case_refused():
    seeds, manifest, preds, ret, mapped = world()
    seeds.append({"case_id": "C9", "source_block_id": "B0", "sampling_stratum": "S"})
    with pytest.raises(ra.AssemblyError):
        ra.build_cases(seeds, manifest, preds, ret, mapped, {"C9": {"label_state": "resolved", "group_purity": "pure"}})


def test_stratum_mismatch_between_seeds_and_manifest_refused():
    seeds, manifest, preds, ret, mapped = world()
    seeds[0]["sampling_stratum"] = "L"
    with pytest.raises(ra.AssemblyError):
        ra.build_cases(seeds, manifest, preds, ret, mapped)


@pytest.mark.skipif(not (SMOKE / "replay" / "predictions.csv").is_file() or not GOLD.is_file(), reason="smoke artifacts not present")
def test_benchmark_mapping_reproduces_the_smoke_diagnostics():
    gold = {r["case_id"]: r["gold_orcid"] for r in csv.DictReader(open(GOLD, encoding="utf-8"))}
    mapped = ra.benchmark_mapping(SMOKE / "captures", gold)
    assert len(mapped) == 50 and sum(1 for v in mapped.values() if v) == 38      # T003: expected ORCID found in the R2 pool for 38 of 50
    text = json.dumps({k: sorted(v) for k, v in mapped.items()})
    assert not any(o in text for o in gold.values())
