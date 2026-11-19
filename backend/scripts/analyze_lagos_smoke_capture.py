"""ORCID-availability diagnostics for a captured LAGOS-AND smoke run.

Reads the saved raw responses and the protected gold register. Outputs contain booleans, counts and ranks only:
no gold ORCID value is written. ORCID equality is a label-availability diagnostic, not independent identity accuracy.
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.dont_write_bytecode = True

from hammer_pilot.capture import classify_author_response

ORCID_RE = re.compile(r"(\d{4}-\d{4}-\d{4}-\d{3}[\dX])")


def items_of(cap: Path, entry: dict) -> list:
    body = (cap / entry["body_file"]).read_bytes() if entry.get("body_file") else None
    return classify_author_response(entry.get("status"), body, entry.get("error"))[2]


def orcid_of(item: dict):
    v = item.get("orcid")
    m = ORCID_RE.search(v) if isinstance(v, str) else None
    return m.group(1) if m else None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--smoke-dir", type=Path, required=True)
    p.add_argument("--gold-register", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    a = p.parse_args()
    cap = a.smoke_dir / "captures"
    index = {e["seq"]: e for e in (json.loads(l) for l in (cap / "capture_index.jsonl").read_text().splitlines())}
    seeds = {r["case_id"]: r for r in csv.DictReader(open(a.smoke_dir / "seeds.csv", encoding="utf-8"))}
    gold = {r["case_id"]: r["gold_orcid"] for r in csv.DictReader(open(a.gold_register, encoding="utf-8"))}
    rows = []
    for case_id in sorted(seeds):
        s = json.loads((cap / "cases" / f"{case_id}.json").read_text())
        arms = {"R0": ([s["R0"]], s["R0"]["status"]), "R2": ([s["R2_primary"]] + ([s["R2_fallback"]] if s["R2_fallback"] else []), s["r2_pool_status"])}
        pools = {}
        for arm, (parts, status) in arms.items():
            items = []
            for part in parts:
                items += items_of(cap, index[part["seq"]])
            ids, seen = [], set()
            for it in items:
                cid = it.get("id", "").rsplit("/", 1)[-1]
                if cid and cid not in seen:
                    seen.add(cid)
                    ids.append((cid, orcid_of(it), "orcid" in it))
            pools[arm] = ids
            exp = gold[case_id]
            with_orcid = sum(1 for _, o, _ in ids if o)
            hits = [i for i, (_, o, _) in enumerate(ids, 1) if o == exp]
            if status in ("provider_failed", "malformed"):
                cls = "provider_failure" if status == "provider_failed" else "malformed_response"
            elif status == "empty" or not ids:
                cls = "empty_pool"
            elif hits:
                cls = "expected_orcid_found"
            elif with_orcid == 0:
                cls = "orcid_field_missing_or_null_in_all_candidates"
            else:
                cls = "expected_orcid_absent_from_successful_pool"
            rows.append({"case_id": case_id, "source_block_id": seeds[case_id]["source_block_id"], "source_split": seeds[case_id]["source_split"],
                         "arm": arm, "response_seq": parts[0]["seq"], "shares_response_with_other_arm": s["R0"]["seq"] == s["R2_primary"]["seq"],
                         "pool_status": status, "pool_size": len(ids), "candidates_with_orcid_value": with_orcid,
                         "candidates_with_orcid_key": sum(1 for _, _, k in ids if k), "candidates_with_expected_orcid": len(hits),
                         "first_rank_of_expected": hits[0] if hits else "", "hit_at_1": bool(hits and hits[0] <= 1), "hit_at_5": bool(hits and hits[0] <= 5),
                         "hit_at_10": bool(hits and hits[0] <= 10), "classification": cls})
        rows[-1]["r0_r2_pools_identical"] = rows[-2]["r0_r2_pools_identical"] = [c for c, _, _ in pools["R0"]] == [c for c, _, _ in pools["R2"]]
    a.out_dir.mkdir(parents=True, exist_ok=False)
    fields = list(rows[0])
    with open(a.out_dir / "orcid_diagnostics.csv", "x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    summary = {"cases": len(seeds), "by_arm_classification": {arm: dict(Counter(r["classification"] for r in rows if r["arm"] == arm)) for arm in ("R0", "R2")},
               "by_split_expected_found_R2": {sp: [sum(1 for r in rows if r["arm"] == "R2" and r["source_split"] == sp and r["classification"] == "expected_orcid_found"),
                                                   sum(1 for r in rows if r["arm"] == "R2" and r["source_split"] == sp)] for sp in sorted({r["source_split"] for r in rows})},
               "blocks": len({r["source_block_id"] for r in rows}),
               "requests": {"total": len(index), "by_status": dict(Counter(e["status"] for e in index.values())),
                            "by_endpoint": dict(Counter(e["endpoint"].rsplit("/", 1)[-1] for e in index.values()))},
               "note": "Descriptive counts of a 50-case, 23-block sample; cases within a block are not independent. ORCID equality is an automatic label-availability diagnostic, not author-resolution accuracy."}
    costs = []
    for e in index.values():
        try:
            m = json.loads((cap / e["body_file"]).read_text()).get("meta", {})
            if isinstance(m.get("cost_usd"), (int, float)):
                costs.append(m["cost_usd"])
        except (ValueError, TypeError, OSError):
            pass
    summary["requests"]["provider_reported_cost_usd_sum"] = round(sum(costs), 6) if costs else None
    summary["requests"]["responses_with_cost_field"] = len(costs)
    (a.out_dir / "orcid_diagnostics_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
