"""Streaming reader, quality statistics, reproducible complete-block sampler and seed builder for LAGOS-AND v2.0.

Source schema is the *observed* 14-column BLOCK-TRIMMED header; raw field names are never renamed. Normalised values
live in separate derived structures with recorded transformation counts.

Rules applied:
  doi            publication join key (lower-cased, DOI prefix stripped; changes are counted)
  pid            kept as a source identifier; never treated as an OpenAlex ID
  duplicates     duplicate DOIs inside one (block, ORCID) group are collapsed; a DOI assigned to several ORCIDs is flagged
                 and its blocks are excluded from the sampling frame
  coauthors      parsed only to count and to strip the author's own name; never emitted into any HAMMER context
  affiliation    '#TAB#' artefacts replaced by a space and whitespace collapsed; original value preserved in the block-row file
"""
from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import re
import tarfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterator

SOURCE_COLUMNS = ["block_fullname", "orcid", "doi", "pid", "author_position", "author_name", "author_affiliation", "coauthors",
                  "coauthor_affliations", "venue", "pub_year", "paper_title", "paper_abstract", "train1_test0_val2"]
EXPECTED_ARCHIVE = {"filename": "LAGOS-AND-BLOCK-TRIMMED.csv.tar.gz", "size": 743558936, "md5": "e9e6703f98d96294e93ba105d6c1c4ac",
                    "dataset_doi": "10.5281/zenodo.7313353", "version": "2.0", "member": "LAGOS-AND-BLOCK-TRIMMED.csv"}
STRATA = (("S", 0, 9), ("M", 10, 49), ("L", 50, 199), ("XL", 200, 10**9))     # block size = unique DOIs; fixed in advance
MAX_GROUPS_PER_BLOCK = 8
SPLIT_NAMES = {"1": "train", "0": "test", "2": "val"}
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
ORCID_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
SEED_FIELDS = ["case_id", "query_text", "identity_group_id", "planned_status", "context_c1_json", "context_c1x_json",
               "context_modified_after_candidates_seen", "source_block_id", "source_split", "sampling_stratum", "c1_institution_missing"]
GOLD_FIELDS = ["case_id", "gold_orcid", "gold_person_id", "source_block_id", "source_block_fullname", "source_split", "groups_in_block",
               "group_raw_rows", "group_unique_dois", "designated_doi", "designated_pid_source_id", "designated_source_row", "sampling_stratum"]
DOI_FIELDS = ["case_id", "doi", "purpose", "registered_by", "justification_if_both"]
BLOCK_ROW_FIELDS = [c for c in SOURCE_COLUMNS if c != "paper_abstract"] + ["source_row"]


class LagosDataError(ValueError):
    """Corrupt, malformed or unexpected dataset input. Processing stops; nothing is repaired silently."""


# --------------------------------------------------------------------------- hashing and archive verification
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class _CountingReader(io.RawIOBase):
    """Adapts a tar member stream (no seek support in streaming mode) to a buffered, counted reader."""

    def __init__(self, raw):
        self.raw, self.count = raw, 0

    def readable(self):
        return True

    def readinto(self, buffer):
        data = self.raw.read(len(buffer))
        buffer[:len(data)] = data
        self.count += len(data)
        return len(data)


def verify_archive(path: Path, expected: dict[str, Any] = EXPECTED_ARCHIVE) -> dict[str, Any]:
    """Exact size, MD5 and tar/gzip integrity (every byte of the member is read). Raises LagosDataError on any mismatch."""
    path = Path(path)
    size = path.stat().st_size
    if size != expected["size"]:
        raise LagosDataError(f"archive size {size} != expected {expected['size']}")
    md5 = md5_file(path)
    if md5 != expected["md5"]:
        raise LagosDataError(f"archive MD5 {md5} != expected {expected['md5']}")
    try:
        with tarfile.open(path, "r|gz") as tar:
            members = []
            for member in tar:
                members.append((member.name, member.size))
                if member.isfile():
                    handle = tar.extractfile(member)
                    read = 0
                    while True:
                        chunk = handle.read(1 << 22)
                        if not chunk:
                            break
                        read += len(chunk)
                    if read != member.size:
                        raise LagosDataError(f"member {member.name}: read {read} bytes, header says {member.size}")
    except (tarfile.TarError, OSError, EOFError) as exc:
        raise LagosDataError(f"tar/gzip integrity check failed: {exc}") from exc
    names = [m[0] for m in members]
    if names != [expected["member"]]:
        raise LagosDataError(f"unexpected archive members: {names}")
    return {"filename": path.name, "size_bytes": size, "md5": md5, "sha256": sha256_file(path), "members": members,
            "csv_member": members[0][0], "csv_member_size": members[0][1], "tar_integrity": "ok"}


def open_csv_rows(archive: Path, member_name: str = EXPECTED_ARCHIVE["member"]) -> Iterator[tuple[int, list[str]]]:
    """Yield (source_row_number, fields) streaming straight from the archive; header is validated and skipped."""
    csv.field_size_limit(1 << 30)
    with tarfile.open(archive, "r|gz") as tar:
        for member in tar:
            if member.name != member_name:
                continue
            text = io.TextIOWrapper(io.BufferedReader(_CountingReader(tar.extractfile(member)), 1 << 20), encoding="utf-8", newline="")
            reader = csv.reader(text)
            header = next(reader, None)
            if header != SOURCE_COLUMNS:
                raise LagosDataError(f"unexpected header: {header}")
            n = 1
            while True:
                try:
                    row = next(reader)
                except StopIteration:
                    return
                except csv.Error:
                    n += 1
                    yield n, []                       # unparseable record: reported as malformed
                    continue
                n += 1
                yield n, row
            return
    raise LagosDataError(f"member {member_name} not found")


# --------------------------------------------------------------------------- normalisation
def normalize_affiliation(raw: str) -> tuple[str, list[str]]:
    out, steps = raw, []
    if "#TAB#" in out:
        out, steps = out.replace("#TAB#", " "), steps + ["tab_marker_replaced"]
    collapsed = re.sub(r"\s+", " ", out).strip()
    if collapsed != out:
        steps.append("whitespace_collapsed")
    return collapsed, steps


def normalize_doi(raw: str) -> tuple[str, list[str]]:
    out = raw.strip()
    steps = []
    if out != raw:
        steps.append("doi_whitespace_stripped")
    low = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)\s*", "", out, flags=re.IGNORECASE).lower()
    if low != out:
        steps.append("doi_normalized")
    return low, steps


def parse_name_list(raw: str) -> list[str] | None:
    text = raw.strip()
    if not text:
        return []
    try:
        value = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return None
    return [str(v) for v in value] if isinstance(value, (list, tuple)) else None


def _norm_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


def strip_own_name(coauthors: list[str], author_name: str) -> tuple[list[str], int]:
    own = _norm_name(author_name)
    kept = [c for c in coauthors if _norm_name(c) != own]
    return kept, len(coauthors) - len(kept)


def stratum_for(size: int) -> str:
    for name, lo, hi in STRATA:
        if lo <= size <= hi:
            return name
    raise LagosDataError(f"no stratum for size {size}")


# --------------------------------------------------------------------------- pass 1: statistics and frame
@dataclass
class Frame:
    stats: Counter = field(default_factory=Counter)
    missing: Counter = field(default_factory=Counter)
    split_rows: Counter = field(default_factory=Counter)
    years: list[int] = field(default_factory=lambda: [10**9, -1])
    block_rows: Counter = field(default_factory=Counter)
    block_splits: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    group_dois: dict[tuple[str, str], set[str]] = field(default_factory=lambda: defaultdict(set))
    group_rows: Counter = field(default_factory=Counter)
    doi_orcids: dict[str, Any] = field(default_factory=dict)             # doi -> orcid, or None once shared by several ORCIDs
    doi_pids: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    orcid_blocks: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    cross_group_dois: set[str] = field(default_factory=set)
    csv_bytes_seen: int = 0


def scan(rows: Iterator[tuple[int, list[str]]]) -> Frame:
    fr = Frame()
    for rownum, r in rows:
        fr.stats["rows_total"] += 1
        if len(r) != len(SOURCE_COLUMNS):
            fr.stats["malformed_rows"] += 1
            continue
        d = dict(zip(SOURCE_COLUMNS, r))
        for c in SOURCE_COLUMNS:
            if not d[c].strip() or d[c].strip() in ("[]", "nan", "NaN", "None"):
                fr.missing[c] += 1
        block, orcid = d["block_fullname"], d["orcid"]
        doi, steps = normalize_doi(d["doi"])
        for s in steps:
            fr.stats["norm_" + s] += 1
        if not DOI_RE.match(doi):
            fr.stats["invalid_doi_rows"] += 1
        if not ORCID_RE.match(orcid):
            fr.stats["invalid_orcid_rows"] += 1
        if not d["pid"].isdigit():
            fr.stats["non_numeric_pid_rows"] += 1
        if "#TAB#" in d["author_affiliation"]:
            fr.stats["affiliation_tab_marker_rows"] += 1
        if d["train1_test0_val2"] not in SPLIT_NAMES:
            fr.stats["invalid_split_rows"] += 1
        fr.split_rows[d["train1_test0_val2"]] += 1
        if d["pub_year"].isdigit():
            y = int(d["pub_year"])
            fr.years[0], fr.years[1] = min(fr.years[0], y), max(fr.years[1], y)
        else:
            fr.stats["invalid_year_rows"] += 1
        names = parse_name_list(d["coauthors"])
        if names is None:
            fr.stats["coauthors_unparseable_rows"] += 1
        else:
            _, removed = strip_own_name(names, d["author_name"])
            if removed:
                fr.stats["coauthors_self_name_rows"] += 1
        fr.block_rows[block] += 1
        fr.block_splits[block].add(d["train1_test0_val2"])
        key = (block, orcid)
        if doi in fr.group_dois[key]:
            fr.stats["duplicate_doi_rows_within_group"] += 1
        fr.group_dois[key].add(doi)
        fr.group_rows[key] += 1
        fr.orcid_blocks[orcid].add(block)
        fr.doi_pids[doi].add(d["pid"])
        seen = fr.doi_orcids.get(doi, "")
        if seen == "":
            fr.doi_orcids[doi] = orcid
        elif seen is not None and seen != orcid:
            fr.doi_orcids[doi] = None
            fr.cross_group_dois.add(doi)
    fr.stats["dois_with_multiple_pids"] = sum(1 for v in fr.doi_pids.values() if len(v) > 1)
    fr.stats["orcids_in_multiple_blocks"] = sum(1 for v in fr.orcid_blocks.values() if len(v) > 1)
    fr.stats["dois_shared_by_multiple_orcids"] = len(fr.cross_group_dois)
    return fr


def block_catalog(fr: Frame) -> dict[str, dict[str, Any]]:
    cat: dict[str, dict[str, Any]] = {}
    groups: dict[str, list[tuple[str, set[str]]]] = defaultdict(list)
    for (block, orcid), dois in fr.group_dois.items():
        groups[block].append((orcid, dois))
    for block, gl in groups.items():
        all_dois = set().union(*(d for _, d in gl))
        cat[block] = {
            "groups": sorted(o for o, _ in gl), "n_groups": len(gl), "unique_dois": len(all_dois),
            "split_values": sorted(fr.block_splits[block]), "cross_group_doi": bool(all_dois & fr.cross_group_dois),
            "case_groups": sorted(o for o, d in gl if len(d) >= 2 and o not in ()), "raw_rows": fr.block_rows[block],
        }
    return cat


def eligibility(info: dict[str, Any]) -> str | None:
    """Return None if eligible, else the exclusion reason (counted, never silent)."""
    if info["n_groups"] < 2:
        return "single_orcid_group"
    if len(info["split_values"]) != 1:
        return "mixed_source_split"
    if info["cross_group_doi"]:
        return "doi_shared_across_orcid_groups"
    if info["n_groups"] > MAX_GROUPS_PER_BLOCK:
        return "more_groups_than_cap"
    if not info["case_groups"]:
        return "no_group_with_two_unique_dois"
    return None


def _key(seed: int, *parts: str) -> str:
    return hashlib.sha256("|".join([str(seed), *parts]).encode("utf-8")).hexdigest()


def select_blocks(catalog: dict[str, dict[str, Any]], seed: int, target_cases: int) -> dict[str, Any]:
    reasons: Counter = Counter()
    strata: dict[str, list[str]] = {s[0]: [] for s in STRATA}
    for block, info in catalog.items():
        why = eligibility(info)
        if why:
            reasons[why] += 1
        else:
            strata[stratum_for(info["unique_dois"])].append(block)
    for s in strata:
        strata[s].sort(key=lambda b: _key(seed, "block", b))                 # deterministic, version-independent order
    cursor = {s: 0 for s in strata}
    chosen: list[tuple[str, str]] = []
    total = 0
    progress = True
    while total < target_cases and progress:
        progress = False
        for s in strata:
            while cursor[s] < len(strata[s]):
                block = strata[s][cursor[s]]
                cursor[s] += 1
                n = len(catalog[block]["case_groups"])
                if total + n <= target_cases:
                    chosen.append((s, block))
                    total += n
                    progress = True
                    break
    return {"selected": chosen, "cases": total, "exclusion_reasons": dict(reasons),
            "eligible_by_stratum": {s: len(v) for s, v in strata.items()}}


# --------------------------------------------------------------------------- pass 2 and seed construction
def collect_rows(rows: Iterator[tuple[int, list[str]]], wanted_blocks: set[str]) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    for rownum, r in rows:
        if len(r) != len(SOURCE_COLUMNS) or r[0] not in wanted_blocks:
            continue
        d = dict(zip(SOURCE_COLUMNS, r))
        d["source_row"] = str(rownum)
        out[d["block_fullname"]].append(d)
    return out


def build_cases(selection: dict[str, Any], catalog: dict[str, dict[str, Any]], block_rows: dict[str, list[dict[str, str]]], seed: int) -> dict[str, Any]:
    raw_cases = []
    for stratum, block in selection["selected"]:
        rows = block_rows.get(block)
        if not rows:
            raise LagosDataError(f"selected block {block!r} has no rows in the second pass (input changed between passes)")
        if len(rows) != catalog[block]["raw_rows"]:
            raise LagosDataError(f"block {block!r}: complete-block check failed ({len(rows)} rows vs {catalog[block]['raw_rows']})")
        by_group: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
        dup_counts: Counter = Counter()
        for d in rows:
            doi, _ = normalize_doi(d["doi"])
            if doi in by_group[d["orcid"]]:
                dup_counts[d["orcid"]] += 1
                continue
            by_group[d["orcid"]][doi] = {**d, "doi_normalized": doi}
        for orcid in catalog[block]["case_groups"]:
            cites = by_group[orcid]
            with_aff = {k: v for k, v in cites.items() if normalize_affiliation(v["author_affiliation"])[0]}
            pool = with_aff or cites
            designated = min(pool, key=lambda k: _key(seed, "cite", orcid, k))
            raw_cases.append({"stratum": stratum, "block": block, "orcid": orcid, "cites": cites, "designated": designated,
                              "n_groups": catalog[block]["n_groups"], "raw_rows": sum(1 for d in rows if d["orcid"] == orcid),
                              "split": SPLIT_NAMES[catalog[block]["split_values"][0]]})
    raw_cases.sort(key=lambda c: _key(seed, "case", c["block"], c["orcid"]))
    seeds, gold, dois = [], [], []
    for i, c in enumerate(raw_cases, 1):
        case_id = f"LG{i:03d}"
        cite = c["cites"][c["designated"]]
        affil, _ = normalize_affiliation(cite["author_affiliation"])
        year = int(cite["pub_year"]) if cite["pub_year"].isdigit() else None
        c1: dict[str, Any] = {}
        if affil:
            c1["institutions"] = [{"name": affil}]
        if year is not None:
            c1["active_year_start"] = year
            c1["active_year_end"] = year
        block_id = "B" + _key(seed, "blockid", c["block"])[:8]
        group_id = "G" + _key(seed, "group", c["orcid"])[:10]
        seeds.append({"case_id": case_id, "query_text": cite["author_name"], "identity_group_id": group_id, "planned_status": "resolved",
                      "context_c1_json": json.dumps(c1, sort_keys=True), "context_c1x_json": json.dumps({"publications": [c["designated"]]}),
                      "context_modified_after_candidates_seen": "false", "source_block_id": block_id, "source_split": c["split"],
                      "sampling_stratum": c["stratum"], "c1_institution_missing": "true" if not affil else "false"})
        gold.append({"case_id": case_id, "gold_orcid": c["orcid"], "gold_person_id": "P" + _key(seed, "person", c["orcid"])[:10],
                     "source_block_id": block_id, "source_block_fullname": c["block"], "source_split": c["split"], "groups_in_block": c["n_groups"],
                     "group_raw_rows": c["raw_rows"], "group_unique_dois": len(c["cites"]), "designated_doi": c["designated"],
                     "designated_pid_source_id": cite["pid"], "designated_source_row": cite["source_row"], "sampling_stratum": c["stratum"]})
        for doi in c["cites"]:
            if doi == c["designated"]:
                dois.append({"case_id": case_id, "doi": doi, "purpose": "both", "registered_by": "dataset_builder",
                             "justification_if_both": "designated query citation: also a member of the ORCID group; exploratory C1x only, never primary C1"})
            else:
                dois.append({"case_id": case_id, "doi": doi, "purpose": "gold_evidence", "registered_by": "dataset_orcid_link", "justification_if_both": ""})
    return {"seeds": seeds, "gold": gold, "dois": dois, "raw_cases": raw_cases}


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", newline="", encoding="utf-8") as stream:
        w = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return sha256_file(path)


def code_hash() -> str:
    h = hashlib.sha256()
    for p in sorted(Path(__file__).resolve().parent.glob("*.py")):
        h.update(p.name.encode() + p.read_bytes())
    return h.hexdigest()


def quality_report(fr: Frame, catalog: dict[str, dict[str, Any]], selection: dict[str, Any], archive_info: dict[str, Any] | None) -> dict[str, Any]:
    groups_per_block = Counter(info["n_groups"] for info in catalog.values())
    rows_per_group = sorted(fr.group_rows.values())
    n = fr.stats["rows_total"]
    split_blocks = Counter(info["split_values"][0] for info in catalog.values() if len(info["split_values"]) == 1)
    return {
        "rows_total": n, "rows_parsed": n - fr.stats["malformed_rows"], "malformed_rows": fr.stats["malformed_rows"],
        "blocks": len(catalog), "orcid_groups_block_orcid_pairs": len(fr.group_dois), "distinct_orcids": len(fr.orcid_blocks),
        "missing_values_by_column": {c: {"count": fr.missing[c], "fraction": round(fr.missing[c] / n, 6) if n else None} for c in SOURCE_COLUMNS},
        "counters": dict(sorted(fr.stats.items())),
        "duplicate_doi_row_fraction_within_group": round(fr.stats["duplicate_doi_rows_within_group"] / n, 6) if n else None,
        "row_split_distribution": dict(sorted(fr.split_rows.items())), "block_split_distribution": dict(sorted(split_blocks.items())),
        "blocks_with_mixed_split": sum(1 for i in catalog.values() if len(i["split_values"]) > 1),
        "groups_per_block_distribution": dict(sorted(groups_per_block.items())),
        "rows_per_group": {"min": rows_per_group[0], "median": rows_per_group[len(rows_per_group) // 2], "max": rows_per_group[-1]} if rows_per_group else None,
        "pub_year_range": fr.years if fr.years[1] >= 0 else None,
        "sampling_frame": {"eligible_blocks_by_stratum": selection["eligible_by_stratum"], "exclusion_reasons": selection["exclusion_reasons"],
                           "eligible_blocks_total": sum(selection["eligible_by_stratum"].values())},
        "archive": archive_info,
    }


def quality_markdown(report: dict[str, Any]) -> str:
    c = report["counters"]
    lines = ["# LAGOS-AND v2.0 BLOCK-TRIMMED: dataset quality report", "",
             f"Rows: {report['rows_total']:,} ({report['malformed_rows']} malformed). Blocks: {report['blocks']:,}. (block, ORCID) groups: {report['orcid_groups_block_orcid_pairs']:,}. Distinct ORCIDs: {report['distinct_orcids']:,}.", "",
             "## Missing values", "", "| column | missing | fraction |", "|---|---:|---:|"]
    lines += [f"| {k} | {v['count']:,} | {v['fraction']} |" for k, v in report["missing_values_by_column"].items()]
    lines += ["", "## Counters", ""] + [f"- {k}: {v:,}" for k, v in c.items()]
    lines += ["", f"Duplicate-DOI row fraction within groups: {report['duplicate_doi_row_fraction_within_group']}",
              f"Row split distribution: {report['row_split_distribution']}; block split distribution: {report['block_split_distribution']}; blocks with mixed split: {report['blocks_with_mixed_split']}",
              f"Groups per block: {report['groups_per_block_distribution']}", f"Rows per group: {report['rows_per_group']}", f"Publication years: {report['pub_year_range']}",
              "", "## Sampling frame", "", f"Eligible blocks by stratum: {report['sampling_frame']['eligible_blocks_by_stratum']}",
              f"Exclusions: {report['sampling_frame']['exclusion_reasons']}"]
    return "\n".join(lines) + "\n"


def prepare(archive: Path, out_dir: Path, *, seed: int, target_cases: int, expected: dict[str, Any] = EXPECTED_ARCHIVE, sampling_date: str | None = None,
            verify: bool = True, max_malformed_fraction: float = 0.001) -> dict[str, Any]:
    archive, out_dir = Path(archive), Path(out_dir)
    info = verify_archive(archive, expected) if verify else None
    fr = scan(open_csv_rows(archive, expected["member"]))
    if fr.stats["rows_total"] == 0:
        raise LagosDataError("no data rows")
    if fr.stats["malformed_rows"] / fr.stats["rows_total"] > max_malformed_fraction:
        raise LagosDataError(f"too many malformed rows: {fr.stats['malformed_rows']} of {fr.stats['rows_total']}")
    catalog = block_catalog(fr)
    selection = select_blocks(catalog, seed, target_cases)
    wanted = {b for _, b in selection["selected"]}
    block_rows = collect_rows(open_csv_rows(archive, expected["member"]), wanted)
    built = build_cases(selection, catalog, block_rows, seed)
    hashes = {}
    hashes["seeds.csv"] = write_csv(out_dir / "seeds.csv", SEED_FIELDS, built["seeds"])
    hashes["gold_identity_register.csv"] = write_csv(out_dir / "gold_identity_register.csv", GOLD_FIELDS, built["gold"])
    hashes["doi_purpose_register.csv"] = write_csv(out_dir / "doi_purpose_register.csv", DOI_FIELDS, built["dois"])
    flat = [{**{k: v for k, v in d.items() if k in BLOCK_ROW_FIELDS}} for rows in (block_rows[b] for _, b in selection["selected"]) for d in rows]
    hashes["selected_block_rows.csv"] = write_csv(out_dir / "selected_block_rows.csv", BLOCK_ROW_FIELDS, flat)
    report = quality_report(fr, catalog, selection, info)
    report_json = json.dumps(report, sort_keys=True, indent=2) + "\n"
    (out_dir / "dataset_quality_report.json").write_text(report_json, encoding="utf-8")
    (out_dir / "dataset_quality_report.md").write_text(quality_markdown(report), encoding="utf-8")
    hashes["dataset_quality_report.json"] = sha256_file(out_dir / "dataset_quality_report.json")
    hashes["dataset_quality_report.md"] = sha256_file(out_dir / "dataset_quality_report.md")
    split_dist = Counter(s["source_split"] for s in built["seeds"])
    manifest = {
        "dataset": {"doi": expected["dataset_doi"], "version": expected["version"], "archive_filename": expected["filename"],
                    "archive_size_bytes": info["size_bytes"] if info else None, "archive_md5_verified": info["md5"] if info else None,
                    "archive_sha256": info["sha256"] if info else None, "csv_member": expected["member"],
                    "csv_member_size_bytes": info["csv_member_size"] if info else None, "tar_integrity": info["tar_integrity"] if info else "not_checked"},
        "sampling": {"seed": seed, "algorithm": "complete-block sampling; eligible blocks ordered by sha256(seed|block) within fixed size strata (unique DOIs: S 0-9, M 10-49, L 50-199, XL 200+); round-robin across strata; a block is taken only if all of its query-eligible groups fit the target; designated citation = minimum sha256(seed|orcid|doi) among citations with an affiliation (else any)",
                     "stratification": "block size only", "max_groups_per_block": MAX_GROUPS_PER_BLOCK, "target_cases": target_cases,
                     "sampling_date": sampling_date or date.today().isoformat()},
        "counts": {"rows_total": fr.stats["rows_total"], "blocks_total": len(catalog), "eligible_blocks": sum(selection["eligible_by_stratum"].values()),
                   "selected_blocks": len(selection["selected"]), "selected_cases": len(built["seeds"]), "exclusion_reasons": selection["exclusion_reasons"],
                   "selected_blocks_by_stratum": dict(Counter(s for s, _ in selection["selected"]))},
        "source_split_distribution_of_cases": dict(split_dist),
        "normalization_rules": ["doi: trimmed, DOI prefix removed, lower-cased (counts in dataset_quality_report.json)", "pid: kept verbatim as a source identifier, never an OpenAlex ID",
                                "duplicate DOIs inside one (block, ORCID) group collapsed; DOIs shared by several ORCIDs flagged and their blocks excluded",
                                "coauthors: parsed to strip the author's own name and counted; never emitted into any HAMMER context",
                                "affiliation: '#TAB#' replaced by a space, whitespace collapsed; originals kept in selected_block_rows.csv"],
        "normalization_counts": {k: v for k, v in fr.stats.items() if k.startswith(("norm_", "coauthors_", "affiliation_", "duplicate_"))},
        "hammer_conditions": {"C0": "name only", "C1": "institution + active-year range from the designated citation; no DOI, no coauthors, no ORCID",
                              "C1x": "C1 plus the designated citation's DOI (exploratory); coauthor evidence is never supplied"},
        "code_sha256": code_hash(), "derived_file_sha256": hashes,
        "variable_fields": ["sampling.sampling_date"],
    }
    (out_dir / "sampling_manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return manifest
