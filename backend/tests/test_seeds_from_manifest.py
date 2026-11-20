"""T012: tests of the selection-manifest to capture-input adapter. Synthetic archive only (invented names, ORCIDs and DOIs); no provider, no real data."""
import csv
import json
import re
from pathlib import Path

import pytest

from hammer_lagos.prep import DOI_FIELDS, GOLD_FIELDS, SEED_FIELDS
from hammer_pilot import selector_c1c as sel
from hammer_pilot import seeds_from_manifest as sfm
from hammer_pilot.common import read_csv
from hammer_pilot.context_rules import derive_contexts, register_by_case
from hammer_pilot.seeds_from_manifest import SeedBuildError
from test_hammer_lagos_prep import make_archive

ORCID = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]")


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("sfm")
    archive, expected = make_archive(tmp)
    catalog = sel.catalog_from_archive(archive, expected)
    p = sel.draw_pilot(catalog, seed=5, dataset_version="synthetic", split="test", smoke_blocks=[], per_stratum={"S": 1, "M": 0, "L": 0, "XL": 0})
    from hammer_lagos.prep import collect_rows, open_csv_rows
    rows = dict(collect_rows(open_csv_rows(archive, expected["member"]), {c["block_id"] for c in p["manifest"]["cases"]}))
    return dict(tmp=tmp, catalog=catalog, pilot=p, rows=rows, archive=archive)


def build(w, secondary=True):
    return sfm.build_capture_inputs(w["pilot"]["manifest"], w["pilot"]["identity_map"], w["catalog"], w["rows"], include_secondary=secondary)


def test_inputs_follow_the_existing_toolkit_layout_and_use_manifest_case_ids(world):
    out = build(world)
    ids = {c["case_id"] for c in world["pilot"]["manifest"]["cases"] + world["pilot"]["manifest"]["secondary_cases"]}
    assert {s["case_id"] for s in out["seeds"]} == ids == {g["case_id"] for g in out["gold"]} and len(out["seeds"]) == 2
    assert all(list(s) == SEED_FIELDS and s["planned_status"] == "resolved" and s["source_split"] == "test" for s in out["seeds"])
    assert all(list(g) == GOLD_FIELDS for g in out["gold"]) and all(list(d) == DOI_FIELDS for d in out["dois"])
    only_primary = build(world, secondary=False)
    assert len(only_primary["seeds"]) == 1 and only_primary["seeds"][0]["case_id"] == world["pilot"]["manifest"]["cases"][0]["case_id"]


def test_designated_citation_belongs_to_the_group_and_doi_purposes_follow_the_rules(world):
    out = build(world)
    for g in out["gold"]:
        group_dois = [d for d in out["dois"] if d["case_id"] == g["case_id"]]
        assert g["designated_doi"] in {d["doi"] for d in group_dois} and len(group_dois) == int(g["group_unique_dois"]) >= 2
        both = [d for d in group_dois if d["purpose"] == "both"]
        assert len(both) == 1 and both[0]["doi"] == g["designated_doi"] and all(d["purpose"] == "gold_evidence" for d in group_dois if d is not both[0])


def test_no_orcid_in_seeds_or_doi_register_but_the_protected_register_has_it(world):
    out = build(world)
    assert not ORCID.search(json.dumps(out["seeds"])) and not ORCID.search(json.dumps(out["dois"]))
    assert all(ORCID.fullmatch(g["gold_orcid"]) for g in out["gold"])
    ident = world["pilot"]["identity_map"]
    assert {g["gold_orcid"] for g in out["gold"]} == {v["orcid"] for v in ident.values()}


def test_contexts_derive_with_the_existing_rules_and_c1x_holds_the_designated_doi_only(world, tmp_path):
    out = build(world, secondary=False)
    hashes = sfm.write_capture_inputs(tmp_path / "cap", tmp_path / "prot", out, world["pilot"]["manifest"])
    seeds = read_csv(tmp_path / "cap" / "seeds.csv", {"case_id", "query_text", "context_c1_json", "context_c1x_json"})
    register = register_by_case(read_csv(tmp_path / "cap" / "doi_register.csv", {"case_id", "doi", "purpose"}))
    ctx = derive_contexts(seeds[0], register[seeds[0]["case_id"]])
    assert set(ctx) >= {"C0", "C1", "C1x"} and ctx["C1"]["institutions"][0]["name"] == "Example University"
    assert json.loads(seeds[0]["context_c1x_json"])["publications"] == [out["gold"][0]["designated_doi"]]
    assert set(hashes) == {"seeds.csv", "doi_register.csv", "gold_identity_register.csv"}


def test_building_is_deterministic(world):
    assert build(world) == build(world)


def test_inconsistent_inputs_are_refused(world):
    m = world["pilot"]["manifest"]
    with pytest.raises(SeedBuildError, match="identity-map"):
        sfm.build_capture_inputs(m, {}, world["catalog"], world["rows"], include_secondary=False)
    with pytest.raises(SeedBuildError, match="no rows"):
        sfm.build_capture_inputs(m, world["pilot"]["identity_map"], world["catalog"], {}, include_secondary=False)
    short = {b: r[:-1] for b, r in world["rows"].items()}
    with pytest.raises(SeedBuildError, match="complete-block"):
        sfm.build_capture_inputs(m, world["pilot"]["identity_map"], world["catalog"], short, include_secondary=False)
    wrong = {k: {"orcid": v["orcid"], "block": "other"} for k, v in world["pilot"]["identity_map"].items()}
    with pytest.raises(SeedBuildError, match="identity-map"):
        sfm.build_capture_inputs(m, wrong, world["catalog"], world["rows"], include_secondary=False)


def test_write_separates_the_protected_register_binds_the_manifest_hash_and_never_overwrites(world, tmp_path):
    out = build(world)
    sfm.write_capture_inputs(tmp_path / "cap", tmp_path / "prot", out, world["pilot"]["manifest"])
    assert {p.name for p in (tmp_path / "cap").iterdir()} == {"seeds.csv", "doi_register.csv", "seed_freeze.json"}
    assert {p.name for p in (tmp_path / "prot").iterdir()} == {"gold_identity_register.csv"}
    freeze = json.loads((tmp_path / "cap" / "seed_freeze.json").read_text())
    assert freeze["manifest_sha256"] == world["pilot"]["manifest"]["manifest_sha256"] and freeze["cases"] == 2
    assert not any(ORCID.search(p.read_text()) for p in (tmp_path / "cap").iterdir())
    with pytest.raises(FileExistsError):
        sfm.write_capture_inputs(tmp_path / "cap", tmp_path / "prot2", out, world["pilot"]["manifest"])
    with pytest.raises(SeedBuildError, match="nested"):
        sfm.write_capture_inputs(tmp_path / "c2", tmp_path / "c2" / "inner", out, world["pilot"]["manifest"])


def test_the_archive_pass_returns_only_the_selected_blocks(world):
    blocks = [c["block_id"] for c in world["pilot"]["manifest"]["cases"]]
    got = sfm.rows_for_blocks(world["archive"], blocks)
    assert set(got) == set(blocks) == set(world["rows"]) and got == world["rows"]
    assert sfm.rows_for_blocks(world["archive"], ["no such block"]) == {}


def test_the_designated_citation_is_the_smallest_hash_among_citations_with_an_affiliation(world):
    from hammer_lagos.prep import _key, normalize_affiliation, normalize_doi
    out = build(world, secondary=False)
    g = out["gold"][0]
    orcid = g["gold_orcid"]
    rows = [r for r in world["rows"][world["pilot"]["manifest"]["cases"][0]["block_id"]] if r["orcid"] == orcid]
    cites = {normalize_doi(r["doi"])[0]: r for r in rows}
    pool = {k: v for k, v in cites.items() if normalize_affiliation(v["author_affiliation"])[0]} or cites
    assert g["designated_doi"] == min(pool, key=lambda k: _key(world["pilot"]["manifest"]["seed"], "cite", orcid, k))


def test_affiliation_less_citations_are_never_designated_when_an_affiliated_one_exists(world):
    from hammer_lagos.prep import _key, normalize_doi
    m = world["pilot"]["manifest"]
    block = m["cases"][0]["block_id"]
    orcid = world["pilot"]["identity_map"][m["cases"][0]["case_id"]]["orcid"]
    rows = [dict(r) for r in world["rows"][block]]
    dois = sorted({normalize_doi(r["doi"])[0] for r in rows if r["orcid"] == orcid})
    smallest = min(dois, key=lambda k: _key(m["seed"], "cite", orcid, k))
    keep = next(d for d in dois if d != smallest)
    for r in rows:
        if r["orcid"] == orcid and normalize_doi(r["doi"])[0] != keep:
            r["author_affiliation"] = ""
    out = sfm.build_capture_inputs(m, world["pilot"]["identity_map"], world["catalog"], {block: rows}, include_secondary=False)
    assert out["gold"][0]["designated_doi"] == keep and out["seeds"][0]["c1_institution_missing"] == "false"


def test_seed_freeze_is_accepted_by_the_capture_step(world, tmp_path):
    """T019 regression: the freeze file written here must satisfy `capture.verify_seed_freeze`, the first thing a real capture checks."""
    from hammer_pilot.capture import verify_seed_freeze
    from hammer_pilot.common import PilotDataError
    sfm.write_capture_inputs(tmp_path / "cap", tmp_path / "prot", build(world), world["pilot"]["manifest"])
    freeze = verify_seed_freeze(tmp_path / "cap")
    assert freeze["seeds_sha256"] and freeze["doi_register_sha256"]
    (tmp_path / "cap" / "seeds.csv").write_text((tmp_path / "cap" / "seeds.csv").read_text() + "\n")
    with pytest.raises(PilotDataError):
        verify_seed_freeze(tmp_path / "cap")
