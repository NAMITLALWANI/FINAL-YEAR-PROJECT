import csv, json, re, sys
from collections import Counter
from pathlib import Path
R = Path("../research_data/lagos_and_v2")
SM = R / "smoke_v1"
pred = list(csv.DictReader(open(SM/"replay/predictions.csv", encoding="utf-8")))
ret = list(csv.DictReader(open(SM/"replay/retrieval.csv", encoding="utf-8")))
print("predictions rows", len(pred), "retrieval rows", len(ret), "cases", len({r['case_id'] for r in pred}))
print("\n[1] outcome by condition/policy")
c = Counter((r["condition"], r["policy"], r["outcome"]) for r in pred)
for k in sorted(c): print("  ", k, c[k])
print("\n[2] pool_status / error_code by arm (retrieval.csv)")
for k, v in sorted(Counter((r["arm"], r["pool_status"], r["error_code"], r["fallback_status"]) for r in ret).items()): print("  ", k, v)
print("\n[3] pool_status in predictions vs outcome (selective_policy_v2, C1)")
for k, v in sorted(Counter((r["pool_status"], r["outcome"]) for r in pred if r["policy"]=="selective_policy_v2" and r["condition"]=="C1").items()): print("  ", k, v)
print("\n[4] distinct outcome values:", sorted({r["outcome"] for r in pred}), "pool_status values:", sorted({r["pool_status"] for r in pred}))
# safeguards on selective_policy_v2 auto rows
def f(x):
    try: return float(x)
    except: return None
viol = Counter(); auto = 0
for r in pred:
    if r["policy"] != "selective_policy_v2" or r["outcome"] != "auto": continue
    auto += 1
    sig = json.loads(r["top_signal_set"] or "[]")
    if (f(r["top_score"]) or 0) < 0.75: viol["score<0.75"] += 1
    if len(sig) < 2: viol["<2 observed signals"] += 1
    if r["auto_blockers"] not in ("[]", ""): viol["blockers present"] += 1
    if r["different_signal_sets_in_pool"] == "True": viol["different signal sets"] += 1
    if r["second_score"] not in ("", None) and (f(r["margin"]) is None or f(r["margin"]) < 0.15): viol["margin<0.15"] += 1
    if not set(sig) & {"institution_similarity","publication_overlap","coauthor_overlap"}: viol["no non-name corroboration"] += 1
    if r["pool_status"] != "ok": viol["pool not ok"] += 1
print("\n[5] selective_policy_v2 auto rows:", auto, "violations:", dict(viol) or "none")
print("    auto_blockers values seen:", Counter(r["auto_blockers"] for r in pred if r["policy"]=="selective_policy_v2").most_common(8))
fa = Counter((r["condition"], r["outcome"]) for r in pred if r["policy"]=="forced_top1")
print("    forced_top1 by condition/outcome:", sorted(fa.items()))
# name-only automatic under selective?
print("    C0 selective auto:", sum(1 for r in pred if r["policy"]=="selective_policy_v2" and r["condition"]=="C0" and r["outcome"]=="auto"))
# leak scan
gold = {r["gold_orcid"] for r in csv.DictReader(open(R/"seed_v1/gold_identity_register.csv", encoding="utf-8")) if r.get("gold_orcid")}
pat = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]")
print("\n[6] leak scan (counts only; gold register has", len(gold), "distinct values)")
def scan(p, label):
    t = p.read_text(encoding="utf-8", errors="replace")
    g = sum(t.count(x) for x in gold); a = len(pat.findall(t))
    print(f"   {label:46s} gold-ORCID hits={g:4d}  any-ORCID-pattern hits={a:4d}")
for rel in ["replay/predictions.csv","replay/retrieval.csv","replay/evidence_snapshot.jsonl","replay/run_manifest.json","seeds.csv","doi_register.csv","seed_freeze.json","diagnostics/orcid_diagnostics.csv","diagnostics/orcid_diagnostics_summary.json"]:
    scan(SM/rel, "smoke_v1/"+rel)
tot_g = tot_a = 0
for p in sorted((SM/"captures/cases").glob("*.json")):
    t = p.read_text(encoding="utf-8"); tot_g += sum(t.count(x) for x in gold); tot_a += len(pat.findall(t))
print(f"   {'smoke_v1/captures/cases/*.json (50 files)':46s} gold-ORCID hits={tot_g:4d}  any-ORCID-pattern hits={tot_a:4d}")
tot_g = tot_a = 0
for p in sorted((SM/"captures/bodies").iterdir()):
    t = p.read_bytes().decode("utf-8", "replace"); tot_g += sum(t.count(x) for x in gold); tot_a += len(pat.findall(t))
print(f"   {'smoke_v1/captures/bodies (raw provider bodies)':46s} gold-ORCID hits={tot_g:4d}  any-ORCID-pattern hits={tot_a:4d}  (provider payload; expected)")
for rel in ["seed_v1/seeds.csv","seed_v1/doi_purpose_register.csv"]:
    scan(R/rel, rel)
