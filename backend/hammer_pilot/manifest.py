"""Reproducible run manifest: no wall-clock fields, so identical inputs give a byte-identical manifest."""
from __future__ import annotations

import importlib.metadata
import platform
import subprocess
from pathlib import Path
from typing import Any

import config
from hammer_pilot.common import canonical_json, sha256_bytes, sha256_file

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
POLICY_VERSION = "selective_policy_v2 / legacy_gates_plus_p3 / forced_top1"
KNOWN_DEVIATIONS = [
    "Ranking orders candidates by a per-candidate renormalised heuristic score; candidates scored on different signal sets are not directly comparable (also for forced_top1).",
    "R0 and R2 primary requests are identical when query normalisation changes nothing; the capture stores that response once and shares it.",
    "Institution comparison is token-sort (provisional), not the original token-set protocol wording; exact OpenAlex/ROR IDs are preferred when supplied.",
    "legacy_gates_plus_p3 is computed from the policy-v2 outcome's threshold-gate result (P0-P3, P9, P10); P4-P8 are not applied.",
    "Scores are heuristic, not calibrated probabilities. No coverage floor or minimum automatic count is applied.",
    "C0 automatic coverage is zero by design for policies requiring >= 2 signals and P5 corroboration.",
]


def git_state() -> dict[str, Any]:
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()
        status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return {"git_sha": None, "working_tree_clean": None, "git_status_sha256": None}
    return {"git_sha": sha, "working_tree_clean": status.strip() == "", "git_status_sha256": sha256_bytes(status.encode("utf-8"))}


def _hash_dir(path: Path, pattern: str, root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha256_file(p) for p in sorted(path.glob(pattern))}


def logical_arm_records(pilot_dir: Path) -> dict[str, Any]:
    """Every logical request (R0, R2 primary, R2 fallback) with its physical response path and SHA-256.

    Identical R0/R2 requests share ONE physical response; both logical records point at it.
    """
    import json
    records = []
    for path in sorted((Path(pilot_dir) / "captures" / "cases").glob("*.json")):
        summary = json.loads(path.read_text(encoding="utf-8"))
        parts = [("R0", "R0", summary["R0"]), ("R2", "R2_primary", summary["R2_primary"]), ("R2", "R2_fallback", summary["R2_fallback"])]
        for arm, role, part in parts:
            if not part:
                continue
            twins = [r for a, r, p in parts if p and r != role and p["seq"] == part["seq"]]
            records.append({"case_id": summary["case_id"], "arm": arm, "role": role, "seq": part["seq"], "body_file": part.get("body_file"),
                            "sha256": part["sha256"], "http_status": part["http_status"], "status": part["status"], "shares_response_with": twins})
    physical = {r["seq"] for r in records}
    return {"logical_requests": records, "logical_request_count": len(records), "physical_response_count": len(physical)}


def build_manifest(pilot_dir: Path, *, git: dict[str, Any] | None = None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    pilot_dir = Path(pilot_dir)
    cap = pilot_dir / "captures"
    inputs = {n: sha256_file(pilot_dir / n) for n in ("seeds.csv", "doi_register.csv", "seed_freeze.json", "review_a.csv", "review_b.csv", "stage_a.csv", "stage_b.csv",
                                                       "development_exclusions.csv") if (pilot_dir / n).is_file()}
    captures = {p.relative_to(pilot_dir).as_posix(): sha256_file(p) for p in sorted(cap.rglob("*")) if p.is_file()}
    packages = {}
    for name in ("httpx", "rapidfuzz", "sqlalchemy", "pydantic", "fastapi"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    manifest = {
        **(git or git_state()),
        "python_version": platform.python_version(),
        "package_versions": packages,
        "effective_weights": dict(config.AUTHOR_SCORE_WEIGHTS),
        "effective_thresholds": {"automatic": config.AUTHOR_AUTO_SCORE_THRESHOLD, "margin": config.AUTHOR_AUTO_MARGIN_THRESHOLD,
                                 "dominance": config.AUTHOR_AUTO_DOMINANCE_THRESHOLD, "manual": config.AUTHOR_MANUAL_SCORE_THRESHOLD,
                                 "minimum_signals": config.AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO},
        "enrichment_bounds": {"per_page": config.AUTHOR_ENRICHMENT_WORKS_PER_PAGE, "max_pages": config.AUTHOR_ENRICHMENT_MAX_PAGES},
        "policy_version": POLICY_VERSION,
        "dataset_version": _dataset_version(pilot_dir),
        "input_hashes": inputs,
        "capture_hashes": captures,
        **logical_arm_records(pilot_dir),
        "author_resolution_source_hashes": _hash_dir(BACKEND / "author_resolution", "*.py", BACKEND),
        "config_hash": sha256_file(BACKEND / "config.py"),
        "evaluator_source_hashes": _hash_dir(BACKEND / "hammer_pilot", "*.py", BACKEND),
        "known_deviations": KNOWN_DEVIATIONS,
        **(extra or {}),
    }
    return manifest


def _dataset_version(pilot_dir: Path) -> str | None:
    import json
    p = pilot_dir / "seed_freeze.json"
    return json.loads(p.read_text(encoding="utf-8")).get("dataset_version") if p.is_file() else None


def manifest_text(manifest: dict[str, Any]) -> str:
    import json
    return json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
