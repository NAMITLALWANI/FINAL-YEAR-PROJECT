"""Small glue between pipeline stages (offline, pure): coverage counts from a replay for the sizing script, and the audit-frame CSV from a replay for the audit draw.

Both use only decision categories and the manifest's strata and primary-case list; neither reads a label or an ORCID."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .common import read_csv


class HelperError(ValueError):
    """Inconsistent inputs between a replay, its seeds and its manifest."""


def _rows(predictions: Path, condition: str, policy: str) -> dict[str, str]:
    rows = [r for r in read_csv(Path(predictions), {"case_id", "condition", "policy", "outcome"}) if r["condition"] == condition and r["policy"] == policy]
    out = {r["case_id"]: r["outcome"] for r in rows}
    if len(out) != len(rows):
        raise HelperError("more than one prediction row per case for this condition and policy")
    return out


def pilot_coverage_counts(predictions: Path, seeds: Path, *, condition: str, policy: str) -> dict[str, dict[str, int]]:
    """Per stratum: automatic assignments and pilot cases of the primary pair (the input of `size_hammer_main_sample.py`). Every seeded case must have a prediction."""
    outcomes = _rows(predictions, condition, policy)
    strata = {r["case_id"]: r["sampling_stratum"] for r in read_csv(Path(seeds), {"case_id", "sampling_stratum"})}
    missing = sorted(set(strata) - set(outcomes))
    if missing:
        raise HelperError(f"{len(missing)} seeded case(s) have no prediction row")
    counts: dict[str, dict[str, int]] = {}
    for cid, h in strata.items():
        d = counts.setdefault(h, {"automatic": 0, "cases": 0})
        d["cases"] += 1
        d["automatic"] += outcomes[cid] == "auto"
    return dict(sorted(counts.items()))


def audit_frame_rows(predictions: Path, seeds: Path, manifest: Mapping[str, Any], *, condition: str, policy: str) -> list[dict[str, str]]:
    """case_id, stratum, outcome for the PRIMARY cases of the manifest under the primary pair (the input of the audit draw)."""
    outcomes = _rows(predictions, condition, policy)
    strata = {r["case_id"]: r["sampling_stratum"] for r in read_csv(Path(seeds), {"case_id", "sampling_stratum"})}
    primary = [c["case_id"] for c in manifest["cases"]]
    missing = [c for c in primary if c not in outcomes or c not in strata]
    if missing:
        raise HelperError(f"{len(missing)} primary case(s) have no prediction or seed row")
    return [{"case_id": c, "stratum": strata[c], "outcome": outcomes[c]} for c in sorted(primary)]


def write_audit_frame(path: Path, rows: Sequence[Mapping[str, str]]) -> None:
    with open(path, "x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["case_id", "stratum", "outcome"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
