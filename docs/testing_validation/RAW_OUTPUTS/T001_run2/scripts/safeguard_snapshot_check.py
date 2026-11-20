import csv, json
from collections import Counter
from pathlib import Path
SM = Path("../research_data/lagos_and_v2/smoke_v1/replay")
snap = {}
for l in open(SM/"evidence_snapshot.jsonl", encoding="utf-8"):
    s = json.loads(l); snap[(s["case_id"], s["condition"])] = s
print("snapshot keys", len(snap))
st = Counter(); av = Counter()
for s in snap.values():
    for c in s["candidates"]:
        for e in c["evidence"]:
            st[e["status"]] += 1; av[(e["signal"], e["availability"], e["status"])] += 1
print("evidence status values:", dict(st))
for k, v in sorted(av.items()): print("  ", k, v)
rows = [r for r in csv.DictReader(open(SM/"predictions.csv", encoding="utf-8")) if r["policy"] == "selective_policy_v2" and r["outcome"] == "auto"]
bad = Counter()
for r in rows:
    s = snap[(r["case_id"], r["condition"])]; cands = s["candidates"]
    top = cands[0]
    if any(c["score"] is None for c in cands): bad["unscored competitor"] += 1
    obs = [e for e in top["evidence"] if e["availability"] == "observed" or e["status"] in ("observed", "available")]
    if any((e["score"] == 0.0) for e in obs): bad["observed 0.0 signal on top"] += 1
    nz = [e for e in obs if e["signal"] in ("institution_similarity", "publication_overlap", "coauthor_overlap") and (e["score"] or 0) > 0]
    if not nz: bad["no non-zero corroborating signal"] += 1
    if len({tuple(c["signal_set"]) for c in cands}) > 1: bad["different signal sets"] += 1
print("auto rows checked:", len(rows), "safeguard violations:", dict(bad) or "none")
print("auto rows by (condition,pool_size):", Counter((r["condition"], r["pool_size"]) for r in rows))
