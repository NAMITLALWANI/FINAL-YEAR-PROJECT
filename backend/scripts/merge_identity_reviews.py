"""Merge blinded independent reviews and adjudication into identity_labels.csv."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

try:
    from .evaluation_dataset import unique_rows
except ImportError:
    from evaluation_dataset import unique_rows


LABEL_FIELDS = [
    "query_id", "query_text", "context_json", "gold_status", "gold_source", "gold_author_id", "evidence_refs_json",
    "reviewer_1", "reviewer_1_status", "reviewer_1_confidence", "reviewer_1_rationale",
    "reviewer_2", "reviewer_2_status", "reviewer_2_confidence", "reviewer_2_rationale",
    "adjudicator", "adjudication_status", "adjudicated_confidence", "notes",
]


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        return list(reader)


def merge_reviews(queries_path: Path, review_1_path: Path, review_2_path: Path, adjudication_path: Path, output_path: Path) -> int:
    queries = load_rows(queries_path)
    query_map = unique_rows(queries, "query_id", queries_path)
    review_maps = []
    for slot, path in (("reviewer_1", review_1_path), ("reviewer_2", review_2_path)):
        rows = load_rows(path)
        by_id = unique_rows(rows, "query_id", path)
        if set(by_id) != set(query_map):
            raise ValueError(f"{slot} rows must cover the exact identity query set")
        if any(not row.get("reviewer_id", "").strip() for row in by_id.values()):
            raise ValueError(f"{slot} file contains a missing reviewer_id")
        reviewer_ids = {row["reviewer_id"].strip() for row in by_id.values()}
        if len(reviewer_ids) != 1:
            raise ValueError(f"{slot} file must be from exactly one reviewer")
        review_maps.append(by_id)
    adjudications = load_rows(adjudication_path)
    adjudication_map = unique_rows(adjudications, "query_id", adjudication_path) if adjudications else {}
    if not set(adjudication_map).issubset(query_map):
        raise ValueError("Adjudication file references an unknown query_id")
    output_rows = []
    for qid, query in query_map.items():
        first, second = review_maps[0][qid], review_maps[1][qid]
        if first.get("reviewer_id", "").strip() == second.get("reviewer_id", "").strip():
            raise ValueError(f"Two distinct reviewers are required for {qid}")


        for label, row in (("reviewer_1", first), ("reviewer_2", second)):
            if row.get("status") not in {"resolved", "unresolved", "uncertain"}:
                raise ValueError(f"{label} has invalid status for {qid}")
            if not row.get("rationale", "").strip():
                raise ValueError(f"{label} rationale is required for {qid}")
            try:
                confidence = int(row.get("confidence", ""))
                refs = json.loads(row.get("evidence_refs_json", ""))
            except (ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"{label} confidence/evidence is invalid for {qid}") from exc
            if confidence not in range(1, 6) or not isinstance(refs, list) or not refs:
                raise ValueError(f"{label} needs confidence 1-5 and evidence references for {qid}")
            if row["status"] == "resolved" and not (row.get("gold_source", "").strip() and row.get("gold_author_id", "").strip()):
                raise ValueError(f"Resolved {label} needs source-scoped ID for {qid}")
            if row["status"] != "resolved" and (row.get("gold_source", "").strip() or row.get("gold_author_id", "").strip()):
                raise ValueError(f"Non-resolved {label} must not include gold ID for {qid}")
        refs_1 = json.loads(first["evidence_refs_json"])
        refs_2 = json.loads(second["evidence_refs_json"])
        refs = refs_1 + refs_2
        reviewer_agree = all(first[k].strip() == second[k].strip() for k in ("status", "gold_source", "gold_author_id"))
        adjudication = adjudication_map.get(qid)
        if reviewer_agree:
            if adjudication:
                raise ValueError(f"Do not adjudicate an agreed query: {qid}")
            status = first["status"].strip()
            decision_state = "uncertain" if status == "uncertain" else "agreed"
            final_source, final_id = first.get("gold_source", "").strip(), first.get("gold_author_id", "").strip()
            confidence = min(int(first["confidence"]), int(second["confidence"]))
            adjudicator = ""
            notes = ""
        else:
            if not adjudication:
                raise ValueError(f"Disagreement requires adjudication or an explicit uncertain adjudication: {qid}")
            status = adjudication.get("status", "").strip()
            if status not in {"resolved", "unresolved", "uncertain"} or not adjudication.get("rationale", "").strip():
                raise ValueError(f"Adjudication needs valid status and rationale for {qid}")
            if not adjudication.get("adjudicator_id", "").strip() or adjudication["adjudicator_id"].strip() in {first["reviewer_id"], second["reviewer_id"]}:
                raise ValueError(f"Adjudicator must be named and distinct from reviewers for {qid}")
            try:
                confidence = int(adjudication.get("confidence", ""))
                adjudication_refs = json.loads(adjudication.get("evidence_refs_json", ""))
            except (ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"Invalid adjudication confidence/evidence for {qid}") from exc
            if confidence not in range(1, 6) or not isinstance(adjudication_refs, list) or not adjudication_refs:
                raise ValueError(f"Adjudication needs confidence 1-5 and evidence references for {qid}")
            final_source = adjudication.get("gold_source", "").strip()
            final_id = adjudication.get("gold_author_id", "").strip()
            if status == "resolved" and not (final_source and final_id):
                raise ValueError(f"Resolved adjudication needs source-scoped ID for {qid}")
            if status != "resolved" and (final_source or final_id):
                raise ValueError(f"Non-resolved adjudication must not include gold ID for {qid}")
            refs += adjudication_refs
            decision_state = "uncertain" if status == "uncertain" else "adjudicated"
            adjudicator = adjudication["adjudicator_id"].strip()
            notes = adjudication["rationale"].strip()
        output_rows.append({
            "query_id": qid, "query_text": query["query_text"].strip(), "context_json": query["context_json"].strip(),
            "gold_status": status, "gold_source": final_source, "gold_author_id": final_id,
            "evidence_refs_json": json.dumps(refs, ensure_ascii=False),
            "reviewer_1": first["reviewer_id"].strip(), "reviewer_1_status": first["status"].strip(),
            "reviewer_1_confidence": first["confidence"].strip(), "reviewer_1_rationale": first["rationale"].strip(),
            "reviewer_2": second["reviewer_id"].strip(), "reviewer_2_status": second["status"].strip(),
            "reviewer_2_confidence": second["confidence"].strip(), "reviewer_2_rationale": second["rationale"].strip(),
            "adjudicator": adjudicator, "adjudication_status": decision_state, "adjudicated_confidence": str(confidence), "notes": notes,
        })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=LABEL_FIELDS)
        writer.writeheader()
        writer.writerows(output_rows)
    return len(output_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--review-1", type=Path, required=True)
    parser.add_argument("--review-2", type=Path, required=True)
    parser.add_argument("--adjudication", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = merge_reviews(args.queries, args.review_1, args.review_2, args.adjudication, args.output)
    print(f"Merged {count} reviewed queries into {args.output}")


if __name__ == "__main__":
    main()