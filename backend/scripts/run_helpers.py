"""Glue commands between pipeline stages (offline; no provider, no archive except `seeds`).

  seeds          manifest + identity map + catalog + archive -> seeds.csv, doi_register.csv (capture directory) and the PROTECTED gold register
  pilot-counts   replay predictions + seeds -> JSON per-stratum automatic counts (input of size_hammer_main_sample.py)
  audit-frame    replay predictions + seeds + manifest -> CSV of primary cases (input of build_selection_manifest.py audit)
Each command refuses to overwrite and takes every parameter explicitly."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.dont_write_bytecode = True

from hammer_pilot import run_helpers as rh
from hammer_pilot import seeds_from_manifest as sfm


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seeds")
    for n in ("manifest", "identity-map", "catalog", "archive"):
        s.add_argument(f"--{n}", type=Path, required=True)
    s.add_argument("--capture-dir", type=Path, required=True)
    s.add_argument("--protected-dir", type=Path, required=True)
    s.add_argument("--include-secondary", choices=("yes", "no"), required=True)
    p = sub.add_parser("pilot-counts")
    audit = sub.add_parser("audit-frame")
    for q in (p, audit):
        q.add_argument("--predictions", type=Path, required=True)
        q.add_argument("--seeds", type=Path, required=True)
        q.add_argument("--condition", required=True)
        q.add_argument("--policy", required=True)
    p.add_argument("--out", type=Path, required=True)
    audit.add_argument("--manifest", type=Path, required=True)
    audit.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    try:
        if a.cmd == "seeds":
            manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
            catalog = json.loads(a.catalog.read_text(encoding="utf-8"))
            ident = json.loads(a.identity_map.read_text(encoding="utf-8"))
            blocks = [c["block_id"] for c in manifest["cases"] + manifest["secondary_cases"]]
            inputs = sfm.build_capture_inputs(manifest, ident, catalog, sfm.rows_for_blocks(a.archive, blocks), include_secondary=a.include_secondary == "yes")
            hashes = sfm.write_capture_inputs(a.capture_dir, a.protected_dir, inputs, manifest)
            print(json.dumps({"cases": len(inputs["seeds"]), "file_sha256": hashes}, indent=1))
        elif a.cmd == "pilot-counts":
            counts = rh.pilot_coverage_counts(a.predictions, a.seeds, condition=a.condition, policy=a.policy)
            with open(a.out, "x", encoding="utf-8") as f:
                f.write(json.dumps(counts, indent=1, sort_keys=True) + "\n")
            print(json.dumps(counts))
        else:
            manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
            rows = rh.audit_frame_rows(a.predictions, a.seeds, manifest, condition=a.condition, policy=a.policy)
            rh.write_audit_frame(a.out, rows)
            print(f"audit frame of {len(rows)} primary cases written")
    except (rh.HelperError, sfm.SeedBuildError, FileExistsError, KeyError) as exc:
        print(f"refused: {exc!r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
