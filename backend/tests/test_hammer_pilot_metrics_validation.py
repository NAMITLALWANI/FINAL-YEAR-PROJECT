import asyncio
import json

import pytest

from hammer_pilot.common import PilotDataError
from hammer_pilot.context_rules import derive_contexts
from hammer_pilot.manifest import build_manifest, manifest_text
from hammer_pilot.metrics import clopper_pearson, retrieval_metrics, selective_metrics, zero_event_upper_bound
from hammer_pilot.pipeline import run_pipeline
from hammer_pilot.reproducibility import verify_reproducibility
from hammer_pilot.validation import validate_pilot
from pilot_fixtures import capture, make_handler, one, seed, write_annotation, write_csv, write_pilot, write_stage_b

def full_pilot(tmp_path, with_capture=True):
    seeds = [seed(f"P{i:02d}", f"Person Number{i}", planned="resolved" if i <= 10 else "unresolved") for i in range(1, 16)]
    reg = [{"case_id": f"P{i:02d}", "doi": f"10.1000/gold{i}", "purpose": "gold_evidence", "registered_by": "reviewer_a", "justification_if_both": ""} for i in range(1, 11)]
    pilot = write_pilot(tmp_path / "p", seeds, reg, frozen_at="2026-01-02T00:00:00Z")
    cases = [{"case": f"P{i:02d}", "a": "resolved" if i <= 10 else "unresolved", "b": "resolved" if i <= 10 else "unresolved",
              "final": "resolved" if i <= 10 else "unresolved", "person": f"person-{i:02d}" if i <= 10 else "",
              "gold_dois": [f"10.1000/gold{i}"] if i <= 10 else []} for i in range(1, 16)]
    write_annotation(pilot, cases)
    if with_capture:
        authors = {f"Person Number{i}": [one(f"A{i}", f"Person Number{i}")] for i in range(1, 16)}
        capture(pilot, make_handler(authors=authors))
        write_stage_b(pilot, [(f"P{i:02d}", f"A{i}", "same" if i <= 10 else "not_same") for i in range(1, 16)])
    return pilot


def test_complete_synthetic_pilot_validates(tmp_path):
    rep = validate_pilot(full_pilot(tmp_path))
    assert rep.ok, rep.errors
    assert rep.info["final_composition"] == {"resolved": 10, "unresolved": 5, "uncertain": 0}


def test_stage_a_ids_are_independent_of_openalex_and_candidate_evidence(tmp_path):
    pilot = full_pilot(tmp_path, with_capture=False)
    (pilot / "stage_a.csv").write_text((pilot / "stage_a.csv").read_text().replace("person-01", "A5031152245"))
    (pilot / "review_a.csv").write_text((pilot / "review_a.csv").read_text().replace("https://example.org/staff/P01", "https://openalex.org/A123456", 1))
    errors = validate_pilot(pilot).errors
    assert any("opaque person ID" in e for e in errors) and any("OpenAlex author profile" in e for e in errors)


def test_validator_reports_composition_duplicates_and_blind_stage_b(tmp_path):
    pilot = full_pilot(tmp_path)
    s = (pilot / "seeds.csv").read_text().replace("G-P02", "G-P01")
    (pilot / "seeds.csv").write_text(s)
    errs = validate_pilot(pilot).errors
    assert any("identity_group_id" in e for e in errs) and any("seed freeze" in e for e in errs)      # edit after freeze is reported, not repaired
    pilot2 = full_pilot(tmp_path / "x")
    b = (pilot2 / "stage_b.csv").read_text().replace("candidate_author_id", "rank,candidate_author_id", 1)
    (pilot2 / "stage_b.csv").write_text(b)
    assert any("blind" in e for e in validate_pilot(pilot2).errors)


def test_validator_detects_incomplete_stage_b_and_missing_capture_hash(tmp_path):
    pilot = full_pilot(tmp_path)
    lines = (pilot / "stage_b.csv").read_text().splitlines()
    (pilot / "stage_b.csv").write_text("\n".join(lines[:5]) + "\n")
    assert any("Stage B incomplete" in e for e in validate_pilot(pilot).errors)
    next((pilot / "captures" / "bodies").iterdir()).unlink()
    assert any("capture" in e for e in validate_pilot(pilot).errors)


def test_doi_leakage_is_detected_without_editing_the_seed(tmp_path):
    seeds = [seed("P1", "Alice Smith", c1={"publications": ["10.1000/shared", "10.1000/ctx"]})]
    reg = [{"case_id": "P1", "doi": "10.1000/shared", "purpose": "gold_evidence", "registered_by": "reviewer_a", "justification_if_both": ""},
           {"case_id": "P1", "doi": "10.1000/ctx", "purpose": "query_context", "registered_by": "frame_preparer", "justification_if_both": ""}]
    pilot = write_pilot(tmp_path / "p", seeds, reg)
    before = (pilot / "seeds.csv").read_bytes()
    from hammer_pilot.context_rules import register_by_case
    ctx = derive_contexts(seeds[0], register_by_case(reg)["P1"])
    assert ctx["C1"]["publications"] == ["10.1000/ctx"] and ctx["removed_from_c1"] == ["10.1000/shared"]
    assert set(ctx["C1x"]["publications"]) == {"10.1000/shared", "10.1000/ctx"}
    rep = validate_pilot(pilot)
    assert any("overlap gold evidence" in w for w in rep.warnings) and rep.info["doi_overlap_cases"] == {"P1": ["10.1000/shared"]}
    assert (pilot / "seeds.csv").read_bytes() == before


def test_both_purpose_requires_justification_and_unregistered_dois_are_errors(tmp_path):
    seeds = [seed("P1", "Alice Smith", c1={"publications": ["10.1000/unreg"]})]
    reg = [{"case_id": "P1", "doi": "10.1000/b", "purpose": "both", "registered_by": "reviewer_a", "justification_if_both": ""}]
    errs = validate_pilot(write_pilot(tmp_path / "p", seeds, reg)).errors
    assert any("needs a justification" in e for e in errs) and any("not in the DOI register" in e for e in errs)


def test_development_leakage_is_reported(tmp_path):
    pilot = full_pilot(tmp_path, with_capture=False)
    write_csv(pilot / "development_exclusions.csv", ["kind", "value"], [{"kind": "name", "value": "person number3"}, {"kind": "doi", "value": "10.1000/gold4"}])
    errs = validate_pilot(pilot).errors
    assert sum("development leakage" in e for e in errs) == 2


def test_inconsistent_prediction_labels_are_reported(tmp_path):
    pilot = full_pilot(tmp_path, with_capture=False)
    write_csv(tmp_path / "pred.csv", ["case_id", "condition", "policy", "outcome"], [{"case_id": "P01", "condition": "C2", "policy": "forced_top1_full", "outcome": "maybe"}])
    assert any("inconsistent label" in e for e in validate_pilot(pilot, tmp_path / "pred.csv").errors)


def test_exact_intervals_and_zero_automatic_assignments():
    lo, hi = clopper_pearson(0, 10)
    assert lo == 0.0 and abs(hi - 0.3085) < 1e-3
    lo, hi = clopper_pearson(5, 10)
    assert abs(lo - 0.1871) < 1e-3 and abs(hi - 0.8129) < 1e-3
    assert clopper_pearson(0, 0) is None
    assert abs(zero_event_upper_bound(59) - 0.0495) < 1e-4
    rows = [{"case_id": "P1", "outcome": "manual", "selected_author_id": ""}]
    m = selective_metrics(rows, {"P1": {"status": "resolved", "mapped": {"A1"}}}, "C0", "selective_policy_v2")
    assert m["automatic_precision"]["value"] is None and m["automatic_precision"]["note"] == "no automatic assignments"
    assert m["automatic_coverage"]["numerator"] == 0 and m["automatic_coverage"]["denominator"] == 1
    assert m["automatic_coverage_zero_by_design"] is True and "BY DESIGN" in m["structural_note"]


def test_zero_error_bound_and_false_acceptance_counted():
    rows = [{"case_id": "P1", "outcome": "auto", "selected_author_id": "A1"}, {"case_id": "P2", "outcome": "auto", "selected_author_id": "A9"}]
    gold = {"P1": {"status": "resolved", "mapped": {"A1"}}, "P2": {"status": "unresolved", "mapped": set()}}
    m = selective_metrics(rows, gold, "C1", "selective_policy_v2")
    assert m["incorrect_automatic"] == 1 and m["false_acceptances_on_unresolved_controls"] == 1 and "zero_error_one_sided_95_upper_bound" not in m
    ok = selective_metrics(rows[:1], {"P1": gold["P1"]}, "C1", "selective_policy_v2")
    assert ok["zero_error_one_sided_95_upper_bound"] == round(zero_event_upper_bound(1), 6)


def test_multiple_stage_b_mappings_for_one_person_count_as_hits():
    case = {"case_id": "P1", "mapped": {"A5", "A6"}, "pools": {"R0": {"status": "ok", "ids": ["A9", "A6", "A5"]}, "R2": {"status": "ok", "ids": ["A5", "A9"]}}}
    m = retrieval_metrics([case])
    assert m["catalog_coverage"]["numerator"] == 1
    assert m["arms"]["R0"]["recall_at_1"]["numerator"] == 0 and m["arms"]["R0"]["recall_at_5"]["numerator"] == 1
    assert m["arms"]["R2"]["recall_at_1"]["numerator"] == 1 and m["arms"]["R2"]["mrr"]["value"] == 1.0 and m["arms"]["R0"]["mrr"]["value"] == 0.5
    assert m["paired_r0_vs_r2_discordant"]["recall_at_1"]["r2_only"] == 1


def test_catalog_gap_stays_in_the_denominator_story():
    case = {"case_id": "P1", "mapped": {"A5"}, "pools": {"R0": {"status": "ok", "ids": ["A9"]}, "R2": {"status": "ok", "ids": ["A9"]}}}
    m = retrieval_metrics([case])
    assert m["catalog_coverage"]["value"] == 0.0 and m["arms"]["R2"]["recall_at_1"]["denominator"] == 0


def test_pipeline_metrics_end_to_end_and_manifest_hashes_real_implementation(tmp_path):
    pilot = full_pilot(tmp_path)
    asyncio.run(run_pipeline(pilot, tmp_path / "out"))
    metrics = json.loads((tmp_path / "out" / "metrics.json").read_text())
    assert metrics["retrieval_RQ2a"]["arms"]["R2"]["recall_at_1"]["numerator"] == 10
    c0 = metrics["selective_RQ2b"]["C0/selective_policy_v2"]
    assert c0["automatic_coverage"]["numerator"] == 0 and c0["automatic_coverage_zero_by_design"] is True
    manifest = json.loads((tmp_path / "out" / "run_manifest.json").read_text())
    hashed = manifest["author_resolution_source_hashes"]
    assert {"author_resolution/policy.py", "author_resolution/evidence.py", "author_resolution/resolver.py", "author_resolution/enrichment.py"} <= set(hashed)
    assert manifest["effective_weights"]["name_similarity"] == 0.35 and manifest["effective_thresholds"]["automatic"] == 0.75
    assert "hammer_pilot/replay.py" in manifest["evaluator_source_hashes"] and manifest["known_deviations"]
    assert "api_key" not in json.dumps(manifest).lower()


def test_manifest_is_reproducible_and_byte_identical_replay(tmp_path):
    pilot = full_pilot(tmp_path)
    m1, m2 = manifest_text(build_manifest(pilot)), manifest_text(build_manifest(pilot))
    assert m1 == m2
    result = asyncio.run(verify_reproducibility(pilot, tmp_path / "work"))
    assert result["identical"] is True and {"predictions.csv", "retrieval.csv", "evidence_snapshot.jsonl", "metrics.json", "run_manifest.json"} <= set(result["files"])
    with pytest.raises(FileExistsError):
        asyncio.run(verify_reproducibility(pilot, tmp_path / "work"))
