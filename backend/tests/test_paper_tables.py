"""T013: tests of the LaTeX result-table generator (traceability of every Results number to a C7 report). Synthetic report only."""
import json
import random
import re
import subprocess
import sys
from pathlib import Path

import pytest

from hammer_pilot import metrics_c7 as m
from hammer_pilot import paper_tables as pt
from hammer_pilot import review_records as rr
from hammer_pilot.paper_tables import TableError

ROOT = Path(__file__).resolve().parents[2]
ORCID = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]")
FRAME = {"S": 1000, "M": 800, "L": 100, "XL": 3}


def make_cases(verified=True):
    rng = random.Random(8)
    cases, n = [], 0
    for h, k in (("S", 30), ("M", 25), ("L", 12), ("XL", 3)):
        for i in range(k):
            n += 1
            auto = rng.random() < 0.3
            pool = ("a", "b", "c")
            kw = {}
            if verified and auto:
                kw = dict(label_state="resolved", group_purity="pure", pool_judgments={"a": "same" if i % 4 else "different", "b": "different", "c": "different"}, audit_subset="automatic")
            elif verified and i % 3 == 0:
                kw = dict(label_state="resolved", group_purity="pure" if i % 6 else "impure", pool_judgments={"a": "same", "b": "different", "c": "different"}, audit_subset="audit_sample")
            cases.append(m.Case(case_id=f"c{n}", block_id=f"b{n}", stratum=h, outcome="auto" if auto else "manual", pool_ids=pool, mapped_ids=frozenset({"a"}),
                                selected_id="a" if auto else "", group_count=1 + i % 3, **kw))
    return cases


SET = m.InferenceSettings(bootstrap_resamples=40, bootstrap_min_stratum_n=5, negligible_weight=0.0001)


@pytest.fixture(scope="module")
def report():
    return m.evaluate_primary(make_cases(), FRAME, SET, seed=3)


def test_final_tables_are_refused_while_parameters_are_unspecified_and_draft_is_marked():
    rep = m.evaluate_primary(make_cases(), FRAME, m.InferenceSettings(bootstrap_resamples=20), seed=3)
    with pytest.raises(TableError, match="not specified"):
        pt.render_all(rep, draft=False)
    tables = pt.render_all(rep, draft=True)
    assert all("DRAFT" in t for t in tables.values())


def test_all_tables_render_and_are_well_formed_latex(report):
    tables = pt.render_all(report, draft=False)
    assert set(tables) == {"res_accounting.tex", "res_retrieval.tex", "res_selective.tex", "res_verified.tex", "res_audit.tex", "res_verified_retrieval.tex", "res_parameters.tex"}
    for name, t in tables.items():
        assert t.count(r"\begin{tabular}") == t.count(r"\end{tabular}") == 1 and "DRAFT" not in t
        env = re.search(r"\\begin\{(table\*?)\}", t).group(1)
        assert t.count(rf"\end{{{env}}}") == 1 and r"\label{tab:res-" in t
        spec = re.search(r"\\begin\{tabular\}\{(\w+)\}", t).group(1)
        for line in t.splitlines():
            if line.endswith(r"\\") and "caption" not in line:
                assert line.count(" & ") == len(spec) - 1, (name, line)
        body = "\n".join(l for l in t.splitlines() if not l.startswith("%"))
        assert not re.search(r"(?<!\\)_", re.sub(r"\\label\{[^}]*\}", "", body))              # every underscore outside labels and comments is escaped
        assert not ORCID.search(t)


def test_numbers_in_the_tables_equal_the_report(report):
    tables = pt.render_all(report, draft=False)
    acc = report["case_accounting"]
    row = next(l for l in tables["res_accounting.tex"].splitlines() if l.startswith("auto"))
    assert row.rstrip(" \\").split(" & ")[-1] == str(acc["outcome_counts"]["auto"])
    q = report["retrieval_benchmark_derived"]["end_to_end_success_at_1"]
    s_cell = q["per_stratum"]["S"]
    row = next(l for l in tables["res_retrieval.tex"].splitlines() if "End-to-end success@1" in l)
    assert f"{s_cell['numerator']}/{s_cell['denominator']} ({pt.pct(s_cell['value'])})" in row
    assert pt.pct(q["pooled"]["E1"]["point"]) in row
    a = report["audit_label_error"]
    assert f"{a['contradicted']} / {a['consistent']} / {a['indeterminate']}" in tables["res_audit.tex"]


def test_census_strata_and_withheld_intervals_are_labelled_not_invented(report):
    t = pt.render_all(report, draft=False)["res_selective.tex"]
    xl_cell = next(l for l in t.splitlines() if l.startswith("auto")).split(" & ")[4]
    assert "/3 (" in xl_cell                                                                   # XL is a census: counts, no interval
    p = report["selective_benchmark_derived"]["benchmark_automatic_precision"]["pooled"]["E1"]
    assert p["interval"] is None and ("R3, counts only" in t or "interval withheld" in t or "census" in t)


def test_incomplete_verification_gives_a_placeholder_and_never_a_verified_rate():
    rep = m.evaluate_primary(make_cases(verified=False), FRAME, SET, seed=3)
    t = pt.render_all(rep, draft=False)["res_verified.tex"]
    assert "no verified rate is reported" in t and "unverified" in t and "Precision" not in t


def test_verified_and_benchmark_tables_are_separate_and_labelled(report):
    tables = pt.render_all(report, draft=False)
    assert "not independently verified" in tables["res_retrieval.tex"] and "not verified accuracy" in tables["res_selective.tex"]
    assert "independent labels" in tables["res_verified.tex"] and "never pooled" in tables["res_verified_retrieval.tex"]
    assert "not a correction factor" in tables["res_audit.tex"]
    assert "Precision (definite labels)" not in tables["res_selective.tex"]


def test_agreement_table_shows_counts_and_undefined_kappa():
    ag = rr.agreement_report([{"case_id": f"c{i}", "reviewer_id": r, "status": "resolved", "group_purity": "pure"} for i in range(4) for r in ("r1", "r2")], [])
    t = pt.table_agreement(ag, draft=False)
    assert "undefined" in t and "4/4" in t and "unstable at small" in t


def test_escaping_and_determinism(report):
    assert pt.esc("a_b & 50% #1 {x}") == r"a\_b \& 50\% \#1 \{x\}"
    assert pt.render_all(report, draft=False) == pt.render_all(report, draft=False)


def test_script_writes_new_files_only_and_refuses_unspecified_parameters(tmp_path):
    full = tmp_path / "report.json"
    full.write_text(m.to_json(m.evaluate_primary(make_cases(), FRAME, SET, seed=3)))
    partial = tmp_path / "partial.json"
    partial.write_text(m.to_json(m.evaluate_primary(make_cases(), FRAME, m.InferenceSettings(bootstrap_resamples=20), seed=3)))
    script = ROOT / "paper" / "HAMMER_IEEE_PAPER" / "tools" / "make_result_tables.py"
    run = lambda *a: subprocess.run([sys.executable, "-I", str(script), *a], capture_output=True, text=True, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})
    ok = run("--report", str(full), "--out-dir", str(tmp_path / "t1"))
    assert ok.returncode == 0 and len(list((tmp_path / "t1").glob("*.tex"))) == 7
    assert run("--report", str(full), "--out-dir", str(tmp_path / "t1")).returncode != 0
    refused = run("--report", str(partial), "--out-dir", str(tmp_path / "t2"))
    assert refused.returncode == 1 and "refused" in refused.stderr and not (tmp_path / "t2").exists()
    assert run("--report", str(partial), "--out-dir", str(tmp_path / "t3"), "--draft").returncode == 0


def test_a_computed_pooled_interval_is_printed_exactly_as_in_the_report(report):
    p = report["label_free"]["rate_auto"]["pooled"]["E1"]
    assert p["interval"] is not None
    t = pt.render_all(report, draft=False)["res_selective.tex"]
    row = next(l for l in t.splitlines() if l.startswith("auto"))
    assert row.rstrip(" \\").endswith(pt.pct(p["point"]) + pt.interval(p["interval"]))
