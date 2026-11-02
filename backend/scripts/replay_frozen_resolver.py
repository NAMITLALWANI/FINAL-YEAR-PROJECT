"""Read-only V1 replay against the candidate and database snapshots in a dataset manifest."""
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import (
    AUTHOR_AUTO_DOMINANCE_THRESHOLD, AUTHOR_AUTO_MARGIN_THRESHOLD, AUTHOR_AUTO_SCORE_THRESHOLD,
    AUTHOR_MANUAL_SCORE_THRESHOLD, AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO, AUTHOR_RESOLVER_VERSION,
    AUTHOR_SCORING_VERSION, AUTHOR_SCORE_WEIGHTS, AUTHOR_THRESHOLD_VERSION,
)
from database import AuthorCandidate
try:
    from .evaluation_dataset import read_csv, sha256_file, unique_rows, validate_dataset_manifest
except ImportError:  # Executed as `python scripts/replay_frozen_resolver.py` from backend/.
    from evaluation_dataset import read_csv, sha256_file, unique_rows, validate_dataset_manifest
from services.author_candidates import OpenAlexCandidate, normalize_name
from services.author_resolution import decide, rank_candidates


def _candidate_snapshot_hash(records: list[dict[str, Any]]) -> str:
    content = json.dumps(records, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _scoring_config_hash() -> str:
    payload = {
        "weights": AUTHOR_SCORE_WEIGHTS,
        "auto_score": AUTHOR_AUTO_SCORE_THRESHOLD,
        "auto_margin": AUTHOR_AUTO_MARGIN_THRESHOLD,
        "auto_dominance": AUTHOR_AUTO_DOMINANCE_THRESHOLD,
        "manual_score": AUTHOR_MANUAL_SCORE_THRESHOLD,
        "minimum_signals": AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _resolver_code_hash() -> str:
    digest = hashlib.sha256()
    paths = [
        BACKEND_DIR / "config.py",
        BACKEND_DIR / "database.py",
        BACKEND_DIR / "services" / "author_candidates.py",
        BACKEND_DIR / "services" / "author_evidence.py",
        BACKEND_DIR / "services" / "author_scoring.py",
        BACKEND_DIR / "services" / "author_resolution.py",
    ]
    for path in paths:
        digest.update(path.relative_to(BACKEND_DIR).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _runtime_environment_hash() -> str:
    packages = sorted((dist.metadata.get("Name", "").casefold(), dist.version) for dist in importlib.metadata.distributions())
    return hashlib.sha256(json.dumps(packages, separators=(",", ":")).encode("utf-8")).hexdigest()


async def replay_rows(session: AsyncSession, rows: list[dict[str, str]], *, dataset_id: str, dataset_version: str, split_version: str, dataset_manifest_sha256: str, database_sha256: str, index_sha256: str, candidate_manifest_sha256: str, run_id: str) -> list[dict[str, str]]:
    query_ids = [row["query_id"].strip() for row in rows]
    if any(not value for value in query_ids) or len(query_ids) != len(set(query_ids)):
        raise ValueError("Frozen candidate manifest query IDs must be non-empty and unique")
    scoring_config_hash = _scoring_config_hash()
    resolver_code_hash = _resolver_code_hash()
    runtime_environment_hash = _runtime_environment_hash()
    python_version = platform.python_version()
    predictions = []
    for row in rows:
        query_id = row["query_id"].strip()
        query_text = row["query_text"].strip()
        try:
            context = json.loads(row["context_json"])
            candidate_ids = json.loads(row["candidate_ids_json"])
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid candidate/context JSON for {query_id}") from exc
        if not query_text or not isinstance(context, dict) or not isinstance(candidate_ids, list) or any(not isinstance(value, str) or not value.strip() for value in candidate_ids):
            raise ValueError(f"Invalid query/context/candidate IDs for {query_id}")
        source_status = row["candidate_source_status"].strip()
        source_error_code = row["candidate_source_error_code"].strip()
        if source_status not in {"ok", "empty", "failed"} or (source_status == "ok") != bool(candidate_ids) or (source_status != "failed" and source_error_code) or (source_status == "failed" and not source_error_code):
            raise ValueError(f"Candidate source status, error code, and snapshot IDs disagree for {query_id}")
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError(f"Duplicate candidate snapshot ID for {query_id}")
        if candidate_ids:
            records = (await session.execute(select(AuthorCandidate).where(AuthorCandidate.id.in_(candidate_ids)))).scalars().all()
            found = {record.id: record for record in records}
            missing = set(candidate_ids) - found.keys()
            if missing:
                raise ValueError(f"Candidate snapshots missing from the frozen database for {query_id}: {sorted(missing)}")
            if any(found[candidate_id].query_normalized != normalize_name(query_text) for candidate_id in candidate_ids):
                raise ValueError(f"Candidate snapshot belongs to a different normalized query: {query_id}")
        else:
            found = {}
        snapshot_rows = []
        candidates = []
        for candidate_id in candidate_ids:
            source_row = found[candidate_id]
            snapshot_rows.append({
                "id": source_row.id,
                "source": source_row.source,
                "source_author_id": source_row.source_author_id,
                "raw_payload_json": source_row.raw_payload_json,
                "retrieved_at": source_row.retrieved_at.isoformat() if source_row.retrieved_at else None,
            })
            candidates.append(OpenAlexCandidate.from_persisted(source_row))
        ranked = rank_candidates(candidates, context)
        if source_status == "failed":
            status, top_score, second_score, margin, dominance, reason = "candidate_source_failed", None, None, None, None, f"Frozen candidate source failure: {source_error_code}."
        else:
            status, top_score, second_score, margin, dominance, reason = decide(ranked)
        selected = ranked[0].candidate if status == "auto_selected" and ranked else None
        top = ranked[0].candidate if ranked else None
        predictions.append({
            "query_id": query_id,
            "predicted_status": status,
            "selected_source": selected.source if selected else "",
            "selected_author_id": selected.source_author_id if selected else "",
            "top_source": top.source if top else "",
            "top_author_id": top.source_author_id if top else "",
            "resolver_version": AUTHOR_RESOLVER_VERSION,
            "scoring_version": AUTHOR_SCORING_VERSION,
            "threshold_version": AUTHOR_THRESHOLD_VERSION,
            "scoring_config_sha256": scoring_config_hash,
            "resolver_code_sha256": resolver_code_hash,
            "runtime_environment_sha256": runtime_environment_hash,
            "python_version": python_version,
            "dataset_id": dataset_id,
            "dataset_version": dataset_version,
            "split_version": split_version,
            "dataset_manifest_sha256": dataset_manifest_sha256,
            "database_snapshot_sha256": database_sha256,
            "index_snapshot_sha256": index_sha256,
            "candidate_manifest_sha256": candidate_manifest_sha256,
            "candidate_snapshot_sha256": _candidate_snapshot_hash(snapshot_rows),
            "candidate_source_status": source_status,
            "candidate_source_error_code": source_error_code,
            "candidate_count": str(len(candidates)),
            "top_score": "" if top_score is None else str(top_score),
            "second_score": "" if second_score is None else str(second_score),
            "score_margin": "" if margin is None else str(margin),
            "dominance_ratio": "" if dominance is None else str(dominance),
            "decision_reason": reason,
            "run_id": run_id,
        })
    return predictions


async def replay_dataset(dataset_manifest: Path, output: Path, run_id: str, *, minimum_queries: int = 100) -> int:
    if not run_id.strip():
        raise ValueError("run_id must not be empty")
    validated = validate_dataset_manifest(dataset_manifest, minimum_queries=minimum_queries)
    manifest = validated["manifest"]
    artifact = validated["artifacts"]["candidate_manifest"]
    rows = read_csv(artifact, {"query_id", "query_text", "context_json", "candidate_source_status", "candidate_source_error_code", "candidate_ids_json"})
    candidate_rows = unique_rows(rows, "query_id", artifact)
    labels = read_csv(validated["artifacts"]["identity_labels"], {"query_id"})
    if set(candidate_rows) != {row["query_id"].strip() for row in labels}:
        raise ValueError("Frozen candidate manifest must contain every labelled query exactly once")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite prediction artifact: {output}")
    database_sha256 = manifest["database_snapshot"]["sha256"]
    index_sha256 = manifest["index_snapshot"]["sha256"]
    if sha256_file(validated["database_path"]) != database_sha256:
        raise ValueError("Database snapshot changed after manifest validation")
    url = URL.create(
        "sqlite+aiosqlite",
        database=f"file:{validated['database_path']}",
        query={"mode": "ro", "immutable": "1", "uri": "true"},
    )
    engine = create_async_engine(url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_factory() as session:
            predictions = await replay_rows(
                session, rows,
                dataset_id=manifest["dataset_id"],
                dataset_version=manifest["dataset_version"],
                split_version=validated["annotations"]["split_version"],
                dataset_manifest_sha256=sha256_file(dataset_manifest),
                database_sha256=database_sha256,
                index_sha256=index_sha256,
                candidate_manifest_sha256=sha256_file(artifact),
                run_id=run_id,
            )
        if sha256_file(validated["database_path"]) != database_sha256:
            raise RuntimeError("Read-only replay detected a changed database snapshot")
        output.parent.mkdir(parents=True, exist_ok=True)
        fields = list(predictions[0]) if predictions else []
        with output.open("x", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(predictions)
        return len(predictions)
    finally:
        await engine.dispose()


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-manifest", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = await replay_dataset(args.dataset_manifest, args.output, args.run_id)
    print(f"Replayed {count} frozen queries to {args.output}; database access was read-only")


if __name__ == "__main__":
    asyncio.run(main())