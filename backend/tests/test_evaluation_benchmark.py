import csv
import hashlib
import json
import sqlite3

import pytest

from scripts.evaluation_dataset import sha256_file, sha256_tree, split_membership_sha256, validate_dataset_manifest
from scripts.evaluate_benchmark import evaluate_identity, evaluate_retrieval
from scripts.capture_retrieval_predictions import capture_dataset, capture_queries
from services import scholarly_retrieval
from scripts.replay_frozen_resolver import replay_dataset
from scripts.seal_evaluation_manifest import seal_manifest


IDENTITY_FIELDS = [
    "query_id", "query_text", "context_json", "gold_status", "gold_source", "gold_author_id", "evidence_refs_json",
    "reviewer_1", "reviewer_1_status", "reviewer_1_confidence", "reviewer_1_rationale",
    "reviewer_2", "reviewer_2_status", "reviewer_2_confidence", "reviewer_2_rationale",
    "adjudicator", "adjudication_status", "adjudicated_confidence", "notes",
]
SPLIT_FIELDS = ["query_id", "identity_group_id", "split", "split_version"]
RETRIEVAL_FIELDS = [
    "query_id", "canonical_publication_id", "relevance", "reviewer_1", "reviewer_1_relevance",
    "reviewer_2", "reviewer_2_relevance", "adjudicator", "adjudicated_relevance", "adjudication_status", "evidence_note",
]


def write_csv(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _sqlite_snapshot(path):
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE alembic_version(version_num TEXT NOT NULL)")
    connection.execute("INSERT INTO alembic_version VALUES ('test_rev_1')")
    connection.execute("CREATE TABLE publications(id INTEGER PRIMARY KEY)")
    connection.execute("CREATE TABLE author_candidates(id TEXT PRIMARY KEY, query_normalized TEXT NOT NULL)")
    connection.executemany("INSERT INTO publications(id) VALUES (?)", [(1,), (2,)])
    connection.commit()
    connection.close()


def _chroma_snapshot(path):
    path.mkdir()
    connection = sqlite3.connect(path / "chroma.sqlite3")
    connection.execute("CREATE TABLE collections(id TEXT PRIMARY KEY, name TEXT)")
    connection.execute("CREATE TABLE segments(id TEXT PRIMARY KEY, collection TEXT, scope TEXT)")
    connection.execute("CREATE TABLE embeddings(id INTEGER PRIMARY KEY, segment_id TEXT)")
    connection.execute("CREATE TABLE embedding_metadata(id INTEGER, key TEXT, string_value TEXT)")
    connection.execute("INSERT INTO collections VALUES ('collection-1', 'scholarly_records_v1')")
    connection.execute("INSERT INTO segments VALUES ('metadata-1', 'collection-1', 'METADATA')")
    connection.execute("INSERT INTO embeddings VALUES (1, 'metadata-1')")
    connection.execute("INSERT INTO embedding_metadata VALUES (1, 'index_version', 'test-index-v1')")
    connection.execute("INSERT INTO embedding_metadata VALUES (1, 'embedding_model', 'test-embedding')")
    connection.commit()
    connection.close()


def _base_rows():
    query_ids = ["q1", "q2", "q3"]
    labels = []
    splits = []
    candidates = []
    split_names = ["train", "development", "test"]
    for index, query_id in enumerate(query_ids):
        gold = "uncertain" if index == 2 else "resolved"
        author_id = "A1" if index == 0 else ("A2" if index == 1 else "")
        labels.append({
            "query_id": query_id, "query_text": f"Researcher {index}", "context_json": "{}",
            "gold_status": gold, "gold_source": "openalex" if author_id else "", "gold_author_id": author_id,
            "evidence_refs_json": json.dumps([{"source": "OpenAlex", "reference": f"https://example.org/{query_id}", "captured_at": "2026-01-01T00:00:00Z", "evidence_type": "official_profile"}]),
            "reviewer_1": "reviewer-a", "reviewer_1_status": gold, "reviewer_1_confidence": "4", "reviewer_1_rationale": "Independent source evidence",
            "reviewer_2": "reviewer-b", "reviewer_2_status": gold, "reviewer_2_confidence": "4", "reviewer_2_rationale": "Independent source evidence",
            "adjudicator": "", "adjudication_status": "uncertain" if gold == "uncertain" else "agreed", "adjudicated_confidence": "4", "notes": "",
        })
        splits.append({"query_id": query_id, "identity_group_id": f"person-{index}", "split": split_names[index], "split_version": "split-v1"})
        candidates.append({"query_id": query_id, "query_text": f"Researcher {index}", "context_json": "{}", "candidate_source_status": "empty", "candidate_source_error_code": "", "candidate_ids_json": "[]"})
    return labels, splits, candidates


def make_dataset(tmp_path, *, retrieval=True):
    root = tmp_path
    db_path = root / "snapshot.sqlite3"
    _sqlite_snapshot(db_path)
    index_path = root / "index_snapshot"
    _chroma_snapshot(index_path)
    labels, splits, candidates = _base_rows()
    labels_path = root / "identity_labels.csv"
    splits_path = root / "split_manifest.csv"
    candidates_path = root / "candidate_manifest.csv"
    write_csv(labels_path, IDENTITY_FIELDS, labels)
    write_csv(splits_path, SPLIT_FIELDS, splits)
    candidate_fields = ["query_id", "query_text", "context_json", "candidate_source_status", "candidate_source_error_code", "candidate_ids_json"]
    write_csv(candidates_path, candidate_fields, candidates)
    freeze_path = root / "split_freeze.json"
    freeze_path.write_text(json.dumps({
        "membership_frozen": True, "frozen_at": "2026-02-01T00:00:00Z", "split_version": "split-v1",
        "split_manifest_sha256": sha256_file(splits_path), "test_membership_sha256": split_membership_sha256(splits),
        "test_membership_count": 1, "labels_sha256_at_freeze": sha256_file(labels_path),
    }), encoding="utf-8")
    manifest = {
        "schema_version": 1, "dataset_id": "test-dataset", "dataset_version": "v1", "frozen_at": "2026-02-02T00:00:00Z",
        "database_snapshot": {"path": "snapshot.sqlite3", "sha256": sha256_file(db_path), "alembic_revision": "test_rev_1", "publication_count": 2},
        "index_snapshot": {"path": "index_snapshot", "sha256": sha256_tree(index_path), "index_version": "test-index-v1", "collection": "scholarly_records_v1", "embedding_model": "test-embedding", "document_count": 1},
        "candidate_manifest": {"path": "candidate_manifest.csv", "sha256": sha256_file(candidates_path)},
        "identity_labels": {"path": "identity_labels.csv", "sha256": sha256_file(labels_path)},
        "split_manifest": {"path": "split_manifest.csv", "sha256": sha256_file(splits_path)},
        "split_freeze": {"path": "split_freeze.json", "sha256": sha256_file(freeze_path)},
    }
    if retrieval:
        manifest["retrieval_metric_k_values"] = [2]
        pool_path = root / "retrieval_pool.csv"
        queries_path = root / "retrieval_queries.csv"
        judgements_path = root / "retrieval_relevance.csv"
        pool_rows = [
            {"query_id": "rq1", "canonical_publication_id": "pub-1", "pool_sources_json": '["gold-known", "run-v1"]'},
            {"query_id": "rq1", "canonical_publication_id": "pub-2", "pool_sources_json": '["run-v1"]'},
            {"query_id": "rq2", "canonical_publication_id": "pub-3", "pool_sources_json": '["gold-known"]'},
        ]
        write_csv(pool_path, ["query_id", "canonical_publication_id", "pool_sources_json"], pool_rows)
        pool_hash = sha256_file(pool_path)
        query_fields = ["query_id", "query_text", "pool_protocol_version", "pool_sha256", "index_snapshot_sha256", "pool_document_count", "review_status", "reviewer_1", "reviewer_2", "adjudicator"]
        write_csv(queries_path, query_fields, [
            {"query_id": "rq1", "query_text": "Graph neural network papers", "pool_protocol_version": "pool-v1", "pool_sha256": pool_hash, "index_snapshot_sha256": manifest["index_snapshot"]["sha256"], "pool_document_count": 2, "review_status": "complete", "reviewer_1": "r1", "reviewer_2": "r2", "adjudicator": ""},
            {"query_id": "rq2", "query_text": "No known work", "pool_protocol_version": "pool-v1", "pool_sha256": pool_hash, "index_snapshot_sha256": manifest["index_snapshot"]["sha256"], "pool_document_count": 1, "review_status": "complete", "reviewer_1": "r1", "reviewer_2": "r2", "adjudicator": ""},
        ])
        write_csv(judgements_path, RETRIEVAL_FIELDS, [
            {"query_id": "rq1", "canonical_publication_id": "pub-1", "relevance": "2", "reviewer_1": "r1", "reviewer_1_relevance": "2", "reviewer_2": "r2", "reviewer_2_relevance": "2", "adjudicator": "", "adjudicated_relevance": "", "adjudication_status": "agreed", "evidence_note": "Source-level publication match"},
            {"query_id": "rq1", "canonical_publication_id": "pub-2", "relevance": "0", "reviewer_1": "r1", "reviewer_1_relevance": "0", "reviewer_2": "r2", "reviewer_2_relevance": "0", "adjudicator": "", "adjudicated_relevance": "", "adjudication_status": "agreed", "evidence_note": "Not relevant"},
            {"query_id": "rq2", "canonical_publication_id": "pub-3", "relevance": "0", "reviewer_1": "r1", "reviewer_1_relevance": "0", "reviewer_2": "r2", "reviewer_2_relevance": "0", "adjudicator": "", "adjudicated_relevance": "", "adjudication_status": "agreed", "evidence_note": "Not relevant"},
        ])
        manifest["retrieval_queries"] = {"path": "retrieval_queries.csv", "sha256": sha256_file(queries_path)}
        manifest["retrieval_pool"] = {"path": "retrieval_pool.csv", "sha256": pool_hash}
        manifest["retrieval_judgements"] = {"path": "retrieval_relevance.csv", "sha256": sha256_file(judgements_path)}
    manifest_path = root / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"root": root, "manifest": manifest_path, "labels": labels_path, "splits": splits_path, "candidates": candidates_path, "queries": root / "retrieval_queries.csv", "judgements": root / "retrieval_relevance.csv", "db": db_path}


def test_valid_manifest_checks_snapshot_identifiers_and_annotation_freeze(tmp_path):
    files = make_dataset(tmp_path)
    before = sha256_file(files["db"])
    report = validate_dataset_manifest(files["manifest"], minimum_queries=3, require_retrieval=True)
    assert report["annotations"]["label_count"] == 3
    assert report["annotations"]["uncertain_count"] == 1
    assert report["annotations"]["split_version"] == "split-v1"
    assert report["retrieval_query_count"] == 2
    assert sha256_file(files["db"]) == before


def test_seal_manifest_records_verified_snapshot_ids_and_never_overwrites(tmp_path):
    files = make_dataset(tmp_path)
    draft = json.loads(files["manifest"].read_text())
    for name in ("database_snapshot", "index_snapshot", "candidate_manifest", "identity_labels", "split_manifest", "split_freeze", "retrieval_queries", "retrieval_pool", "retrieval_judgements"):
        draft[name].pop("sha256", None)
    draft["database_snapshot"].pop("alembic_revision", None)
    draft["database_snapshot"].pop("publication_count", None)
    draft["index_snapshot"].pop("index_version", None)
    draft["index_snapshot"].pop("embedding_model", None)
    draft["index_snapshot"].pop("document_count", None)
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps(draft), encoding="utf-8")
    output = tmp_path / "sealed.json"
    sealed = seal_manifest(draft_path, output, minimum_queries=3)
    assert sealed["database_snapshot"]["alembic_revision"] == "test_rev_1"
    assert sealed["database_snapshot"]["publication_count"] == 2
    assert sealed["index_snapshot"]["document_count"] == 1
    assert sealed["index_snapshot"]["embedding_model"] == "test-embedding"
    with pytest.raises(FileExistsError):
        seal_manifest(draft_path, output, minimum_queries=3)


def test_dataset_manifest_rejects_artifact_hash_mismatch(tmp_path):
    files = make_dataset(tmp_path)
    files["labels"].write_text(files["labels"].read_text() + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        validate_dataset_manifest(files["manifest"], minimum_queries=3)


def test_annotation_validator_rejects_inconsistent_adjudicated_label(tmp_path):
    files = make_dataset(tmp_path)
    labels = list(csv.DictReader(files["labels"].open()))
    labels[0]["reviewer_2_status"] = "unresolved"
    # Keep the final label marked as agreed, which is invalid when reviewers disagree.
    write_csv(files["labels"], IDENTITY_FIELDS, labels)
    manifest = json.loads(files["manifest"].read_text())
    manifest["identity_labels"]["sha256"] = sha256_file(files["labels"])
    freeze = json.loads((tmp_path / "split_freeze.json").read_text())
    freeze["labels_sha256_at_freeze"] = sha256_file(files["labels"])
    (tmp_path / "split_freeze.json").write_text(json.dumps(freeze), encoding="utf-8")
    manifest["split_freeze"]["sha256"] = sha256_file(tmp_path / "split_freeze.json")
    files["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Reviewers disagree"):
        validate_dataset_manifest(files["manifest"], minimum_queries=3)


def test_dataset_manifest_rejects_wrong_canonical_database_or_index_identifiers(tmp_path):
    files = make_dataset(tmp_path)
    manifest = json.loads(files["manifest"].read_text())
    manifest["database_snapshot"]["publication_count"] = 99
    files["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="revision/publication count"):
        validate_dataset_manifest(files["manifest"], minimum_queries=3)
    manifest["database_snapshot"]["publication_count"] = 2
    manifest["index_snapshot"]["embedding_model"] = "not-the-embedded-model"
    files["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="index/model metadata"):
        validate_dataset_manifest(files["manifest"], minimum_queries=3)


def test_dataset_manifest_rejects_duplicate_candidate_snapshot_ids(tmp_path):
    files = make_dataset(tmp_path)
    candidates = list(csv.DictReader(files["candidates"].open()))
    candidates[0]["candidate_source_status"] = "ok"
    candidates[0]["candidate_source_status"] = "ok"
    candidates[0]["candidate_ids_json"] = '["same-id", "same-id"]'
    write_csv(files["candidates"], ["query_id", "query_text", "context_json", "candidate_source_status", "candidate_source_error_code", "candidate_ids_json"], candidates)
    manifest = json.loads(files["manifest"].read_text())
    manifest["candidate_manifest"]["sha256"] = sha256_file(files["candidates"])
    files["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate candidate snapshot ID"):
        validate_dataset_manifest(files["manifest"], minimum_queries=3)


def test_dataset_manifest_rejects_candidate_id_absent_from_frozen_database(tmp_path):
    files = make_dataset(tmp_path)
    candidates = list(csv.DictReader(files["candidates"].open()))
    candidates[0]["candidate_source_status"] = "ok"
    candidates[0]["candidate_ids_json"] = '["missing-candidate"]'
    write_csv(files["candidates"], ["query_id", "query_text", "context_json", "candidate_source_status", "candidate_source_error_code", "candidate_ids_json"], candidates)
    manifest = json.loads(files["manifest"].read_text())
    manifest["candidate_manifest"]["sha256"] = sha256_file(files["candidates"])
    files["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="missing from database snapshot"):
        validate_dataset_manifest(files["manifest"], minimum_queries=3)


def test_annotation_validator_rejects_duplicate_query_ids(tmp_path):
    files = make_dataset(tmp_path)
    rows = list(csv.DictReader(files["labels"].open()))
    write_csv(files["labels"], IDENTITY_FIELDS, rows + [rows[0]])
    manifest = json.loads(files["manifest"].read_text())
    manifest["identity_labels"]["sha256"] = sha256_file(files["labels"])
    files["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate query_id"):
        validate_dataset_manifest(files["manifest"], minimum_queries=3)


def test_split_freeze_rejects_identity_group_leakage(tmp_path):
    files = make_dataset(tmp_path)
    splits = list(csv.DictReader(files["splits"].open()))
    splits[1]["identity_group_id"] = splits[0]["identity_group_id"]
    write_csv(files["splits"], SPLIT_FIELDS, splits)
    manifest = json.loads(files["manifest"].read_text())
    manifest["split_manifest"]["sha256"] = sha256_file(files["splits"])
    freeze_path = tmp_path / "split_freeze.json"
    freeze = json.loads(freeze_path.read_text())
    freeze["split_manifest_sha256"] = sha256_file(files["splits"])
    freeze["test_membership_sha256"] = split_membership_sha256(splits)
    freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
    manifest["split_freeze"]["sha256"] = sha256_file(freeze_path)
    files["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="crosses data splits"):
        validate_dataset_manifest(files["manifest"], minimum_queries=3)


def test_retrieval_manifest_rejects_query_with_missing_judgments(tmp_path):
    files = make_dataset(tmp_path)
    rows = list(csv.DictReader(files["judgements"].open()))
    write_csv(files["judgements"], RETRIEVAL_FIELDS, rows[:-1])
    manifest = json.loads(files["manifest"].read_text())
    manifest["retrieval_judgements"]["sha256"] = sha256_file(files["judgements"])
    files["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="exact frozen pool"):
        validate_dataset_manifest(files["manifest"], minimum_queries=3, require_retrieval=True)


def test_identity_metrics_report_denominators_and_detect_incomplete_predictions(tmp_path):
    files = make_dataset(tmp_path)
    predictions = tmp_path / "predictions.csv"
    write_csv(predictions, ["query_id", "predicted_status", "selected_source", "selected_author_id", "top_source", "top_author_id", "resolver_version", "run_id"], [
        {"query_id": "q1", "predicted_status": "auto_selected", "selected_source": "openalex", "selected_author_id": "A1", "top_source": "openalex", "top_author_id": "A1", "resolver_version": "v1", "run_id": "r1"},
        {"query_id": "q2", "predicted_status": "manual_selection_required", "top_source": "openalex", "top_author_id": "A2", "resolver_version": "v1", "run_id": "r1"},
        {"query_id": "q3", "predicted_status": "unresolved", "resolver_version": "v1", "run_id": "r1"},
    ])
    report = evaluate_identity(files["labels"], predictions, files["splits"])
    overall = report["metrics_by_split"]["all"]
    assert overall["auto_accuracy"] == 1.0
    assert overall["auto_coverage"] == 0.5
    assert overall["abstention_count"] == 1
    assert overall["denominators"]["auto_coverage"].startswith("all resolved")
    write_csv(predictions, ["query_id", "predicted_status"], [{"query_id": "q1", "predicted_status": "unresolved"}])
    with pytest.raises(ValueError, match="prediction coverage mismatch"):
        evaluate_identity(files["labels"], predictions, files["splits"])


def test_retrieval_metrics_require_complete_predictions_and_all_hit_judgments(tmp_path):
    files = make_dataset(tmp_path)
    predictions = tmp_path / "retrieval_predictions.json"
    predictions.write_text(json.dumps({
        "index_version": "test-index-v1", "embedding_model": "test-embedding",
        "queries": [
            {"query_id": "rq1", "hits": [{"canonical_id": "pub-1"}, {"canonical_id": "pub-2"}], "latency_ms": 10},
            {"query_id": "rq2", "hits": [{"canonical_id": "pub-3"}], "latency_ms": 20},
        ],
    }), encoding="utf-8")
    result = evaluate_retrieval(files["judgements"], predictions, files["queries"], k=2)
    assert result["mean_recall_at_k"] == 1.0
    assert result["mean_precision_at_k"] == 0.25
    assert result["recall_denominator_queries"] == 1
    assert result["empty_result_rate"] == 0.0
    predictions.write_text(json.dumps({"queries": [{"query_id": "rq1", "hits": []}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="prediction coverage mismatch"):
        evaluate_retrieval(files["judgements"], predictions, files["queries"], k=2)
    predictions.write_text(json.dumps({"queries": [
        {"query_id": "rq1", "hits": [{"canonical_id": "unjudged-pub"}]},
        {"query_id": "rq2", "hits": [{"canonical_id": "pub-3"}]},
    ]}), encoding="utf-8")
    with pytest.raises(ValueError, match="lack relevance judgments"):
        evaluate_retrieval(files["judgements"], predictions, files["queries"], k=2)


def test_retrieval_capture_records_ordered_canonical_ids_and_latency(tmp_path):
    class Hit:
        def __init__(self, canonical_id, score):
            self.canonical_id = canonical_id
            self.score = score

    async def fake_retrieve(query, *, top_k, path):
        assert path == tmp_path
        assert top_k == 2
        return [Hit("pub-a", 0.9), Hit("pub-b", 0.7)] if query == "query one" else []

    rows = [
        {"query_id": "q1", "query_text": "query one"},
        {"query_id": "q2", "query_text": "query two"},
    ]
    captured = __import__("asyncio").run(capture_queries(rows, fake_retrieve, index_path=tmp_path, top_k=2))
    assert [hit["canonical_id"] for hit in captured[0]["hits"]] == ["pub-a", "pub-b"]
    assert captured[0]["hits"][0]["rank"] == 1
    assert captured[1]["hits"] == []
    assert captured[0]["latency_ms"] >= 0


def test_retrieval_capture_uses_disposable_index_copy_and_preserves_source_snapshot(tmp_path, monkeypatch):
    files = make_dataset(tmp_path)
    source_index = tmp_path / "index_snapshot"
    before = sha256_tree(source_index)

    class Hit:
        canonical_id = "pub-1"
        score = 0.8

    def fake_status(path):
        assert path != source_index
        return {"status": "ready", "document_count": 1, "index_version": "test-index-v1", "embedding_model": "test-embedding"}

    async def fake_retrieve(query, *, top_k, path):
        assert path != source_index
        return [Hit()] if "Graph" in query else []

    monkeypatch.setattr(scholarly_retrieval, "index_status", fake_status)
    monkeypatch.setattr(scholarly_retrieval, "retrieve", fake_retrieve)
    output = tmp_path / "retrieval_predictions.json"
    payload = __import__("asyncio").run(capture_dataset(files["manifest"], output, "retrieval-run", top_k=2, minimum_queries=3))
    assert len(payload["queries"]) == 2
    assert payload["queries"][0]["hits"][0]["canonical_id"] == "pub-1"
    assert payload["run_id"] == "retrieval-run"
    assert sha256_tree(source_index) == before


def test_read_only_frozen_v1_replay_writes_predictions_without_changing_database(tmp_path):
    files = make_dataset(tmp_path, retrieval=False)
    candidate_rows = list(csv.DictReader(files["candidates"].open()))
    candidate_rows[0]["candidate_source_status"] = "failed"
    candidate_rows[0]["candidate_source_error_code"] = "timeout"
    write_csv(files["candidates"], ["query_id", "query_text", "context_json", "candidate_source_status", "candidate_source_error_code", "candidate_ids_json"], candidate_rows)
    manifest = json.loads(files["manifest"].read_text())
    manifest["candidate_manifest"]["sha256"] = sha256_file(files["candidates"])
    files["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "predictions.csv"
    before = sha256_file(files["db"])
    count = __import__("asyncio").run(replay_dataset(files["manifest"], output, "unit-run", minimum_queries=3))
    rows = list(csv.DictReader(output.open()))
    assert count == 3
    assert len(rows) == 3
    assert {row["predicted_status"] for row in rows} == {"unresolved", "candidate_source_failed"}
    assert rows[0]["candidate_source_error_code"] == "timeout"
    assert rows[0]["run_id"] == "unit-run"
    assert rows[0]["database_snapshot_sha256"] == before
    assert sha256_file(files["db"]) == before
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        __import__("asyncio").run(replay_dataset(files["manifest"], output, "unit-run-2", minimum_queries=3))