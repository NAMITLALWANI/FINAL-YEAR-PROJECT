"""Freeze a query-level split assignment and immutable test-membership hash."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from evaluation_dataset import SPLIT_FIELDS, read_csv, sha256_file, split_membership_sha256, unique_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--splits", type=Path, required=True)
    parser.add_argument("--split-version", required=True)
    parser.add_argument("--frozen-at", required=True, help="Timezone-aware ISO-8601 timestamp")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        timestamp = datetime.fromisoformat(args.frozen_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("--frozen-at must be an ISO-8601 timestamp") from exc
    if timestamp.tzinfo is None:
        raise ValueError("--frozen-at must include a timezone")
    if args.output.exists():
        raise FileExistsError(f"Refusing to replace split freeze record: {args.output}")
    labels = unique_rows(read_csv(args.labels, {"query_id", "gold_status", "gold_source", "gold_author_id"}), "query_id", args.labels)
    splits = unique_rows(read_csv(args.splits, SPLIT_FIELDS), "query_id", args.splits)
    if set(labels) != set(splits):
        raise ValueError("Split manifest query IDs must match identity labels exactly")
    group_split = {}
    author_group = {}

    for query_id, row in splits.items():
        if row["split_version"].strip() != args.split_version:
            raise ValueError(f"Unexpected split version for {query_id}")
        group = row["identity_group_id"].strip()
        split = row["split"].strip()
        if not group or split not in {"train", "development", "test"}:
            raise ValueError(f"Invalid split/group for {query_id}")
        if group_split.setdefault(group, split) != split:
            raise ValueError(f"Identity group {group!r} crosses data splits")
        label = labels[query_id]
        if label["gold_status"].strip() == "resolved":
            identity = (label["gold_source"].strip(), label["gold_author_id"].strip())
            if not all(identity) or author_group.setdefault(identity, group) != group:
                raise ValueError(f"Resolved author {identity!r} crosses identity groups")

    if {row["split"].strip() for row in splits.values()} != {"train", "development", "test"}:
        raise ValueError("Train, development, and test must all have members before freezing")
    record = {
        "membership_frozen": True,
        "frozen_at": args.frozen_at,
        "split_version": args.split_version,
        "split_manifest_sha256": sha256_file(args.splits),
        "test_membership_sha256": split_membership_sha256(list(splits.values())),
        "test_membership_count": sum(row["split"].strip() == "test" for row in splits.values()),
        "labels_sha256_at_freeze": sha256_file(args.labels),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
    print(f"Frozen split membership to {args.output}; test queries={record['test_membership_count']}")


if __name__ == "__main__":
    main()