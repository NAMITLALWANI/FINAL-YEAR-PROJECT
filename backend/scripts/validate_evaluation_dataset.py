"""Validate a sealed, immutable evaluation dataset without writing to it."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation_dataset import validate_dataset_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-manifest", type=Path, required=True)
    parser.add_argument("--require-retrieval", action="store_true")
    args = parser.parse_args()
    report = validate_dataset_manifest(args.dataset_manifest, require_retrieval=args.require_retrieval)
    print(json.dumps({
        "dataset_id": report["manifest"]["dataset_id"],
        "dataset_version": report["manifest"]["dataset_version"],
        "database_snapshot_sha256": report["manifest"]["database_snapshot"]["sha256"],
        "index_snapshot_sha256": report["manifest"]["index_snapshot"]["sha256"],
        "annotations": report["annotations"],
        "retrieval_query_count": report["retrieval_query_count"],
        "candidate_query_count": report["candidate_query_count"],
        "valid": True,
    }, indent=2))


if __name__ == "__main__":
    main()