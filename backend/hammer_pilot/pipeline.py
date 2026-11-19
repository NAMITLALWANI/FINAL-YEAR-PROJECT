"""Replay + metrics + manifest in one deterministic pipeline."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from hammer_pilot.common import (
    CONDITIONS, POLICIES, canonical_json, read_csv, sha256_file, write_text_exclusive,
)
from hammer_pilot.manifest import build_manifest, manifest_text
from hammer_pilot.metrics import retrieval_metrics, selective_metrics
from hammer_pilot.replay import replay


def _load_gold(pilot_dir: Path) -> dict[str, dict[str, Any]] | None:
    a, b = pilot_dir / "stage_a.csv", pilot_dir / "stage_b.csv"
    if not (a.is_file() and b.is_file()):
        return None
    gold = {r["case_id"].strip(): {"status": r["final_status"].strip(), "mapped": set()} for r in read_csv(a, {"case_id", "final_status"})}
    for r in read_csv(b, {"case_id", "candidate_author_id", "final_judgment"}):
        if r["final_judgment"].strip() == "same" and r["case_id"].strip() in gold:
            gold[r["case_id"].strip()]["mapped"].add(r["candidate_author_id"].strip())
    return gold


def derive_run_id(pilot_dir: Path) -> str:
    """Deterministic run ID from the frozen inputs, so identical inputs always give the same ID."""
    import hashlib
    h = hashlib.sha256()
    for n in ("seeds.csv", "doi_register.csv", "seed_freeze.json", "stage_a.csv", "stage_b.csv"):
        p = Path(pilot_dir) / n
        h.update(n.encode() + (sha256_file(p).encode() if p.is_file() else b"-"))
    index = Path(pilot_dir) / "captures" / "capture_index.jsonl"
    h.update(sha256_file(index).encode() if index.is_file() else b"-")
    return "run-" + h.hexdigest()[:12]


def compute_metrics(pilot_dir: Path, out_dir: Path) -> dict[str, Any] | None:
    gold = _load_gold(pilot_dir)
    if gold is None:
        return None
    retr = read_csv(out_dir / "retrieval.csv", {"case_id", "arm", "pool_status", "ordered_candidate_ids"})
    preds = read_csv(out_dir / "predictions.csv", {"case_id", "condition", "policy", "outcome", "selected_author_id", "auto_blockers", "top_signal_set", "threshold_gates_passed"})
    pools: dict[str, dict[str, dict[str, Any]]] = {}
    for r in retr:
        pools.setdefault(r["case_id"], {})[r["arm"]] = {"status": r["pool_status"], "ids": json.loads(r["ordered_candidate_ids"]), "sha": r.get("response_sha256", "")}
    resolved_cases = [{"case_id": c, "mapped": g["mapped"], "pools": pools[c]} for c, g in sorted(gold.items()) if g["status"] == "resolved" and c in pools]
    result: dict[str, Any] = {"retrieval_RQ2a": retrieval_metrics(resolved_cases), "selective_RQ2b": {}, "signal_set_composition": {},
                              "withheld_by_safeguard": {}, "error_categories_policy_v2": {}}
    for cond in CONDITIONS:
        for pol in POLICIES:
            rows = [r for r in preds if r["condition"] == cond and r["policy"] == pol]
            result["selective_RQ2b"][f"{cond}/{pol}"] = selective_metrics(rows, gold, cond, pol)
        v2 = [r for r in preds if r["condition"] == cond and r["policy"] == "selective_policy_v2"]
        result["signal_set_composition"][cond] = dict(sorted(Counter(r["top_signal_set"] for r in v2 if r["top_signal_set"] not in ("", "[]")).items()))
        blockers: Counter = Counter()
        for r in v2:
            if r["outcome"] != "auto" and r["threshold_gates_passed"] == "True":
                blockers.update(json.loads(r["auto_blockers"] or "[]"))
        result["withheld_by_safeguard"][cond] = dict(sorted(blockers.items()))
        cats: Counter = Counter()
        for r in v2:
            g = gold.get(r["case_id"])
            if not g or g["status"] == "uncertain":
                continue
            if g["status"] == "unresolved":
                cats["unresolved_control_" + ("false_acceptance" if r["outcome"] == "auto" else "abstained")] += 1
                continue
            pool = pools.get(r["case_id"], {}).get("R2", {"status": "", "ids": []})
            if r["outcome"] in ("provider_failed", "empty_pool", "no_score"):
                cats[r["outcome"]] += 1
            elif r["outcome"] == "auto":
                cats["correct_automatic" if r["selected_author_id"] in g["mapped"] else "wrong_automatic"] += 1
            elif not (g["mapped"] & set(pool["ids"])):
                cats["retrieval_miss_or_mapping_gap"] += 1
            else:
                cats["withheld_" + r["outcome"]] += 1
        result["error_categories_policy_v2"][cond] = dict(sorted(cats.items()))
    result["trace"] = {"run_id": retr[0].get("run_id") if retr else None,
                       "frozen_inputs_sha256": {n: sha256_file(pilot_dir / n) for n in ("seeds.csv", "doi_register.csv", "seed_freeze.json", "review_a.csv", "review_b.csv", "stage_a.csv", "stage_b.csv") if (pilot_dir / n).is_file()},
                       "derived_tables_sha256": {n: sha256_file(out_dir / n) for n in ("retrieval.csv", "predictions.csv")},
                       "note": "Every metric is computed from these frozen inputs and derived tables; counts and denominators accompany every rate."}
    result["limitation"] = "Candidates scored on different signal sets are not directly comparable; scores are heuristic, not probabilities."
    return result


async def run_pipeline(pilot_dir: Path, out_dir: Path, *, git: dict[str, Any] | None = None, run_id: str | None = None) -> dict[str, Any]:
    pilot_dir, out_dir = Path(pilot_dir), Path(out_dir)
    run_id = run_id or derive_run_id(pilot_dir)
    summary = await replay(pilot_dir, out_dir, run_id)
    metrics = compute_metrics(pilot_dir, out_dir)
    if metrics is not None:
        write_text_exclusive(out_dir / "metrics.json", json.dumps(metrics, sort_keys=True, indent=2) + "\n")
    manifest = build_manifest(pilot_dir, git=git, extra={"run_id": run_id, "replay_summary": summary, "metrics_computed": metrics is not None})
    write_text_exclusive(out_dir / "run_manifest.json", manifest_text(manifest))
    return summary
