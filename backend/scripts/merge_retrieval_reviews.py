"""Merge blinded relevance reviews/adjudication into retrieval_relevance.csv."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

FIELDS = ["query_id", "canonical_publication_id", "relevance", "reviewer_1", "reviewer_1_relevance", "reviewer_2", "reviewer_2_relevance", "adjudicator", "adjudicated_relevance", "adjudication_status", "evidence_note"]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        return list(reader)


def merge_reviews(pool_path: Path, review_1_path: Path, review_2_path: Path, adjudication_path: Path, output_path: Path) -> int:
    pool = rows(pool_path)
    pair_keys = [(r["query_id"].strip(), r["canonical_publication_id"].strip()) for r in pool]
    if not pair_keys or len(pair_keys) != len(set(pair_keys)):
        raise ValueError("Frozen pool must contain unique query/publication pairs")
    maps = []
    for path in (review_1_path, review_2_path):
        review_rows = rows(path)
        keyed = {(r.get("query_id", "").strip(), r.get("canonical_publication_id", "").strip()): r for r in review_rows}
        if len(keyed) != len(review_rows) or set(keyed) != set(pair_keys):
            raise ValueError("Each reviewer must submit exactly one judgment for every pooled pair")
        reviewer_ids = {r.get("reviewer_id", "").strip() for r in keyed.values()}
        if len(reviewer_ids) != 1 or not next(iter(reviewer_ids)):
            raise ValueError("Each review file must identify exactly one reviewer")
        maps.append(keyed)
    adjudication_rows = rows(adjudication_path)
    adjudication_map = {(r.get("query_id", "").strip(), r.get("canonical_publication_id", "").strip()): r for r in adjudication_rows}
    if len(adjudication_map) != len(adjudication_rows) or not set(adjudication_map).issubset(pair_keys):
        raise ValueError("Adjudication rows must be unique members of the frozen pool")
    output = []
    for pair in pair_keys:
        a, b = maps[0][pair], maps[1][pair]
        reviewer_1, reviewer_2 = a["reviewer_id"].strip(), b["reviewer_id"].strip()
        if reviewer_1 == reviewer_2:
            raise ValueError(f"Two distinct reviewers are required for {pair}")
        grades = [a.get("relevance", "").strip(), b.get("relevance", "").strip()]
        if any(g not in {"0", "1", "2"} for g in grades) or any(not r.get("evidence_note", "").strip() for r in (a, b)):
            raise ValueError(f"Both reviewers need a valid grade and evidence note for {pair}")
        adjudication = adjudication_map.get(pair)
        if grades[0] == grades[1]:
            if adjudication:
                raise ValueError(f"Do not adjudicate an agreed relevance pair: {pair}")
            final, adjudicator, adjudicated, state = grades[0], "", "", "agreed"
            evidence = f"Reviewer 1: {a['evidence_note'].strip()} Reviewer 2: {b['evidence_note'].strip()}"
        else:
            if not adjudication:
                raise ValueError(f"Relevance disagreement requires adjudication: {pair}")
            final = adjudication.get("relevance", "").strip()
            adjudicator = adjudication.get("adjudicator_id", "").strip()
            if final not in {"0", "1", "2"} or not adjudicator or adjudicator in {reviewer_1, reviewer_2} or not adjudication.get("evidence_note", "").strip():
                raise ValueError(f"Invalid adjudication for {pair}")
            adjudicated, state = final, "adjudicated"
            evidence = f"Reviewer 1: {a['evidence_note'].strip()} Reviewer 2: {b['evidence_note'].strip()} Adjudicator: {adjudication['evidence_note'].strip()}"
        output.append({"query_id": pair[0], "canonical_publication_id": pair[1], "relevance": final, "reviewer_1": reviewer_1, "reviewer_1_relevance": grades[0], "reviewer_2": reviewer_2, "reviewer_2_relevance": grades[1], "adjudicator": adjudicator, "adjudicated_relevance": adjudicated, "adjudication_status": state, "evidence_note": evidence})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output)
    return len(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--review-1", type=Path, required=True)
    parser.add_argument("--review-2", type=Path, required=True)
    parser.add_argument("--adjudication", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(f"Merged {merge_reviews(args.pool, args.review_1, args.review_2, args.adjudication, args.output)} relevance judgments")


if __name__ == "__main__":
    main()