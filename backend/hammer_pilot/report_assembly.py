"""Assemble the C7 report from a frozen selection manifest, the capture directory, the offline replay and (optionally) adjudicated verified labels (T016).

Benchmark ORCIDs are read into memory only to build the benchmark mapping (which pool candidates carry the expected ORCID); they are never written.
Verified fields come from `review_records.to_c7_fields` and are merged per case; without them every case is benchmark-derived and the report says verification is pending.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from hammer_pilot import metrics_c7 as m
from hammer_pilot.capture import classify_author_response
from hammer_pilot.replay import load_index

ORCID = re.compile(r"(\d{4}-\d{4}-\d{4}-\d{3}[\dX])")
VERIFIED_KEYS = {"label_state", "selected_judgment", "pool_judgments", "group_purity", "audit_subset"}


class AssemblyError(ValueError):
    pass


def benchmark_mapping(capture_dir: Path, gold_by_case: Mapping[str, str]) -> dict[str, set[str]]:
    """Pool candidates (R2 primary plus fallback) whose provider ORCID equals the benchmark ORCID. A provisional label, never verification."""
    index = {e["seq"]: e for e in load_index(capture_dir)}
    mapped: dict[str, set[str]] = {}
    for case, gold in gold_by_case.items():
        summary = json.loads((capture_dir / "cases" / f"{case}.json").read_text(encoding="utf-8"))
        parts = [summary["R2_primary"]] + ([summary["R2_fallback"]] if summary.get("R2_fallback") else [])
        ids: set[str] = set()
        for part in parts:
            e = index[part["seq"]]
            body = (capture_dir / e["body_file"]).read_bytes() if e.get("body_file") else None
            for item in classify_author_response(e.get("status"), body, e.get("error"))[2]:
                found = ORCID.search(item["orcid"]) if isinstance(item.get("orcid"), str) else None
                if found and found.group(1) == gold:
                    ids.add(item["id"].rsplit("/", 1)[-1])
        mapped[case] = ids
    return mapped


def build_cases(seeds: Sequence[Mapping[str, str]], manifest: Mapping[str, Any], predictions: Sequence[Mapping[str, str]], retrieval: Sequence[Mapping[str, str]],
                mapped: Mapping[str, set[str]], verified: Mapping[str, Mapping[str, Any]] | None = None, *, condition: str = "C1",
                policy: str = "selective_policy_v2") -> list[m.Case]:
    s = {r["case_id"]: r for r in seeds}
    primary = {c["case_id"]: c for c in manifest["cases"] if c.get("is_primary", True)}
    secondary = {c["case_id"] for c in manifest.get("secondary_cases", [])}
    missing = sorted(set(primary) - {r["case_id"] for r in predictions if r["condition"] == condition and r["policy"] == policy})
    if missing:
        raise AssemblyError(f"{len(missing)} primary cases have no prediction (first: {missing[0]})")
    unknown = sorted({r["case_id"] for r in predictions} - set(primary) - secondary)
    if unknown:
        raise AssemblyError(f"predictions for cases that are not in the manifest: {unknown[:3]}")
    block = {c: s[c]["source_block_id"] for c in s}
    stratum = {c: s[c]["sampling_stratum"] for c in s}
    for c, info in primary.items():
        if c not in s:
            raise AssemblyError(f"primary case {c} has no seed row")
        if stratum[c] != info["stratum"]:
            raise AssemblyError(f"stratum of {c} differs between seeds and manifest")
    groups = {c: info["case_eligible_groups"] for c, info in primary.items()}
    cases = m.cases_from_replay(predictions, retrieval, condition=condition, policy=policy, block_by_case=block, stratum_by_case=stratum,
                                mapped_by_case=mapped, group_by_case=groups)
    out = []
    for c in cases:
        fields = dict(verified.get(c.case_id, {})) if verified else {}
        bad = set(fields) - VERIFIED_KEYS
        if bad:
            raise AssemblyError(f"unexpected verified fields for {c.case_id}: {sorted(bad)}")
        if fields and c.case_id not in primary:
            raise AssemblyError(f"verified labels supplied for a secondary case {c.case_id}")
        base = {**c.__dict__, "is_primary": c.case_id in primary}
        out.append(m.Case(**{**base, **fields}))
    return out


def verification_status(cases: Sequence[m.Case]) -> dict[str, Any]:
    prim = [c for c in cases if c.is_primary]
    auto = [c for c in prim if c.outcome == "auto"]
    done = [c for c in auto if c.label_state is not None]
    audited = [c for c in prim if c.audit_subset == "audit_sample"]
    state = "pending" if not any(c.label_state for c in prim) else ("complete" if len(done) == len(auto) else "incomplete")
    return {"state": state, "n_primary": len(prim), "n_automatic": len(auto), "n_automatic_verified": len(done), "n_audit_sample_verified": len(audited)}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assemble_report(cases: Sequence[m.Case], manifest: Mapping[str, Any], settings: m.InferenceSettings, seed: int, provenance: Mapping[str, Any]) -> dict[str, Any]:
    frame = {s: n for s, n in manifest["frame_post_exclusion"].items() if n > 0}
    report = m.evaluate_primary(cases, frame, settings, seed)
    report["verification_status"] = verification_status(cases)
    report["provenance"] = dict(provenance)
    return report
