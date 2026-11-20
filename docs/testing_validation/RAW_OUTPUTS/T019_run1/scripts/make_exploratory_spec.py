"""T019: write the spec of the EXPLORATORY benchmark-derived sample (drawn from the main frame, disjoint from the smoke and pilot blocks). Counts only."""
import json, sys
from pathlib import Path
repo, out, src, freeze_path, pilot_spec, pilot_manifest, n = sys.argv[1:8]
fz = json.loads(Path(freeze_path).read_text()); pm = json.loads(Path(pilot_manifest).read_text()); ps = json.loads(Path(pilot_spec).read_text())
spec = {"action": "main", "catalog": str(Path(src) / "block_catalog_PROTECTED.json"), "seed": fz["seeds"]["main"], "dataset_version": "lagos-and-v2.0-exploratory-" + fz["freeze_id"][-2:],
        "split": "test", "smoke_blocks": ps["smoke_blocks"], "pilot_blocks": pm["pilot_blocks"], "n_total": int(n), "floors": {"S": 0, "M": 0, "L": 0, "XL": 0}}
Path(out).write_text(json.dumps(spec))
print("exploratory spec: n_total", n, "| seed", spec["seed"], "| smoke blocks", len(spec["smoke_blocks"]), "| pilot blocks", len(spec["pilot_blocks"]))
