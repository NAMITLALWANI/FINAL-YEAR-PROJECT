"""Stratified predictive sizing of Decision C9 (revision 3): offline calculation, no data, no provider access, no sampling.

Given post-exclusion stratum sizes, allocation floors, per-stratum pilot counts and the planning parameters, find the smallest total sample size N
for which the predictive probability of obtaining at least m' automatic assignments is at least 1 - beta, for every N' in the search range up to N_max.

Method (C9 steps 2 to 6):
  1. Per stratum h with a_h automatic assignments among n_p,h pilot cases, coverage c_h ~ Beta(a0 + a_h, b0 + n_p,h - a_h), where (a0, b0) is the
     prior: Jeffreys (1/2, 1/2) primary, uniform (1, 1) sensitivity. A stratum without pilot observations keeps the prior.
  2. For a total N, the C3 allocation gives n_h(N) (floors, census caps, iterative redistribution, largest-remainder rounding).
  3. A_h | n_h ~ BetaBinomial(n_h, alpha_h, beta_h), independent across strata; the total A = sum A_h has the exact convolution of the stratum pmfs.
  4. N is the smallest value with P(A >= m') >= 1 - beta such that the condition also holds for EVERY N' in [N, N_max] (guards against non-monotone
     allocation from rounding, floors and caps).
  5. Sensitivity: replace each c_h by its exact one-sided Clopper-Pearson lower limit at level 1 - gamma/H (Bonferroni over the H strata of the frame;
     0 for a stratum without pilot data) and use the same search with Binomial(n_h, c_L,h).

The module chooses NO open parameter: m', beta, gamma, N_max, floors and pilot counts are required arguments with no default. Its output is a
planning calculation conditional on those inputs, and freezes nothing. Probabilities are exact up to floating-point rounding (pmfs are built in log
space and normalisation is checked). numpy is used for the convolution.
"""
from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from .metrics import clopper_pearson

PRIORS: dict[str, tuple[float, float]] = {"jeffreys": (0.5, 0.5), "uniform": (1.0, 1.0)}
NORMALISATION_TOLERANCE = 1e-9
BORDERLINE_MARGIN = 1e-9


class SizingError(ValueError):
    """Invalid input or an infeasible sizing request. Raised instead of returning a guess."""


class AllocationInfeasible(SizingError):
    """The C3 allocation cannot be formed for this N (floors exceed N, N exceeds the frame, or simultaneous binding cannot sum to N)."""


# --------------------------------------------------------------------------- input validation
def _int(name: str, value: Any, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < minimum:
        raise SizingError(f"{name} must be an integer of at least {minimum}, got {value!r}")
    return int(value)


def _open_probability(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.floating)) or not math.isfinite(value) or not 0 < value < 1:
        raise SizingError(f"{name} must be a number strictly between 0 and 1, got {value!r}")
    return float(value)


def validate_frame(frame: Mapping[str, int]) -> dict[str, int]:
    if not frame:
        raise SizingError("the frame must contain at least one stratum")
    return {str(h): _int(f"frame size of stratum {h!r}", n, 1) for h, n in frame.items()}


def validate_floors(floors: Mapping[str, int], frame: Mapping[str, int]) -> dict[str, int]:
    if set(floors) != set(frame):
        raise SizingError(f"floors must be given explicitly for exactly the strata of the frame {sorted(frame)} (use 0 for none)")
    return {h: _int(f"floor of stratum {h!r}", floors[h], 0) for h in frame}


def validate_pilot(pilot: Mapping[str, Mapping[str, int]], frame: Mapping[str, int]) -> dict[str, tuple[int, int]]:
    """Per stratum (automatic, cases). A stratum absent from `pilot`, or with 0 cases, has no pilot observations and keeps the prior."""
    unknown = set(pilot) - set(frame)
    if unknown:
        raise SizingError(f"pilot data for strata missing from the frame: {sorted(unknown)}")
    out = {}
    for h in frame:
        p = pilot.get(h, {"automatic": 0, "cases": 0})
        n_p, a = _int(f"pilot cases of stratum {h!r}", p.get("cases", 0), 0), _int(f"pilot automatic count of stratum {h!r}", p.get("automatic", 0), 0)
        if a > n_p:
            raise SizingError(f"stratum {h!r}: {a} automatic assignments exceed {n_p} pilot cases")
        out[h] = (a, n_p)
    return out


# --------------------------------------------------------------------------- C3 allocation
def allocate(total: int, frame: Mapping[str, int], floors: Mapping[str, int]) -> dict[str, int]:
    """C3: proportional allocation with floors and census caps, iterative redistribution, largest-remainder rounding.

    Per round (simultaneous binding): among unbound strata, a stratum whose proportional share exceeds its frame size is bound at the frame size (census);
    one whose share is below its effective floor min(floor, frame size) is bound at that floor. Bound strata stay bound and the remainder is allocated
    to the unbound strata proportionally to their frame sizes. Repeat until nothing new binds. Arithmetic is exact (Fractions); ties in the largest-remainder
    step go to the larger frame size, then to the earlier stratum. Raises AllocationInfeasible when no allocation summing to N can be formed."""
    frame, floors = validate_frame(frame), validate_floors(floors, frame)
    total = _int("N", total, 1)
    strata = list(frame)
    if total > sum(frame.values()):
        raise AllocationInfeasible(f"N = {total} exceeds the frame size {sum(frame.values())}")
    eff = {h: min(floors[h], frame[h]) for h in strata}
    if sum(eff.values()) > total:
        raise AllocationInfeasible(f"the floors (capped at frame size) sum to {sum(eff.values())}, more than N = {total}: the plan is rejected")
    fixed: dict[str, int] = {}
    while True:
        unbound = [h for h in strata if h not in fixed]
        if not unbound:
            break
        remaining = total - sum(fixed.values())
        base = sum(frame[h] for h in unbound)
        if remaining < 0 or remaining > base:
            raise AllocationInfeasible(f"simultaneous binding leaves {remaining} to allocate across strata holding {base}")
        share = {h: Fraction(remaining * frame[h], base) for h in unbound}
        newly = {h: frame[h] for h in unbound if share[h] > frame[h]}
        newly.update({h: eff[h] for h in unbound if h not in newly and share[h] < eff[h]})
        if not newly:
            break
        fixed.update(newly)
    allocation = dict(fixed)
    unbound = [h for h in strata if h not in fixed]
    if unbound:
        remaining = total - sum(fixed.values())
        base = sum(frame[h] for h in unbound)
        share = {h: Fraction(remaining * frame[h], base) for h in unbound}
        floor_part = {h: share[h].numerator // share[h].denominator for h in unbound}
        leftover = remaining - sum(floor_part.values())
        order = sorted(unbound, key=lambda h: (-(share[h] - floor_part[h]), -frame[h], strata.index(h)))
        allocation.update({h: floor_part[h] + (1 if i < leftover else 0) for i, h in enumerate(order)})
    elif sum(allocation.values()) != total:
        raise AllocationInfeasible(f"every stratum is bound and the allocation sums to {sum(allocation.values())}, not N = {total}")
    for h in strata:
        if not eff[h] <= allocation[h] <= frame[h]:
            raise AllocationInfeasible(f"stratum {h!r}: allocation {allocation[h]} outside [{eff[h]}, {frame[h]}]")
    if sum(allocation.values()) != total:
        raise AllocationInfeasible("allocation does not sum to N")
    return {h: allocation[h] for h in strata}


# --------------------------------------------------------------------------- distributions
def _checked(pmf: np.ndarray, what: str) -> np.ndarray:
    if abs(float(pmf.sum()) - 1.0) > NORMALISATION_TOLERANCE or not np.all(np.isfinite(pmf)) or np.any(pmf < 0):
        raise SizingError(f"{what}: pmf failed the normalisation check (sum {float(pmf.sum())!r})")
    return pmf


def betabinomial_pmf(n: int, alpha: float, beta: float) -> np.ndarray:
    """pmf of BetaBinomial(n, alpha, beta) on 0..n, built in log space from the ratio recurrence."""
    n = _int("n", n, 0)
    if not (math.isfinite(alpha) and math.isfinite(beta) and alpha > 0 and beta > 0):
        raise SizingError(f"alpha and beta must be positive and finite, got {alpha!r}, {beta!r}")
    if n == 0:
        return np.array([1.0])
    k = np.arange(n, dtype=float)
    log_ratio = np.log(n - k) - np.log(k + 1.0) + np.log(k + alpha) - np.log(n - k - 1.0 + beta)
    log0 = float(np.sum(np.log(beta + k) - np.log(alpha + beta + k)))        # = log B(alpha, n+beta)/B(alpha, beta); a sum of n small terms, accurate for huge alpha, beta
    return _checked(np.exp(log0 + np.concatenate(([0.0], np.cumsum(log_ratio)))), f"BetaBinomial({n}, {alpha}, {beta})")


def binomial_pmf(n: int, c: float) -> np.ndarray:
    n = _int("n", n, 0)
    if not (math.isfinite(c) and 0 <= c <= 1):
        raise SizingError(f"coverage must lie in [0, 1], got {c!r}")
    pmf = np.zeros(n + 1)
    if n == 0 or c == 0:
        pmf[0] = 1.0
        return pmf
    if c == 1:
        pmf[n] = 1.0
        return pmf
    k = np.arange(n, dtype=float)
    log_ratio = np.log(n - k) - np.log(k + 1.0) + math.log(c) - math.log1p(-c)
    return _checked(np.exp(n * math.log1p(-c) + np.concatenate(([0.0], np.cumsum(log_ratio)))), f"Binomial({n}, {c})")


def convolve(pmfs: Sequence[np.ndarray]) -> np.ndarray:
    """Exact (up to floating point) pmf of the sum of independent variables."""
    out = np.array([1.0])
    for p in pmfs:
        out = np.convolve(out, p)
    return _checked(out, "convolution")


def tail_probability(pmf: np.ndarray, m_prime: int) -> float:
    """P(A >= m')."""
    m_prime = _int("m'", m_prime, 1)
    return float(pmf[m_prime:].sum()) if m_prime < len(pmf) else 0.0


# --------------------------------------------------------------------------- posteriors and limits
def posterior_parameters(pilot: Mapping[str, tuple[int, int]], prior: str) -> dict[str, dict[str, Any]]:
    if prior not in PRIORS:
        raise SizingError(f"prior must be one of {sorted(PRIORS)}")
    a0, b0 = PRIORS[prior]
    return {h: {"automatic": a, "pilot_cases": n_p, "alpha": a0 + a, "beta": b0 + n_p - a, "no_pilot_data": n_p == 0} for h, (a, n_p) in pilot.items()}


def lower_confidence_limits(pilot: Mapping[str, tuple[int, int]], gamma: float, n_strata: int) -> dict[str, dict[str, Any]]:
    """Exact one-sided lower limits at level 1 - gamma/H (Bonferroni over the H strata of the frame); 0 where there is no pilot data."""
    gamma = _open_probability("gamma", gamma)
    level_tail = gamma / n_strata
    out = {}
    for h, (a, n_p) in pilot.items():
        if n_p == 0:
            out[h] = {"lower": 0.0, "no_pilot_data": True, "tail": level_tail}
        else:
            out[h] = {"lower": 0.0 if a == 0 else clopper_pearson(a, n_p, alpha=2 * level_tail)[0], "no_pilot_data": False, "tail": level_tail}
    return out


# --------------------------------------------------------------------------- search
def search(probability_at: Callable[[int], float | None], n_lo: int, n_max: int, target: float) -> dict[str, Any]:
    """Smallest N in [n_lo, n_max] with probability >= target that also holds for every larger N' up to n_max.

    `probability_at(N)` returns None when no allocation exists for N; such an N' fails the condition (it is reported, never skipped)."""
    if n_lo > n_max:
        return {"status": "not_found_within_N_max", "reason": f"the smallest N that could reach m' ({n_lo}) exceeds N_max ({n_max})", "range": [n_lo, n_max],
                "N": None, "first_N_meeting_condition": None, "probability_at_N": None, "non_monotone": False, "infeasible_N": []}
    grid = list(range(n_lo, n_max + 1))
    prob = {n: probability_at(n) for n in grid}
    ok = {n: (prob[n] is not None and prob[n] >= target) for n in grid}
    first = next((n for n in grid if ok[n]), None)
    guarded = None                     # smallest N whose whole suffix [N, n_max] satisfies the condition (None if N_max itself fails)
    for n in reversed(grid):
        if not ok[n]:
            break
        guarded = n
    infeasible = [n for n in grid if prob[n] is None]
    feasible = {n: p for n, p in prob.items() if p is not None}
    best_n = max(feasible, key=lambda n: (feasible[n], -n)) if feasible else None
    dips = [n for n in grid if first is not None and n > first and not ok[n]]
    out: dict[str, Any] = {"range": [n_lo, n_max], "target": target, "first_N_meeting_condition": first, "N": guarded,
                           "probability_at_N": prob[guarded] if guarded is not None else None,
                           "non_monotone": bool(dips), "failing_N_after_first_meeting": dips[:20], "failing_N_after_first_meeting_count": len(dips),
                           "infeasible_N": infeasible[:20], "infeasible_N_count": len(infeasible),
                           "probability_at_N_max": prob[n_max], "max_probability_in_range": {"N": best_n, "probability": feasible[best_n]} if best_n is not None else None}
    if guarded is not None:
        before = prob.get(guarded - 1)
        out["status"] = "found"
        out["borderline"] = abs(prob[guarded] - target) < BORDERLINE_MARGIN or (before is not None and abs(before - target) < BORDERLINE_MARGIN)
    else:
        out["status"] = "not_found_within_N_max"
        out["reason"] = ("the probability condition does not hold at N_max" if not ok[n_max]
                         else "no N in the range satisfies the condition for every larger N'")
        if first is not None:
            out["reason"] += f"; the condition is first met at N = {first} but fails at larger N'"
    return out


def _check_common(frame: Mapping[str, int], floors: Mapping[str, int], m_prime: int, beta: float, n_max: int) -> tuple[dict[str, int], dict[str, int], int, float, int]:
    frame, floors = validate_frame(frame), validate_floors(floors, frame)
    m_prime, beta, n_max = _int("m'", m_prime, 1), _open_probability("beta", beta), _int("N_max", n_max, 1)
    if n_max > sum(frame.values()):
        raise SizingError(f"N_max = {n_max} exceeds the frame size {sum(frame.values())}; a sample cannot exceed the frame")
    return frame, floors, m_prime, beta, n_max


def _grid_start(frame: Mapping[str, int], floors: Mapping[str, int], m_prime: int) -> int:
    return max(m_prime, sum(min(floors[h], frame[h]) for h in frame), 1)


def _with_allocation(frame: Mapping[str, int], floors: Mapping[str, int], pmf_for: Callable[[str, int], np.ndarray], m_prime: int) -> Callable[[int], float | None]:
    cache: dict[tuple[str, int], np.ndarray] = {}

    def probability_at(n_total: int) -> float | None:
        try:
            alloc = allocate(n_total, frame, floors)
        except AllocationInfeasible:
            return None
        parts = []
        for h, n_h in alloc.items():
            if (h, n_h) not in cache:
                cache[(h, n_h)] = pmf_for(h, n_h)
            parts.append(cache[(h, n_h)])
        return tail_probability(convolve(parts), m_prime)
    return probability_at


def predictive_probability(n_total: int, frame: Mapping[str, int], floors: Mapping[str, int], posterior: Mapping[str, Mapping[str, Any]], m_prime: int) -> tuple[float, dict[str, int]]:
    """P(A >= m') for one N under the stratified beta-binomial predictive distribution, with the C3 allocation used."""
    alloc = allocate(n_total, frame, floors)
    pmf = convolve([betabinomial_pmf(n_h, posterior[h]["alpha"], posterior[h]["beta"]) for h, n_h in alloc.items()])
    return tail_probability(pmf, m_prime), alloc


# --------------------------------------------------------------------------- top-level procedures
def size_predictive(frame: Mapping[str, int], floors: Mapping[str, int], pilot: Mapping[str, Mapping[str, int]], *, m_prime: int, beta: float, n_max: int,
                    prior: str) -> dict[str, Any]:
    """C9 steps 2 to 5 for one prior."""
    frame, floors, m_prime, beta, n_max = _check_common(frame, floors, m_prime, beta, n_max)
    post = posterior_parameters(validate_pilot(pilot, frame), prior)
    fn = _with_allocation(frame, floors, lambda h, n_h: betabinomial_pmf(n_h, post[h]["alpha"], post[h]["beta"]), m_prime)
    result = search(fn, _grid_start(frame, floors, m_prime), n_max, 1 - beta)
    result.update({"method": "stratified beta-binomial predictive, exact convolution", "prior": prior, "prior_parameters": list(PRIORS[prior]), "posterior": post})
    if result["N"] is not None:
        result["allocation_at_N"] = allocate(result["N"], frame, floors)
    return result


def size_lower_bound(frame: Mapping[str, int], floors: Mapping[str, int], pilot: Mapping[str, Mapping[str, int]], *, m_prime: int, beta: float, gamma: float,
                     n_max: int) -> dict[str, Any]:
    """C9 step 6: the lower-confidence-bound sensitivity check (Bonferroni over the strata of the frame)."""
    frame, floors, m_prime, beta, n_max = _check_common(frame, floors, m_prime, beta, n_max)
    limits = lower_confidence_limits(validate_pilot(pilot, frame), gamma, len(frame))
    fn = _with_allocation(frame, floors, lambda h, n_h: binomial_pmf(n_h, limits[h]["lower"]), m_prime)
    result = search(fn, _grid_start(frame, floors, m_prime), n_max, 1 - beta)
    result.update({"method": "binomial at exact one-sided lower confidence limits, Bonferroni over the strata of the frame", "gamma": gamma,
                   "strata_in_bonferroni": len(frame), "tail_per_stratum": gamma / len(frame), "lower_limits": limits})
    if result["N"] is not None:
        result["allocation_at_N"] = allocate(result["N"], frame, floors)
    return result


def size_known_coverage(frame: Mapping[str, int], floors: Mapping[str, int], coverage: Mapping[str, float], *, m_prime: int, beta: float, n_max: int) -> dict[str, Any]:
    """Validation helper: the same search with coverage treated as exactly known (binomial). It reproduces the illustrative pooled values of C9
    for a single stratum and is NOT a substitute for the stratified predictive procedure."""
    frame, floors, m_prime, beta, n_max = _check_common(frame, floors, m_prime, beta, n_max)
    if set(coverage) != set(frame):
        raise SizingError("coverage must be given for exactly the strata of the frame")
    fn = _with_allocation(frame, floors, lambda h, n_h: binomial_pmf(n_h, float(coverage[h])), m_prime)
    result = search(fn, _grid_start(frame, floors, m_prime), n_max, 1 - beta)
    result["method"] = "known-coverage binomial (validation helper, not the C9 procedure)"
    return result


def size_sample(frame: Mapping[str, int], floors: Mapping[str, int], pilot: Mapping[str, Mapping[str, int]], *, m_prime: int, beta: float, gamma: float,
                n_max: int, m: int | None = None) -> dict[str, Any]:
    """Full C9 calculation: Jeffreys primary, uniform-prior sensitivity, and the lower-bound sensitivity check. Nothing is chosen or frozen here."""
    frame_v, floors_v, m_prime_v, beta_v, n_max_v = _check_common(frame, floors, m_prime, beta, n_max)
    return {
        "status_of_this_output": "planning calculation conditional on the supplied inputs; it selects and freezes nothing (Decision C9 step 7 is a separate act)",
        "inputs": {"frame_post_exclusion": frame_v, "floors": floors_v, "pilot": {h: {"automatic": a, "cases": n} for h, (a, n) in validate_pilot(pilot, frame_v).items()},
                   "m": m, "m_prime": m_prime_v, "beta": beta_v, "gamma": gamma, "N_max": n_max_v,
                   "parameter_status": "supplied by the caller; none is a default or a frozen value"},
        "primary_jeffreys": size_predictive(frame_v, floors_v, pilot, m_prime=m_prime_v, beta=beta_v, n_max=n_max_v, prior="jeffreys"),
        "sensitivity_uniform_prior": size_predictive(frame_v, floors_v, pilot, m_prime=m_prime_v, beta=beta_v, n_max=n_max_v, prior="uniform"),
        "sensitivity_lower_bound": size_lower_bound(frame_v, floors_v, pilot, m_prime=m_prime_v, beta=beta_v, gamma=gamma, n_max=n_max_v),
        "assumptions": ["independent strata", "the pilot is representative of its stratum in the main frame", "coverage is stable under frozen code",
                        "the beta-binomial treats strata as infinite populations (expected conservative in the lower tail; to be checked)",
                        "the same guarded search rule is applied to the lower-bound check (C9 states the guard in step 5 only)"],
    }
