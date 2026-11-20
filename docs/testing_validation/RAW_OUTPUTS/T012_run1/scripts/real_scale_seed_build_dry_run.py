"""In-memory check of the seeds adapter on the REAL archive with a DUMMY test manifest (nothing saved; counts only; no ORCID, block or author name printed)."""
import json, re, sys, time
sys.dont_write_bytecode = True
sys.path.insert(0, ".")
from hammer_pilot import selector_c1c as sel, seeds_from_manifest as sfm
catalog_path, archive = sys.argv[1], sys.argv[2]
cat = json.load(open(catalog_path))
p = sel.draw_pilot(cat, seed=1, dataset_version="v2.0-dry-run", split="test", smoke_blocks=[], per_stratum={"S": 20, "M": 20, "L": 10, "XL": 0})
blocks = [c["block_id"] for c in p["manifest"]["cases"]]
t = time.time()
rows = sfm.rows_for_blocks(archive, blocks)
print("archive second pass seconds", round(time.time() - t), "blocks found", len(rows), "of", len(blocks))
out = sfm.build_capture_inputs(p["manifest"], p["identity_map"], cat, rows, include_secondary=True)
ORCID = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]")
print("seeds", len(out["seeds"]), "gold", len(out["gold"]), "doi rows", len(out["dois"]), "| primary cases", len(p["manifest"]["cases"]), "secondary", len(p["manifest"]["secondary_cases"]))
print("C1 institution missing:", sum(s["c1_institution_missing"] == "true" for s in out["seeds"]), "| ORCID in seeds or DOI register:", bool(ORCID.search(json.dumps(out["seeds"]) + json.dumps(out["dois"]))))
print("designated DOI always in its group's register:", all(g["designated_doi"] in {d["doi"] for d in out["dois"] if d["case_id"] == g["case_id"]} for g in out["gold"]))
