"""Assemble report.json (C7) from a frozen selection. Offline. Refuses to overwrite.

  python scripts/assemble_c7_report.py --manifest main_manifest.json --seeds capture/seeds.csv --capture-dir capture/captures --replay-dir replay \
      --gold-register PROTECTED/gold_identity_register.csv --freeze freeze_F1.json --out report.json [--verified verified_fields.json]
Run from backend/. The gold register (benchmark ORCIDs) is read into memory only."""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hammer_pilot import metrics_c7 as m
from hammer_pilot import report_assembly as ra


def rows(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "seeds", "capture-dir", "replay-dir", "gold-register", "freeze", "out"):
        ap.add_argument(f"--{name}", type=Path, required=True)
    ap.add_argument("--verified", type=Path, default=None)
    ap.add_argument("--resamples", type=int, default=10_000)
    a = ap.parse_args()
    try:
        manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
        freeze = json.loads(a.freeze.read_text(encoding="utf-8"))
        inf = freeze["parameters"]["inference"]
        settings = m.InferenceSettings(bootstrap_resamples=a.resamples, bootstrap_min_stratum_n=inf["bootstrap_min_stratum_cases"],
                                       negligible_weight=inf["negligible_stratum_weight"], sampling_fraction_flag=inf["diagnostics"]["sampling_fraction_warn"],
                                       sparse_automatic_warn=inf["diagnostics"]["sparse_automatic_warn"], sparse_error_warn=inf["diagnostics"]["sparse_errors_warn"])
        gold = {r["case_id"]: r["gold_orcid"] for r in rows(a.gold_register)}
        mapped = ra.benchmark_mapping(a.capture_dir, gold)
        verified = json.loads(a.verified.read_text(encoding="utf-8")) if a.verified else None
        cases = ra.build_cases(rows(a.seeds), manifest, rows(a.replay_dir / "predictions.csv"), rows(a.replay_dir / "retrieval.csv"), mapped, verified)
        prov = {"freeze_id": freeze["freeze_id"], "freeze_manifest_sha256": freeze["manifest_sha256"], "selection_manifest_sha256": manifest["manifest_sha256"],
                "predictions_sha256": ra.file_sha256(a.replay_dir / "predictions.csv"), "retrieval_sha256": ra.file_sha256(a.replay_dir / "retrieval.csv"),
                "verified_fields_sha256": ra.file_sha256(a.verified) if a.verified else None, "condition": "C1", "policy": "selective_policy_v2"}
        report = ra.assemble_report(cases, manifest, settings, freeze["seeds"]["main"], prov)
        with open(a.out, "x", encoding="utf-8") as f:
            f.write(m.to_json(report))
    except (ra.AssemblyError, m.C7Error, KeyError, FileExistsError) as exc:
        print(f"refused: {exc!r}", file=sys.stderr)
        return 1
    print(f"wrote {a.out}; verification {report['verification_status']['state']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
