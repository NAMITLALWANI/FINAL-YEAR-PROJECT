"""LAGOS-AND preparation tests on fabricated data only (names, ORCIDs and DOIs are invented)."""
import csv
import hashlib
import io
import json
import tarfile

import pytest

from hammer_lagos.prep import (
    EXPECTED_ARCHIVE, SOURCE_COLUMNS, LagosDataError, normalize_affiliation, normalize_doi, parse_name_list, prepare, stratum_for,
    strip_own_name, verify_archive,
)

DOI_N = [0]


def row(block, orcid, doi, name, split="1", affil="Example University#TAB#", coauthors=None, pid=None, year="2015"):
    DOI_N[0] += 1
    co = coauthors if coauthors is not None else [name, "Some Coauthor"]
    return [block, orcid, doi, pid or str(2000000000 + DOI_N[0]), "1", name, affil, str(co), "[]", "Journal", year, f"Title {doi}", "Abstract text", split]


def dois(prefix, n):
    return [f"10.9999/{prefix}{i}" for i in range(n)]


def synthetic_rows():
    rows = []
    for block, groups, split in (("ann, lee", [("0000-0001-0000-0001", 4), ("0000-0001-0000-0002", 3)], "1"),
                                 ("bob, ray", [("0000-0001-0000-0003", 3), ("0000-0001-0000-0004", 2)], "0"),
                                 ("gus, day", [("0000-0001-0000-0010", 3), ("0000-0001-0000-0011", 3)], "2")):
        for orcid, n in groups:
            for d in dois(orcid[-4:], n):
                rows.append(row(block, orcid, d, f"{block.split(',')[0].title()} {block.split(',')[1].title()}", split))
    rows += [row("cy, kim", "0000-0001-0000-0005", d, "Cy Kim", "1") for d in dois("cy", 5)]                        # single group
    shared = "10.9999/shared"
    rows += [row("dee, fox", "0000-0001-0000-0006", d, "Dee Fox") for d in dois("d6", 2) + [shared]]
    rows += [row("dee, fox", "0000-0001-0000-0007", d, "Dee Fox") for d in dois("d7", 2) + [shared]]              # DOI in two groups
    rows += [row("eve, poe", "0000-0001-0000-0008", d, "Eve Poe", "1") for d in dois("e8", 2)]
    rows += [row("eve, poe", "0000-0001-0000-0009", d, "Eve Poe", "0") for d in dois("e9", 2)]                     # mixed split
    ids = dois("f8", 3)
    rows += [row("fay, roe", "0000-0001-0000-0012", d, "Fay Roe") for d in ids + [ids[0]]]                         # duplicate DOI in group
    rows += [row("fay, roe", "0000-0001-0000-0013", "10.9999/f9only", "Fay Roe")]                                  # group with one DOI
    return rows


def make_archive(tmp_path, rows=None, header=None, name="x.csv.tar.gz", member="LAGOS-AND-BLOCK-TRIMMED.csv"):
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header or SOURCE_COLUMNS)
    w.writerows(rows if rows is not None else synthetic_rows())
    data = buf.getvalue().encode()
    path = tmp_path / name
    with tarfile.open(path, "w:gz") as tar:
        info = tarfile.TarInfo(member)
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    expected = {**EXPECTED_ARCHIVE, "size": path.stat().st_size, "md5": hashlib.md5(path.read_bytes()).hexdigest(), "member": member}
    return path, expected


def run(tmp_path, tag="a", seed=7, target=4, rows=None):
    archive, expected = make_archive(tmp_path, rows)
    out = tmp_path / f"out_{tag}"
    manifest = prepare(archive, out, seed=seed, target_cases=target, expected=expected, sampling_date="2026-01-01")
    return out, manifest


def csv_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_sampling_and_outputs_are_deterministic(tmp_path):
    archive, expected = make_archive(tmp_path)                           # one archive: gzip embeds a timestamp, so rebuilding would change its hash
    outs = []
    for tag in ("a", "b"):
        outs.append(tmp_path / tag)
        manifest = prepare(archive, outs[-1], seed=7, target_cases=4, expected=expected, sampling_date="2026-01-01")
    assert json.loads((outs[0] / "sampling_manifest.json").read_text()) == json.loads((outs[1] / "sampling_manifest.json").read_text())
    for name in ("seeds.csv", "gold_identity_register.csv", "doi_purpose_register.csv", "selected_block_rows.csv", "dataset_quality_report.json", "sampling_manifest.json"):
        assert (outs[0] / name).read_bytes() == (outs[1] / name).read_bytes()
    c = tmp_path / "c"
    prepare(archive, c, seed=8, target_cases=4, expected=expected, sampling_date="2026-01-01")
    assert (c / "seeds.csv").exists()                                    # a different seed is allowed to select differently


def test_complete_blocks_are_preserved(tmp_path):
    out, manifest = run(tmp_path, target=8)
    blocks = csv_rows(out / "selected_block_rows.csv")
    expected = {}
    for r in synthetic_rows():
        expected.setdefault(r[0], []).append(r)
    selected = {b["block_fullname"] for b in blocks}
    assert selected and all(len([b for b in blocks if b["block_fullname"] == s]) == len(expected[s]) for s in selected)    # every row of every chosen block
    gold = csv_rows(out / "gold_identity_register.csv")
    for s in selected:
        groups_in_file = {b["orcid"] for b in blocks if b["block_fullname"] == s}
        assert groups_in_file == {r[1] for r in expected[s]}


def test_case_ids_unique_and_complete_blocks_fit_the_target(tmp_path):
    out, manifest = run(tmp_path, target=5)
    ids = [r["case_id"] for r in csv_rows(out / "seeds.csv")]
    assert len(ids) == len(set(ids)) and manifest["counts"]["selected_cases"] == len(ids) <= 5


def test_no_orcid_or_gold_fields_reach_the_query_input(tmp_path):
    out, _ = run(tmp_path, target=8)
    seeds_text = (out / "seeds.csv").read_text()
    gold = csv_rows(out / "gold_identity_register.csv")
    assert gold and all(g["gold_orcid"] not in seeds_text and g["gold_orcid"] not in (out / "doi_purpose_register.csv").read_text() for g in gold)
    for s in csv_rows(out / "seeds.csv"):
        for key in ("context_c1_json", "context_c1x_json"):
            ctx = json.loads(s[key])
            assert not ({"orcid", "coauthors", "pid", "gold"} & set(ctx))
        assert s["identity_group_id"].startswith("G") and "0000-" not in s["identity_group_id"] and "gold_orcid" not in s


def test_doi_purpose_separation_and_c1x_only_overlap(tmp_path):
    out, _ = run(tmp_path, target=8)
    register = csv_rows(out / "doi_purpose_register.csv")
    by_case = {}
    for r in register:
        by_case.setdefault(r["case_id"], []).append(r)
    for s in csv_rows(out / "seeds.csv"):
        c1, c1x = json.loads(s["context_c1_json"]), json.loads(s["context_c1x_json"])
        assert "publications" not in c1                                           # primary C1 carries no DOI at all
        regs = by_case[s["case_id"]]
        both = [r for r in regs if r["purpose"] == "both"]
        assert len(both) == 1 and both[0]["justification_if_both"] and c1x["publications"] == [both[0]["doi"]]
        assert all(r["purpose"] == "gold_evidence" for r in regs if r not in both)


def test_no_doi_is_shared_across_cases_and_shared_blocks_are_excluded(tmp_path):
    out, manifest = run(tmp_path, target=20)
    seen = [r["doi"] for r in csv_rows(out / "doi_purpose_register.csv")]
    assert len(seen) == len(set(seen)) and "10.9999/shared" not in seen
    reasons = manifest["counts"]["exclusion_reasons"]
    assert reasons.get("doi_shared_across_orcid_groups") == 1


def test_exclusions_are_counted_not_silent(tmp_path):
    _, manifest = run(tmp_path, target=20)
    r = manifest["counts"]["exclusion_reasons"]
    assert r.get("single_orcid_group") == 1 and r.get("mixed_source_split") == 1 and manifest["counts"]["blocks_total"] == 7


def test_pid_is_never_an_openalex_id(tmp_path):
    out, _ = run(tmp_path, target=8)
    gold = csv_rows(out / "gold_identity_register.csv")
    assert "designated_pid_source_id" in gold[0] and not any("openalex" in k.lower() or k.lower().endswith("work_id") for k in gold[0])
    import re
    assert not any(re.search(r"\bW\d{6,}\b", (out / n).read_text()) for n in ("seeds.csv", "doi_purpose_register.csv"))


def test_no_coauthor_signal_in_the_benchmark(tmp_path):
    out, manifest = run(tmp_path, target=8)
    assert "Some Coauthor" not in (out / "seeds.csv").read_text()
    assert "coauthor" not in json.dumps([json.loads(s["context_c1x_json"]) for s in csv_rows(out / "seeds.csv")]).lower()
    assert "coauthor" in manifest["hammer_conditions"]["C1x"] and "never supplied" in manifest["hammer_conditions"]["C1x"]


def test_split_flag_is_preserved_and_blocks_never_mix_splits(tmp_path):
    out, manifest = run(tmp_path, target=20)
    splits = {s["source_block_id"]: s["source_split"] for s in csv_rows(out / "seeds.csv")}
    assert set(splits.values()) <= {"train", "test", "val"} and manifest["source_split_distribution_of_cases"]
    blocks = csv_rows(out / "selected_block_rows.csv")
    for b in {r["block_fullname"] for r in blocks}:
        assert len({r["train1_test0_val2"] for r in blocks if r["block_fullname"] == b}) == 1
    assert not any(r["block_fullname"] == "eve, poe" for r in blocks)


def test_normalization_and_duplicate_handling(tmp_path):
    out, manifest = run(tmp_path, target=20)
    c = manifest["normalization_counts"]
    assert c["affiliation_tab_marker_rows"] > 0 and c["coauthors_self_name_rows"] > 0 and c["duplicate_doi_rows_within_group"] == 1
    gold = {g["case_id"]: g for g in csv_rows(out / "gold_identity_register.csv")}
    fay = next(g for g in gold.values() if g["gold_orcid"] == "0000-0001-0000-0012")
    assert fay["group_raw_rows"] == "4" and fay["group_unique_dois"] == "3"                # duplicate collapsed, raw count kept
    raw_block_rows = csv_rows(out / "selected_block_rows.csv")
    assert any("#TAB#" in r["author_affiliation"] for r in raw_block_rows)               # original preserved
    seeds = csv_rows(out / "seeds.csv")
    assert not any("#TAB#" in s["context_c1_json"] for s in seeds)


def test_normalization_helpers():
    assert normalize_affiliation("Univ.#TAB# of  X#TAB#") == ("Univ. of X", ["tab_marker_replaced", "whitespace_collapsed"])
    assert normalize_doi(" https://doi.org/10.1/ABC ")[0] == "10.1/abc"
    assert strip_own_name(["Ann Lee", "Bo Ray"], "ann  lee") == (["Bo Ray"], 1)
    assert parse_name_list("['A B','C D']") == ["A B", "C D"] and parse_name_list("not a list") is None
    assert [stratum_for(n) for n in (0, 9, 10, 49, 50, 199, 200)] == ["S", "S", "M", "M", "L", "L", "XL"]


def test_archive_verification_detects_every_failure(tmp_path):
    path, expected = make_archive(tmp_path)
    info = verify_archive(path, expected)
    assert info["csv_member"] == "LAGOS-AND-BLOCK-TRIMMED.csv" and info["tar_integrity"] == "ok" and info["md5"] == expected["md5"]
    with pytest.raises(LagosDataError):
        verify_archive(path, {**expected, "md5": "0" * 32})
    with pytest.raises(LagosDataError):
        verify_archive(path, {**expected, "size": expected["size"] + 1})
    corrupt = tmp_path / "corrupt.tar.gz"
    corrupt.write_bytes(path.read_bytes()[:-40] + b"x" * 40)
    with pytest.raises(LagosDataError):
        verify_archive(corrupt, {**expected, "size": corrupt.stat().st_size, "md5": hashlib.md5(corrupt.read_bytes()).hexdigest()})
    wrong_member, exp2 = make_archive(tmp_path, member="other.csv", name="o.tar.gz")
    with pytest.raises(LagosDataError):
        verify_archive(wrong_member, {**exp2, "member": EXPECTED_ARCHIVE["member"]})


def test_malformed_input_fails_safely(tmp_path):
    bad_header, exp = make_archive(tmp_path, header=SOURCE_COLUMNS[:-1] + ["split"], name="h.tar.gz")
    with pytest.raises(LagosDataError):
        prepare(bad_header, tmp_path / "o1", seed=1, target_cases=4, expected=exp)
    rows = synthetic_rows() + [["only", "three", "fields"]] * 50
    archive, exp = make_archive(tmp_path, rows, name="m.tar.gz")
    with pytest.raises(LagosDataError):
        prepare(archive, tmp_path / "o2", seed=1, target_cases=4, expected=exp)               # malformed fraction above the limit
    assert not (tmp_path / "o2" / "seeds.csv").exists()
    archive, exp = make_archive(tmp_path, rows[:len(synthetic_rows()) + 1], name="k.tar.gz")
    out = tmp_path / "o3"
    manifest = prepare(archive, out, seed=1, target_cases=4, expected=exp, max_malformed_fraction=0.5)
    assert json.loads((out / "dataset_quality_report.json").read_text())["malformed_rows"] == 1 and manifest["counts"]["selected_cases"] > 0


def test_derived_file_hashes_in_manifest_match_files(tmp_path):
    out, manifest = run(tmp_path)
    for name, digest in manifest["derived_file_sha256"].items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest
    assert manifest["dataset"]["doi"] == "10.5281/zenodo.7313353" and manifest["dataset"]["archive_md5_verified"] and manifest["code_sha256"]


def test_existing_output_directory_files_are_never_overwritten(tmp_path):
    archive, expected = make_archive(tmp_path)
    out = tmp_path / "o"
    prepare(archive, out, seed=1, target_cases=4, expected=expected)
    with pytest.raises(FileExistsError):
        prepare(archive, out, seed=1, target_cases=4, expected=expected)
