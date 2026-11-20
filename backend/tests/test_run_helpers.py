"""T012: tests of the pipeline glue (pilot coverage counts, audit-frame CSV, seeds command). Synthetic only."""
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from hammer_pilot import run_helpers as rh
from hammer_pilot import selector_c1c as sel
from test_hammer_lagos_prep import make_archive

BACKEND = Path(__file__).resolve().parents[1]


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def preds(outcomes):
    rows = []
    for cid, o in outcomes.items():
        for cond, pol in (("C0", "selective_policy_v2"), ("C1", "selective_policy_v2"), ("C1", "forced_top1")):
            rows.append({"case_id": cid, "condition": cond, "policy": pol, "outcome": o if (cond, pol) == ("C1", "selective_policy_v2") else "manual"})
    return rows


def test_pilot_counts_use_only_the_primary_pair_and_the_seeded_strata(tmp_path):
    write_csv(tmp_path / "p.csv", preds({"a": "auto", "b": "manual", "c": "auto", "d": "empty_pool", "e": "provider_failed"}))
    write_csv(tmp_path / "s.csv", [{"case_id": c, "sampling_stratum": h} for c, h in (("a", "S"), ("b", "S"), ("c", "M"), ("d", "M"), ("e", "L"))])
    counts = rh.pilot_coverage_counts(tmp_path / "p.csv", tmp_path / "s.csv", condition="C1", policy="selective_policy_v2")
    assert counts == {"L": {"automatic": 0, "cases": 1}, "M": {"automatic": 1, "cases": 2}, "S": {"automatic": 1, "cases": 2}}
    other = rh.pilot_coverage_counts(tmp_path / "p.csv", tmp_path / "s.csv", condition="C0", policy="selective_policy_v2")
    assert sum(v["automatic"] for v in other.values()) == 0


def test_missing_predictions_and_duplicate_rows_are_refused(tmp_path):
    write_csv(tmp_path / "p.csv", preds({"a": "auto"}))
    write_csv(tmp_path / "s.csv", [{"case_id": "a", "sampling_stratum": "S"}, {"case_id": "z", "sampling_stratum": "S"}])
    with pytest.raises(rh.HelperError, match="no prediction"):
        rh.pilot_coverage_counts(tmp_path / "p.csv", tmp_path / "s.csv", condition="C1", policy="selective_policy_v2")
    dup = preds({"a": "auto"}) + preds({"a": "auto"})
    write_csv(tmp_path / "d.csv", dup)
    with pytest.raises(rh.HelperError, match="more than one"):
        rh.pilot_coverage_counts(tmp_path / "d.csv", tmp_path / "s.csv", condition="C1", policy="selective_policy_v2")


def test_audit_frame_lists_only_primary_cases_with_their_outcome(tmp_path):
    write_csv(tmp_path / "p.csv", preds({"a": "auto", "b": "manual", "sec": "auto"}))
    write_csv(tmp_path / "s.csv", [{"case_id": c, "sampling_stratum": "S"} for c in ("a", "b", "sec")])
    manifest = {"cases": [{"case_id": "a"}, {"case_id": "b"}], "secondary_cases": [{"case_id": "sec"}]}
    rows = rh.audit_frame_rows(tmp_path / "p.csv", tmp_path / "s.csv", manifest, condition="C1", policy="selective_policy_v2")
    assert rows == [{"case_id": "a", "stratum": "S", "outcome": "auto"}, {"case_id": "b", "stratum": "S", "outcome": "manual"}]
    rh.write_audit_frame(tmp_path / "frame.csv", rows)
    with pytest.raises(FileExistsError):
        rh.write_audit_frame(tmp_path / "frame.csv", rows)
    with pytest.raises(rh.HelperError):
        rh.audit_frame_rows(tmp_path / "p.csv", tmp_path / "s.csv", {"cases": [{"case_id": "ghost"}]}, condition="C1", policy="selective_policy_v2")


def run(*args):
    return subprocess.run([sys.executable, "-I", str(BACKEND / "scripts" / "run_helpers.py"), *args], capture_output=True, text=True, cwd=BACKEND,
                          env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})


def test_command_line_glue_chains_selection_seeds_counts_and_audit_frame(tmp_path):
    archive, expected = make_archive(tmp_path)
    catalog = sel.catalog_from_archive(archive, expected)
    p = sel.draw_pilot(catalog, seed=5, dataset_version="synthetic", split="test", smoke_blocks=[], per_stratum={"S": 1, "M": 0, "L": 0, "XL": 0})
    (tmp_path / "manifest.json").write_text(json.dumps(p["manifest"]))
    (tmp_path / "identity.json").write_text(json.dumps(p["identity_map"]))
    (tmp_path / "catalog.json").write_text(json.dumps(catalog))
    r = run("seeds", "--manifest", str(tmp_path / "manifest.json"), "--identity-map", str(tmp_path / "identity.json"), "--catalog", str(tmp_path / "catalog.json"),
            "--archive", str(archive), "--capture-dir", str(tmp_path / "cap"), "--protected-dir", str(tmp_path / "prot"), "--include-secondary", "no")
    assert r.returncode == 0, r.stderr
    assert {x.name for x in (tmp_path / "cap").iterdir()} == {"seeds.csv", "doi_register.csv", "seed_freeze.json"} and (tmp_path / "prot" / "gold_identity_register.csv").exists()
    cid = p["manifest"]["cases"][0]["case_id"]
    write_csv(tmp_path / "pred.csv", preds({cid: "auto"}))
    r = run("pilot-counts", "--predictions", str(tmp_path / "pred.csv"), "--seeds", str(tmp_path / "cap" / "seeds.csv"), "--condition", "C1", "--policy", "selective_policy_v2", "--out", str(tmp_path / "counts.json"))
    assert r.returncode == 0 and json.loads((tmp_path / "counts.json").read_text()) == {"S": {"automatic": 1, "cases": 1}}
    r = run("audit-frame", "--predictions", str(tmp_path / "pred.csv"), "--seeds", str(tmp_path / "cap" / "seeds.csv"), "--manifest", str(tmp_path / "manifest.json"), "--condition", "C1",
            "--policy", "selective_policy_v2", "--out", str(tmp_path / "frame.csv"))
    assert r.returncode == 0 and "1 primary cases" in r.stdout
    again = run("audit-frame", "--predictions", str(tmp_path / "pred.csv"), "--seeds", str(tmp_path / "cap" / "seeds.csv"), "--manifest", str(tmp_path / "manifest.json"),
                "--condition", "C1", "--policy", "selective_policy_v2", "--out", str(tmp_path / "frame.csv"))
    assert again.returncode == 1 and "refused" in again.stderr
