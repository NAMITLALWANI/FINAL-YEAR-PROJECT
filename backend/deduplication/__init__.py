"""Publication Normalization and Deduplication Subsystem for HAMMER."""
from deduplication.normalize import (
    CanonicalRecord,
    normalize,
    normalized_title_for_compare,
    normalize_author_key,
    author_key_set,
)
from deduplication.engine import (
    deduplicate,
    deduplicate_v1,
    MergedPublication,
    _title_sim as title_similarity,
    _author_sim as author_similarity,
    _fuzzy_score as calculate_similarity,
)

__all__ = [
    "CanonicalRecord",
    "normalize",
    "normalized_title_for_compare",
    "normalize_author_key",
    "author_key_set",
    "deduplicate",
    "deduplicate_v1",
    "MergedPublication",
    "title_similarity",
    "author_similarity",
    "calculate_similarity",
]
