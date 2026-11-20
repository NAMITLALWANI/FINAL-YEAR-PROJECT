"""T019: build a replay input directory restricted to the cases whose capture completed (progress event case_done). Nothing is edited in place; the capture is copied."""
import csv, hashlib, json, shutil, sys
from pathlib import Path
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
done = [json.loads(l)["case_id"] for l in (src / "captures" / "progress.jsonl").read_text().splitlines() if json.loads(l)["event"] == "case_done"]
done_set = set(done)
dst.mkdir(parents=True)
def subset(name):
    rows = list(csv.DictReader(open(src / name, encoding="utf-8")))
    keep = [r for r in rows if r["case_id"] in done_set]
    with open(dst / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n"); w.writeheader(); w.writerows(keep)
    return hashlib.sha256((dst / name).read_bytes()).hexdigest(), len(keep)
hs, ns = subset("seeds.csv"); hd, _ = subset("doi_register.csv")
orig = json.loads((src / "seed_freeze.json").read_text())
fz = {**orig, "seeds_sha256": hs, "doi_register_sha256": hd, "cases": ns, "restricted_to_completed_cases_of": orig["manifest_sha256"]}
(dst / "seed_freeze.json").write_text(json.dumps(fz, indent=1, sort_keys=True) + "\n")
shutil.copytree(src / "captures", dst / "captures")
cfg = json.loads((dst / "captures" / "capture_config.json").read_text()); cfg["seeds_sha256"] = hs
(dst / "captures" / "capture_config.json").write_text(json.dumps(cfg, sort_keys=True) + "\n")
print("completed cases:", ns)
