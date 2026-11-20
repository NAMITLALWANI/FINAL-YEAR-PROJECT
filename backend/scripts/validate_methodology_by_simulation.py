"""Methodology validation by simulation (synthetic populations only; no data, no provider, no real parameters).

1. Estimators: on a seeded synthetic finite population (four strata, block random effects, case-eligible group counts correlated with the outcome), repeat the
   C1c/C3 sampling design many times and check, with the C7 module's own estimators, that
   - the E1 pooled estimate is unbiased for the block-level truth and the E2 pooled estimate for the person-level truth,
   - E1 weights are NOT unbiased for the person-level truth (negative control: the test can detect wrong weights),
   - per-stratum Clopper-Pearson intervals and the pooled stratified-bootstrap interval reach at least their nominal coverage (conservative, as stated in C5).
2. Sizing calibration: draw true coverage per stratum, a pilot, run the stratified predictive sizing, then the main sample, and check that the frequency of reaching
   m' automatic assignments is at least 1 - beta, while the plug-in rule N = ceil(m'/c_hat) is not.
All sizes, seeds and thresholds below are TEST values, not proposals for the real study."""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.dont_write_bytecode = True

from hammer_pilot import metrics_c7 as m
from hammer_pilot import sizing_c9 as z

STRATA = ("S", "M", "L", "XL")
FRAME = {"S": 800, "M": 600, "L": 80, "XL": 10}
SAMPLE = {"S": 40, "M": 30, "L": 20, "XL": 10}               # XL is a census
MEAN = {"S": 0.10, "M": 0.18, "L": 0.30, "XL": 0.40}


def build_population(seed: int = 1):
    """Blocks with g case-eligible groups; the block rate rises with g so that the block-level and person-level truths differ."""
    rng = np.random.default_rng(seed)
    pop = {}
    for h in STRATA:
        blocks = []
        for _ in range(FRAME[h]):
            g = int(rng.integers(1, 7))
            p = min(0.95, max(0.01, rng.beta(2, 2 / MEAN[h] * 0.6 + 1e-9) * 0.9 + 0.04 * (g - 1)))
            blocks.append(rng.random(g) < p)                     # fixed realised outcomes of the g persons
        pop[h] = blocks
    truth = {"E1": sum(sum(sum(b) / len(b) for b in pop[h]) for h in STRATA) / sum(FRAME.values()),
             "E2": sum(sum(sum(b) for b in pop[h]) for h in STRATA) / sum(sum(len(b) for b in pop[h]) for h in STRATA),
             "E1_stratum": {h: sum(sum(b) / len(b) for b in pop[h]) / FRAME[h] for h in STRATA}}
    return pop, truth


def draw_cases(pop, rng):
    cases = []
    for h in STRATA:
        for bi in rng.choice(FRAME[h], size=SAMPLE[h], replace=False):
            block = pop[h][bi]
            y = bool(block[rng.integers(len(block))])
            cases.append(m.Case(case_id=f"{h}{bi}", block_id=f"{h}{bi}", stratum=h, outcome="auto" if y else "manual", pool_ids=("a",), selected_id="a" if y else "",
                                group_count=len(block)))
    return cases


def simulate_estimators(reps: int, seed: int, resamples: int) -> dict:
    pop, truth = build_population(seed=1)
    rng = np.random.default_rng(seed)
    settings = m.InferenceSettings(bootstrap_resamples=resamples, bootstrap_min_stratum_n=10)
    q = m.label_free_quantities()[0]                                                    # automatic rate over all N primary cases
    e1, e2, e1_vs_e2, cp_hit, cp_n, boot_hit, boot_n = [], [], [], {h: 0 for h in STRATA}, {h: 0 for h in STRATA}, 0, 0
    for r in range(reps):
        cases = draw_cases(pop, rng)
        _, _, info = m._validate_sample(cases, FRAME)
        est = m.estimate(q, cases, info, settings, seed=seed * 100000 + r)
        e1.append(est["pooled"]["E1"]["point"])
        e2.append(est["pooled"]["E2"]["point"])
        for h in STRATA:
            iv = est["per_stratum"][h]["interval"]
            if iv:
                cp_n[h] += 1
                cp_hit[h] += iv[0] <= truth["E1_stratum"][h] <= iv[1]
        iv = est["pooled"]["E1"]["interval"]
        if iv:
            boot_n += 1
            boot_hit += iv[0] <= truth["E1"] <= iv[1]
    se = lambda x: float(np.std(x, ddof=1) / math.sqrt(len(x)))
    return {"reps": reps, "truth": {"E1": truth["E1"], "E2": truth["E2"]},
            "E1_mean_estimate": float(np.mean(e1)), "E1_bias_in_se": (float(np.mean(e1)) - truth["E1"]) / se(e1),
            "E2_mean_estimate": float(np.mean(e2)), "E2_bias_in_se": (float(np.mean(e2)) - truth["E2"]) / se(e2),
            "negative_control_E1_weights_for_E2_truth_bias_in_se": (float(np.mean(e1)) - truth["E2"]) / se(e1),
            "cp_coverage_by_stratum": {h: (cp_hit[h] / cp_n[h]) if cp_n[h] else None for h in STRATA},
            "pooled_bootstrap_E1_coverage": (boot_hit / boot_n) if boot_n else None, "bootstrap_intervals": boot_n}


def simulate_sizing(reps: int, seed: int, generator: str, m_prime: int = 8, beta: float = 0.10, gamma: float = 0.10, n_max: int = 700) -> dict:
    """generator "jeffreys": true coverage drawn from the Jeffreys prior itself (exact Bayesian calibration expected);
    generator "beta_3_20": a realistic, narrower distribution than the prior (calibration is not guaranteed; reported as a limitation)."""
    draw = {"jeffreys": lambda rng: rng.beta(0.5, 0.5), "beta_3_20": lambda rng: rng.beta(3, 20)}[generator]
    frame, floors = {"S": 3000, "M": 3000, "L": 400, "XL": 20}, {h: 0 for h in STRATA}
    pilot_n = {"S": 40, "M": 40, "L": 30, "XL": 10}
    rng = np.random.default_rng(seed)
    out = {"pred": [0, 0, 0], "lb": [0, 0, 0], "plug": [0, 0]}                 # [found, hits, not_found] ; plug: [used, hits]
    sizes = []
    for _ in range(reps):
        c = {h: draw(rng) for h in STRATA}
        pilot = {h: {"automatic": int(rng.binomial(pilot_n[h], c[h])), "cases": pilot_n[h]} for h in STRATA}
        for key, res in (("pred", z.size_predictive(frame, floors, pilot, m_prime=m_prime, beta=beta, n_max=n_max, prior="jeffreys")),
                         ("lb", z.size_lower_bound(frame, floors, pilot, m_prime=m_prime, beta=beta, gamma=gamma, n_max=n_max))):
            if res["N"] is None:
                out[key][2] += 1
            else:
                out[key][0] += 1
                out[key][1] += sum(int(rng.binomial(n, c[h])) for h, n in res["allocation_at_N"].items()) >= m_prime
                if key == "pred":
                    sizes.append(res["N"])
        total = sum(frame.values())
        c_hat = sum(frame[h] / total * pilot[h]["automatic"] / pilot_n[h] for h in STRATA)
        if c_hat > 0 and math.ceil(m_prime / c_hat) <= n_max:
            alloc = z.allocate(max(math.ceil(m_prime / c_hat), 1), frame, floors)
            out["plug"][0] += 1
            out["plug"][1] += sum(int(rng.binomial(n, c[h])) for h, n in alloc.items()) >= m_prime
    rate = lambda hit, n: (hit / n) if n else None
    return {"generator": generator, "reps": reps, "m_prime": m_prime, "target_probability": 1 - beta, "gamma": gamma,
            "predictive_found": out["pred"][0], "predictive_not_found": out["pred"][2], "predictive_success_frequency": rate(out["pred"][1], out["pred"][0]),
            "predictive_success_se": math.sqrt(max(out["pred"][1] / max(out["pred"][0], 1) * (1 - out["pred"][1] / max(out["pred"][0], 1)), 0) / max(out["pred"][0], 1)),
            "median_N_predictive": float(np.median(sizes)) if sizes else None,
            "lower_bound_found": out["lb"][0], "lower_bound_not_found": out["lb"][2], "lower_bound_success_frequency": rate(out["lb"][1], out["lb"][0]),
            "plug_in_rule_used": out["plug"][0], "plug_in_success_frequency": rate(out["plug"][1], out["plug"][0])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reps-estimators", type=int, required=True)
    parser.add_argument("--reps-sizing", type=int, required=True)
    parser.add_argument("--bootstrap", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    out = {"estimators": simulate_estimators(args.reps_estimators, args.seed, args.bootstrap),
           "sizing_prior_matched": simulate_sizing(args.reps_sizing, args.seed, "jeffreys"), "sizing_realistic_mismatch": simulate_sizing(args.reps_sizing, args.seed, "beta_3_20")}
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
