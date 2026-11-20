"""Build a pilot, main or audit selection manifest from a block catalog JSON (offline; no archive, no provider). Every parameter comes from the spec file.

spec (JSON): {"action": "pilot" | "main" | "audit", ...}
  pilot: catalog, seed, dataset_version, split, smoke_blocks, per_stratum
  main:  catalog, seed, dataset_version, split, smoke_blocks, pilot_blocks, n_total, floors
  audit: predictions_csv (case_id, stratum, outcome), seed, dataset_version, n_audit, merge_rule (object or null), predictions_sha256
Outputs (new files only, never overwritten): manifest.json, and for pilot and main also identity_map.json (PROTECTED: holds benchmark ORCIDs)."""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.dont_write_bytecode = True

from hammer_pilot import selector_c1c as sel


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    try:
        action = spec["action"]
        if action in ("pilot", "main"):
            catalog = json.loads(Path(spec["catalog"]).read_text(encoding="utf-8"))
            common = dict(seed=spec["seed"], dataset_version=spec["dataset_version"], split=spec["split"], smoke_blocks=spec["smoke_blocks"])
            result = (sel.draw_pilot(catalog, per_stratum=spec["per_stratum"], **common) if action == "pilot"
                      else sel.draw_main(catalog, pilot_blocks=spec["pilot_blocks"], n_total=spec["n_total"], floors=spec["floors"], **common))
            outputs = {"manifest.json": result["manifest"], "identity_map.json": result["identity_map"]}
        elif action == "audit":
            rows = list(csv.DictReader(open(spec["predictions_csv"], encoding="utf-8")))
            auto = [r["case_id"] for r in rows if r["outcome"] == "auto"]
            rest = [{"case_id": r["case_id"], "stratum": r["stratum"]} for r in rows if r["outcome"] != "auto"]
            outputs = {"manifest.json": sel.draw_audit(rest, auto, seed=spec["seed"], dataset_version=spec["dataset_version"], n_audit=spec["n_audit"],
                                                       merge_rule=spec["merge_rule"], predictions_sha256=spec["predictions_sha256"])}
        else:
            raise sel.SelectionError(f"unknown action {action!r}")
    except (KeyError, sel.SelectionError, ValueError) as exc:
        print(f"selection refused: {exc!r}", file=sys.stderr)
        return 1
    args.out_dir.mkdir(parents=True, exist_ok=False)
    for name, obj in outputs.items():
        with open(args.out_dir / name, "x", encoding="utf-8") as f:
            f.write(json.dumps(obj, indent=1, sort_keys=True) + "\n")
    print(f"{action}: wrote {', '.join(outputs)} to {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
