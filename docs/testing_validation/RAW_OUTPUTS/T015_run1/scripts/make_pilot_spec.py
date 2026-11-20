"""T015: write the pilot selection spec (no ORCID or name printed). Smoke blocks are recovered from the frozen smoke seeds exactly as in T011."""
import csv, hashlib, json, sys
from pathlib import Path
repo = Path(sys.argv[1]); out = Path(sys.argv[2]); src = Path(sys.argv[3])
freeze = json.loads(Path(sys.argv[4]).read_text())
catalog = json.loads((src / "block_catalog_PROTECTED.json").read_text())
smoke_manifest = json.loads((repo / "research_data/lagos_and_v2/seed_v1/sampling_manifest.json").read_text())
smoke_seed = smoke_manifest["sampling"]["seed"]
ids = {r["source_block_id"] for r in csv.DictReader(open(repo / "research_data/lagos_and_v2/seed_v1/seeds.csv", encoding="utf-8"))}
smoke_blocks = sorted(b for b in catalog if "B" + hashlib.sha256(f"{smoke_seed}|blockid|{b}".encode()).hexdigest()[:8] in ids)
assert len(smoke_blocks) == smoke_manifest["counts"]["selected_blocks"] == 23, len(smoke_blocks)
spec = {"action": "pilot", "catalog": str(src / "block_catalog_PROTECTED.json"), "seed": freeze["seeds"]["pilot"], "dataset_version": "lagos-and-v2.0-pilot-" + freeze["freeze_id"][-2:],
        "split": "test", "smoke_blocks": smoke_blocks, "per_stratum": freeze["parameters"]["pilot"]["per_stratum"]}
out.write_text(json.dumps(spec), encoding="utf-8")
print("smoke blocks found:", len(smoke_blocks), "| pilot seed:", spec["seed"], "| per_stratum:", spec["per_stratum"])
