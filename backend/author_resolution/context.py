"""Typed query-side context for author resolution.

The context carries only what a caller actually knows about the intended author.
Nothing here is inferred from candidates: an absent field means "not provided",
which the evidence layer reports as unavailable rather than as a mismatch.

Accepted publication identifiers are DOIs and OpenAlex work IDs. Title-only
entries are not compared (title strings are not stable publication identities);
they are recorded in ``ignored_title_only`` so the omission is visible.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

MAX_ALIASES = 10
MAX_INSTITUTIONS = 10
MAX_PUBLICATIONS = 50
MAX_COAUTHORS = 50
MAX_TEXT_LENGTH = 300
YEAR_MIN, YEAR_MAX = 1800, 2200

_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
_DOI_PREFIX_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:)\s*", re.IGNORECASE)
_OPENALEX_RE = {
    "author": re.compile(r"^A\d+$", re.IGNORECASE),
    "work": re.compile(r"^W\d+$", re.IGNORECASE),
    "institution": re.compile(r"^I\d+$", re.IGNORECASE),
}
_ROR_RE = re.compile(r"^0[a-z0-9]{8}$")


class ContextValidationError(ValueError):
    """Raised for structurally invalid caller-supplied context (strict mode)."""


def normalize_doi(value: Any) -> str | None:
    """Return a lower-case bare DOI, or None if the value is not a valid DOI."""
    if not isinstance(value, str):
        return None
    text = _DOI_PREFIX_RE.sub("", value.strip()).strip().rstrip(".,;)").lower()
    return text if _DOI_RE.match(text) else None


def normalize_openalex_id(value: Any, kind: str) -> str | None:
    """Return a bare upper-case OpenAlex ID (A…, W…, I…) from a bare ID or URL."""
    if not isinstance(value, str) or kind not in _OPENALEX_RE:
        return None
    text = value.strip().rstrip("/").rsplit("/", 1)[-1].upper()
    return text if _OPENALEX_RE[kind].match(text) else None


def normalize_ror(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip().rstrip("/").rsplit("/", 1)[-1].lower()
    return text if _ROR_RE.match(text) else None


def _clean_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = re.sub(r"\s+", " ", value).strip()
    return text[:MAX_TEXT_LENGTH] if text else None


@dataclass(frozen=True)
class InstitutionRef:
    name: str | None = None
    openalex_id: str | None = None
    ror: str | None = None


@dataclass(frozen=True)
class CoauthorRef:
    name: str | None = None
    openalex_id: str | None = None


@dataclass(frozen=True)
class QueryContext:
    aliases: tuple[str, ...] = ()
    institutions: tuple[InstitutionRef, ...] = ()
    publication_dois: tuple[str, ...] = ()
    publication_work_ids: tuple[str, ...] = ()
    coauthors: tuple[CoauthorRef, ...] = ()
    active_year_start: int | None = None
    active_year_end: int | None = None
    ignored_title_only: int = 0
    rejected_inputs: tuple[str, ...] = ()

    @property
    def has_publications(self) -> bool:
        return bool(self.publication_dois or self.publication_work_ids)

    @property
    def has_coauthors(self) -> bool:
        return bool(self.coauthors)

    @property
    def has_coauthor_ids(self) -> bool:
        """Only OpenAlex author IDs can contribute coauthor evidence; names alone cannot."""
        return any(c.openalex_id for c in self.coauthors)

    @property
    def has_years(self) -> bool:
        return self.active_year_start is not None and self.active_year_end is not None

    def publication_fingerprint(self) -> str | None:
        """Stable hash of the publication identifiers used for enrichment."""
        if not self.has_publications:
            return None
        payload = json.dumps([sorted(self.publication_dois), sorted(self.publication_work_ids)])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def provided_categories(self) -> dict[str, bool]:
        return {
            "institution": bool(self.institutions),
            "publications": self.has_publications,
            "coauthors": self.has_coauthors,
            "active_years": self.has_years,
            "aliases": bool(self.aliases),
        }

    @classmethod
    def from_any(cls, context: "QueryContext | dict[str, Any] | None", institution_hint: str | None = None, *, strict: bool = False) -> "QueryContext":
        """Build a QueryContext from the legacy dict shape and/or an institution hint.

        ``strict`` raises ContextValidationError for invalid or oversized input;
        otherwise invalid entries are recorded in ``rejected_inputs`` and omitted.
        """
        if isinstance(context, QueryContext):
            if not institution_hint:
                return context
            context = {"institution_hints": [institution_hint]}
        if not isinstance(context or {}, dict):
            raise ContextValidationError("context must be an object")
        raw = dict(context or {})
        rejected: list[str] = []

        def reject(message: str) -> None:
            if strict:
                raise ContextValidationError(message)
            rejected.append(message)

        def as_list(key: str) -> list[Any]:
            value = raw.get(key)
            if value is None:
                return []
            if isinstance(value, (str, dict)):
                return [value]
            if isinstance(value, (list, tuple)):
                return list(value)
            reject(f"{key} must be a list")
            return []

        def bounded(items: list[Any], limit: int, key: str) -> list[Any]:
            if len(items) > limit:
                reject(f"{key} accepts at most {limit} entries")
                return items[:limit]
            return items

        aliases: list[str] = []
        for item in bounded(as_list("aliases"), MAX_ALIASES, "aliases"):
            text = _clean_text(item)
            if text and text not in aliases:
                aliases.append(text)

        institution_items = as_list("institutions") + as_list("institution_hints")
        if institution_hint:
            institution_items.append(institution_hint)
        institutions: list[InstitutionRef] = []
        for item in bounded(institution_items, MAX_INSTITUTIONS, "institutions"):
            if isinstance(item, str):
                ref = InstitutionRef(name=_clean_text(item))
            elif isinstance(item, dict):
                ref = InstitutionRef(
                    name=_clean_text(item.get("name") or item.get("display_name")),
                    openalex_id=normalize_openalex_id(item.get("openalex_id") or item.get("id"), "institution"),
                    ror=normalize_ror(item.get("ror")),
                )
                supplied_id = item.get("openalex_id") or item.get("id")
                if supplied_id and not ref.openalex_id:
                    reject("institution identifier is not a valid OpenAlex institution ID")
                if item.get("ror") and not ref.ror:
                    reject("institution ROR is not valid")
            else:
                reject("institution entries must be text or objects")
                continue
            if (ref.name or ref.openalex_id or ref.ror) and ref not in institutions:
                institutions.append(ref)

        dois: list[str] = []
        work_ids: list[str] = []
        ignored_titles = 0
        for item in bounded(as_list("publications") + as_list("publication_ids"), MAX_PUBLICATIONS, "publications"):
            candidates = [item] if not isinstance(item, dict) else [item.get("doi"), item.get("openalex_id") or item.get("id")]
            recognised = False
            for value in candidates:
                if value is None:
                    continue
                doi = normalize_doi(value)
                work = normalize_openalex_id(value, "work")
                if doi:
                    recognised = True
                    if doi not in dois:
                        dois.append(doi)
                elif work:
                    recognised = True
                    if work not in work_ids:
                        work_ids.append(work)
                elif isinstance(item, str):
                    reject("publication identifiers must be DOIs or OpenAlex work IDs")
                    recognised = True
                else:
                    reject("publication identifier is not a valid DOI or OpenAlex work ID")
                    recognised = True
            if not recognised and isinstance(item, dict) and item.get("title"):
                ignored_titles += 1

        coauthors: list[CoauthorRef] = []
        for item in bounded(as_list("coauthors"), MAX_COAUTHORS, "coauthors"):
            if isinstance(item, str):
                ref = CoauthorRef(name=_clean_text(item))
            elif isinstance(item, dict):
                ref = CoauthorRef(
                    name=_clean_text(item.get("name") or item.get("display_name")),
                    openalex_id=normalize_openalex_id(item.get("openalex_id") or item.get("id"), "author"),
                )
                if (item.get("openalex_id") or item.get("id")) and not ref.openalex_id:
                    reject("coauthor identifier is not a valid OpenAlex author ID")
            else:
                reject("coauthor entries must be text or objects")
                continue
            if (ref.name or ref.openalex_id) and ref not in coauthors:
                coauthors.append(ref)

        start = raw.get("active_year_start")
        end = raw.get("active_year_end")
        year_start = year_end = None
        if start is not None or end is not None:
            try:
                year_start, year_end = int(start), int(end)
            except (TypeError, ValueError):
                reject("active_year_start and active_year_end must both be integers")
                year_start = year_end = None
            else:
                if not (YEAR_MIN <= year_start <= YEAR_MAX and YEAR_MIN <= year_end <= YEAR_MAX) or year_start > year_end:
                    reject(f"active years must be {YEAR_MIN}-{YEAR_MAX} with start <= end")
                    year_start = year_end = None

        return cls(
            aliases=tuple(aliases),
            institutions=tuple(institutions),
            publication_dois=tuple(dois),
            publication_work_ids=tuple(work_ids),
            coauthors=tuple(coauthors),
            active_year_start=year_start,
            active_year_end=year_end,
            ignored_title_only=ignored_titles,
            rejected_inputs=tuple(rejected),
        )
