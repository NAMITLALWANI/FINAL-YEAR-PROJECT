"""Derive C0 / C1 / C1x contexts from a frozen seed and the DOI register (the seed is never edited).

DOI leakage rule:
  gold_evidence  used by Stage A reviewers; removed from primary C1.
  query_context  chosen independently of gold evidence; eligible for primary C1.
  both           documentation / exploratory only; its publication evidence belongs in C1x.
"""
from __future__ import annotations

from typing import Any

from author_resolution.context import QueryContext, normalize_doi
from hammer_pilot.common import DOI_PURPOSES, PilotDataError, json_field


def register_by_case(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        if row["purpose"].strip() not in DOI_PURPOSES:
            raise PilotDataError(f"DOI register: invalid purpose {row['purpose']!r} for {row['case_id']}")
        doi = normalize_doi(row["doi"])
        if not doi:
            raise PilotDataError(f"DOI register: invalid DOI for {row['case_id']}")
        grouped.setdefault(row["case_id"].strip(), []).append({**row, "doi": doi, "purpose": row["purpose"].strip()})
    return grouped


def seed_dois(context: dict[str, Any]) -> list[str]:
    return list(QueryContext.from_any(context).publication_dois)


def derive_contexts(seed: dict[str, str], register: list[dict[str, str]]) -> dict[str, Any]:
    """Return {"C0", "C1", "C1x", "removed_from_c1", "gold_dois", "both_dois"} for one seed row."""
    case = seed["case_id"].strip()
    c1 = json_field(seed, "context_c1_json", case, {}) or {}
    c1x_seed = json_field(seed, "context_c1x_json", case, {}) or {}
    if not isinstance(c1, dict) or not isinstance(c1x_seed, dict):
        raise PilotDataError(f"{case}: context JSON must be an object")
    gold = {r["doi"] for r in register if r["purpose"] in ("gold_evidence", "both")}
    both = {r["doi"] for r in register if r["purpose"] == "both"}
    c1_dois = seed_dois(c1)
    removed = [d for d in c1_dois if d in gold]
    primary = {k: v for k, v in c1.items() if k not in ("publications", "publication_ids")}
    kept = [d for d in c1_dois if d not in gold]
    work_ids = list(QueryContext.from_any(c1).publication_work_ids)
    if kept or work_ids:
        primary["publications"] = kept + work_ids
    c1x = {k: v for k, v in c1x_seed.items() if k not in ("publications", "publication_ids")}
    for key, value in c1.items():
        if key not in ("publications", "publication_ids"):
            c1x.setdefault(key, value)
    x_dois = sorted(set(c1_dois) | set(seed_dois(c1x_seed)) | both)
    if x_dois or work_ids:
        c1x["publications"] = x_dois + work_ids
    return {"C0": {}, "C1": primary, "C1x": c1x, "removed_from_c1": removed,
            "gold_dois": sorted(gold), "both_dois": sorted(both)}
