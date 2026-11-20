"""T019: tests of the exploratory benchmark-derived analysis. The smoke figures are cross-checked against values recorded independently in T003 (read-only; skipped if absent)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import analyze_free_evaluation as afe

SMOKE_OK = (afe.DATASETS["smoke"]["replay"] / "predictions.csv").is_file() and afe.DATASETS["smoke"]["gold"].is_file()


def test_first_per_block_takes_the_smallest_case_id_of_each_block():
    blocks = {"c3": "B1", "c1": "B1", "c2": "B2", "c4": "B2", "c5": "B3"}
    assert afe.first_per_block(list(blocks), blocks) == ["c1", "c2", "c5"]


def test_rate_and_interval_edge_cases():
    assert afe.rate(0, 0) == {"x": 0, "n": 0, "rate": None, "ci95": None}
    r = afe.rate(0, 18)
    assert r["ci95"][0] == 0.0 and 0.18 < r["ci95"][1] < 0.19      # exact upper limit for 0 of 18
    assert afe.rate(2, 2)["ci95"][1] == 1.0


def test_planning_rows_are_monotone_in_m_and_in_coverage():
    plan = afe.planning()
    by = {(r["assumed_coverage"], r["m_prime"]): r["N_jeffreys"] for r in plan["rows"]}
    assert by[(0.10, 16)] < by[(0.10, 32)] < by[(0.10, 100)]
    assert by[(0.20, 32)] < by[(0.10, 32)] < by[(0.05, 32)]
    assert by[(0.05, 100)] is None                                   # beyond N_max
    assert plan["status"].startswith("illustration")


@pytest.mark.skipif(not SMOKE_OK, reason="smoke artifacts not present")
def test_smoke_figures_equal_the_independently_recorded_t003_values():
    res = afe.analyze("smoke")["scopes"]["all_cases"]
    r2, r0 = res["retrieval"]["R2"], res["retrieval"]["R0"]
    assert [r2[k]["x"] for k in ("mapped_in_pool", "success@1", "success@5", "success@10")] == [38, 22, 34, 38]
    assert [r0[k]["x"] for k in ("mapped_in_pool", "success@1", "success@5")] == [36, 21, 32]
    assert res["selective"]["C1|selective_policy_v2"]["automatic_coverage"]["x"] == 4
    assert res["selective"]["C0|selective_policy_v2"]["automatic_coverage"]["x"] == 0
    assert res["selective"]["C1x|selective_policy_v2"]["automatic_coverage"]["x"] == 7
    assert res["selective"]["C1x|legacy_gates_plus_p3"]["automatic_coverage"]["x"] == 26
    assert sum(res["outcomes"]["C1|selective_policy_v2"].values()) == 50
