"""Compute reproducible identity-baseline and retrieval metrics from frozen annotations."""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any

try:
    from .evaluation_dataset import read_csv, sha256_file, unique_rows, validate_dataset_manifest
except ImportError:  # Executed as `python scripts/evaluate_benchmark.py` from backend/.
    from evaluation_dataset import read_csv, sha256_file, unique_rows, validate_dataset_manifest


PREDICTION_STATUSES = {"auto_selected", "manual_selected", "manual_selection_required", "unresolved", "candidate_source_failed"}


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _identity_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    included = [row for row in rows if row["gold_status"].strip() in {"resolved", "unresolved"}]
    uncertain = len(rows) - len(included)
    resolved = [row for row in included if row["gold_status"].strip() == "resolved"]
    auto = [row for row in included if row["predicted_status"].strip() == "auto_selected"]
    manual = [row for row in included if row["predicted_status"].strip() == "manual_selected"]
    review = [row for row in included if row["predicted_status"].strip() == "manual_selection_required"]
    unresolved = [row for row in included if row["predicted_status"].strip() == "unresolved"]
    failed = [row for row in included if row["predicted_status"].strip() == "candidate_source_failed"]

    def same_target(row: dict[str, str], prefix: str) -> bool:
        return (
            row.get("gold_status", "").strip() == "resolved"
            and bool(row.get("gold_author_id", "").strip())
            and row.get(f"{prefix}_source", "").strip() == row.get("gold_source", "").strip()
            and row.get(f"{prefix}_author_id", "").strip() == row.get("gold_author_id", "").strip()
        )

    correct_auto = sum(same_target(row, "selected") for row in auto)
    correct_manual = sum(same_target(row, "selected") for row in manual)
    correct_top1 = sum(same_target(row, "top") for row in resolved)
    gold_unresolved_n = sum(row["gold_status"].strip() == "unresolved" for row in included)
    correctly_unresolved = sum(row["gold_status"].strip() == "unresolved" for row in unresolved)
    n = len(included)
    abstentions = len(review) + len(unresolved) + len(failed)
    return {
        "labelled_queries": n,
        "excluded_uncertain_queries": uncertain,
        "gold_resolved_queries": len(resolved),
        "gold_unresolved_queries": gold_unresolved_n,
        "automatic_decision_count": len(auto),
        "automatic_correct_count": correct_auto,
        "auto_accuracy": _ratio(correct_auto, len(auto)),
        "false_merge_count": len(auto) - correct_auto,
        "false_merge_rate_among_auto": _ratio(len(auto) - correct_auto, len(auto)),
        "auto_coverage": _ratio(len(auto), n),
        "resolved_target_automatic_recall": _ratio(correct_auto, len(resolved)),
        "top1_correct_count": correct_top1,
        "top1_candidate_accuracy_on_resolved": _ratio(correct_top1, len(resolved)),
        "manual_review_count": len(review),
        "manual_review_rate": _ratio(len(review), n),
        "manual_selection_count": len(manual),
        "manual_selection_accuracy": _ratio(correct_manual, len(manual)),
        "unresolved_count": len(unresolved),
        "unresolved_rate": _ratio(len(unresolved), n),
        "unresolved_recall_on_gold_unresolved": _ratio(correctly_unresolved, gold_unresolved_n),
        "candidate_source_failure_count": len(failed),
        "abstention_count": abstentions,
        "abstention_rate": _ratio(abstentions, n),
        "denominators": {
            "selective_accuracy": "automatic decisions",
            "auto_coverage": "all resolved and unresolved gold queries; uncertain excluded",
            "resolved_target_automatic_recall": "all gold resolved queries; incorrect or abstaining decisions are misses",
            "top1_candidate_accuracy_on_resolved": "all gold resolved queries; missing/wrong top candidate is a miss",
            "manual_review_rate": "all resolved and unresolved gold queries; uncertain excluded",
            "unresolved_recall_on_gold_unresolved": "all gold unresolved queries",
            "abstention_rate": "manual review + unresolved + candidate-source failure over resolved and unresolved gold queries",
        },
    }


def evaluate_identity(labels_path: Path, predictions_path: Path, splits_path: Path | None = None) -> dict[str, Any]:
    labels = unique_rows(read_csv(labels_path, {"query_id", "gold_status", "gold_source", "gold_author_id"}), "query_id", labels_path)
    predictions = unique_rows(read_csv(predictions_path, {"query_id", "predicted_status"}), "query_id", predictions_path)
    if set(labels) != set(predictions):
        missing = sorted(set(labels) - set(predictions))
        extra = sorted(set(predictions) - set(labels))
        raise ValueError(f"Identity prediction coverage mismatch; missing={missing}, extra={extra}")
    joined = []
    for query_id, label in labels.items():
        pred = predictions[query_id]
        status = pred["predicted_status"].strip()
        if status not in PREDICTION_STATUSES:
            raise ValueError(f"Invalid predicted_status for {query_id}: {status!r}")
        if status in {"auto_selected", "manual_selected"} and (not pred.get("selected_source", "").strip() or not pred.get("selected_author_id", "").strip()):
            raise ValueError(f"Selected outcome {query_id} is missing selected source/author ID")
        if not label["gold_status"].strip() in {"resolved", "unresolved", "uncertain"}:
            raise ValueError(f"Invalid gold_status for {query_id}")
        joined.append({**label, **pred})
    split_hash = None
    split_groups: dict[str, list[dict[str, str]]] | None = None
    if splits_path:
        split_rows = unique_rows(read_csv(splits_path, {"query_id", "identity_group_id", "split", "split_version"}), "query_id", splits_path)
        if set(split_rows) != set(labels):
            raise ValueError("Split manifest query IDs must match identity labels exactly")
        by_identity: dict[tuple[str, str], str] = {}
        by_group: dict[str, str] = {}

        for query_id, split_row in split_rows.items():
            split = split_row["split"].strip()
            group = split_row["identity_group_id"].strip()
            if split not in {"train", "development", "test"} or not group or not split_row["split_version"].strip():
                raise ValueError(f"Invalid split assignment for {query_id}")
            previous = by_group.setdefault(group, split)
            if previous != split:
                raise ValueError(f"Identity groups cross data splits: {group}")
            label = labels[query_id]
            if label.get("gold_status", "").strip() == "resolved":
                key = (label.get("gold_source", "").strip(), label.get("gold_author_id", "").strip())
                if not all(key):
                    raise ValueError(f"Resolved label {query_id} has no source-scoped author ID")
                prior_group = by_identity.setdefault(key, group)
                if prior_group != group:
                    raise ValueError(f"Verified author {key!r} appears in multiple identity groups")

        for row in joined:
            row["split"] = split_rows[row["query_id"]]["split"].strip()
        groups = {"all": joined, **{split: [row for row in joined if row["split"] == split] for split in ("train", "development", "test")}}
        split_hash = sha256_file(splits_path)
    versions = {field: sorted({row.get(field, "").strip() for row in predictions.values() if row.get(field, "").strip()}) for field in ("resolver_version", "scoring_version", "threshold_version", "scoring_config_sha256", "resolver_code_sha256", "runtime_environment_sha256", "python_version", "run_id", "dataset_id", "dataset_version", "dataset_manifest_sha256", "database_snapshot_sha256", "index_snapshot_sha256")}
    return {
        "evaluation": "identity_baseline_v1",
        "inputs": {"labels_sha256": sha256_file(labels_path), "predictions_sha256": sha256_file(predictions_path), "splits_sha256": split_hash},
        "versions": versions,
        "metrics_by_split": {name: _identity_metrics(rows) for name, rows in groups.items()},
        "warning": "Only independently adjudicated resolved/unresolved labels belong in primary metrics. This baseline does not measure retrieval or explanation quality.",
    }


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))], 3)


def _validate_identity_prediction_snapshot(path: Path, dataset: dict[str, Any], split_version: str, dataset_manifest_sha256: str) -> None:
    rows = read_csv(path, {"query_id", "predicted_status", "dataset_id", "dataset_version", "split_version", "dataset_manifest_sha256", "database_snapshot_sha256", "index_snapshot_sha256", "candidate_manifest_sha256", "candidate_snapshot_sha256", "scoring_config_sha256", "resolver_code_sha256", "runtime_environment_sha256", "python_version", "run_id"})
    expected = {
        "dataset_id": dataset["dataset_id"],
        "dataset_version": dataset["dataset_version"],
        "split_version": split_version,
        "dataset_manifest_sha256": dataset_manifest_sha256,
        "database_snapshot_sha256": dataset["database_snapshot"]["sha256"],
        "index_snapshot_sha256": dataset["index_snapshot"]["sha256"],
        "candidate_manifest_sha256": dataset["candidate_manifest"]["sha256"],
    }
    run_ids = set()
    for row in rows:
        for field, value in expected.items():
            if row[field].strip() != str(value):
                raise ValueError(f"Prediction {row['query_id']} {field} does not match frozen dataset")
        if any(not re.fullmatch(r"[0-9a-f]{64}", row[field].strip()) for field in ("candidate_snapshot_sha256", "scoring_config_sha256", "resolver_code_sha256", "runtime_environment_sha256")) or not row["python_version"].strip():
            raise ValueError(f"Prediction {row['query_id']} is missing a valid snapshot/configuration/runtime hash")
        if not row["run_id"].strip():
            raise ValueError(f"Prediction {row['query_id']} has no run_id")
        run_ids.add(row["run_id"].strip())
    if len(run_ids) != 1:
        raise ValueError("Prediction file must contain exactly one non-empty run_id")


def _validate_retrieval_prediction_snapshot(path: Path, dataset: dict[str, Any], artifacts: dict[str, Path], dataset_manifest_sha256: str) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    index = dataset["index_snapshot"]
    expected = {
        "dataset_id": dataset["dataset_id"],
        "dataset_version": dataset["dataset_version"],
        "database_snapshot_sha256": dataset["database_snapshot"]["sha256"],
        "index_snapshot_sha256": index["sha256"],
        "index_version": index["index_version"],
        "embedding_model": index["embedding_model"],
        "retrieval_queries_sha256": sha256_file(artifacts["retrieval_queries"]),
        "retrieval_judgements_sha256": sha256_file(artifacts["retrieval_judgements"]),
        "retrieval_pool_sha256": sha256_file(artifacts["retrieval_pool"]),
        "dataset_manifest_sha256": dataset_manifest_sha256,
    }
    if not isinstance(payload, dict) or any(payload.get(key) != value for key, value in expected.items()) or not isinstance(payload.get("run_id"), str) or not payload["run_id"].strip():
        raise ValueError("Retrieval predictions must carry matching dataset/index identifiers and a run_id")
    if not isinstance(payload.get("top_k"), int) or isinstance(payload.get("top_k"), bool) or not 1 <= payload["top_k"] <= 20:
        raise ValueError("Retrieval predictions need a valid captured top_k")
    if not re.fullmatch(r"[0-9a-f]{64}", str(payload.get("retrieval_code_sha256", ""))) or not re.fullmatch(r"[0-9a-f]{64}", str(payload.get("runtime_environment_sha256", ""))) or not payload.get("python_version"):
        raise ValueError("Retrieval predictions need code/runtime hashes and a Python version")


def evaluate_retrieval(judgements_path: Path, predictions_path: Path, queries_path: Path, k: int = 5) -> dict[str, Any]:
    if k < 1:
        raise ValueError("k must be positive")
    query_rows = unique_rows(read_csv(queries_path, {"query_id", "review_status"}), "query_id", queries_path)
    if any(row["review_status"].strip() not in {"ready", "complete"} for row in query_rows.values()):
        raise ValueError("Every retrieval query must have complete annotation status before evaluation")
    raw_judgements = read_csv(judgements_path, {"query_id", "canonical_publication_id", "relevance", "adjudication_status"})
    judged: dict[str, dict[str, int]] = {}
    for row in raw_judgements:
        query_id = row["query_id"].strip()
        publication_id = row["canonical_publication_id"].strip()
        if query_id not in query_rows or not publication_id:
            raise ValueError(f"Judgment references unknown query or missing publication ID: {query_id!r}/{publication_id!r}")
        if row["adjudication_status"].strip() not in {"agreed", "adjudicated"} or row["relevance"].strip() not in {"0", "1", "2"}:
            raise ValueError(f"Incomplete or invalid relevance judgment for {query_id}/{publication_id}")
        if publication_id in judged.setdefault(query_id, {}):
            raise ValueError(f"Duplicate relevance judgment for {query_id}/{publication_id}")
        judged[query_id][publication_id] = int(row["relevance"])
    missing_judgments = set(query_rows) - set(judged)
    if missing_judgments:
        raise ValueError(f"Retrieval queries lack relevance judgments: {sorted(missing_judgments)}")

    try:
        payload = json.loads(predictions_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Cannot read retrieval predictions JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("queries"), list):
        raise ValueError("Retrieval predictions JSON must contain a queries list")
    prediction_rows = []
    for row in payload["queries"]:
        if not isinstance(row, dict) or row.get("query_id") in (None, ""):
            raise ValueError("Every retrieval prediction needs a query_id")
        prediction_rows.append({**row, "query_id": str(row["query_id"])})
    predicted = unique_rows(prediction_rows, "query_id", predictions_path)
    if set(predicted) != set(query_rows):
        raise ValueError(f"Retrieval prediction coverage mismatch; missing={sorted(set(query_rows)-set(predicted))}, extra={sorted(set(predicted)-set(query_rows))}")
    per_query = []
    for query_id in sorted(query_rows):
        row = predicted[query_id]
        hits = row.get("hits", [])
        if not isinstance(hits, list):
            raise ValueError(f"Hits must be a list for {query_id}")
        canonical_hits = []
        for hit in hits:
            if not isinstance(hit, dict) or not isinstance(hit.get("canonical_id"), str) or not hit["canonical_id"].strip():
                raise ValueError(f"Every hit needs a canonical_id for {query_id}")
            canonical_hits.append(hit["canonical_id"].strip())
        if len(canonical_hits) != len(set(canonical_hits)):
            raise ValueError(f"Duplicate canonical publication IDs in retrieval predictions for {query_id}")
        unjudged_hits = set(canonical_hits) - set(judged[query_id])
        if unjudged_hits:
            raise ValueError(f"Retrieved publications lack relevance judgments for {query_id}: {sorted(unjudged_hits)}")
        top_k = canonical_hits[:k]
        relevant = {doc_id for doc_id, grade in judged[query_id].items() if grade > 0}
        relevant_found = sum(judged[query_id][doc_id] > 0 for doc_id in top_k)
        first_relevant_rank = next((rank for rank, doc_id in enumerate(canonical_hits, 1) if judged[query_id][doc_id] > 0), None)
        latency = row.get("latency_ms")
        try:
            latency_value = float(latency) if latency not in (None, "") else None
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid latency_ms for {query_id}") from exc
        if latency_value is not None and (not math.isfinite(latency_value) or latency_value < 0):
            raise ValueError(f"Invalid latency_ms for {query_id}")
        per_query.append({
            "query_id": query_id,
            "relevant_document_count": len(relevant),
            f"recall_at_{k}": relevant_found / len(relevant) if relevant else None,
            "mrr": 1 / first_relevant_rank if first_relevant_rank else 0.0,
            f"precision_at_{k}": relevant_found / k,
            "empty_result": not canonical_hits,
            "latency_ms": latency_value,
        })
    recall = [row[f"recall_at_{k}"] for row in per_query if row[f"recall_at_{k}"] is not None]
    reciprocal_ranks = [row["mrr"] for row in per_query if row["relevant_document_count"] > 0]
    precisions = [row[f"precision_at_{k}"] for row in per_query]
    latency_values = [row["latency_ms"] for row in per_query if row["latency_ms"] is not None]
    n = len(per_query)
    return {
        "evaluation": "retrieval_relevance_v1",
        "run_id": payload.get("run_id"),
        "k": k,
        "index_version": payload.get("index_version"),
        "embedding_model": payload.get("embedding_model"),
        "retrieval_code_sha256": payload.get("retrieval_code_sha256"),
        "runtime_environment_sha256": payload.get("runtime_environment_sha256"),
        "python_version": payload.get("python_version"),
        "inputs": {"queries_sha256": sha256_file(queries_path), "judgements_sha256": sha256_file(judgements_path), "predictions_sha256": sha256_file(predictions_path)},
        "query_count": n,
        "mean_recall_at_k": round(sum(recall) / len(recall), 6) if recall else None,
        "recall_denominator_queries": len(recall),
        "mrr": round(sum(reciprocal_ranks) / len(reciprocal_ranks), 6) if reciprocal_ranks else None,
        "mrr_denominator_queries": len(reciprocal_ranks),
        "mean_precision_at_k": round(sum(precisions) / n, 6) if n else None,
        "precision_denominator_queries": n,
        "empty_result_count": sum(row["empty_result"] for row in per_query),
        "empty_result_rate": round(sum(row["empty_result"] for row in per_query) / n, 6) if n else None,
        "latency_p50_ms": _percentile(latency_values, 0.50),
        "latency_p95_ms": _percentile(latency_values, 0.95),
        "per_query": per_query,
        "denominators": {
            f"recall_at_{k}": "queries with at least one independently judged relevant publication; relevant set is all completely judged publications in that query's frozen pool",
            "mrr": "queries with at least one independently judged relevant publication",
            f"precision_at_{k}": f"all fully judged retrieval queries; fixed denominator k={k}, including missing result slots",
            "empty_result_rate": "all fully judged retrieval queries",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="task", required=True)
    identity = sub.add_parser("identity")
    identity.add_argument("--dataset-manifest", type=Path, required=True)
    identity.add_argument("--predictions", type=Path, required=True)
    identity.add_argument("--output", type=Path, required=True)
    retrieval = sub.add_parser("retrieval")
    retrieval.add_argument("--dataset-manifest", type=Path, required=True)
    retrieval.add_argument("--predictions", type=Path, required=True)
    retrieval.add_argument("--k", type=int, default=5)
    retrieval.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite evaluation report: {args.output}")
    data = validate_dataset_manifest(args.dataset_manifest, require_retrieval=args.task == "retrieval")
    artifacts = data["artifacts"]
    if args.task == "identity":
        _validate_identity_prediction_snapshot(args.predictions, data["manifest"], data["annotations"]["split_version"], sha256_file(args.dataset_manifest))
        report = evaluate_identity(artifacts["identity_labels"], args.predictions, artifacts["split_manifest"])
    else:
        _validate_retrieval_prediction_snapshot(args.predictions, data["manifest"], artifacts, sha256_file(args.dataset_manifest))
        if args.k not in data["manifest"]["retrieval_metric_k_values"]:
            raise ValueError(f"k={args.k} was not preregistered in retrieval_metric_k_values")
        captured_top_k = json.loads(args.predictions.read_text(encoding="utf-8"))["top_k"]
        if captured_top_k < args.k:
            raise ValueError(f"Captured retrieval top_k={captured_top_k} is less than requested evaluation k={args.k}")
        report = evaluate_retrieval(artifacts["retrieval_judgements"], args.predictions, artifacts["retrieval_queries"], args.k)
    report["dataset_id"] = data["manifest"]["dataset_id"]
    report["dataset_version"] = data["manifest"]["dataset_version"]
    report["database_snapshot_sha256"] = data["manifest"]["database_snapshot"]["sha256"]
    report["index_snapshot_sha256"] = data["manifest"]["index_snapshot"]["sha256"]
    report["dataset_manifest_sha256"] = sha256_file(args.dataset_manifest)
    report["split_freeze_sha256"] = data["manifest"]["split_freeze"]["sha256"]
    if args.task == "retrieval":
        report["retrieval_pool_sha256"] = sha256_file(artifacts["retrieval_pool"])
        report["retrieval_query_manifest_sha256"] = sha256_file(artifacts["retrieval_queries"])
        report["retrieval_judgements_sha256"] = sha256_file(artifacts["retrieval_judgements"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"Saved {args.task} evaluation to {args.output}")


if __name__ == "__main__":
    main()