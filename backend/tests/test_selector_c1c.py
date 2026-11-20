"""T007: tests of the selector and manifest builder (Decisions C1c, C3, C4, C9, Decision A audit). Synthetic catalogs only; no archive, no provider."""
import csv
import hashlib
import io
import json
import random
import re
import subprocess
import sys
import tarfile
from collections import Counter
from pathlib import Path

import pytest

from hammer_lagos.prep import SOURCE_COLUMNS
from hammer_pilot import selector_c1c as sel
from hammer_pilot.selector_c1c import SelectionError
from hammer_pilot.sizing_c9 import allocate

BACKEND = Path(__file__).resolve().parents[1]
ORCID = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]")


def make_catalog(n=600, seed=3):
    rng = random.Random(seed)
    cat = {}
    for i in range(n):
        size = rng.choices([rng.randint(2, 9), rng.randint(10, 49), rng.randint(50, 199), rng.randint(200, 400)], weights=[50, 40, 9, 1])[0]
        n_groups = rng.choice([2, 2, 2, 3, 4, 5, 9])
        groups = [f"0000-{i:04d}-{k:04d}-{(k * 7) % 10:03d}{'X' if k % 3 == 0 else '1'}" for k in range(n_groups)]
        cat[f"blk{i:04d}"] = {"groups": groups, "n_groups": n_groups, "unique_dois": size, "split_values": [rng.choice(["0", "1", "2"])],
                              "cross_group_doi": rng.random() < 0.05, "case_groups": groups[: rng.randint(0, n_groups)], "raw_rows": size}
    return cat


CAT = make_catalog()


def frame(split="test", exclude=()):
    return sel.eligible_frame(CAT, split=split, exclude_blocks=exclude)


# ---------------------------------------------------------------- frame
def test_frame_contains_only_eligible_blocks_of_the_requested_split_by_band():
    f = frame()
    assert set(f["strata"]) == {"S", "M", "L", "XL"}
    for s, blocks in f["strata"].items():
        for b in blocks:
            info = CAT[b]
            assert sel.eligibility(info) is None and info["split_values"] == ["0"]
            assert sel.stratum_for(info["unique_dois"]) == s
    assert f["sizes"] == {s: len(b) for s, b in f["strata"].items()} and sum(f["sizes"].values()) > 0
    assert f["not_in_frame_counts"]["other_split"] > 0


@pytest.mark.parametrize("dois,band", [(0, "S"), (9, "S"), (10, "M"), (49, "M"), (50, "L"), (199, "L"), (200, "XL"), (5000, "XL")])
def test_band_boundaries(dois, band):
    assert sel.stratum_for(dois) == band


def test_exclusion_counts_every_reason_and_excluded_blocks_leave_the_frame():
    base = frame()
    victim = base["strata"]["S"][0]
    f = frame(exclude=[victim])
    assert victim not in f["strata"]["S"] and f["sizes"]["S"] == base["sizes"]["S"] - 1 and f["not_in_frame_counts"]["excluded_block"] == 1
    reasons = set(base["not_in_frame_counts"])
    assert reasons <= {"single_orcid_group", "mixed_source_split", "doi_shared_across_orcid_groups", "more_groups_than_cap", "no_group_with_two_unique_dois", "other_split"}
    with pytest.raises(SelectionError):
        frame(exclude=["no-such-block"])
    with pytest.raises(SelectionError):
        sel.eligible_frame(CAT, split="holdout")


# ---------------------------------------------------------------- pilot
def pilot(seed=11, per=None, smoke=()):
    return sel.draw_pilot(CAT, seed=seed, dataset_version="v2.0", split="test", smoke_blocks=list(smoke), per_stratum=per or {"S": 5, "M": 5, "L": 3, "XL": 0})


def test_pilot_draw_is_deterministic_seed_dependent_and_independent_of_catalog_order():
    a, b, c = pilot(), pilot(), pilot(seed=12)
    assert a["manifest"] == b["manifest"] and a["identity_map"] == b["identity_map"]
    assert a["manifest"]["manifest_sha256"] != c["manifest"]["manifest_sha256"]
    shuffled = dict(reversed(list(CAT.items())))
    d = sel.draw_pilot(shuffled, seed=11, dataset_version="v2.0", split="test", smoke_blocks=[], per_stratum={"S": 5, "M": 5, "L": 3, "XL": 0})
    assert d["manifest"] == a["manifest"]


def test_pilot_excludes_smoke_blocks_and_reports_the_post_exclusion_frame_before_sizing():
    base = frame()
    smoke = base["strata"]["S"][:4]
    p = pilot(smoke=smoke)
    m = p["manifest"]
    blocks = {c["block_id"] for c in m["cases"]}
    assert not blocks & set(smoke) and len(blocks) == 13
    post = m["post_exclusion_frame_after_pilot"]
    assert post == {"S": base["sizes"]["S"] - 4 - 5, "M": base["sizes"]["M"] - 5, "L": base["sizes"]["L"] - 3, "XL": base["sizes"]["XL"]}
    assert p["post_exclusion_frame"]["sizes"] == post and m["frame_post_exclusion"]["S"] == base["sizes"]["S"] - 4


def test_pilot_requests_beyond_the_frame_or_unknown_strata_are_refused():
    with pytest.raises(SelectionError, match="requested from"):
        pilot(per={"S": 10 ** 6})
    with pytest.raises(SelectionError, match="unknown strata"):
        pilot(per={"Q": 1})
    with pytest.raises(SelectionError):
        pilot(per={"S": -1})
    with pytest.raises(SelectionError):
        pilot(per={"S": True})


# ---------------------------------------------------------------- primary and secondary cases, inclusion probabilities, identity map
def test_primary_case_is_the_group_with_the_smallest_hash_and_the_rest_are_secondary():
    m = pilot(per={"S": 8, "M": 8, "L": 0, "XL": 0})
    for c in m["manifest"]["cases"]:
        groups = CAT[c["block_id"]]["case_groups"]
        want = min(groups, key=lambda o: sel.key(11, "primary", c["block_id"], o))
        assert m["identity_map"][c["case_id"]]["orcid"] == want and c["case_eligible_groups"] == len(groups) and c["is_primary"]
    sec = {c["primary_case_id"] for c in m["manifest"]["secondary_cases"]}
    assert sec <= {c["case_id"] for c in m["manifest"]["cases"]}
    n_secondary = sum(len(CAT[c["block_id"]]["case_groups"]) - 1 for c in m["manifest"]["cases"])
    assert len(m["manifest"]["secondary_cases"]) == n_secondary


def test_inclusion_probabilities_are_exact_fractions():
    m = pilot()["manifest"]
    big = m["frame_post_exclusion"]
    for c in m["cases"]:
        n_h, N_h, g = m["sampled_blocks"][c["stratum"]], big[c["stratum"]], c["case_eligible_groups"]
        num, den = map(int, c["inclusion_probability_block"].split("/"))
        assert num * N_h == n_h * den
        num, den = map(int, c["inclusion_probability_person"].split("/"))
        assert num * N_h * g == n_h * den


def test_manifests_contain_no_orcid_and_the_identity_map_is_separate():
    p = pilot()
    text = json.dumps(p["manifest"])
    assert not ORCID.search(text)
    assert p["identity_map"] and all(ORCID.fullmatch(v["orcid"]) for v in p["identity_map"].values())
    assert set(p["identity_map"]) == {c["case_id"] for c in p["manifest"]["cases"] + p["manifest"]["secondary_cases"]}


def test_manifest_hash_detects_tampering_and_records_the_selector_hash():
    m = pilot()["manifest"]
    assert sel.verify_manifest(m) and m["selector_source_sha256"] == sel.source_sha256()
    bad = json.loads(json.dumps(m))
    bad["cases"][0]["stratum"] = "XL"
    assert not sel.verify_manifest(bad)
    assert sel.seal({"a": 1})["manifest_sha256"] == sel.seal({"a": 1})["manifest_sha256"] != sel.seal({"a": 2})["manifest_sha256"]


# ---------------------------------------------------------------- main
def main_draw(n=60, floors=None, seed=21, smoke=(), pilot_blocks=()):
    return sel.draw_main(CAT, seed=seed, dataset_version="v2.0", split="test", smoke_blocks=list(smoke), pilot_blocks=list(pilot_blocks), n_total=n,
                         floors=floors or {"S": 0, "M": 0, "L": 0, "XL": 0})


def test_main_allocation_is_the_c3_allocation_over_the_post_exclusion_frame():
    p = pilot()
    pilot_blocks = [c["block_id"] for c in p["manifest"]["cases"]]
    r = main_draw(80, {"S": 0, "M": 0, "L": 2, "XL": 0}, pilot_blocks=pilot_blocks)
    sizes = {s: n for s, n in r["manifest"]["frame_post_exclusion"].items() if n}
    assert r["manifest"]["allocation"] == {**{s: 0 for s in sel.STRATUM_ORDER}, **allocate(80, sizes, {s: (2 if s == "L" else 0) for s in sizes})}
    assert len(r["manifest"]["cases"]) == 80 == sum(r["manifest"]["sampled_blocks"].values())
    assert len({c["block_id"] for c in r["manifest"]["cases"]}) == 80                                 # one primary case per block


def test_floors_must_be_explicit_and_infeasible_requests_are_refused():
    with pytest.raises(SelectionError, match="explicitly"):
        sel.draw_main(CAT, seed=1, dataset_version="v", split="test", smoke_blocks=[], pilot_blocks=[], n_total=20, floors={"S": 0})
    with pytest.raises(Exception, match="exceeds the frame|floors"):
        main_draw(10 ** 6)
    with pytest.raises(Exception, match="floors"):
        main_draw(5, {"S": 10, "M": 10, "L": 10, "XL": 0})


def test_census_when_a_floor_reaches_the_stratum_size():
    f = frame()
    xl = f["sizes"]["XL"]
    r = main_draw(60, {"S": 0, "M": 0, "L": 0, "XL": xl + 5})
    assert r["manifest"]["allocation"]["XL"] == xl                                                    # floor capped at the frame size: census
    assert {c["block_id"] for c in r["manifest"]["cases"] if c["stratum"] == "XL"} == set(f["strata"]["XL"])


def test_smoke_pilot_and_main_samples_are_disjoint_and_overlap_is_refused():
    f = frame()
    smoke = f["strata"]["M"][:6]
    p = pilot(smoke=smoke)
    pb = [c["block_id"] for c in p["manifest"]["cases"]]
    m = main_draw(90, smoke=smoke, pilot_blocks=pb)
    rep = sel.disjointness_report(smoke, p["manifest"], m["manifest"])
    assert rep == {"smoke": 6, "pilot": 13, "main": 90, "disjoint": True}
    clash = main_draw(90, smoke=smoke)                                                                  # built without excluding the pilot: may overlap
    overlap = {c["block_id"] for c in clash["manifest"]["cases"]} & set(pb)
    if overlap:
        with pytest.raises(SelectionError, match="share"):
            sel.disjointness_report(smoke, p["manifest"], clash["manifest"])
    forced = json.loads(json.dumps(m["manifest"]))
    forced["cases"][0]["block_id"] = pb[0]
    with pytest.raises(SelectionError, match="share"):
        sel.disjointness_report(smoke, p["manifest"], forced)


def test_each_role_draws_by_its_own_hash_key_so_the_same_seed_gives_different_pilot_and_main_samples():
    f = frame()
    alloc = {"S": 20, "M": 0, "L": 0, "XL": 0}
    drawn_pilot = sel._draw(f["strata"], alloc, 5, "pilot")["S"]
    drawn_main = sel._draw(f["strata"], alloc, 5, "main")["S"]
    assert drawn_pilot == sorted(f["strata"]["S"], key=lambda b: sel.key(5, "pilot", "block", b))[:20] and set(drawn_pilot) != set(drawn_main)
    r = main_draw(60, seed=5)
    for s, n in r["manifest"]["allocation"].items():
        expect = sorted(r["post_exclusion_frame"]["strata"][s], key=lambda b: sel.key(5, "main", "block", b))[:n]
        assert [c["block_id"] for c in r["manifest"]["cases"] if c["stratum"] == s] == [b for b in expect]                  # each stratum's draw is the first n in main-key order
    p = pilot(seed=5, per={"S": 20, "M": 0, "L": 0, "XL": 0})
    assert [c["block_id"] for c in p["manifest"]["cases"]] == drawn_pilot


# ---------------------------------------------------------------- audit
def audit_inputs(n_cases=200, seed=2):
    rng = random.Random(seed)
    rows = [{"case_id": f"C{i:04d}", "stratum": rng.choices(["S", "M", "L", "XL"], weights=[50, 40, 9, 1])[0], "outcome": "auto" if rng.random() < 0.15 else "manual"} for i in range(n_cases)]
    return [{"case_id": r["case_id"], "stratum": r["stratum"]} for r in rows if r["outcome"] != "auto"], [r["case_id"] for r in rows if r["outcome"] == "auto"], rows


H64 = hashlib.sha256(b"frozen predictions").hexdigest()


def audit(n=30, merge=None, seed=9):
    rest, auto, _ = audit_inputs()
    return sel.draw_audit(rest, auto, seed=seed, dataset_version="v2.0", n_audit=n, merge_rule=merge, predictions_sha256=H64), rest, auto


def test_audit_is_proportional_stratified_by_largest_remainder_with_hash_order():
    m, rest, auto = audit(30)
    sizes = Counter(c["stratum"] for c in rest)
    assert m["original_stratum_sizes"] == dict(sorted(sizes.items())) and m["group_sizes"] == dict(sorted(sizes.items()))
    assert m["group_allocation"] == allocate(30, dict(sorted(sizes.items())), {s: 0 for s in sizes}) and len(m["audit_case_ids"]) == 30
    for s in sizes:
        members = sorted((c["case_id"] for c in rest if c["stratum"] == s), key=lambda c: sel.key(9, "audit", c))
        assert set(m["audit_case_ids"]) & set(members) == set(members[: m["group_allocation"][s]])
    assert m["verification_population"] == sorted(auto) and m["predictions_sha256"] == H64 and sel.verify_manifest(m)
    from fractions import Fraction
    for g, n_g in m["group_allocation"].items():
        f = Fraction(n_g, m["group_sizes"][g])
        assert m["selection_probability_by_group"][g] == f"{f.numerator}/{f.denominator}"


def test_audit_merging_rule_is_recorded_and_original_counts_are_kept():
    m, rest, _ = audit(30, merge={"XL": "L"})
    assert m["merge_rule"] == {"XL": "L"} and "XL" in m["original_stratum_sizes"] and "XL" not in m["group_sizes"]
    assert m["group_sizes"]["L"] == m["original_stratum_sizes"]["L"] + m["original_stratum_sizes"].get("XL", 0)
    assert len(m["audit_case_ids"]) == 30


def test_audit_never_reads_labels_and_its_selection_depends_only_on_seed_and_frame():
    a, rest, auto = audit(30, seed=9)
    b = sel.draw_audit(rest, auto, seed=9, dataset_version="v2.0", n_audit=30, merge_rule=None, predictions_sha256=hashlib.sha256(b"other").hexdigest())
    assert a["audit_case_ids"] == b["audit_case_ids"] and a["manifest_sha256"] != b["manifest_sha256"]      # the hash binds the frozen predictions
    c, _, _ = audit(30, seed=10)
    assert a["audit_case_ids"] != c["audit_case_ids"]


def test_audit_input_validation():
    rest, auto, _ = audit_inputs()
    kw = dict(seed=1, dataset_version="v", merge_rule=None, predictions_sha256=H64)
    with pytest.raises(SelectionError, match="exceeds"):
        sel.draw_audit(rest, auto, n_audit=10 ** 6, **kw)
    with pytest.raises(SelectionError):
        sel.draw_audit(rest, auto, n_audit=0, **kw)
    with pytest.raises(SelectionError, match="unique"):
        sel.draw_audit(rest + rest[:1], auto, n_audit=5, **kw)
    with pytest.raises(SelectionError, match="unique"):
        sel.draw_audit(rest, auto + [rest[0]["case_id"]], n_audit=5, **kw)
    with pytest.raises(SelectionError, match="SHA-256"):
        sel.draw_audit(rest, auto, n_audit=5, seed=1, dataset_version="v", merge_rule=None, predictions_sha256="abc")


# ---------------------------------------------------------------- statistical sanity of the hash-order draw
def test_hash_order_selection_is_uniform_over_blocks_and_primary_groups():
    blocks = [f"b{i}" for i in range(40)]
    counts = Counter()
    reps = 1500
    for seed in range(reps):
        counts.update(sorted(blocks, key=lambda b: sel.key(seed, "main", "block", b))[:8])
    p = 8 / 40
    sd = (reps * p * (1 - p)) ** 0.5
    assert all(abs(counts[b] - reps * p) < 5 * sd for b in blocks)                                 # each block drawn with probability n/N
    groups = ["g1", "g2", "g3"]
    first = Counter(min(groups, key=lambda o: sel.key(s, "primary", "bX", o)) for s in range(3000))
    assert all(abs(first[g] - 1000) < 5 * (3000 / 3 * 2 / 3) ** 0.5 for g in groups)               # each group is primary with probability 1/g


# ---------------------------------------------------------------- command-line scripts and the archive catalog
def run_script(name, *args):
    return subprocess.run([sys.executable, "-I", str(BACKEND / "scripts" / name), *args], capture_output=True, text=True, cwd=BACKEND, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})


def test_selection_cli_writes_new_files_only_and_refuses_bad_specs(tmp_path):
    cat = tmp_path / "catalog.json"
    cat.write_text(json.dumps(CAT))
    spec = {"action": "pilot", "catalog": str(cat), "seed": 11, "dataset_version": "v2.0", "split": "test", "smoke_blocks": [], "per_stratum": {"S": 5, "M": 5, "L": 3, "XL": 0}}
    sp = tmp_path / "spec.json"
    sp.write_text(json.dumps(spec))
    out = tmp_path / "out"
    r = run_script("build_selection_manifest.py", "--spec", str(sp), "--out-dir", str(out))
    assert r.returncode == 0 and (out / "manifest.json").exists() and (out / "identity_map.json").exists()
    manifest = json.loads((out / "manifest.json").read_text())
    assert sel.verify_manifest(manifest) and manifest == pilot()["manifest"] and not ORCID.search(json.dumps(manifest))
    assert run_script("build_selection_manifest.py", "--spec", str(sp), "--out-dir", str(out)).returncode != 0                 # refuses to overwrite
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({**spec, "per_stratum": {"S": 10 ** 6}}))
    r2 = run_script("build_selection_manifest.py", "--spec", str(bad), "--out-dir", str(tmp_path / "o2"))
    assert r2.returncode == 1 and "selection refused" in r2.stderr and not (tmp_path / "o2").exists()
    pred = tmp_path / "pred.csv"
    rest, auto, rows = audit_inputs()
    with open(pred, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["case_id", "stratum", "outcome"])
        w.writeheader()
        w.writerows(rows)
    asp = tmp_path / "aspec.json"
    asp.write_text(json.dumps({"action": "audit", "predictions_csv": str(pred), "seed": 9, "dataset_version": "v2.0", "n_audit": 30, "merge_rule": None, "predictions_sha256": H64}))
    r3 = run_script("build_selection_manifest.py", "--spec", str(asp), "--out-dir", str(tmp_path / "o3"))
    assert r3.returncode == 0 and json.loads((tmp_path / "o3" / "manifest.json").read_text())["audit_case_ids"] == audit(30)[0]["audit_case_ids"]


def test_catalog_from_a_synthetic_archive_matches_the_existing_reader_and_refuses_a_wrong_archive(tmp_path):
    rows = []
    for block, split in (("ann, lee", "0"), ("bob, ray", "1")):
        for orcid in ("0000-0001-0000-0001", "0000-0001-0000-0002"):
            for i in range(3):
                rows.append([block, orcid + block[:1], f"10.9999/{block[:1]}{orcid[-1]}{i}", str(2000000000 + len(rows)), "1", "N", "Univ#TAB#", "['N']", "[]", "J", "2015", "T", "A", split])
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(SOURCE_COLUMNS)
    w.writerows(rows)
    data = buf.getvalue().encode()
    path = tmp_path / "a.csv.tar.gz"
    with tarfile.open(path, "w:gz") as tar:
        info = tarfile.TarInfo("LAGOS-AND-BLOCK-TRIMMED.csv")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    expected = {"filename": "a", "size": path.stat().st_size, "md5": hashlib.md5(path.read_bytes()).hexdigest(), "dataset_doi": "x", "version": "t", "member": "LAGOS-AND-BLOCK-TRIMMED.csv"}
    cat = sel.catalog_from_archive(path, expected)
    assert set(cat) == {"ann, lee", "bob, ray"} and cat["ann, lee"]["split_values"] == ["0"] and cat["ann, lee"]["n_groups"] == 2
    assert len(cat["ann, lee"]["case_groups"]) == 2 and cat["ann, lee"]["unique_dois"] == 6
    with pytest.raises(Exception, match="size"):
        sel.catalog_from_archive(path, {**expected, "size": 1})
    r = run_script("build_block_catalog.py", "--archive", str(path), "--out", str(tmp_path / "c.json"))
    assert r.returncode != 0 and not (tmp_path / "c.json").exists()                                  # the real script is strict: this archive is not the LAGOS-AND archive


def test_no_provider_or_archive_access_in_the_selector_module():
    src = Path(sel.__file__).read_text()
    assert not re.search(r"^\s*(import|from)\s+(httpx|requests|urllib|socket|aiohttp)", src, re.M)
