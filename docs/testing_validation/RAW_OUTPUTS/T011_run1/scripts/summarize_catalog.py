"""Summarise a block catalog built from the real LAGOS-AND archive and cross-check it against the totals recorded earlier (dataset_quality_report.json).
Counts only: no ORCID, no block name and no author name is written. Run from backend/ (needs the selector module)."""
import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, ".")

from hammer_lagos.prep import SPLIT_NAMES, eligibility, stratum_for
from hammer_pilot import selector_c1c as sel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--quality-report", type=Path, required=True)
    ap.add_argument("--sampling-manifest", type=Path, required=True)
    ap.add_argument("--smoke-seeds", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    catalog = json.loads(a.catalog.read_text(encoding="utf-8"))
    quality = json.loads(a.quality_report.read_text(encoding="utf-8"))
    manifest = json.loads(a.sampling_manifest.read_text(encoding="utf-8"))
    smoke_seed = manifest["sampling"]["seed"]
    smoke_ids = {r["source_block_id"] for r in csv.DictReader(open(a.smoke_seeds, encoding="utf-8"))}
    smoke_blocks = [b for b in catalog if "B" + hashlib.sha256(f"{smoke_seed}|blockid|{b}".encode()).hexdigest()[:8] in smoke_ids]

    reasons, band_all, band_by_split = Counter(), Counter(), {}
    split_all = Counter()
    for b, info in catalog.items():
        split_all[info["split_values"][0] if len(info["split_values"]) == 1 else "mixed"] += 1
        why = eligibility(dict(info))
        if why:
            reasons[why] += 1
            continue
        s = stratum_for(info["unique_dois"])
        band_all[s] += 1
        band_by_split.setdefault(SPLIT_NAMES[info["split_values"][0]], Counter())[s] += 1
    test_frame = sel.eligible_frame(catalog, split="test", exclude_blocks=smoke_blocks)
    test_frame_no_exclusion = sel.eligible_frame(catalog, split="test")
    smoke_by_band = Counter(stratum_for(catalog[b]["unique_dois"]) for b in smoke_blocks)

    rep_blocks = quality["blocks"]
    checks = {
        "blocks_total": (len(catalog), rep_blocks),
        "rows_total": (sum(i["raw_rows"] for i in catalog.values()), quality["rows_total"]),
        "orcid_group_pairs": (sum(i["n_groups"] for i in catalog.values()), quality["orcid_groups_block_orcid_pairs"]),
        "eligible_blocks_total": (sum(band_all.values()), quality["sampling_frame"]["eligible_blocks_total"]),
        "eligible_by_band": (dict(sorted(band_all.items())), quality["sampling_frame"]["eligible_blocks_by_stratum"]),
        "block_split_distribution": ({k: split_all[k] for k in ("0", "1", "2")}, quality["block_split_distribution"]),
        "mixed_split_blocks": (split_all["mixed"], quality["blocks_with_mixed_split"]),
        "exclusion_reasons": (dict(sorted(reasons.items())), quality["sampling_frame"]["exclusion_reasons"]),
        "smoke_blocks_found": (len(smoke_blocks), manifest["counts"]["selected_blocks"]),
    }
    result = {"cross_check_against_recorded_totals": {k: {"computed": c, "recorded": r, "equal": c == r} for k, (c, r) in checks.items()},
              "all_equal": all(c == r for c, r in checks.values()),
              "eligible_blocks_by_split_and_band_all_splits_before_any_exclusion": {k: dict(sorted(v.items())) for k, v in sorted(band_by_split.items())},
              "test_split_eligible_frame_before_smoke_exclusion": test_frame_no_exclusion["sizes"],
              "smoke_blocks_by_band": dict(sorted(smoke_by_band.items())),
              "test_split_eligible_frame_after_smoke_exclusion": test_frame["sizes"],
              "status": "informational: not the post-exclusion frame (pilot blocks are removed later); nothing is frozen and no sample was drawn"}
    with open(a.out, "x", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"all_equal": result["all_equal"], "test_after_smoke_exclusion": result["test_split_eligible_frame_after_smoke_exclusion"]}))
    return 0 if result["all_equal"] else 1


if __name__ == "__main__":
    sys.exit(main())
