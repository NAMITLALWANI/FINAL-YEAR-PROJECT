"""Typed, serialisable candidate-side enrichment evidence.

``status`` values:
  not_requested  - no query input required this evidence, nothing was retrieved
  ok             - retrieval succeeded and produced usable data
  empty          - retrieval succeeded and returned nothing usable (not a failure)
  failed         - retrieval failed (timeout, HTTP error, malformed body, ...)

Unknown (``None`` evidence object) is distinct from empty (``status == "empty"``)
and from failed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

NOT_REQUESTED = "not_requested"
OK = "ok"
EMPTY = "empty"
FAILED = "failed"


@dataclass(frozen=True)
class PublicationLinkEvidence:
    """Which of the query's own works list this candidate as an author."""
    status: str
    context_fingerprint: str | None = None
    comparable_work_ids: tuple[str, ...] = ()
    matched_work_ids: tuple[str, ...] = ()
    matched_dois: tuple[str, ...] = ()
    unresolved_identifiers: tuple[str, ...] = ()
    truncated_author_work_ids: tuple[str, ...] = ()
    retrieved_at: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "PublicationLinkEvidence | None":
        if not isinstance(data, dict) or "status" not in data:
            return None
        tup = lambda key: tuple(str(x) for x in (data.get(key) or []))
        return cls(
            status=str(data["status"]), context_fingerprint=data.get("context_fingerprint"),
            comparable_work_ids=tup("comparable_work_ids"), matched_work_ids=tup("matched_work_ids"),
            matched_dois=tup("matched_dois"), unresolved_identifiers=tup("unresolved_identifiers"),
            truncated_author_work_ids=tup("truncated_author_work_ids"), retrieved_at=data.get("retrieved_at"),
            provenance=dict(data.get("provenance") or {}), error_code=data.get("error_code"),
        )


@dataclass(frozen=True)
class CoauthorEvidence:
    """Coauthors derived from the candidate's own works' authorships (stable OpenAlex IDs)."""
    status: str
    coauthors: tuple[dict[str, Any], ...] = ()   # {"openalex_id", "display_name", "work_ids"}
    works_examined: int = 0
    works_total: int | None = None
    complete: bool = False                        # True only if every one of the author's works was examined
    retrieved_at: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["coauthors"] = [dict(c) for c in self.coauthors]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "CoauthorEvidence | None":
        if not isinstance(data, dict) or "status" not in data:
            return None
        return cls(
            status=str(data["status"]), coauthors=tuple(dict(c) for c in (data.get("coauthors") or []) if isinstance(c, dict)),
            works_examined=int(data.get("works_examined") or 0), works_total=data.get("works_total"),
            complete=bool(data.get("complete")), retrieved_at=data.get("retrieved_at"),
            provenance=dict(data.get("provenance") or {}), error_code=data.get("error_code"),
        )
