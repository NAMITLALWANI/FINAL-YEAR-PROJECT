"""Evaluation freeze manifest (T015): records the code, configuration, parameters and derived seeds before any provider capture.

The manifest is written once and never overwritten. Seeds are derived, not chosen: the first 8 hex digits of SHA-256("HAMMER|<role>|<freeze id>")
read as an integer, so no favourable seed can be selected. `verify_freeze` re-hashes the frozen files and reports every difference.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

SEED_ROLES = ("pilot", "main", "audit", "packets")
OVERRIDE_PREFIXES = ("AUTHOR_", "ENABLE_AUTHOR_", "DEDUP_")


class FreezeError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def derive_seed(role: str, freeze_id: str) -> int:
    if role not in SEED_ROLES:
        raise FreezeError(f"unknown seed role {role!r}")
    if not freeze_id or "|" in freeze_id:
        raise FreezeError("freeze id must be non-empty and contain no '|'")
    return int(hashlib.sha256(f"HAMMER|{role}|{freeze_id}".encode()).hexdigest()[:8], 16)


def override_env(env: Mapping[str, str]) -> list[str]:
    return sorted(k for k in env if k.startswith(OVERRIDE_PREFIXES))


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def build_freeze(repo: Path, freeze_id: str, files: Sequence[str], effective_config: Mapping[str, Any], params: Mapping[str, Any],
                 env: Mapping[str, str], git: Callable[..., str] = _git) -> dict[str, Any]:
    bad = override_env(env)
    if bad:
        raise FreezeError(f"configuration environment overrides are set: {bad}")
    if not files:
        raise FreezeError("no files to freeze")
    hashes = {}
    for rel in sorted(set(files)):
        p = repo / rel
        if not p.is_file():
            raise FreezeError(f"frozen file missing: {rel}")
        hashes[rel] = sha256_file(p)
    status = git(repo, "status", "--porcelain")
    manifest = {
        "freeze_id": freeze_id,
        "git_head": git(repo, "rev-parse", "HEAD").strip(),
        "git_branch": git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip(),
        "working_tree_dirty": bool(status.strip()),
        "git_status_porcelain_sha256": hashlib.sha256(status.encode()).hexdigest(),
        "frozen_file_sha256": hashes,
        "effective_config": dict(effective_config),
        "effective_config_sha256": hashlib.sha256(canonical(dict(effective_config)).encode()).hexdigest(),
        "parameters": dict(params),
        "parameters_sha256": hashlib.sha256(canonical(dict(params)).encode()).hexdigest(),
        "seeds": {r: derive_seed(r, freeze_id) for r in SEED_ROLES},
        "seed_rule": "int(sha256('HAMMER|<role>|<freeze id>')[:8], 16)",
        "environment_overrides_present": [],
    }
    manifest["manifest_sha256"] = hashlib.sha256(canonical(manifest).encode()).hexdigest()
    return manifest


def verify_freeze(manifest: Mapping[str, Any], repo: Path) -> list[str]:
    """Return a list of human-readable differences; empty means the frozen files, config and seeds are unchanged."""
    problems = []
    body = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    if hashlib.sha256(canonical(body).encode()).hexdigest() != manifest.get("manifest_sha256"):
        problems.append("manifest content does not match its own hash")
    for rel, want in manifest["frozen_file_sha256"].items():
        p = repo / rel
        if not p.is_file():
            problems.append(f"missing: {rel}")
        elif sha256_file(p) != want:
            problems.append(f"changed: {rel}")
    for role, seed in manifest["seeds"].items():
        if derive_seed(role, manifest["freeze_id"]) != seed:
            problems.append(f"seed {role} is not the derived value")
    if hashlib.sha256(canonical(manifest["effective_config"]).encode()).hexdigest() != manifest["effective_config_sha256"]:
        problems.append("effective configuration hash mismatch")
    return problems
