"""Shared helpers: hashing, canonical JSON, exclusive writes, CSV reading, constants."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONDITIONS = ("C0", "C1", "C1x")
POLICIES = ("forced_top1", "selective_policy_v2", "legacy_gates_plus_p3")
OUTCOMES = ("auto", "manual", "unresolved", "no_score", "provider_failed", "empty_pool")
ARMS = ("R0", "R2")
DOI_PURPOSES = ("gold_evidence", "query_context", "both")
VOLATILE_KEYS = {"retrieved_at", "captured_at"}
SECRET_PARAMS = {"api_key", "mailto"}


class PilotDataError(ValueError):
    """Invalid or inconsistent pilot input. Never repaired silently."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def write_text_exclusive(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8", newline="") as stream:
        stream.write(text)


def write_bytes_exclusive(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "xb") as stream:
        stream.write(data)


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    path = Path(path)
    if not path.is_file():
        raise PilotDataError(f"Missing file: {path.name}")
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise PilotDataError(f"{path.name} is missing columns: {sorted(missing)}")
        return [{k: (v or "") for k, v in row.items()} for row in reader]


def write_csv_exclusive(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: ("" if row.get(k) is None else row.get(k)) for k in fields})


def parse_ts(value: str, label: str = "timestamp") -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise PilotDataError(f"{label} is not an ISO-8601 timestamp: {value!r}") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def strip_volatile(obj: Any) -> Any:
    """Remove wall-clock fields so replay outputs are byte-identical across runs."""
    if isinstance(obj, dict):
        return {k: strip_volatile(v) for k, v in obj.items() if k not in VOLATILE_KEYS}
    if isinstance(obj, (list, tuple)):
        return [strip_volatile(v) for v in obj]
    return obj


def json_field(row: dict[str, str], key: str, case: str, default: Any = None) -> Any:
    text = (row.get(key) or "").strip()
    if not text:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise PilotDataError(f"{case}: {key} is not valid JSON") from exc
