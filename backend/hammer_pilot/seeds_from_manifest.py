"""Turn a selection manifest (selector_c1c) into the capture inputs the pilot toolkit already consumes: seeds.csv, doi_register.csv and the PROTECTED gold register.

This is the missing link between sampling and capture. It reads the archive only (a second pass restricted to the selected blocks) and makes no provider request.
The row layout, the DOI purpose rules and the designated-citation rule are those of `hammer_lagos.prep.build_cases`, so the existing capture, replay and
validation code runs unchanged. Case identifiers come from the manifest (opaque). `seeds.csv` and `doi_register.csv` never contain a benchmark ORCID; the gold register
does, and must stay protected.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from hammer_lagos.prep import (DOI_FIELDS, GOLD_FIELDS, SEED_FIELDS, SPLIT_NAMES, _key, collect_rows, normalize_affiliation, normalize_doi, open_csv_rows, write_csv)

from .common import sha256_file


class SeedBuildError(ValueError):
    """The manifest, identity map and archive rows are inconsistent. Nothing is repaired silently."""


def rows_for_blocks(archive: Path, blocks: Sequence[str]) -> dict[str, list[dict[str, str]]]:
    """Second pass over the archive restricted to the selected blocks."""
    return dict(collect_rows(open_csv_rows(Path(archive)), set(blocks)))


def build_capture_inputs(manifest: Mapping[str, Any], identity_map: Mapping[str, Mapping[str, str]], catalog: Mapping[str, Mapping[str, Any]],
                         block_rows: Mapping[str, Sequence[Mapping[str, str]]], *, include_secondary: bool) -> dict[str, list[dict[str, Any]]]:
    """Seeds, DOI register and gold register for the manifest's primary cases (and, if asked, its secondary cases)."""
    seed = manifest["seed"]
    cases = list(manifest["cases"]) + (list(manifest["secondary_cases"]) if include_secondary else [])
    seeds, gold, dois = [], [], []
    for c in sorted(cases, key=lambda c: c["case_id"]):
        cid, block = c["case_id"], c["block_id"]
        ident = identity_map.get(cid)
        if ident is None or ident["block"] != block:
            raise SeedBuildError(f"{cid}: no matching identity-map entry")
        orcid = ident["orcid"]
        rows = block_rows.get(block)
        if not rows:
            raise SeedBuildError(f"{cid}: block has no rows in the archive pass")
        if len(rows) != catalog[block]["raw_rows"]:
            raise SeedBuildError(f"{cid}: complete-block check failed ({len(rows)} rows vs {catalog[block]['raw_rows']})")
        cites: dict[str, dict[str, str]] = {}
        for d in rows:
            if d["orcid"] != orcid:
                continue
            doi, _ = normalize_doi(d["doi"])
            cites.setdefault(doi, {**d, "doi_normalized": doi})
        if len(cites) < 2:
            raise SeedBuildError(f"{cid}: the group has fewer than two unique DOIs")
        with_aff = {k: v for k, v in cites.items() if normalize_affiliation(v["author_affiliation"])[0]}
        pool = with_aff or cites
        designated = min(pool, key=lambda k: _key(seed, "cite", orcid, k))
        cite = cites[designated]
        affil, _ = normalize_affiliation(cite["author_affiliation"])
        year = int(cite["pub_year"]) if cite["pub_year"].isdigit() else None
        c1: dict[str, Any] = {}
        if affil:
            c1["institutions"] = [{"name": affil}]
        if year is not None:
            c1["active_year_start"] = year
            c1["active_year_end"] = year
        split = SPLIT_NAMES[catalog[block]["split_values"][0]]
        group_id = "G" + _key(seed, "group", orcid)[:10]
        block_id = "B" + _key(seed, "blockid", block)[:8]
        seeds.append({"case_id": cid, "query_text": cite["author_name"], "identity_group_id": group_id, "planned_status": "resolved",
                      "context_c1_json": json.dumps(c1, sort_keys=True), "context_c1x_json": json.dumps({"publications": [designated]}),
                      "context_modified_after_candidates_seen": "false", "source_block_id": block_id, "source_split": split, "sampling_stratum": c["stratum"],
                      "c1_institution_missing": "true" if not affil else "false"})
        gold.append({"case_id": cid, "gold_orcid": orcid, "gold_person_id": "P" + _key(seed, "person", orcid)[:10], "source_block_id": block_id,
                     "source_block_fullname": block, "source_split": split, "groups_in_block": catalog[block]["n_groups"],
                     "group_raw_rows": sum(1 for d in rows if d["orcid"] == orcid), "group_unique_dois": len(cites), "designated_doi": designated,
                     "designated_pid_source_id": cite["pid"], "designated_source_row": cite["source_row"], "sampling_stratum": c["stratum"]})
        for doi in cites:
            if doi == designated:
                dois.append({"case_id": cid, "doi": doi, "purpose": "both", "registered_by": "dataset_builder",
                             "justification_if_both": "designated query citation: also a member of the ORCID group; exploratory C1x only, never primary C1"})
            else:
                dois.append({"case_id": cid, "doi": doi, "purpose": "gold_evidence", "registered_by": "dataset_orcid_link", "justification_if_both": ""})
    return {"seeds": seeds, "gold": gold, "dois": dois}


def write_capture_inputs(out_dir: Path, protected_dir: Path, inputs: Mapping[str, list[dict[str, Any]]], manifest: Mapping[str, Any]) -> dict[str, str]:
    """Write seeds.csv and doi_register.csv to `out_dir` (the capture directory) and the gold register to a separate protected directory (new files only)."""
    out_dir, protected_dir = Path(out_dir), Path(protected_dir)
    if out_dir.resolve() == protected_dir.resolve() or protected_dir.resolve() in out_dir.resolve().parents or out_dir.resolve() in protected_dir.resolve().parents:
        raise SeedBuildError("the protected directory must not be the capture directory or nested with it")
    hashes = {"seeds.csv": write_csv(out_dir / "seeds.csv", SEED_FIELDS, inputs["seeds"]),
              "doi_register.csv": write_csv(out_dir / "doi_register.csv", DOI_FIELDS, inputs["dois"]),
              "gold_identity_register.csv": write_csv(protected_dir / "gold_identity_register.csv", GOLD_FIELDS, inputs["gold"])}
    # The capture step (`capture.verify_seed_freeze`) requires `frozen_at`, `seeds_sha256` and `doi_register_sha256`; the first real attempt (T019) failed without them.
    freeze = {"manifest_sha256": manifest["manifest_sha256"], "role": manifest["role"], "seed": manifest["seed"], "file_sha256": hashes, "cases": len(inputs["seeds"]),
              "dataset_version": manifest.get("dataset_version", ""), "frozen_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "seeds_sha256": hashes["seeds.csv"], "doi_register_sha256": hashes["doi_register.csv"]}
    with open(out_dir / "seed_freeze.json", "x", encoding="utf-8") as f:
        f.write(json.dumps(freeze, indent=1, sort_keys=True) + "\n")
    return hashes
