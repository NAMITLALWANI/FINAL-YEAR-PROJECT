"""Deterministic selector and manifest builder for the pilot, main and audit draws (Decisions C1c, C3, C4, C9 and the Decision A audit).

Offline and pure: it consumes a block catalog (the structure produced by `hammer_lagos.prep.block_catalog`) and writes plain dictionaries. It does not open the
LAGOS archive, touch a provider, or choose any parameter: seeds, per-stratum sizes, N, floors, the audit size and the stratum-merging rule are required arguments.

Rules implemented
  frame        eligible blocks (hammer_lagos.prep.eligibility) of one source split, minus excluded blocks (smoke, pilot); strata are the fixed S/M/L/XL bands
  order        within a stratum, blocks are ordered by SHA-256 of "seed|role|block"; the first n_h are drawn (equivalent to simple random sampling without replacement)
  primary      per drawn block, the case-eligible group with the smallest SHA-256 of "seed|primary|block|orcid"; the other case-eligible groups are secondary
  pilot        drawn before the main sample; the post-exclusion stratum sizes are computed right after the pilot draw and before sizing (clarification X-02)
  main         allocation by the C3 algorithm (sizing_c9.allocate) over the post-exclusion frame
  audit        proportional stratified draw from the non-automatic primary cases (largest remainder, SHA-256 order), with an explicit, pre-declared merging rule;
               every automatic case is placed in the verification population
Case identifiers are opaque. The identity map (case identifier to benchmark ORCID) is returned separately and never appears in a manifest. Manifests carry a
SHA-256 over their canonical JSON and the hash of this module's source.
"""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence

from hammer_lagos.prep import EXPECTED_ARCHIVE, SPLIT_NAMES, STRATA, block_catalog, eligibility, open_csv_rows, scan, stratum_for, verify_archive

from .sizing_c9 import allocate, validate_floors, validate_frame

STRATUM_ORDER = tuple(s[0] for s in STRATA)
SPLIT_CODE = {name: code for code, name in SPLIT_NAMES.items()}
ROLES = ("pilot", "main")


class SelectionError(ValueError):
    """Invalid selection input. Raised instead of guessing or silently dropping."""


def source_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def key(seed: int | str, role: str, *parts: str) -> str:
    """Deterministic, version-independent ordering key."""
    return hashlib.sha256("|".join([str(seed), role, *map(str, parts)]).encode("utf-8")).hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def seal(manifest: dict[str, Any]) -> dict[str, Any]:
    body = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    return {**body, "manifest_sha256": hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()}


def verify_manifest(manifest: Mapping[str, Any]) -> bool:
    body = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    return manifest.get("manifest_sha256") == hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def _need(name: str, value: Any, kind: type = int, minimum: int | None = None) -> Any:
    if isinstance(value, bool) or not isinstance(value, kind) or (minimum is not None and value < minimum):
        raise SelectionError(f"{name} must be a {kind.__name__}{'' if minimum is None else f' of at least {minimum}'}, got {value!r}")
    return value


def _fraction(f: Fraction) -> str:
    return f"{f.numerator}/{f.denominator}"


# --------------------------------------------------------------------------- catalog and frame
def catalog_from_archive(archive: Path, expected: Mapping[str, Any] = EXPECTED_ARCHIVE) -> dict[str, dict[str, Any]]:
    """Verify the archive (size, MD5, tar integrity) and build the block catalog with the existing streaming reader. Reads only the archive."""
    verify_archive(Path(archive), dict(expected))
    return block_catalog(scan(open_csv_rows(Path(archive), expected["member"])))


# --------------------------------------------------------------------------- frame
def eligible_frame(catalog: Mapping[str, Mapping[str, Any]], *, split: str, exclude_blocks: Sequence[str] = ()) -> dict[str, Any]:
    """Eligible blocks of one source split by stratum, minus the excluded blocks. Returns the frame and counts of every exclusion reason."""
    if split not in SPLIT_CODE:
        raise SelectionError(f"split must be one of {sorted(SPLIT_CODE)}")
    excluded = set(exclude_blocks)
    unknown = excluded - set(catalog)
    if unknown:
        raise SelectionError(f"excluded blocks are not in the catalog: {sorted(unknown)[:5]}")
    strata: dict[str, list[str]] = {s: [] for s in STRATUM_ORDER}
    reasons: dict[str, int] = {}
    for block, info in catalog.items():
        why = eligibility(dict(info))
        if why is None and info["split_values"] != [SPLIT_CODE[split]]:
            why = "other_split"
        if why is None and block in excluded:
            why = "excluded_block"
        if why:
            reasons[why] = reasons.get(why, 0) + 1
            continue
        strata[stratum_for(info["unique_dois"])].append(block)
    for s in strata:
        strata[s].sort()
    return {"strata": strata, "sizes": {s: len(b) for s, b in strata.items()}, "not_in_frame_counts": dict(sorted(reasons.items())), "split": split}


def _draw(strata: Mapping[str, Sequence[str]], per_stratum: Mapping[str, int], seed: int | str, role: str) -> dict[str, list[str]]:
    drawn = {}
    for s in STRATUM_ORDER:
        n = _need(f"sample size of stratum {s}", per_stratum.get(s, 0), int, 0)
        if n > len(strata[s]):
            raise SelectionError(f"stratum {s}: {n} blocks requested from {len(strata[s])} available")
        drawn[s] = sorted(strata[s], key=lambda b: key(seed, role, "block", b))[:n]
    unknown = set(per_stratum) - set(STRATUM_ORDER)
    if unknown:
        raise SelectionError(f"unknown strata: {sorted(unknown)}")
    return drawn


def case_identifier(seed: int | str, role: str, block: str, orcid: str) -> str:
    return f"{role[0].upper()}-" + key(seed, "case", role, block, orcid)[:12]


def _cases_for(drawn: Mapping[str, Sequence[str]], catalog: Mapping[str, Mapping[str, Any]], frame_sizes: Mapping[str, int], per_stratum: Mapping[str, int],
               seed: int | str, role: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, str]]]:
    primary, secondary, identity = [], [], {}
    for s in STRATUM_ORDER:
        n_h, big_n = per_stratum.get(s, 0), frame_sizes[s]
        for block in drawn[s]:
            groups = sorted(catalog[block]["case_groups"], key=lambda o: key(seed, "primary", block, o))
            g = len(groups)
            cid = case_identifier(seed, role, block, groups[0])
            identity[cid] = {"orcid": groups[0], "block": block}
            primary.append({"case_id": cid, "block_id": block, "stratum": s, "case_eligible_groups": g, "is_primary": True,
                            "inclusion_probability_block": _fraction(Fraction(n_h, big_n)), "inclusion_probability_person": _fraction(Fraction(n_h, big_n * g))})
            for o in groups[1:]:
                sid = case_identifier(seed, role, block, o)
                identity[sid] = {"orcid": o, "block": block}
                secondary.append({"case_id": sid, "block_id": block, "stratum": s, "primary_case_id": cid, "is_primary": False})
    return primary, secondary, identity


def _manifest(role: str, seed: int | str, dataset_version: str, split: str, frame_sizes: Mapping[str, int], per_stratum: Mapping[str, int],
              primary: Sequence[dict], secondary: Sequence[dict], excluded: Mapping[str, int], extra: Mapping[str, Any]) -> dict[str, Any]:
    return seal({"role": role, "seed": seed, "dataset_version": dataset_version, "split": split, "selector_source_sha256": source_sha256(),
                 "frame_post_exclusion": dict(frame_sizes), "sampled_blocks": {s: per_stratum.get(s, 0) for s in STRATUM_ORDER},
                 "excluded_block_counts": dict(excluded), "cases": list(primary), "secondary_cases": list(secondary), **extra})


# --------------------------------------------------------------------------- pilot and main
def draw_pilot(catalog: Mapping[str, Mapping[str, Any]], *, seed: int | str, dataset_version: str, split: str, smoke_blocks: Sequence[str],
               per_stratum: Mapping[str, int]) -> dict[str, Any]:
    """Draw the label-free coverage pilot (one primary case per block) from the eligible blocks of `split` minus the smoke blocks.
    Also returns the post-exclusion frame (minus smoke and pilot blocks), computed immediately and without any outcome (X-02)."""
    frame = eligible_frame(catalog, split=split, exclude_blocks=smoke_blocks)
    drawn = _draw(frame["strata"], per_stratum, seed, "pilot")
    primary, secondary, identity = _cases_for(drawn, catalog, frame["sizes"], per_stratum, seed, "pilot")
    pilot_blocks = [b for s in STRATUM_ORDER for b in drawn[s]]
    post = eligible_frame(catalog, split=split, exclude_blocks=list(smoke_blocks) + pilot_blocks)
    manifest = _manifest("pilot", seed, dataset_version, split, frame["sizes"], per_stratum, primary, secondary, {"smoke": len(set(smoke_blocks))},
                         {"post_exclusion_frame_after_pilot": post["sizes"], "pilot_blocks": sorted(pilot_blocks)})
    return {"manifest": manifest, "identity_map": identity, "post_exclusion_frame": post}


def draw_main(catalog: Mapping[str, Mapping[str, Any]], *, seed: int | str, dataset_version: str, split: str, smoke_blocks: Sequence[str], pilot_blocks: Sequence[str],
              n_total: int, floors: Mapping[str, int]) -> dict[str, Any]:
    """Draw the main sample: allocation by the C3 algorithm over the post-exclusion frame, one primary case per sampled block, other groups secondary."""
    frame = eligible_frame(catalog, split=split, exclude_blocks=list(smoke_blocks) + list(pilot_blocks))
    if set(floors) != set(STRATUM_ORDER):
        raise SelectionError("floors must be given explicitly for every stratum S, M, L and XL (use 0 for none)")
    for s in STRATUM_ORDER:
        _need(f"floor of stratum {s}", floors[s], int, 0)
    empty = [s for s in STRATUM_ORDER if frame["sizes"][s] == 0 and floors[s] > 0]
    if empty:
        raise SelectionError(f"floors are positive for strata with no eligible block: {empty}")
    sizes = {s: n for s, n in frame["sizes"].items() if n > 0}
    if not sizes:
        raise SelectionError("the post-exclusion frame is empty")
    floors_v = validate_floors({s: floors[s] for s in sizes}, sizes)
    alloc = allocate(_need("N", n_total, int, 1), validate_frame(sizes), floors_v)
    per_stratum = {s: alloc.get(s, 0) for s in STRATUM_ORDER}
    drawn = _draw(frame["strata"], per_stratum, seed, "main")
    primary, secondary, identity = _cases_for(drawn, catalog, frame["sizes"], per_stratum, seed, "main")
    manifest = _manifest("main", seed, dataset_version, split, frame["sizes"], per_stratum, primary, secondary,
                         {"smoke": len(set(smoke_blocks)), "pilot": len(set(pilot_blocks))}, {"N": n_total, "floors": dict(floors_v), "allocation": per_stratum})
    return {"manifest": manifest, "identity_map": identity, "post_exclusion_frame": frame}


def disjointness_report(smoke_blocks: Sequence[str], pilot: Mapping[str, Any], main: Mapping[str, Any]) -> dict[str, Any]:
    """Raise if smoke, pilot and main samples share a block; otherwise report the counts."""
    sets = {"smoke": set(smoke_blocks), "pilot": {c["block_id"] for c in pilot["cases"]}, "main": {c["block_id"] for c in main["cases"]}}
    for a in sets:
        for b in sets:
            if a < b and sets[a] & sets[b]:
                raise SelectionError(f"{a} and {b} share {len(sets[a] & sets[b])} block(s)")
    return {k: len(v) for k, v in sets.items()} | {"disjoint": True}


# --------------------------------------------------------------------------- audit
def draw_audit(non_automatic: Sequence[Mapping[str, str]], automatic_case_ids: Sequence[str], *, seed: int | str, dataset_version: str, n_audit: int,
               merge_rule: Mapping[str, str] | None, predictions_sha256: str) -> dict[str, Any]:
    """Proportional stratified draw from the non-automatic primary cases of the primary pair.

    `merge_rule` (required; None means no merging) maps stratum to a merged group and must be fixed before the draw. Allocation across (merged) groups uses
    largest-remainder rounding (the C3 algorithm with zero floors); cases within a group are taken in SHA-256 order. Every automatic case is in the
    verification population. The manifest records the original stratum sizes, the merged groups, selection probabilities and the hash of the frozen predictions."""
    _need("n_audit", n_audit, int, 1)
    if not (isinstance(predictions_sha256, str) and len(predictions_sha256) == 64):
        raise SelectionError("predictions_sha256 must be the SHA-256 of the frozen predictions")
    ids = [c["case_id"] for c in non_automatic]
    if len(set(ids)) != len(ids) or set(ids) & set(automatic_case_ids):
        raise SelectionError("case identifiers must be unique and a case cannot be both automatic and non-automatic")
    original: dict[str, int] = {}
    for c in non_automatic:
        original[c["stratum"]] = original.get(c["stratum"], 0) + 1
    group_of = {s: (merge_rule or {}).get(s, s) for s in original}
    groups: dict[str, list[str]] = {}
    for c in non_automatic:
        groups.setdefault(group_of[c["stratum"]], []).append(c["case_id"])
    sizes = {g: len(v) for g, v in sorted(groups.items())}
    if n_audit > sum(sizes.values()):
        raise SelectionError(f"n_audit = {n_audit} exceeds the non-automatic frame of {sum(sizes.values())} cases")
    alloc = allocate(n_audit, validate_frame(sizes), {g: 0 for g in sizes})
    selected, probs = [], {}
    for g, members in sorted(groups.items()):
        take = sorted(members, key=lambda c: key(seed, "audit", c))[: alloc[g]]
        selected += take
        probs[g] = _fraction(Fraction(alloc[g], sizes[g]))
    return seal({"role": "audit", "seed": seed, "dataset_version": dataset_version, "selector_source_sha256": source_sha256(), "predictions_sha256": predictions_sha256,
                 "n_audit": n_audit, "original_stratum_sizes": dict(sorted(original.items())), "merge_rule": dict(merge_rule) if merge_rule else None,
                 "group_sizes": sizes, "group_allocation": alloc, "selection_probability_by_group": probs, "audit_case_ids": sorted(selected),
                 "verification_population": sorted(automatic_case_ids), "frame_definition": "all non-automatic primary cases of the primary pair; no benchmark label is used"})
