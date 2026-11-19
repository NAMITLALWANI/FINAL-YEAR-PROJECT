"""Exact binomial intervals and the pilot's retrieval and selective-resolution metrics."""
from __future__ import annotations

import math
from typing import Any, Iterable

ALPHA = 0.05


def _binom_cdf(k: int, n: int, p: float) -> float:
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 1.0 if k >= n else 0.0
    return min(1.0, sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(0, k + 1)))


def _bisect(f, lo: float = 0.0, hi: float = 1.0) -> float:
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def clopper_pearson(x: int, n: int, alpha: float = ALPHA) -> tuple[float, float] | None:
    """Two-sided exact (Clopper-Pearson) interval; None when n == 0."""
    if n <= 0:
        return None
    if not 0 <= x <= n:
        raise ValueError("x must be between 0 and n")
    lower = 0.0 if x == 0 else _bisect(lambda p: (1 - _binom_cdf(x - 1, n, p)) - alpha / 2)
    upper = 1.0 if x == n else _bisect(lambda p: alpha / 2 - _binom_cdf(x, n, p))
    return lower, upper


def zero_event_upper_bound(n: int, alpha: float = ALPHA) -> float | None:
    """One-sided exact upper bound on the rate after 0 events in n trials: 1 - alpha**(1/n)."""
    return None if n <= 0 else 1 - alpha ** (1 / n)


def rate(num: int, den: int) -> dict[str, Any]:
    ci = clopper_pearson(num, den)
    return {"numerator": num, "denominator": den, "value": (num / den) if den else None,
            "ci95_exact": [round(ci[0], 6), round(ci[1], 6)] if ci else None}


def first_mapped_rank(pool: list[str], mapped: set[str]) -> int | None:
    for i, cid in enumerate(pool, 1):
        if cid in mapped:
            return i
    return None


def retrieval_metrics(cases: list[dict[str, Any]], ks: Iterable[int] = (1, 5, 10)) -> dict[str, Any]:
    """cases: {"case_id", "mapped": set, "pools": {"R0": {"status","ids"}, "R2": {...}}} for resolved cases only.

    M = resolved cases with at least one mapped profile in the union of the captured pools.
    """
    ks = tuple(ks)
    resolved_n = len(cases)
    in_m = [c for c in cases if c["mapped"] & {i for arm in c["pools"].values() for i in arm["ids"]}]
    out: dict[str, Any] = {"resolved_cases": resolved_n, "catalog_coverage": rate(len(in_m), resolved_n), "arms": {}}
    ranks: dict[str, dict[str, int | None]] = {}
    for arm in ("R0", "R2"):
        arm_ranks = {c["case_id"]: first_mapped_rank(c["pools"][arm]["ids"], c["mapped"]) for c in in_m}
        ranks[arm] = arm_ranks
        sizes = [len(c["pools"][arm]["ids"]) for c in cases]
        statuses = [c["pools"][arm]["status"] for c in cases]
        out["arms"][arm] = {
            **{f"recall_at_{k}": rate(sum(1 for r in arm_ranks.values() if r is not None and r <= k), len(in_m)) for k in ks},
            "mrr": {"value": (sum(1 / r for r in arm_ranks.values() if r) / len(in_m)) if in_m else None, "denominator": len(in_m)},
            "pool_size_mean": (sum(sizes) / len(sizes)) if sizes else None,
            "pool_size_median": sorted(sizes)[len(sizes) // 2] if sizes else None,
            "empty_pools": rate(sum(1 for s in statuses if s == "empty"), resolved_n),
            "provider_failures": rate(sum(1 for s in statuses if s == "provider_failed"), resolved_n),
        }
    paired = {}
    for k in ks:
        r0 = {c: (ranks["R0"][c] is not None and ranks["R0"][c] <= k) for c in ranks["R0"]}
        r2 = {c: (ranks["R2"][c] is not None and ranks["R2"][c] <= k) for c in ranks["R2"]}
        paired[f"recall_at_{k}"] = {"both_hit": sum(1 for c in r0 if r0[c] and r2[c]), "r0_only": sum(1 for c in r0 if r0[c] and not r2[c]),
                                    "r2_only": sum(1 for c in r0 if r2[c] and not r0[c]), "neither": sum(1 for c in r0 if not r0[c] and not r2[c]), "n": len(r0)}
    shared = [c for c in cases if c["pools"]["R0"].get("sha") and c["pools"]["R0"].get("sha") == c["pools"]["R2"].get("sha")]
    out["response_provenance"] = {
        "cases_where_R0_and_R2_share_one_physical_response": len(shared), "cases": resolved_n,
        "distinct_physical_responses": len({a.get("sha") for c in cases for a in c["pools"].values() if a.get("sha")}),
        "note": "A shared response is one provider observation used for both logical arms; it is not two independent observations, "
                "so shared cases are tied by construction and carry no information about R0 vs R2."}
    paired["independent_comparison_cases"] = {"n": resolved_n - len(shared), "shared_response_cases_excluded": len(shared)}
    out["paired_r0_vs_r2_discordant"] = paired
    out["note"] = "Descriptive pilot counts; intervals are exact binomial; no significance claim."
    return out


STRUCTURAL_C0_NOTE = ("C0 supplies only the name signal. Policies that require >= 2 available signals (and P5 corroboration) cannot "
                      "assign automatically in C0: automatic coverage is zero BY DESIGN. This is not a measured safety or accuracy result.")


def selective_metrics(rows: list[dict[str, Any]], gold: dict[str, dict[str, Any]], condition: str, policy: str) -> dict[str, Any]:
    """rows: prediction rows for one condition+policy. gold[case] = {"status", "mapped": set}.

    Eligible = labelled resolved or unresolved cases (uncertain excluded and counted).
    """
    eligible = [r for r in rows if gold.get(r["case_id"], {}).get("status") in ("resolved", "unresolved")]
    n = len(eligible)
    excluded_uncertain = sum(1 for r in rows if gold.get(r["case_id"], {}).get("status") == "uncertain")
    counts = {o: sum(1 for r in eligible if r["outcome"] == o) for o in ("auto", "manual", "unresolved", "no_score", "provider_failed", "empty_pool")}
    result: dict[str, Any] = {"condition": condition, "policy": policy, "eligible_cases": n, "excluded_uncertain": excluded_uncertain, "outcome_counts": counts}
    if policy == "forced_top1":
        resolved = [r for r in eligible if gold[r["case_id"]]["status"] == "resolved"]
        correct = sum(1 for r in resolved if r["outcome"] == "auto" and r["selected_author_id"] in gold[r["case_id"]]["mapped"])
        result["forced_top1_correct_on_resolved"] = rate(correct, len(resolved))
        result["no_score"] = rate(counts["no_score"], n)
        result["provider_failed"] = rate(counts["provider_failed"], n)
        result["empty_pool"] = rate(counts["empty_pool"], n)
        result["note"] = "forced_top1 selects rank 1 whenever its score is non-null; in C0 it is name-only top-1."
        return result
    auto = [r for r in eligible if r["outcome"] == "auto"]
    correct = sum(1 for r in auto if gold[r["case_id"]]["status"] == "resolved" and r["selected_author_id"] in gold[r["case_id"]]["mapped"])
    incorrect = len(auto) - correct
    result.update({
        "automatic_coverage": rate(len(auto), n),
        "automatic_precision": rate(correct, len(auto)) if auto else {"numerator": 0, "denominator": 0, "value": None, "ci95_exact": None, "note": "no automatic assignments"},
        "selective_risk": rate(incorrect, len(auto)) if auto else {"numerator": 0, "denominator": 0, "value": None, "ci95_exact": None, "note": "no automatic assignments"},
        "incorrect_automatic": incorrect,
        "false_acceptances_on_unresolved_controls": sum(1 for r in auto if gold[r["case_id"]]["status"] == "unresolved"),
        "manual_review_rate": rate(counts["manual"], n),
        "unresolved_rate": rate(counts["unresolved"], n),
        "no_score": rate(counts["no_score"], n),
        "provider_failed": rate(counts["provider_failed"], n),
        "empty_pool": rate(counts["empty_pool"], n),
    })
    if auto and incorrect == 0:
        result["zero_error_one_sided_95_upper_bound"] = round(zero_event_upper_bound(len(auto)), 6)
    if condition == "C0":
        result["structural_note"] = STRUCTURAL_C0_NOTE
        result["automatic_coverage_zero_by_design"] = True
    return result
