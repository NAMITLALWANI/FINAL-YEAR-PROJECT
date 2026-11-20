"""T006: tests of the stratified predictive sizing procedure of Decision C9 (revision 3). Offline; no data, no provider, no sampling."""
import inspect
import json
import math
import random
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from hammer_pilot import sizing_c9 as z
from hammer_pilot.metrics import clopper_pearson
from hammer_pilot.sizing_c9 import AllocationInfeasible, SizingError

BACKEND = Path(__file__).resolve().parents[1]
BIG = {"S": 100_000}
NO_FLOOR = {"S": 0}

# A four-stratum fixture in which the Hamilton (largest-remainder) allocation is not monotone in N: stratum M receives 3 at N = 32 and 2 at N = 33.
ALABAMA = dict(frame={"S": 40, "M": 12, "L": 40, "XL": 60}, floors={"S": 0, "M": 0, "L": 1, "XL": 0},
               pilot={"S": {"automatic": 2, "cases": 13}, "M": {"automatic": 4, "cases": 4}, "L": {"automatic": 4, "cases": 14}, "XL": {"automatic": 0, "cases": 13}})


# ---------------------------------------------------------------- independent exact reference (Fractions)
def bb_exact(n, a, b):
    """BetaBinomial pmf in exact rational arithmetic: P(0) = prod (b+i)/(a+b+i); then the ratio recurrence."""
    p = Fraction(1)
    for i in range(n):
        p *= (b + i) / (a + b + i)
    out = [p]
    for k in range(n):
        out.append(out[-1] * Fraction(n - k, k + 1) * (a + k) / (b + n - k - 1))
    return out


def binom_exact(n, c):
    return [math.comb(n, k) * c ** k * (1 - c) ** (n - k) for k in range(n + 1)]


def conv_exact(pmfs):
    out = [Fraction(1)]
    for p in pmfs:
        new = [Fraction(0)] * (len(out) + len(p) - 1)
        for i, x in enumerate(out):
            for j, y in enumerate(p):
                new[i + j] += x * y
        out = new
    return out


def tail_exact(pmf, m):
    return sum(pmf[m:], Fraction(0)) if m < len(pmf) else Fraction(0)


def posterior(fx, prior="jeffreys"):
    return z.posterior_parameters(z.validate_pilot(fx["pilot"], fx["frame"]), prior)


# ================================================================ input validation
@pytest.mark.parametrize("frame", [{}, {"S": 0}, {"S": -3}, {"S": 2.5}, {"S": True}, {"S": "10"}])
def test_invalid_frames_are_rejected(frame):
    with pytest.raises(SizingError):
        z.validate_frame(frame)


@pytest.mark.parametrize("floors", [{}, {"S": 0, "M": 0}, {"M": 0}, {"S": -1}, {"S": 1.5}, {"S": True}])
def test_floors_must_be_explicit_for_exactly_the_frame_strata_and_valid(floors):
    with pytest.raises(SizingError):
        z.validate_floors(floors, {"S": 10})


def test_pilot_validation_and_no_pilot_strata():
    frame = {"S": 10, "M": 10}
    assert z.validate_pilot({"S": {"automatic": 2, "cases": 5}}, frame) == {"S": (2, 5), "M": (0, 0)}           # missing stratum = no pilot observations
    assert z.validate_pilot({"S": {"automatic": 0, "cases": 0}}, frame)["S"] == (0, 0)
    with pytest.raises(SizingError, match="exceed"):
        z.validate_pilot({"S": {"automatic": 6, "cases": 5}}, frame)
    with pytest.raises(SizingError, match="missing from the frame"):
        z.validate_pilot({"Q": {"automatic": 1, "cases": 5}}, frame)
    with pytest.raises(SizingError):
        z.validate_pilot({"S": {"automatic": -1, "cases": 5}}, frame)


@pytest.mark.parametrize("kw", [dict(beta=0), dict(beta=1), dict(beta=-0.1), dict(beta=float("nan")), dict(beta=True), dict(m_prime=0), dict(m_prime=2.5),
                                dict(n_max=0), dict(n_max=100_001), dict(gamma=0), dict(gamma=1), dict(gamma=float("inf"))])
def test_invalid_planning_parameters_are_rejected(kw):
    base = dict(m_prime=5, beta=0.1, gamma=0.1, n_max=1000)
    with pytest.raises(SizingError):
        z.size_sample(BIG, NO_FLOOR, {}, **{**base, **kw})


def test_no_open_parameter_has_a_default_and_the_priors_are_the_c9_ones():
    sig = inspect.signature(z.size_sample)
    for name in ("frame", "floors", "pilot", "m_prime", "beta", "gamma", "n_max"):
        assert sig.parameters[name].default is inspect.Parameter.empty, name
    assert z.PRIORS == {"jeffreys": (0.5, 0.5), "uniform": (1.0, 1.0)}
    with pytest.raises(SizingError):
        z.posterior_parameters({"S": (1, 5)}, "flat")


def test_inputs_are_not_mutated_and_output_declares_nothing_is_frozen():
    frame, floors, pilot = dict(ALABAMA["frame"]), dict(ALABAMA["floors"]), json.loads(json.dumps(ALABAMA["pilot"]))
    out = z.size_sample(frame, floors, pilot, m_prime=6, beta=0.30, gamma=0.10, n_max=80)
    assert (frame, floors, pilot) == (ALABAMA["frame"], ALABAMA["floors"], ALABAMA["pilot"])
    assert "freezes nothing" in out["status_of_this_output"] and "none is a default or a frozen value" in out["inputs"]["parameter_status"]
    assert any("guarded search" in a for a in out["assumptions"])


# ================================================================ C3 allocation
def test_largest_remainder_rounding_and_deterministic_ties():
    assert z.allocate(7, {"A": 50, "B": 30, "C": 20}, {"A": 0, "B": 0, "C": 0}) == {"A": 4, "B": 2, "C": 1}      # shares 3.5, 2.1, 1.4
    assert z.allocate(10, {"A": 10, "B": 10, "C": 10}, {"A": 0, "B": 0, "C": 0}) == {"A": 4, "B": 3, "C": 3}    # equal remainders: earlier stratum first


def test_floor_binding_and_redistribution():
    out = z.allocate(20, {"S": 100, "M": 100, "L": 10}, {"S": 0, "M": 0, "L": 5})                                  # L share 0.95 < floor 5
    assert out == {"S": 8, "M": 7, "L": 5} and sum(out.values()) == 20


def test_census_when_the_floor_reaches_the_frame_size():
    out = z.allocate(50, {"S": 100, "XL": 3}, {"S": 0, "XL": 5})                                                    # floor 5 capped at the frame size 3: census
    assert out == {"S": 47, "XL": 3}


def test_allocation_infeasible_cases_are_reported():
    with pytest.raises(AllocationInfeasible, match="floors"):
        z.allocate(2, {"S": 100, "XL": 3}, {"S": 0, "XL": 5})                                                       # effective floors 3 > N = 2
    with pytest.raises(AllocationInfeasible, match="exceeds the frame"):
        z.allocate(101, {"S": 100}, {"S": 0})
    with pytest.raises(AllocationInfeasible, match="floors"):
        z.allocate(9, {"S": 100, "M": 100}, {"S": 5, "M": 5})


def test_allocation_properties_hold_on_random_inputs():
    rng = random.Random(6)
    for _ in range(400):
        names = ["S", "M", "L", "XL"][: rng.choice([2, 3, 4])]
        frame = {h: rng.choice([1, 3, 12, 40, 250, 4000]) for h in names}
        floors = {h: rng.choice([0, 0, 1, 3, 20]) for h in names}
        n = rng.randint(1, sum(frame.values()))
        try:
            a = z.allocate(n, frame, floors)
        except AllocationInfeasible:
            continue
        assert sum(a.values()) == n
        assert all(min(floors[h], frame[h]) <= a[h] <= frame[h] for h in names)
        assert a == z.allocate(n, frame, floors)                                                                    # deterministic


def test_hamilton_allocation_is_not_monotone_in_N_in_the_fixture():
    f, fl = ALABAMA["frame"], ALABAMA["floors"]
    assert z.allocate(32, f, fl)["M"] == 3 and z.allocate(33, f, fl)["M"] == 2                                      # a larger N gives stratum M fewer cases


# ================================================================ distributions: exact reference, normalisation, stability
@pytest.mark.parametrize("n,a,b", [(0, 0.5, 0.5), (1, 0.5, 0.5), (7, 0.5, 0.5), (25, 1.0, 1.0), (30, 4.5, 8.5), (40, 1.5, 0.5), (12, 200.5, 3.5)])
def test_betabinomial_pmf_matches_exact_rational_arithmetic(n, a, b):
    exact = bb_exact(n, Fraction(a).limit_denominator(10), Fraction(b).limit_denominator(10))
    got = z.betabinomial_pmf(n, a, b)
    assert len(got) == n + 1 and abs(got.sum() - 1) < 1e-12
    assert max(abs(float(e) - g) for e, g in zip(exact, got)) < 1e-12


def test_huge_pilot_parameters_keep_the_pmf_normalised_to_machine_precision():
    # regression: a log-gamma difference lost about 4e-9 of normalisation here; the product form keeps it near 1e-15
    pmf = z.betabinomial_pmf(32, 200_000.5, 1_800_000.5)
    assert abs(pmf.sum() - 1) < 1e-12
    assert max(abs(g - float(e)) for g, e in zip(pmf, bb_exact(32, Fraction(400001, 2), Fraction(3600001, 2)))) < 1e-12


def test_betabinomial_moments():
    n, a, b = 60, 3.5, 9.5
    pmf, k = z.betabinomial_pmf(n, a, b), np.arange(61)
    mean = float((k * pmf).sum())
    assert mean == pytest.approx(n * a / (a + b), rel=1e-10)
    assert float(((k - mean) ** 2 * pmf).sum()) == pytest.approx(n * a * b * (a + b + n) / ((a + b) ** 2 * (a + b + 1)), rel=1e-9)


def test_binomial_pmf_matches_exact_and_edge_cases():
    got = z.binomial_pmf(20, 0.3)
    assert max(abs(g - e) for g, e in zip(got, binom_exact(20, 0.3))) < 1e-14
    assert list(z.binomial_pmf(4, 0.0)) == [1, 0, 0, 0, 0] and list(z.binomial_pmf(4, 1.0)) == [0, 0, 0, 0, 1] and list(z.binomial_pmf(0, 0.4)) == [1.0]


@pytest.mark.parametrize("call", [lambda: z.betabinomial_pmf(5, 0, 1), lambda: z.betabinomial_pmf(5, 1, -1), lambda: z.betabinomial_pmf(-1, 1, 1),
                                  lambda: z.betabinomial_pmf(5, float("nan"), 1), lambda: z.binomial_pmf(5, 1.2), lambda: z.binomial_pmf(5, float("nan"))])
def test_invalid_distribution_parameters_raise(call):
    with pytest.raises(SizingError):
        call()


def test_convolution_matches_exact_rational_convolution():
    parts = [(5, Fraction(1, 2), Fraction(1, 2)), (4, Fraction(7, 2), Fraction(3, 2)), (6, Fraction(1), Fraction(1))]
    exact = conv_exact([bb_exact(n, a, b) for n, a, b in parts])
    got = z.convolve([z.betabinomial_pmf(n, float(a), float(b)) for n, a, b in parts])
    assert len(got) == len(exact) and max(abs(float(e) - g) for e, g in zip(exact, got)) < 1e-13
    for m in (1, 3, 8, 15):
        assert z.tail_probability(got, m) == pytest.approx(float(tail_exact(exact, m)), abs=1e-13)


def test_tail_probability_edges():
    pmf = z.betabinomial_pmf(10, 0.5, 0.5)
    assert z.tail_probability(pmf, 1) == pytest.approx(1 - pmf[0], abs=1e-15)
    assert z.tail_probability(pmf, 11) == 0.0
    with pytest.raises(SizingError):
        z.tail_probability(pmf, 0)


def test_numerical_stability_for_large_and_extreme_parameters():
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        for n, a, b in [(5000, 0.5, 0.5), (5000, 1.0, 1.0), (3000, 1e-3, 1e-3), (3000, 2e6 + 0.5, 1.8e7 + 0.5), (2500, 0.5, 5e5)]:
            pmf = z.betabinomial_pmf(n, a, b)
            assert np.all(np.isfinite(pmf)) and abs(pmf.sum() - 1) < 1e-9 and pmf.min() >= 0
        for n, c in [(5000, 1e-6), (5000, 1 - 1e-6), (4000, 0.5)]:
            pmf = z.binomial_pmf(n, c)
            assert abs(pmf.sum() - 1) < 1e-9 and np.all(np.isfinite(pmf))
        total = z.convolve([z.betabinomial_pmf(800, 0.5, 0.5)] * 3)
        assert 0 <= z.tail_probability(total, 100) <= 1


# ================================================================ posteriors, priors and limits
def test_jeffreys_and_uniform_posteriors():
    assert z.posterior_parameters({"S": (3, 10)}, "jeffreys")["S"] == {"automatic": 3, "pilot_cases": 10, "alpha": 3.5, "beta": 7.5, "no_pilot_data": False}
    assert z.posterior_parameters({"S": (3, 10)}, "uniform")["S"]["alpha"] == 4 and z.posterior_parameters({"S": (3, 10)}, "uniform")["S"]["beta"] == 8


def test_a_stratum_without_pilot_observations_keeps_the_prior():
    post = z.posterior_parameters(z.validate_pilot({"S": {"automatic": 1, "cases": 4}}, {"S": 10, "XL": 5}), "jeffreys")
    assert (post["XL"]["alpha"], post["XL"]["beta"], post["XL"]["no_pilot_data"]) == (0.5, 0.5, True)
    assert post["S"]["no_pilot_data"] is False


def test_lower_limits_use_bonferroni_over_all_strata_and_zero_without_data():
    pilot = {"S": (6, 60), "M": (0, 40), "L": (3, 25), "XL": (0, 0)}
    lim = z.lower_confidence_limits(pilot, 0.10, 4)
    assert lim["S"]["lower"] == pytest.approx(clopper_pearson(6, 60, alpha=2 * 0.025)[0], abs=1e-12) and lim["S"]["tail"] == 0.025
    assert lim["M"]["lower"] == 0.0 and lim["XL"]["lower"] == 0.0 and lim["XL"]["no_pilot_data"] is True
    assert 0 < lim["S"]["lower"] < 6 / 60 and 0 < lim["L"]["lower"] < 3 / 25
    wider = z.lower_confidence_limits(pilot, 0.10, 8)                                                              # more strata, smaller tail, lower limit
    assert wider["S"]["lower"] < lim["S"]["lower"]


# ================================================================ search and the guard against non-monotone behaviour
def test_search_returns_the_smallest_N_whose_whole_suffix_satisfies_the_condition():
    curve = {1: 0.2, 2: 0.95, 3: 0.4, 4: 0.96, 5: 0.97, 6: 0.99}
    r = z.search(lambda n: curve[n], 1, 6, 0.9)
    assert (r["first_N_meeting_condition"], r["N"], r["status"]) == (2, 4, "found")
    assert r["non_monotone"] is True and r["failing_N_after_first_meeting"] == [3]


def test_search_reports_failure_at_N_max_and_when_no_N_satisfies():
    r = z.search(lambda n: {1: 0.95, 2: 0.96, 3: 0.5}[n], 1, 3, 0.9)
    assert r["status"] == "not_found_within_N_max" and r["N"] is None and r["first_N_meeting_condition"] == 1 and "fails at larger N'" in r["reason"]
    r = z.search(lambda n: 0.1, 1, 5, 0.9)
    assert r["status"] == "not_found_within_N_max" and r["first_N_meeting_condition"] is None and r["max_probability_in_range"]["probability"] == 0.1
    assert z.search(lambda n: 1.0, 10, 5, 0.9)["status"] == "not_found_within_N_max"                                 # range empty: N cannot reach m' within N_max


def test_an_infeasible_N_inside_the_range_fails_the_condition_and_is_reported():
    r = z.search(lambda n: None if n == 4 else 0.95, 1, 6, 0.9)
    assert r["N"] == 5 and r["infeasible_N"] == [4] and r["first_N_meeting_condition"] == 1


def test_monotone_curve_gives_the_first_meeting_N():
    r = z.search(lambda n: min(1.0, n / 10), 1, 12, 0.65)
    assert r["N"] == r["first_N_meeting_condition"] == 7 and r["non_monotone"] is False and r["borderline"] is False


def test_borderline_is_flagged_not_adjusted():
    r = z.search(lambda n: 0.9 if n >= 3 else 0.1, 1, 5, 0.9)                                                         # probability exactly equals the target
    assert r["N"] == 3 and r["borderline"] is True


def test_non_monotone_allocation_cannot_cause_a_wrong_smallest_N():
    fx = ALABAMA
    res = z.size_predictive(fx["frame"], fx["floors"], fx["pilot"], m_prime=6, beta=0.30, n_max=80, prior="jeffreys")
    post, target = posterior(fx), 0.70
    p = lambda n: z.predictive_probability(n, fx["frame"], fx["floors"], post, 6)[0]
    assert p(31) >= target > p(33) and p(32) >= target and p(34) >= target                                          # the dip is real
    assert res["first_N_meeting_condition"] == 31 and res["N"] == 34 and res["non_monotone"] and res["failing_N_after_first_meeting"] == [33]
    for n in range(res["N"], 81):                                                                                     # independent re-check of the guard over the range
        assert p(n) >= target, n
    assert p(res["N"] - 1) < target or any(p(n) < target for n in range(res["N"] - 1, 81))                          # and N is the smallest such value
    assert res["allocation_at_N"] == z.allocate(34, fx["frame"], fx["floors"]) and sum(res["allocation_at_N"].values()) == 34


def test_the_guard_reports_a_dip_at_the_end_of_the_range_as_not_found():
    fx = ALABAMA
    res = z.size_predictive(fx["frame"], fx["floors"], fx["pilot"], m_prime=6, beta=0.30, n_max=33, prior="jeffreys")      # N_max falls on the dip
    assert res["status"] == "not_found_within_N_max" and res["N"] is None and res["first_N_meeting_condition"] == 31
    assert res["probability_at_N_max"] < 0.70 and "first met at N = 31" in res["reason"]


# ================================================================ validation against the illustrative C9 values (known coverage; not the stratified procedure)
C9_TABLE = [(16, 0.10, 0.10, 210), (16, 0.10, 0.05, 227), (32, 0.10, 0.10, 390), (32, 0.10, 0.05, 413), (32, 0.20, 0.10, 193), (32, 0.20, 0.05, 204),
            (100, 0.10, 0.10, 1123), (100, 0.10, 0.05, 1161), (100, 0.30, 0.10, 370), (100, 0.30, 0.05, 381)]


@pytest.mark.parametrize("m,c,beta,expected", C9_TABLE)
def test_known_coverage_search_reproduces_the_illustrative_c9_values(m, c, beta, expected):
    r = z.size_known_coverage(BIG, NO_FLOOR, {"S": c}, m_prime=m, beta=beta, n_max=2600)
    assert r["status"] == "found" and r["N"] == expected and r["first_N_meeting_condition"] == expected and "validation helper" in r["method"]


def test_n_390_and_413_are_confirmed_by_exact_rational_binomial_tails():
    c = Fraction(1, 10)
    tail = lambda n: sum(math.comb(n, k) * c ** k * (1 - c) ** (n - k) for k in range(32, n + 1))
    assert tail(389) < Fraction(9, 10) <= tail(390)                                                                  # beta = 0.10
    assert tail(412) < Fraction(95, 100) <= tail(413)                                                                # beta = 0.05


def test_ceil_m_over_c_gives_only_about_one_half_probability():
    n = math.ceil(32 / 0.10)
    p = z.tail_probability(z.binomial_pmf(n, 0.10), 32)
    assert n == 320 and 0.50 < p < 0.57                                                                              # C9: the expected-count rule is not enough


def test_the_stratified_predictive_procedure_is_not_the_pooled_binomial():
    pilot = {"S": {"automatic": 10, "cases": 100}}                                                                   # 10 percent observed, but with finite pilot information
    r = z.size_predictive(BIG, NO_FLOOR, pilot, m_prime=32, beta=0.10, n_max=2600, prior="jeffreys")
    assert r["status"] == "found" and r["N"] > 390                                                                   # parameter uncertainty raises N above the known-coverage value


def test_with_a_very_large_pilot_the_predictive_n_approaches_the_known_coverage_value():
    pilot = {"S": {"automatic": 200_000, "cases": 2_000_000}}
    r = z.size_predictive(BIG, NO_FLOOR, pilot, m_prime=32, beta=0.10, n_max=2600, prior="jeffreys")
    assert abs(r["N"] - 390) <= 1


# ================================================================ zero-pilot strata, census strata, floors
def test_prior_only_single_stratum_matches_the_exact_beta_binomial():
    post = posterior(dict(frame={"S": 10_000}, pilot={}))
    p, alloc = z.predictive_probability(300, {"S": 10_000}, NO_FLOOR, post, 5)
    assert alloc == {"S": 300}
    assert p == pytest.approx(float(tail_exact(bb_exact(300, Fraction(1, 2), Fraction(1, 2)), 5)), abs=1e-12)


def test_all_strata_without_pilot_data_gives_zero_lower_bound_and_a_clear_failure():
    r = z.size_lower_bound({"S": 5000, "M": 5000}, {"S": 0, "M": 0}, {}, m_prime=3, beta=0.1, gamma=0.1, n_max=500)
    assert r["status"] == "not_found_within_N_max" and r["probability_at_N_max"] == 0.0 and r["lower_limits"]["S"]["lower"] == 0.0
    assert r["strata_in_bonferroni"] == 2 and r["tail_per_stratum"] == 0.05


def test_a_zero_pilot_stratum_adds_nothing_to_the_lower_bound_and_is_wide_in_the_predictive():
    frame, floors = {"S": 4000, "XL": 4000}, {"S": 0, "XL": 0}
    pilot = {"S": {"automatic": 10, "cases": 50}}
    lb = z.size_lower_bound(frame, floors, pilot, m_prime=20, beta=0.1, gamma=0.1, n_max=900)
    cL = lb["lower_limits"]["S"]["lower"]
    n = lb["N"]
    alloc = z.allocate(n, frame, floors)
    only_s = z.tail_probability(z.binomial_pmf(alloc["S"], cL), 20)
    assert lb["probability_at_N"] == pytest.approx(only_s, abs=1e-12)                                              # XL contributes 0 automatic assignments
    pred = z.size_predictive(frame, floors, pilot, m_prime=20, beta=0.1, n_max=900, prior="jeffreys")
    assert pred["posterior"]["XL"]["no_pilot_data"] is True and pred["posterior"]["XL"]["alpha"] == 0.5


def test_census_stratum_is_taken_whole_at_every_N_and_floors_hold():
    frame, floors = {"S": 5000, "XL": 3}, {"S": 0, "XL": 3}
    for n in (10, 100, 400):
        assert z.allocate(n, frame, floors)["XL"] == 3
    r = z.size_predictive(frame, floors, {"S": {"automatic": 8, "cases": 50}, "XL": {"automatic": 2, "cases": 3}}, m_prime=20, beta=0.1, n_max=600, prior="jeffreys")
    assert r["status"] == "found" and r["allocation_at_N"]["XL"] == 3


def test_floors_that_make_the_plan_infeasible_within_N_max_are_reported_not_hidden():
    r = z.size_predictive({"S": 5000, "M": 5000}, {"S": 300, "M": 300}, {}, m_prime=5, beta=0.1, n_max=500, prior="jeffreys")
    assert r["status"] == "not_found_within_N_max" and "exceeds N_max" in r["reason"] and r["range"][0] == 600
    with pytest.raises(SizingError, match="exceeds the frame"):
        z.size_predictive({"S": 100}, {"S": 0}, {}, m_prime=5, beta=0.1, n_max=101, prior="jeffreys")


# ================================================================ exact convolution against an independent simulation
def test_exact_convolution_agrees_with_a_seeded_simulation_of_the_stratified_model():
    fx = dict(frame={"S": 4000, "M": 4000, "L": 300}, floors={"S": 0, "M": 0, "L": 0},
              pilot={"S": {"automatic": 6, "cases": 60}, "M": {"automatic": 9, "cases": 60}, "L": {"automatic": 5, "cases": 20}})
    n_total, m = 120, 16
    post = posterior(fx)
    exact, alloc = z.predictive_probability(n_total, fx["frame"], fx["floors"], post, m)
    rng, reps = np.random.default_rng(20261120), 400_000
    total = np.zeros(reps, dtype=np.int64)
    for h, n_h in alloc.items():
        total += rng.binomial(n_h, rng.beta(post[h]["alpha"], post[h]["beta"], size=reps))
    mc = float((total >= m).mean())
    assert abs(mc - exact) < 5 * math.sqrt(exact * (1 - exact) / reps)
    pmf = z.convolve([z.betabinomial_pmf(n_h, post[h]["alpha"], post[h]["beta"]) for h, n_h in alloc.items()])
    k = np.arange(len(pmf))
    assert float((k * pmf).sum()) == pytest.approx(sum(n_h * post[h]["alpha"] / (post[h]["alpha"] + post[h]["beta"]) for h, n_h in alloc.items()), rel=1e-10)
    assert float(total.mean()) == pytest.approx(float((k * pmf).sum()), rel=5e-3)


def test_exact_convolution_agrees_with_rational_arithmetic_for_a_small_stratified_case():
    fx = dict(frame={"S": 60, "M": 40, "L": 12}, floors={"S": 0, "M": 0, "L": 2},
              pilot={"S": {"automatic": 1, "cases": 8}, "M": {"automatic": 2, "cases": 6}, "L": {"automatic": 0, "cases": 0}})
    post = posterior(fx)
    p, alloc = z.predictive_probability(30, fx["frame"], fx["floors"], post, 7)
    ex = conv_exact([bb_exact(n_h, Fraction(post[h]["alpha"]).limit_denominator(10), Fraction(post[h]["beta"]).limit_denominator(10)) for h, n_h in alloc.items()])
    assert p == pytest.approx(float(tail_exact(ex, 7)), abs=1e-13) and sum(alloc.values()) == 30


# ================================================================ full procedure and CLI
def test_size_sample_reports_all_three_calculations_and_is_deterministic():
    fx = ALABAMA
    kw = dict(m_prime=6, beta=0.30, gamma=0.10, n_max=80)
    a = z.size_sample(fx["frame"], fx["floors"], fx["pilot"], **kw)
    b = z.size_sample(fx["frame"], fx["floors"], fx["pilot"], **kw)
    assert json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)
    assert a["primary_jeffreys"]["prior_parameters"] == [0.5, 0.5] and a["sensitivity_uniform_prior"]["prior_parameters"] == [1.0, 1.0]
    assert a["sensitivity_lower_bound"]["strata_in_bonferroni"] == 4 and a["sensitivity_lower_bound"]["tail_per_stratum"] == 0.10 / 4
    assert a["inputs"]["N_max"] == 80 and a["inputs"]["m_prime"] == 6


def test_probabilities_stay_within_zero_and_one_over_a_scan():
    fx = ALABAMA
    post = posterior(fx)
    for n in range(1, 120):
        try:
            p, _ = z.predictive_probability(n, fx["frame"], fx["floors"], post, 6)
        except AllocationInfeasible:
            continue
        assert 0.0 <= p <= 1.0


def run_cli(tmp_path, spec, name="out.json"):
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps(spec))
    out = tmp_path / name
    proc = subprocess.run([sys.executable, "-I", str(BACKEND / "scripts" / "size_hammer_main_sample.py"), "--inputs", str(inp), "--out", str(out)],
                          capture_output=True, text=True, cwd=BACKEND, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})
    return proc, out


def test_cli_runs_requires_every_input_refuses_to_overwrite_and_reports_refusals(tmp_path):
    spec = dict(frame=ALABAMA["frame"], floors=ALABAMA["floors"], pilot=ALABAMA["pilot"], m_prime=6, beta=0.30, gamma=0.10, n_max=80)
    proc, out = run_cli(tmp_path, spec)
    assert proc.returncode == 0 and "primary_jeffreys: found, N = 34" in proc.stdout
    assert json.loads(out.read_text())["primary_jeffreys"]["N"] == 34
    before = out.read_bytes()
    proc2, _ = run_cli(tmp_path, spec)
    assert proc2.returncode != 0 and out.read_bytes() == before                                                      # refuses to overwrite
    missing = {k: v for k, v in spec.items() if k != "beta"}
    proc3, out3 = run_cli(tmp_path, missing, "o3.json")
    assert proc3.returncode == 2 and "no defaults" in proc3.stderr and not out3.exists()
    proc4, out4 = run_cli(tmp_path, {**spec, "beta": 5}, "o4.json")
    assert proc4.returncode == 1 and "sizing refused" in proc4.stderr and not out4.exists()
