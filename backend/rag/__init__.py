"""Dense Semantic Vector Retrieval Subsystem for HAMMER."""
from rag.retrieval import (
    ScholarlyDocument,
    RetrievalHit,
    build_document,
    index_status,
    build_index,
    retrieve,
    INDEX_PATH,
    COLLECTION_NAME,
)

__all__ = [
    "ScholarlyDocument",
    "RetrievalHit",
    "build_document",
    "index_status",
    "build_index",
    "retrieve",
    "INDEX_PATH",
    "COLLECTION_NAME",
]
