"""Fill snapshot identifiers and checksums, then validate and seal a dataset manifest."""
from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

try:
    from .evaluation_dataset import sha256_file, sha256_tree, validate_dataset_manifest
except ImportError:  # Executed as `python scripts/seal_evaluation_manifest.py` from backend/.
    from evaluation_dataset import sha256_file, sha256_tree, validate_dataset_manifest


def _resolve(root: Path, entry: dict[str, Any], key: str) -> Path:
    path = entry.get("path")
    if not isinstance(path, str) or not path.strip():
        raise ValueError(f"Manifest draft artifact {key} needs a relative or absolute path")
    return Path(path) if Path(path).is_absolute() else (root / path).resolve()


def seal_manifest(draft_path: Path, output: Path, *, minimum_queries: int = 100) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite sealed dataset manifest: {output}")
    if output.resolve().parent != draft_path.resolve().parent:
        raise ValueError("Sealed manifest must be written next to its draft so relative artifact paths remain stable")
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    root = draft_path.resolve().parent
    db_entry = draft["database_snapshot"]
    db_path = _resolve(root, db_entry, "database_snapshot")
    if Path(str(db_path) + "-wal").exists() or Path(str(db_path) + "-shm").exists():
        raise ValueError("Create a checkpointed, closed SQLite snapshot before sealing")
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        publications = connection.execute("SELECT COUNT(*) FROM publications").fetchone()[0]
    db_entry["sha256"] = sha256_file(db_path)
    db_entry["alembic_revision"] = revision
    db_entry["publication_count"] = publications

    index_entry = draft["index_snapshot"]
    index_path = _resolve(root, index_entry, "index_snapshot")
    chroma_db = index_path / "chroma.sqlite3"
    if Path(str(chroma_db) + "-wal").exists() or Path(str(chroma_db) + "-shm").exists():
        raise ValueError("Copy a closed, checkpointed Chroma index before sealing")
    with sqlite3.connect(f"file:{chroma_db}?mode=ro", uri=True) as connection:
        collection = connection.execute("SELECT id,name FROM collections WHERE name = ?", (index_entry.get("collection"),)).fetchone()
        if not collection:
            raise ValueError("Requested collection is missing from Chroma snapshot")
        count = connection.execute("SELECT COUNT(*) FROM embeddings WHERE segment_id IN (SELECT id FROM segments WHERE collection = ? AND scope = 'METADATA')", (collection[0],)).fetchone()[0]
        version = {row[0] for row in connection.execute("SELECT DISTINCT m.string_value FROM embedding_metadata m JOIN embeddings e ON e.id=m.id JOIN segments s ON s.id=e.segment_id WHERE s.collection=? AND s.scope='METADATA' AND m.key='index_version'", (collection[0],)).fetchall()}
        models = {row[0] for row in connection.execute("SELECT DISTINCT m.string_value FROM embedding_metadata m JOIN embeddings e ON e.id=m.id JOIN segments s ON s.id=e.segment_id WHERE s.collection=? AND s.scope='METADATA' AND m.key='embedding_model'", (collection[0],)).fetchall()}
    if len(version) != 1 or len(models) != 1:
        raise ValueError("Chroma snapshot must have exactly one recorded index version and embedding model")
    index_entry["sha256"] = sha256_tree(index_path)
    index_entry["index_version"] = next(iter(version))
    index_entry["embedding_model"] = next(iter(models))
    index_entry["document_count"] = count

    names = ("candidate_manifest", "identity_labels", "split_manifest", "split_freeze", "retrieval_queries", "retrieval_pool", "retrieval_judgements")
    for name in names:
        entry = draft.get(name)
        if entry is None:
            continue
        artifact_path = _resolve(root, entry, name)
        entry["sha256"] = sha256_tree(artifact_path) if artifact_path.is_dir() else sha256_file(artifact_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", dir=output.parent, delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(draft, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    created_output = False
    try:
        validate_dataset_manifest(temporary, minimum_queries=minimum_queries, require_retrieval="retrieval_queries" in draft)
        # Output sits beside the draft so all relative artifact paths remain valid.
        with output.open("x", encoding="utf-8") as sealed_stream:
            created_output = True
            sealed_stream.write(temporary.read_text(encoding="utf-8"))
    except Exception:
        if created_output:
            output.unlink(missing_ok=True)
        raise
    finally:
        temporary.unlink(missing_ok=True)
    return draft


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = seal_manifest(args.draft, args.output)
    print(f"Sealed dataset {manifest['dataset_id']} {manifest['dataset_version']} at {args.output}")


if __name__ == "__main__":
    main()