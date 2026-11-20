"""Blinded dossier packet builder and leak scanner (Decision B: B1 two-stage review, B3 allow-list, hash-seeded shuffle, opaque IDs, zero-match leak scan).

Offline and pure. It builds reviewer-facing packet dictionaries from benchmark rows (Stage A) and provider author objects (Stage B), keeping only explicitly
allow-listed fields. It never writes to a provider, chooses a parameter (the group-paper cap K, the works cap and the seed are required arguments) or reads
an ORCID value into a packet. The mapping from opaque identifiers to candidates (the crosswalk) and the flag that says which cases were automatic or audited are
returned separately and are never part of a packet.

Leak scan (zero-match before release): an ORCID-shaped string or orcid.org URL anywhere; a key containing "orcid"; an OpenAlex identifier or URL; a provider
field that reveals rank or the profile (relevance_score, works_api_url, block_key, ...); a HAMMER output term in a key; and, if supplied, any exact gold value.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCANNER_VERSION = "dossier-leakscan-1"
ORCID_RE = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dXx]")
ORCID_HOST_RE = re.compile(r"orcid\.org", re.I)
OPENALEX_RE = re.compile(r"(openalex\.org|api\.openalex)", re.I)
OPENALEX_ID_RE = re.compile(r"\bA\d{8,11}\b")
FORBIDDEN_KEY_RE = re.compile(r"(orcid|openalex|relevance|score|rank|signal|selected|decision|policy|hammer|block_key|works_api_url|awards_api_url|provider_order|crosswalk|gold|pid\b)", re.I)

STAGE_A_PAPER_FIELDS = ("title", "doi", "year", "venue", "author_names", "affiliation", "coauthor_names")
STAGE_B_WORK_FIELDS = ("title", "doi", "year", "venue", "author_names")


class DossierError(ValueError):
    """Invalid input to the packet builder."""


class LeakFound(DossierError):
    """A packet failed the zero-match leak scan and must not be released."""

    def __init__(self, report: Mapping[str, Any]):
        super().__init__(f"leak scan found {len(report['findings'])} problem(s): {[f['type'] for f in report['findings']]}")
        self.report = report


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def key(seed: int | str, *parts: str) -> str:
    return sha256_text("|".join([str(seed), *map(str, parts)]))


def _need_int(name: str, value: Any, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise DossierError(f"{name} must be an integer of at least {minimum}, got {value!r}")
    return value


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _names(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return [_text(v) for v in (value or []) if _text(v)]


# --------------------------------------------------------------------------- Stage A
def build_stage_a_packet(case_id: str, query_name: str, papers: Sequence[Mapping[str, Any]], *, seed: int | str, k: int, designated_doi: str) -> dict[str, Any]:
    """Identity packet: the printed query name and up to K group papers (the designated paper always included, the rest chosen and ordered by hash).
    Only allow-listed paper fields are copied; ORCID, pid, block name, split flag and source row never are."""
    k = _need_int("K", k, 1)
    designated = [p for p in papers if _text(p.get("doi")).lower() == designated_doi.strip().lower()]
    if len(designated) != 1:
        raise DossierError(f"the designated paper must appear exactly once among the group papers (found {len(designated)})")
    others = sorted((p for p in papers if p is not designated[0]), key=lambda p: key(seed, "stage_a", case_id, _text(p.get("doi")) or _text(p.get("title"))))
    chosen = [designated[0]] + others[: k - 1]
    chosen.sort(key=lambda p: key(seed, "stage_a_order", case_id, _text(p.get("doi")) or _text(p.get("title"))))
    return {"packet_type": "stage_a", "packet_id": "A-" + key(seed, "packet", "stage_a", case_id)[:12], "query_name": _text(query_name),
            "paper_count_shown": len(chosen), "papers": [{"title": _text(p.get("title")), "doi": _text(p.get("doi")), "year": _text(p.get("year")), "venue": _text(p.get("venue")),
                                                        "author_names": _names(p.get("author_names")), "affiliation": _text(p.get("affiliation")),
                                                        "coauthor_names": _names(p.get("coauthor_names"))} for p in chosen]}


# --------------------------------------------------------------------------- Stage B
def allowlisted_candidate(item: Mapping[str, Any]) -> dict[str, Any]:
    """Copy only allow-listed facts of a provider author object. Identifiers, URLs, ORCID fields, rank and every unknown field are dropped by construction."""
    affiliations = []
    for a in item.get("affiliations") or []:
        inst = (a or {}).get("institution") or {}
        if _text(inst.get("display_name")):
            affiliations.append({"institution": _text(inst["display_name"]), "country": _text(inst.get("country_code")), "years": sorted(int(y) for y in (a.get("years") or []) if isinstance(y, int))})
    topics = [{"topic": _text(t.get("display_name")), "field": _text((t.get("field") or {}).get("display_name")), "works": t.get("count")}
              for t in (item.get("topics") or [])[:10] if _text((t or {}).get("display_name"))]
    yearly = [{"year": c.get("year"), "works": c.get("works_count")} for c in (item.get("counts_by_year") or []) if isinstance(c, Mapping) and isinstance(c.get("year"), int)]
    return {"display_name": _text(item.get("display_name")), "name_variants": _names(item.get("display_name_alternatives")), "affiliations": affiliations,
            "last_known_institutions": [_text((i or {}).get("display_name")) for i in (item.get("last_known_institutions") or []) if _text((i or {}).get("display_name"))],
            "topics": topics, "works_count": item.get("works_count") if isinstance(item.get("works_count"), int) else None, "works_per_year": sorted(yearly, key=lambda y: y["year"])}


def allowlisted_work(work: Mapping[str, Any]) -> dict[str, Any]:
    names = []
    for a in work.get("authorships") or []:
        n = _text(((a or {}).get("author") or {}).get("display_name"))
        if n:
            names.append(n)
    names = names or _names(work.get("author_names"))
    return {"title": _text(work.get("title") or work.get("display_name")), "doi": _text(work.get("doi")), "year": _text(work.get("publication_year") or work.get("year")),
            "venue": _text(work.get("venue") or ((work.get("primary_location") or {}).get("source") or {}).get("display_name")), "author_names": names}


def build_stage_b_packet(case_id: str, candidates: Sequence[Mapping[str, Any]], *, seed: int | str, works_cap: int,
                         works_by_candidate: Mapping[str, Sequence[Mapping[str, Any]]] | None = None) -> tuple[dict[str, Any], dict[str, str]]:
    """Candidate packet: every pool candidate, allow-listed, in a hash-seeded order independent of provider and HAMMER rank, under opaque identifiers.
    Returns (packet, crosswalk); the crosswalk (opaque id to provider candidate id) must be held outside any reviewer-facing location."""
    works_cap = _need_int("works cap", works_cap, 0)
    ids = [_text(c.get("id")).rsplit("/", 1)[-1] for c in candidates]
    if any(not i for i in ids) or len(set(ids)) != len(ids):
        raise DossierError("every candidate needs a unique provider id (used only for the crosswalk)")
    order = sorted(range(len(candidates)), key=lambda i: key(seed, "stage_b", case_id, ids[i]))
    entries, crosswalk = [], {}
    for pos, i in enumerate(order, 1):
        opaque = "K-" + key(seed, "candidate", case_id, ids[i])[:10]
        works = [allowlisted_work(w) for w in (works_by_candidate or {}).get(ids[i], [])]
        works = sorted(works, key=lambda w: (-(int(w["year"]) if w["year"].isdigit() else 0), key(seed, "works", opaque, w["doi"] or w["title"])))[:works_cap]
        entries.append({"candidate": opaque, "position": pos, **allowlisted_candidate(candidates[i]), "works_shown": works})
        crosswalk[opaque] = ids[i]
    return {"packet_type": "stage_b", "packet_id": "B-" + key(seed, "packet", "stage_b", case_id)[:12], "candidate_count": len(entries), "candidates": entries}, crosswalk


# --------------------------------------------------------------------------- leak scan and release
def _walk(obj: Any, path: str = "$") -> Iterable[tuple[str, str, Any]]:
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            yield "key", f"{path}.{k}", k
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield "value", path, obj


def leak_scan(packet: Mapping[str, Any], *, gold_values: Sequence[str] = ()) -> dict[str, Any]:
    """Zero-match scan of a reviewer-facing packet. The report stores the packet hash and the scanner version."""
    findings: list[dict[str, str]] = []
    gold = [g for g in gold_values if g]
    for kind, path, item in _walk(packet):
        if kind == "key":
            if FORBIDDEN_KEY_RE.search(str(item)):
                findings.append({"type": "forbidden_key", "where": path})
            continue
        text = str(item)
        for name, rx in (("orcid_pattern", ORCID_RE), ("orcid_url", ORCID_HOST_RE), ("openalex_url", OPENALEX_RE), ("openalex_id", OPENALEX_ID_RE)):
            if rx.search(text):
                findings.append({"type": name, "where": path})
        if any(g in text for g in gold):
            findings.append({"type": "gold_value", "where": path})
    return {"scanner": SCANNER_VERSION, "packet_id": packet.get("packet_id"), "packet_sha256": sha256_text(canonical(packet)), "findings": findings, "released": not findings}


def release(packet: Mapping[str, Any], *, gold_values: Sequence[str] = ()) -> tuple[Mapping[str, Any], dict[str, Any]]:
    """Return (packet, scan report) only if the scan finds nothing; otherwise raise LeakFound."""
    report = leak_scan(packet, gold_values=gold_values)
    if not report["released"]:
        raise LeakFound(report)
    return packet, report


def verify_packet(packet: Mapping[str, Any], report: Mapping[str, Any]) -> bool:
    """True if the packet is byte-for-byte the packet that was scanned (detects hand edits after release)."""
    return report.get("released") is True and report.get("packet_sha256") == sha256_text(canonical(packet))


def build_queue(packets: Sequence[Mapping[str, Any]], *, seed: int | str) -> list[str]:
    """Reviewer queue: packet ids in hash order, independent of whether a case is an automatic assignment or an audited non-automatic case."""
    return [p["packet_id"] for p in sorted(packets, key=lambda p: key(seed, "queue", p["packet_id"]))]


def write_release(reviewer_dir: Path, protected_dir: Path, packets: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]], crosswalk: Mapping[str, Any],
                  case_flags: Mapping[str, str]) -> dict[str, str]:
    """Write released packets and scan reports to the reviewer directory and the crosswalk and case flags to a separate protected directory (new files only)."""
    reviewer_dir, protected_dir = Path(reviewer_dir), Path(protected_dir)
    if reviewer_dir.resolve() == protected_dir.resolve() or protected_dir.resolve() in reviewer_dir.resolve().parents or reviewer_dir.resolve() in protected_dir.resolve().parents:
        raise DossierError("the protected directory must not be the reviewer directory or nested with it")
    reviewer_dir.mkdir(parents=True, exist_ok=False)
    protected_dir.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for packet, report in packets:
        if not verify_packet(packet, report):
            raise DossierError(f"packet {packet.get('packet_id')} is not a released, unmodified packet")
        for name, obj in ((f"{packet['packet_id']}.json", packet), (f"{packet['packet_id']}.scan.json", report)):
            with open(reviewer_dir / name, "x", encoding="utf-8") as f:
                f.write(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
        hashes[packet["packet_id"]] = report["packet_sha256"]
    for name, obj in (("crosswalk.json", crosswalk), ("case_flags.json", case_flags)):
        with open(protected_dir / name, "x", encoding="utf-8") as f:
            f.write(json.dumps(obj, indent=1, sort_keys=True) + "\n")
    return hashes
