"""Capture ranked retrieval outputs from a sealed index snapshot without mutating it."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import platform
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from .evaluation_dataset import read_csv, sha256_file, sha256_tree, validate_dataset_manifest
except ImportError:  # Executed as `python scripts/capture_retrieval_predictions.py` from backend/.
    from evaluation_dataset import read_csv, sha256_file, sha256_tree, validate_dataset_manifest


async def capture_queries(query_rows: list[dict[str, str]], retrieve_fn: Callable[..., Awaitable[list[Any]]], *, index_path: Path, top_k: int) -> list[dict[str, Any]]:
    results = []
    for row in query_rows:
        started = time.perf_counter()
        hits = await retrieve_fn(row["query_text"], top_k=top_k, path=index_path)
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        results.append({
            "query_id": row["query_id"],
            "hits": [{"canonical_id": hit.canonical_id, "rank": rank, "score": hit.score} for rank, hit in enumerate(hits, 1)],
            "latency_ms": latency_ms,
        })
    return results


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _runtime_hash() -> str:
    versions = sorted((dist.metadata.get("Name", "").casefold(), dist.version) for dist in importlib.metadata.distributions())
    return hashlib.sha256(json.dumps(versions, separators=(",", ":")).encode("utf-8")).hexdigest()


async def capture_dataset(dataset_manifest: Path, output: Path, run_id: str, *, top_k: int = 5, minimum_queries: int = 100) -> dict[str, Any]:
    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")
    if not run_id.strip():
        raise ValueError("run_id must not be empty")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite retrieval predictions: {output}")
    data = validate_dataset_manifest(dataset_manifest, minimum_queries=minimum_queries, require_retrieval=True)
    manifest = data["manifest"]
    if top_k < max(manifest["retrieval_metric_k_values"]):
        raise ValueError("Captured top_k must be at least the maximum preregistered retrieval metric k")
    index_source = data["index_path"]
    index_hash = manifest["index_snapshot"]["sha256"]
    if sha256_tree(index_source) != index_hash:
        raise ValueError("Index snapshot changed after dataset validation")
    query_rows = read_csv(data["artifacts"]["retrieval_queries"], {"query_id", "query_text", "review_status"})
    if any(not row["query_text"].strip() or row["review_status"].strip() != "complete" for row in query_rows):
        raise ValueError("Retrieval queries must be fully annotated before prediction capture")
    from services.scholarly_retrieval import index_status, retrieve

    with tempfile.TemporaryDirectory(prefix="scholarly-retrieval-eval-") as temp_dir:
        disposable_index = Path(temp_dir) / "index"
        shutil.copytree(index_source, disposable_index)
        status = index_status(disposable_index)
        if status["status"] != "ready" or status["document_count"] != manifest["index_snapshot"]["document_count"] or status["index_version"] != manifest["index_snapshot"]["index_version"] or status["embedding_model"] != manifest["index_snapshot"]["embedding_model"]:
            raise ValueError("Disposable Chroma index does not match sealed manifest identifiers")
        query_predictions = await capture_queries(query_rows, retrieve, index_path=disposable_index, top_k=top_k)
    if sha256_tree(index_source) != index_hash:
        raise RuntimeError("Retrieval capture detected a changed source index snapshot")
    payload = {
        "evaluation_predictions_version": "retrieval-v1",
        "dataset_id": manifest["dataset_id"],
        "dataset_version": manifest["dataset_version"],
        "database_snapshot_sha256": manifest["database_snapshot"]["sha256"],
        "index_snapshot_sha256": index_hash,
        "index_version": manifest["index_snapshot"]["index_version"],
        "embedding_model": manifest["index_snapshot"]["embedding_model"],
        "retrieval_queries_sha256": sha256_file(data["artifacts"]["retrieval_queries"]),
        "retrieval_pool_sha256": sha256_file(data["artifacts"]["retrieval_pool"]),
        "retrieval_judgements_sha256": sha256_file(data["artifacts"]["retrieval_judgements"]),
        "retrieval_code_sha256": _file_hash(Path(__file__).resolve().parents[1] / "services" / "scholarly_retrieval.py"),
        "runtime_environment_sha256": _runtime_hash(),
        "python_version": platform.python_version(),
        "dataset_manifest_sha256": sha256_file(dataset_manifest),
        "run_id": run_id,
        "top_k": top_k,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "queries": query_predictions,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    return payload


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-manifest", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = await capture_dataset(args.dataset_manifest, args.output, args.run_id, top_k=args.top_k)
    print(f"Captured {len(payload['queries'])} queries from a disposable copy of the frozen index to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())