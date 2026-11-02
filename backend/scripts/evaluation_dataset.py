"""Validation helpers for frozen, source-audited evaluation datasets."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


IDENTITY_FIELDS = {
    "query_id", "query_text", "context_json", "gold_status", "gold_source", "gold_author_id",
    "evidence_refs_json", "reviewer_1", "reviewer_1_status", "reviewer_1_confidence",
    "reviewer_1_rationale", "reviewer_2", "reviewer_2_status", "reviewer_2_confidence",
    "reviewer_2_rationale", "adjudicator", "adjudication_status", "adjudicated_confidence", "notes",
}
SPLIT_FIELDS = {"query_id", "identity_group_id", "split", "split_version"}
RETRIEVAL_QUERY_FIELDS = {"query_id", "query_text", "pool_protocol_version", "pool_sha256", "index_snapshot_sha256", "pool_document_count", "review_status", "reviewer_1", "reviewer_2", "adjudicator"}
RETRIEVAL_POOL_FIELDS = {"query_id", "canonical_publication_id", "pool_sources_json"}
RELEVANCE_FIELDS = {
    "query_id", "canonical_publication_id", "relevance", "reviewer_1", "reviewer_1_relevance",
    "reviewer_2", "reviewer_2_relevance", "adjudicator", "adjudicated_relevance",
    "adjudication_status", "evidence_note",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_tree(path: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    if not path.is_dir():
        raise ValueError(f"Snapshot path does not exist: {path}")
    digest = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file())
    if not files:
        raise ValueError(f"Snapshot directory is empty: {path}")
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(item)))
    return digest.hexdigest()


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"CSV contains no annotation rows: {path}")
    return rows


def unique_rows(rows: list[dict[str, str]], field: str, source: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        value = (row.get(field) or "").strip()
        if not value:
            raise ValueError(f"Missing {field} in {source}")
        if value in result:
            raise ValueError(f"Duplicate {field}={value!r} in {source}")
        result[value] = row
    return result


def _parse_time(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed


def _artifact_path(root: Path, manifest: dict[str, Any], name: str, *, directory: bool = False) -> Path:
    entry = manifest.get(name)
    if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not isinstance(entry.get("sha256"), str):
        raise ValueError(f"Manifest artifact {name!r} requires path and sha256")
    path = (root / entry["path"]).resolve()
    if not path.exists() or (directory and not path.is_dir()) or (not directory and not path.is_file()):
        raise ValueError(f"Manifest artifact {name!r} has a missing or wrong-kind path: {path}")
    actual = sha256_tree(path) if directory else sha256_file(path)
    if actual != entry["sha256"]:
        raise ValueError(f"SHA-256 mismatch for manifest artifact {name!r}")
    return path


def validate_annotation_rows(labels_path: Path, splits_path: Path, freeze_path: Path, *, minimum_queries: int = 100) -> dict[str, Any]:
    labels = read_csv(labels_path, IDENTITY_FIELDS)
    label_by_id = unique_rows(labels, "query_id", labels_path)
    if len(labels) < minimum_queries:
        raise ValueError(f"At least {minimum_queries} independently reviewed author queries are required; found {len(labels)}")
    for query_id, row in label_by_id.items():
        status = (row["gold_status"] or "").strip()
        if status not in {"resolved", "unresolved", "uncertain"}:
            raise ValueError(f"Invalid gold_status for {query_id}: {status!r}")
        if not row["query_text"].strip() or not row["context_json"].strip():
            raise ValueError(f"Missing query text or context for {query_id}")
        try:
            context = json.loads(row["context_json"])
            refs = json.loads(row["evidence_refs_json"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid JSON context/evidence for {query_id}") from exc
        if not isinstance(context, dict) or not isinstance(refs, list) or not refs:
            raise ValueError(f"Context must be an object and evidence_refs_json a non-empty list for {query_id}")
        for ref in refs:
            if not isinstance(ref, dict) or not all(str(ref.get(key, "")).strip() for key in ("source", "reference", "captured_at", "evidence_type")):
                raise ValueError(f"Each evidence reference for {query_id} needs source, reference, captured_at, evidence_type")
            _parse_time(ref["captured_at"], f"evidence captured_at for {query_id}")
        if status == "resolved":
            if not row["gold_source"].strip() or not row["gold_author_id"].strip():
                raise ValueError(f"Resolved label {query_id} needs a source-scoped author ID")
        elif row["gold_source"].strip() or row["gold_author_id"].strip():
            raise ValueError(f"{status} label {query_id} must not set a gold author ID")
        reviewers = []
        for n in (1, 2):
            reviewer = row[f"reviewer_{n}"].strip()
            reviewer_status = row[f"reviewer_{n}_status"].strip()
            rationale = row[f"reviewer_{n}_rationale"].strip()
            try:
                confidence = int(row[f"reviewer_{n}_confidence"])
            except ValueError as exc:
                raise ValueError(f"Reviewer {n} confidence for {query_id} must be an integer from 1 to 5") from exc
            if not reviewer or not rationale or reviewer_status not in {"resolved", "unresolved", "uncertain"} or confidence not in range(1, 6):
                raise ValueError(f"Incomplete reviewer {n} annotation for {query_id}")
            reviewers.append(reviewer)
        if reviewers[0] == reviewers[1]:
            raise ValueError(f"Identity annotations for {query_id} require two distinct reviewers")
        adjudication = row["adjudication_status"].strip()
        if adjudication not in {"agreed", "adjudicated", "uncertain"}:
            raise ValueError(f"Invalid adjudication_status for {query_id}: {adjudication!r}")
        try:
            final_confidence = int(row["adjudicated_confidence"])
        except ValueError as exc:
            raise ValueError(f"Adjudicated confidence for {query_id} must be from 1 to 5") from exc
        if final_confidence not in range(1, 6):
            raise ValueError(f"Adjudicated confidence for {query_id} must be from 1 to 5")
        if status == "uncertain" and adjudication != "uncertain":
            raise ValueError(f"Uncertain gold label {query_id} must have uncertain adjudication status")
        if status != "uncertain" and adjudication == "uncertain":
            raise ValueError(f"Non-uncertain gold label {query_id} cannot have uncertain adjudication status")
        if adjudication == "adjudicated" and not row["adjudicator"].strip():
            raise ValueError(f"Adjudicated label {query_id} needs an adjudicator")
        if adjudication == "agreed" and row["reviewer_1_status"].strip() != row["reviewer_2_status"].strip():
            raise ValueError(f"Reviewers disagree for {query_id}; mark it adjudicated or uncertain")
        if adjudication == "agreed" and status != row["reviewer_1_status"].strip():
            raise ValueError(f"Agreed final label differs from reviewer labels for {query_id}")

    split_rows = read_csv(splits_path, SPLIT_FIELDS)
    split_by_id = unique_rows(split_rows, "query_id", splits_path)
    if set(split_by_id) != set(label_by_id):
        raise ValueError("Split manifest query IDs must match identity labels exactly")
    group_split: dict[str, str] = {}
    identity_groups: dict[tuple[str, str], str] = {}

    for query_id, row in split_by_id.items():
        group = row["identity_group_id"].strip()
        split = row["split"].strip()
        version = row["split_version"].strip()
        if not group or split not in {"train", "development", "test"} or not version:
            raise ValueError(f"Invalid split/group/version for {query_id}")
        previous = group_split.setdefault(group, split)
        if previous != split:
            raise ValueError(f"Identity group {group!r} crosses data splits")
        label = label_by_id[query_id]
        if label["gold_status"].strip() == "resolved":
            key = (label["gold_source"].strip(), label["gold_author_id"].strip())
            prior_group = identity_groups.setdefault(key, group)
            if prior_group != group:
                raise ValueError(f"Verified author {key!r} is assigned to multiple identity groups")


    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if not isinstance(freeze, dict) or freeze.get("membership_frozen") is not True:
        raise ValueError("Split freeze record must set membership_frozen=true")
    frozen_at = _parse_time(freeze.get("frozen_at"), "split freeze frozen_at")
    split_hash = sha256_file(splits_path)
    if freeze.get("split_manifest_sha256") != split_hash:
        raise ValueError("Split freeze record hash does not match split manifest")
    if freeze.get("test_membership_sha256") != split_membership_sha256(split_rows):
        raise ValueError("Split freeze record test membership hash does not match split manifest")
    if freeze.get("test_membership_count") != sum(row["split"].strip() == "test" for row in split_by_id.values()):
        raise ValueError("Split freeze record test membership count does not match split manifest")
    if freeze.get("labels_sha256_at_freeze") != sha256_file(labels_path):
        raise ValueError("Identity labels changed after split membership was frozen")
    if freeze.get("split_version") != sorted({row["split_version"].strip() for row in split_rows})[0] or len({row["split_version"].strip() for row in split_rows}) != 1:
        raise ValueError("Split versions must be uniform and match split freeze record")
    if {row["split"].strip() for row in split_rows} != {"train", "development", "test"}:
        raise ValueError("Frozen splits must include non-empty train, development, and test membership")
    return {"label_count": len(labels), "uncertain_count": sum(row["gold_status"].strip() == "uncertain" for row in labels), "split_version": freeze["split_version"], "frozen_at": frozen_at.isoformat(), "split_manifest_sha256": split_hash}


def split_membership_sha256(split_rows: list[dict[str, str]]) -> str:
    material = sorted((row["query_id"].strip(), row["identity_group_id"].strip()) for row in split_rows if row["split"].strip() == "test")
    return hashlib.sha256(json.dumps(material, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def validate_dataset_manifest(path: Path, *, minimum_queries: int = 100, require_retrieval: bool = False) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read dataset manifest: {path}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("Dataset manifest schema_version must be 1")
    for key in ("dataset_id", "dataset_version"):
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            raise ValueError(f"Dataset manifest needs {key}")
    dataset_frozen_at = dataset_frozen_at = _parse_time(manifest.get("frozen_at"), "dataset frozen_at")
    root = path.resolve().parent
    database = _artifact_path(root, manifest, "database_snapshot")
    if not database.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
        raise ValueError("database_snapshot must reference a SQLite snapshot file")
    if Path(str(database) + "-wal").exists() or Path(str(database) + "-shm").exists():
        raise ValueError("Database snapshot must be checkpointed and closed (no adjacent WAL/SHM files)")
    database_entry = manifest["database_snapshot"]
    if not database_entry.get("alembic_revision") or not isinstance(database_entry.get("publication_count"), int) or isinstance(database_entry.get("publication_count"), bool) or database_entry["publication_count"] < 0:
        raise ValueError("database_snapshot needs alembic_revision and publication_count identifiers")
    try:
        with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
            revision_row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
            publication_count = connection.execute("SELECT COUNT(*) FROM publications").fetchone()[0]
    except sqlite3.Error as exc:
        raise ValueError(f"Cannot verify read-only SQLite snapshot identifiers: {exc}") from exc
    revision = revision_row[0] if revision_row else ""
    if revision != database_entry["alembic_revision"] or publication_count != database_entry["publication_count"]:
        raise ValueError("Database snapshot revision/publication count does not match manifest")
    index = _artifact_path(root, manifest, "index_snapshot", directory=True)
    required_index_metadata = ("index_version", "collection", "embedding_model", "document_count")
    index_entry = manifest["index_snapshot"]
    if any(index_entry.get(field) in (None, "") for field in required_index_metadata) or int(index_entry["document_count"]) < 0:
        raise ValueError("index_snapshot needs index_version, collection, embedding_model, and non-negative document_count")
    chroma_db = index / "chroma.sqlite3"
    if not chroma_db.is_file():
        raise ValueError("index_snapshot is missing chroma.sqlite3")
    if Path(str(chroma_db) + "-wal").exists() or Path(str(chroma_db) + "-shm").exists():
        raise ValueError("Chroma snapshot must be closed and checkpointed (no adjacent WAL/SHM files)")
    try:
        with sqlite3.connect(f"file:{chroma_db}?mode=ro", uri=True) as connection:
            collection = connection.execute("SELECT id FROM collections WHERE name = ?", (index_entry["collection"],)).fetchone()
            if not collection:
                raise ValueError("index_snapshot collection name does not exist in Chroma snapshot")
            vector_count = connection.execute("SELECT COUNT(*) FROM embeddings WHERE segment_id IN (SELECT id FROM segments WHERE collection = ? AND scope = 'METADATA')", (collection[0],)).fetchone()[0]
            recorded_index_versions = {row[0] for row in connection.execute(
                "SELECT DISTINCT m.string_value FROM embedding_metadata m JOIN embeddings e ON e.id = m.id JOIN segments s ON s.id = e.segment_id WHERE s.collection = ? AND s.scope = 'METADATA' AND m.key = 'index_version'",
                (collection[0],),
            ).fetchall()}
            recorded_embedding_models = {row[0] for row in connection.execute(
                "SELECT DISTINCT m.string_value FROM embedding_metadata m JOIN embeddings e ON e.id = m.id JOIN segments s ON s.id = e.segment_id WHERE s.collection = ? AND s.scope = 'METADATA' AND m.key = 'embedding_model'",
                (collection[0],),
            ).fetchall()}
    except sqlite3.Error as exc:
        raise ValueError(f"Cannot verify read-only Chroma snapshot: {exc}") from exc
    if vector_count != int(index_entry["document_count"]):
        raise ValueError("Chroma snapshot document count does not match manifest")
    if recorded_index_versions != {index_entry["index_version"]} or recorded_embedding_models != {index_entry["embedding_model"]}:
        raise ValueError("Chroma snapshot index/model metadata does not match manifest")
    artifacts = {}
    for name in ("candidate_manifest", "identity_labels", "split_manifest", "split_freeze"):
        artifacts[name] = _artifact_path(root, manifest, name)
    annotation_summary = validate_annotation_rows(artifacts["identity_labels"], artifacts["split_manifest"], artifacts["split_freeze"], minimum_queries=minimum_queries)
    split_frozen_at = _parse_time(annotation_summary["frozen_at"], "split freeze frozen_at")
    if split_frozen_at > dataset_frozen_at:
        raise ValueError("Dataset snapshot cannot be frozen before its split membership")
    retrieval_names = ("retrieval_queries", "retrieval_pool", "retrieval_judgements")
    present = [name in manifest and isinstance(manifest[name], dict) and manifest[name].get("path") and manifest[name].get("sha256") for name in retrieval_names]
    if any(present) and not all(present):
        raise ValueError("Retrieval query manifest and relevance judgments must both be present")
    if all(present):
        metric_ks = manifest.get("retrieval_metric_k_values")
        if not isinstance(metric_ks, list) or not metric_ks or any(not isinstance(k, int) or isinstance(k, bool) or not 1 <= k <= 20 for k in metric_ks) or len(metric_ks) != len(set(metric_ks)):
            raise ValueError("Manifest retrieval_metric_k_values must be a non-empty list of unique integers from 1 to 20")
        artifacts["retrieval_queries"] = _artifact_path(root, manifest, "retrieval_queries")
        artifacts["retrieval_pool"] = _artifact_path(root, manifest, "retrieval_pool")
        artifacts["retrieval_judgements"] = _artifact_path(root, manifest, "retrieval_judgements")
    query_count: int | None = None
    if require_retrieval and not all(present):
        raise ValueError("Retrieval query manifest and relevance judgments are required for retrieval evaluation")
    if all(present):
        query_rows = read_csv(artifacts["retrieval_queries"], RETRIEVAL_QUERY_FIELDS)
        query_map = unique_rows(query_rows, "query_id", artifacts["retrieval_queries"])
        if any(row["review_status"].strip() != "complete" for row in query_map.values()):
            raise ValueError("Every retrieval query must be completely pool-judged before evaluation")
        if any(not row["reviewer_1"].strip() or not row["reviewer_2"].strip() or row["reviewer_1"].strip() == row["reviewer_2"].strip() for row in query_map.values()):
            raise ValueError("Every retrieval query needs two distinct pool reviewers")
        if any(not row["query_text"].strip() for row in query_map.values()):
            raise ValueError("Every retrieval query needs query text")
        if any(
            not row["pool_protocol_version"].strip()
            or row["pool_sha256"].strip() != manifest["retrieval_pool"]["sha256"]
            or row["index_snapshot_sha256"].strip() != index_entry["sha256"]
            for row in query_map.values()
        ):
            raise ValueError("Retrieval queries must bind to the frozen pool protocol, pool hash, and index snapshot")
        pool_rows = read_csv(artifacts["retrieval_pool"], RETRIEVAL_POOL_FIELDS)
        pool_pairs = set()
        per_query_pool_count: dict[str, int] = {}
        for row in pool_rows:
            qid = row["query_id"].strip()
            publication_id = row["canonical_publication_id"].strip()
            if qid not in query_map or not publication_id:
                raise ValueError(f"Pool references unknown query or empty publication ID: {qid!r}/{publication_id!r}")
            pair = (qid, publication_id)
            if pair in pool_pairs:
                raise ValueError(f"Duplicate document in retrieval pool: {pair}")
            try:
                pool_sources = json.loads(row["pool_sources_json"])
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid pool_sources_json for {pair}") from exc
            if not isinstance(pool_sources, list) or not pool_sources or any(not isinstance(source, str) or not source.strip() for source in pool_sources):
                raise ValueError(f"Every pooled document needs at least one recorded pool source: {pair}")
            pool_pairs.add(pair)
            per_query_pool_count[qid] = per_query_pool_count.get(qid, 0) + 1
        for qid, row in query_map.items():
            if not per_query_pool_count.get(qid) or int(row["pool_document_count"]) != per_query_pool_count[qid]:
                raise ValueError(f"Retrieval pool count mismatch or empty pool for {qid}")
        judgement_rows = read_csv(artifacts["retrieval_judgements"], RELEVANCE_FIELDS)
        pair_keys = set()
        judged_queries = set()
        for row in judgement_rows:
            qid = row["query_id"].strip()
            publication_id = row["canonical_publication_id"].strip()
            if qid not in query_map or not publication_id:
                raise ValueError(f"Relevance judgement references unknown query or empty publication ID: {qid!r}/{publication_id!r}")
            key = (qid, publication_id)
            if key in pair_keys:
                raise ValueError(f"Duplicate relevance judgement for {key}")
            pair_keys.add(key)
            judged_queries.add(qid)
            if row["relevance"].strip() not in {"0", "1", "2"}:
                raise ValueError(f"Invalid final relevance for {key}; expected 0, 1, or 2")
            if not row["reviewer_1"].strip() or not row["reviewer_2"].strip() or row["reviewer_1"].strip() == row["reviewer_2"].strip():
                raise ValueError(f"Relevance judgement {key} requires two distinct reviewers")
            if (row["reviewer_1"].strip(), row["reviewer_2"].strip()) != (query_map[qid]["reviewer_1"].strip(), query_map[qid]["reviewer_2"].strip()):
                raise ValueError(f"Relevance reviewers do not match pool assignment for {key}")
            if not row["evidence_note"].strip():
                raise ValueError(f"Relevance judgement {key} needs an evidence note")
            if row["reviewer_1_relevance"].strip() not in {"0", "1", "2"} or row["reviewer_2_relevance"].strip() not in {"0", "1", "2"}:
                raise ValueError(f"Relevance judgement {key} needs both independent reviewer grades")
            status = row["adjudication_status"].strip()
            if status not in {"agreed", "adjudicated"}:
                raise ValueError(f"Relevance judgement {key} is not agreed/adjudicated")
            if status == "agreed" and (row["reviewer_1_relevance"].strip() != row["reviewer_2_relevance"].strip() or row["relevance"].strip() != row["reviewer_1_relevance"].strip()):
                raise ValueError(f"Relevance reviewers disagree or final grade mismatch for {key}; adjudicate it")
            if status == "adjudicated" and (not row["adjudicator"].strip() or row["adjudicated_relevance"].strip() != row["relevance"].strip()):
                raise ValueError(f"Adjudicated relevance mismatch or missing adjudicator for {key}")
            if status == "adjudicated" and row["adjudicator"].strip() != query_map[qid]["adjudicator"].strip():
                raise ValueError(f"Relevance adjudicator does not match pool assignment for {key}")
            if (row["reviewer_1"].strip(), row["reviewer_2"].strip()) != (query_map[qid]["reviewer_1"].strip(), query_map[qid]["reviewer_2"].strip()):
                raise ValueError(f"Relevance reviewers do not match pool assignment for {key}")
            if not row["evidence_note"].strip():
                raise ValueError(f"Relevance judgment {key} needs an evidence note")
        if pair_keys != pool_pairs:
            raise ValueError(f"Relevance judgments must cover the exact frozen pool; missing={sorted(pool_pairs-pair_keys)}, extra={sorted(pair_keys-pool_pairs)}")
        missing_judgments = set(query_map) - judged_queries
        if missing_judgments:
            raise ValueError(f"Retrieval queries lack relevance judgments: {sorted(missing_judgments)}")
        query_count = len(query_map)
    candidate_rows = read_csv(artifacts["candidate_manifest"], {"query_id", "query_text", "context_json", "candidate_ids_json", "candidate_source_status", "candidate_source_error_code"})
    candidate_map = unique_rows(candidate_rows, "query_id", artifacts["candidate_manifest"])
    label_ids = unique_rows(read_csv(artifacts["identity_labels"], IDENTITY_FIELDS), "query_id", artifacts["identity_labels"])
    if set(candidate_map) != set(label_ids):
        raise ValueError("Candidate manifest query IDs must match identity labels exactly")
    seen_per_query: dict[str, set[str]] = {}
    for qid, row in candidate_map.items():
        try:
            context = json.loads(row["context_json"])
            candidate_ids = json.loads(row["candidate_ids_json"])
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid frozen candidate JSON for {qid}") from exc
        if not row["query_text"].strip() or not isinstance(context, dict) or not isinstance(candidate_ids, list) or any(not isinstance(item, str) or not item.strip() for item in candidate_ids):
            raise ValueError(f"Invalid context or candidate snapshot IDs for {qid}")
        source_status = row["candidate_source_status"].strip()
        source_error = row["candidate_source_error_code"].strip()
        if source_status not in {"ok", "empty", "failed"}:
            raise ValueError(f"Invalid candidate_source_status for {qid}: {source_status!r}")
        if (source_status == "ok") != bool(candidate_ids) or (source_status != "failed" and source_error) or (source_status == "failed" and not source_error):
            raise ValueError(f"Candidate source status, error code, and snapshot IDs disagree for {qid}")
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError(f"Duplicate candidate snapshot ID for {qid}")
        seen_per_query[qid] = set(candidate_ids)
        label = label_ids[qid]
        if row["query_text"].strip() != label["query_text"].strip() or context != json.loads(label["context_json"]):
            raise ValueError(f"Candidate manifest query text/context differs from identity annotation for {qid}")
    all_candidate_ids = sorted({candidate_id for ids in seen_per_query.values() for candidate_id in ids})
    if all_candidate_ids:
        try:
            with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
                placeholders = ",".join("?" for _ in all_candidate_ids)
                candidate_rows = connection.execute(
                    f"SELECT id, query_normalized FROM author_candidates WHERE id IN ({placeholders})",
                    all_candidate_ids,
                ).fetchall()
        except sqlite3.Error as exc:
            raise ValueError(f"Cannot verify frozen candidate IDs in database snapshot: {exc}") from exc
        candidates_by_id = {candidate_id: query for candidate_id, query in candidate_rows}
        missing_candidates = set(all_candidate_ids) - candidates_by_id.keys()
        if missing_candidates:
            raise ValueError(f"Candidate snapshot IDs missing from database snapshot: {sorted(missing_candidates)}")
        normalize = lambda text: re.sub(r"\s+", " ", text.strip().casefold())
        for query_id, row in candidate_map.items():
            if any(candidates_by_id[candidate_id] != normalize(row["query_text"]) for candidate_id in seen_per_query[query_id]):
                raise ValueError(f"Candidate snapshot ID belongs to a different query: {query_id}")
    return {"manifest": manifest, "root": root, "database_path": database, "index_path": index, "artifacts": artifacts, "annotations": annotation_summary, "retrieval_query_count": query_count, "candidate_query_count": len(candidate_map)}
