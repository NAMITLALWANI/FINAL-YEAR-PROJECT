"""In-memory scale check of the selector on the REAL catalog with TEST parameters (nothing saved, no block list or ORCID printed; the dummy seeds and sizes are not
the study's). Reports timing, counts, determinism and the absence of ORCID in the manifest only. Run from backend/."""
import hashlib, json, random, re, sys, time
sys.dont_write_bytecode = True
sys.path.insert(0, ".")
from hammer_pilot import selector_c1c as sel

cat = json.load(open(sys.argv[1]))
ORCID = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]")
t = time.time()
f = sel.eligible_frame(cat, split="test")
print("eligible_frame seconds", round(time.time() - t, 2), f["sizes"])
smoke = []
args = dict(seed=1, dataset_version="v2.0-dry-run", split="test", smoke_blocks=smoke)
t = time.time()
p1 = sel.draw_pilot(cat, per_stratum={"S": 50, "M": 50, "L": 30, "XL": 0}, **args)
p2 = sel.draw_pilot(dict(random.Random(3).sample(list(cat.items()), len(cat))), per_stratum={"S": 50, "M": 50, "L": 30, "XL": 0}, **args)
print("two pilot draws seconds", round(time.time() - t, 2), "identical manifests (also with a shuffled catalogue):", p1["manifest"] == p2["manifest"])
pb = [c["block_id"] for c in p1["manifest"]["cases"]]
m = sel.draw_main(cat, seed=2, dataset_version="v2.0-dry-run", split="test", smoke_blocks=smoke, pilot_blocks=pb, n_total=300, floors={"S": 0, "M": 0, "L": 0, "XL": 0})
print("main allocation", m["manifest"]["allocation"], "cases", len(m["manifest"]["cases"]), "secondary", len(m["manifest"]["secondary_cases"]))
print("disjointness", sel.disjointness_report(smoke, p1["manifest"], m["manifest"]))
print("post-exclusion frame after pilot", p1["manifest"]["post_exclusion_frame_after_pilot"])
print("manifests verify:", sel.verify_manifest(p1["manifest"]), sel.verify_manifest(m["manifest"]), "| ORCID in a manifest:", bool(ORCID.search(json.dumps(m["manifest"]))))
xl = sel.draw_main(cat, seed=2, dataset_version="v", split="test", smoke_blocks=smoke, pilot_blocks=pb, n_total=300, floors={"S": 0, "M": 0, "L": 0, "XL": 12})
print("with an XL floor above its size 12: XL allocation", xl["manifest"]["allocation"]["XL"], "(census)")
