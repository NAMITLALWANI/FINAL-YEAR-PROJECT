"""Exploratory, BENCHMARK-DERIVED evaluation of the offline replays that exist (T019). No network, no database. Writes results.json and LaTeX tables (new files only).

Datasets: smoke (50 cases, 23 blocks; not a probability sample) and the completed cases of the exploratory F4 draw. Labels are the provisional ORCID agreement of the benchmark
(held in memory only). Nothing here is independent verification, and nothing is pooled across datasets or with verified results.

  python scripts/analyze_free_evaluation.py --out-dir DIR --tex-dir DIR
"""
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from hammer_pilot import report_assembly as ra
from hammer_pilot import sizing_c9 as z
from hammer_pilot.metrics import clopper_pearson, zero_event_upper_bound

ROOT = BACKEND.parent / "research_data" / "lagos_and_v2"
PROT = BACKEND.parent.parent / "LAGOS_SOURCE" / "protected"
DATASETS = {
    "smoke": dict(seeds=ROOT / "smoke_v1" / "seeds.csv", cap=ROOT / "smoke_v1" / "captures", replay=ROOT / "smoke_v1" / "replay", gold=ROOT / "seed_v1" / "gold_identity_register.csv"),
    "exploratory": dict(seeds=ROOT / "eval_F4" / "exploratory" / "replay_input" / "seeds.csv", cap=ROOT / "eval_F4" / "exploratory" / "replay_input" / "captures",
                        replay=ROOT / "eval_F4" / "exploratory" / "replay", gold=PROT / "expl_F4" / "gold" / "gold_identity_register.csv"),
}
POLICIES = ("selective_policy_v2", "legacy_gates_plus_p3", "forced_top1")
CONDS = ("C0", "C1", "C1x")
OUTCOMES = ("auto", "manual", "unresolved", "empty_pool", "provider_failed", "no_score")


def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def ci(x, n):
    c = clopper_pearson(x, n)
    return None if c is None else [round(c[0], 4), round(c[1], 4)]


def rate(x, n):
    return {"x": x, "n": n, "rate": None if n == 0 else round(x / n, 4), "ci95": ci(x, n)}


def load(name):
    d = DATASETS[name]
    seeds = {r["case_id"]: r for r in rows(d["seeds"])}
    gold = {r["case_id"]: r for r in rows(d["gold"]) if r["case_id"] in seeds}
    mapped = ra.benchmark_mapping(d["cap"], {c: g["gold_orcid"] for c, g in gold.items()})
    preds = [r for r in rows(d["replay"] / "predictions.csv") if r["case_id"] in seeds]
    ret = [r for r in rows(d["replay"] / "retrieval.csv") if r["case_id"] in seeds]
    blocks = {c: s["source_block_id"] for c, s in seeds.items()}
    return seeds, mapped, preds, ret, blocks


def first_per_block(cases, blocks):
    seen, out = set(), []
    for c in sorted(cases):
        if blocks[c] not in seen:
            seen.add(blocks[c]); out.append(c)
    return out


def analyze(name):
    seeds, mapped, preds, ret, blocks = load(name)
    all_cases = sorted(seeds)
    scopes = {"all_cases": all_cases}
    if len({*blocks.values()}) < len(all_cases):
        scopes["one_case_per_block"] = first_per_block(all_cases, blocks)
    out = {"n_cases": len(all_cases), "n_blocks": len(set(blocks.values())), "strata": dict(Counter(s["sampling_stratum"] for s in seeds.values())), "scopes": {}}
    pool = {r["case_id"]: json.loads(r["ordered_candidate_ids"]) for r in ret if r["arm"] == "R2"}
    r0 = {r["case_id"]: (r["pool_status"], json.loads(r["ordered_candidate_ids"])) for r in ret if r["arm"] == "R0"}
    r2s = {r["case_id"]: r["pool_status"] for r in ret if r["arm"] == "R2"}
    for scope, ids in scopes.items():
        S = set(ids); n = len(ids)
        sc = {"n": n, "outcomes": {}, "selective": {}, "retrieval": {}, "signals": {}}
        for cond in CONDS:
            for pol in POLICIES:
                sel = [r for r in preds if r["case_id"] in S and r["condition"] == cond and r["policy"] == pol]
                oc = Counter(r["outcome"] for r in sel)
                sc["outcomes"][f"{cond}|{pol}"] = {o: oc.get(o, 0) for o in OUTCOMES}
                auto = [r for r in sel if r["outcome"] == "auto"]
                correct = sum(1 for r in auto if r["selected_author_id"] in mapped[r["case_id"]])
                sc["selective"][f"{cond}|{pol}"] = {"automatic_coverage": rate(len(auto), n), "benchmark_precision": rate(correct, len(auto)),
                                                   "zero_error_upper95": zero_event_upper_bound(len(auto)) if correct == len(auto) and auto else None}
        # retrieval (R2 primary pool; R0 descriptive), benchmark-derived
        def retr(poolmap):
            found = ranks = 0
            r1 = r5 = r10 = fnd = 0; mrr = 0.0
            for c in ids:
                p = poolmap.get(c, [])
                rk = next((i + 1 for i, a in enumerate(p) if a in mapped[c]), None)
                if rk is not None:
                    fnd += 1; mrr += 1 / rk
                    r1 += rk <= 1; r5 += rk <= 5; r10 += rk <= 10
            return {"mapped_in_pool": rate(fnd, n), "success@1": rate(r1, n), "success@5": rate(r5, n), "success@10": rate(r10, n),
                    "conditional_recall@1": rate(r1, fnd), "mrr_end_to_end": round(mrr / n, 4) if n else None}
        sc["retrieval"]["R2"] = retr(pool)
        sc["retrieval"]["R0"] = retr({c: r0[c][1] for c in ids})
        sc["retrieval"]["pool_status_R2"] = dict(Counter(r2s[c] for c in ids))
        sc["retrieval"]["pool_status_R0"] = dict(Counter(r0[c][0] for c in ids))
        sc["retrieval"]["pool_size_R2"] = {"mean": round(sum(len(pool.get(c, [])) for c in ids) / n, 2), "max": max(len(pool.get(c, [])) for c in ids)}
        # C1 signals and safeguards (selective policy)
        c1 = [r for r in preds if r["case_id"] in S and r["condition"] == "C1" and r["policy"] == "selective_policy_v2" and r["pool_status"] == "ok"]
        sc["signals"]["C1_top_candidate_signal_sets"] = dict(Counter(r["top_signal_set"] for r in c1))
        sc["signals"]["C1_institution_observed"] = rate(sum("institution_similarity" in r["top_signal_set"] for r in c1), len(c1))
        sc["signals"]["C1_temporal_observed"] = rate(sum("temporal_compatibility" in r["top_signal_set"] for r in c1), len(c1))
        sc["signals"]["C1_different_signal_sets_in_pool"] = rate(sum(r["different_signal_sets_in_pool"] == "True" for r in c1), len(c1))
        def f(x):
            return float(x) if x not in ("", None) else None
        fails = Counter()
        for r in c1:
            sig = len(json.loads(r["top_signal_set"]))
            fails["score_below_0.75"] += (f(r["top_score"]) or 0) < 0.75
            fails["fewer_than_2_signals"] += sig < 2
            fails["margin_below_0.15"] += (f(r["margin"]) is not None and f(r["second_score"]) is not None and f(r["margin"]) < 0.15)
            fails["dominance_below_1.35"] += (f(r["dominance"]) is not None and f(r["dominance"]) < 1.35)
        sc["signals"]["C1_gate_failures_non_exclusive"] = {"cases_with_candidates": len(c1), **dict(fails)}
        sc["signals"]["C1_top_score_median"] = sorted(f(r["top_score"]) or 0 for r in c1)[len(c1) // 2] if c1 else None
        sc["signals"]["C1_top_score_max"] = max((f(r["top_score"]) or 0 for r in c1), default=None)
        top1_provider = sum(1 for c in ids if pool.get(c) and pool[c][0] in mapped[c])
        sc["signals"]["provider_first_agrees_with_benchmark"] = rate(top1_provider, n)
        passed = [r for r in c1 if r["threshold_gates_passed"] == "True"]
        sc["signals"]["C1_threshold_gates_passed"] = len(passed)
        sc["signals"]["C1_blockers_among_gate_passers"] = dict(Counter(b for r in passed for b in json.loads(r["auto_blockers"])))
        out["scopes"][scope] = sc
    return out


def planning():
    pm = json.loads((ROOT / "eval_F4" / "pilot" / "pilot_manifest.json").read_text())
    frame = {h: n for h, n in pm["post_exclusion_frame_after_pilot"].items() if n > 0}
    floors = {"S": 0, "M": 0, "L": 0, "XL": 9}
    table = []
    for c in (0.05, 0.10, 0.20):
        pilot = {h: {"automatic": round(c * n), "cases": n} for h, n in (("S", 100), ("M", 100), ("L", 50))}
        for m in (16, 32, 100):
            r = z.size_sample(frame, floors, pilot, m_prime=m, beta=0.05, gamma=0.10, n_max=2500)
            table.append({"assumed_coverage": c, "m_prime": m, "N_jeffreys": r["primary_jeffreys"]["N"], "N_uniform": r["sensitivity_uniform_prior"]["N"],
                          "N_lower_bound": r["sensitivity_lower_bound"]["N"]})
    return {"status": "illustration: ASSUMED pilot outcomes (coverage c in every stratum, pilot 100/100/50), not data", "frame": frame, "floors": floors, "beta": 0.05, "gamma": 0.10, "n_max": 2500, "rows": table}


def pct(r):
    return "--" if r["rate"] is None else f"{100 * r['rate']:.0f}\\%"


def frac(r):
    return f"{r['x']}/{r['n']}"


def interval(r):
    return "--" if r["ci95"] is None else f"[{r['ci95'][0]:.2f}, {r['ci95'][1]:.2f}]"


def tex_outcomes(res):
    L = ["% generated by scripts/analyze_free_evaluation.py (T019); do not edit by hand", "\\begin{table*}[t]",
         "\\caption{Outcome categories of the offline replay under each condition and policy (benchmark-independent counts). Smoke: 50 cases from 23 blocks. Exploratory: 18 complete cases from 18 blocks. Auto = automatic, Man = manual review, Unres = unresolved, Empty = successful empty pool, Fail = provider failure, NoSc = no defined score.}",
         "\\label{tab:exp-outcomes}", "\\centering", "\\footnotesize", "\\begin{tabular}{@{}llrrrrrrrrrrrr@{}}", "\\toprule",
         " & & \\multicolumn{6}{c}{Smoke (50)} & \\multicolumn{6}{c}{Exploratory (18)} \\\\", "\\cmidrule(lr){3-8}\\cmidrule(lr){9-14}",
         "Cond. & Policy & Auto & Man & Unres & Empty & Fail & NoSc & Auto & Man & Unres & Empty & Fail & NoSc \\\\", "\\midrule"]
    short = {"selective_policy_v2": "selective", "legacy_gates_plus_p3": "gates+P3", "forced_top1": "forced top-1"}
    for cond in CONDS:
        for pol in POLICIES:
            cells = []
            for ds in ("smoke", "exploratory"):
                o = res[ds]["scopes"]["all_cases"]["outcomes"][f"{cond}|{pol}"]
                cells += [str(o[k]) for k in OUTCOMES]
            L.append(f"{cond} & {short[pol]} & " + " & ".join(cells) + " \\\\")
    L += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    return "\n".join(L) + "\n"


def tex_retrieval(res):
    L = ["% generated by scripts/analyze_free_evaluation.py (T019); do not edit by hand", "\\begin{table*}[t]",
         "\\caption{Benchmark-derived retrieval diagnostics (provisional ORCID agreement, not identity accuracy). The pool is the captured R2 pool; R0 is descriptive and shares its response with R2 whenever the requests are identical. Rank is the provider's order. Intervals are Clopper--Pearson and ignore clustering of cases within blocks.}",
         "\\label{tab:exp-retrieval}", "\\centering", "\\footnotesize", "\\begin{tabular}{@{}lrrrr@{}}", "\\toprule",
         " & \\multicolumn{2}{c}{Smoke (50)} & \\multicolumn{2}{c}{Explor.\\ (18)} \\\\", "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}", "Measure (R2 pool) & Count & 95\\% CI & Count & 95\\% CI \\\\", "\\midrule"]
    for key, lab in (("mapped_in_pool", "Expected ORCID in pool"), ("success@1", "Success@1 (end to end)"), ("success@5", "Success@5"), ("success@10", "Success@10")):
        a, b = (res[d]["scopes"]["all_cases"]["retrieval"]["R2"][key] for d in ("smoke", "exploratory"))
        L.append(f"{lab} & {frac(a)} & {interval(a)} & {frac(b)} & {interval(b)} \\\\")
    a, b = (res[d]["scopes"]["all_cases"]["retrieval"]["R2"]["conditional_recall@1"] for d in ("smoke", "exploratory"))
    L.append(f"Conditional Recall@1 & {frac(a)} & {interval(a)} & {frac(b)} & {interval(b)} \\\\")
    a, b = (res[d]["scopes"]["all_cases"]["retrieval"]["R0"]["mapped_in_pool"] for d in ("smoke", "exploratory"))
    L.append(f"R0: expected ORCID in pool & {frac(a)} & {interval(a)} & {frac(b)} & {interval(b)} \\\\")
    L += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    return "\n".join(L) + "\n"


def tex_selective(res):
    L = ["% generated by scripts/analyze_free_evaluation.py (T019); do not edit by hand", "\\begin{table*}[t]",
         "\\caption{Benchmark-derived selective results. Coverage is the share of cases assigned automatically; precision is the share of automatic assignments whose selected profile carries the benchmark ORCID (provisional, never independent verification). Forced top-1 never abstains, so its precision is a top-1 agreement rate. With zero errors in $n$ automatic assignments the one-sided 95\\% upper bound on the error rate is $1-0.05^{1/n}$.}",
         "\\label{tab:exp-selective}", "\\centering", "\\footnotesize", "\\begin{tabular}{@{}llrrrr@{}}", "\\toprule",
         "Dataset & Cond. / policy & Automatic & Coverage (95\\% CI) & Agree with benchmark & Precision (95\\% CI) \\\\", "\\midrule"]
    short = {"selective_policy_v2": "selective", "legacy_gates_plus_p3": "gates+P3", "forced_top1": "forced top-1"}
    for ds, lab, scope in (("smoke", "Smoke, 50 cases", "all_cases"), ("smoke", "Smoke, 23 blocks", "one_case_per_block"), ("exploratory", "Exploratory, 18", "all_cases")):
        for cond, pol in (("C1", "selective_policy_v2"), ("C1", "legacy_gates_plus_p3"), ("C1", "forced_top1"), ("C1x", "selective_policy_v2"), ("C1x", "legacy_gates_plus_p3")):
            s = res[ds]["scopes"][scope]["selective"][f"{cond}|{pol}"]
            cov, pr = s["automatic_coverage"], s["benchmark_precision"]
            prec = "undefined" if pr["n"] == 0 else f"{pct(pr)} {interval(pr)}"
            L.append(f"{lab} & {cond}, {short[pol]} & {cov['x']} & {pct(cov)} {interval(cov)} & {pr['x']} & {prec} \\\\")
        L.append("\\midrule")
    L[-1] = "\\bottomrule"
    L += ["\\end{tabular}", "\\end{table*}"]
    return "\n".join(L) + "\n"


def tex_planning(plan):
    L = ["% generated by scripts/analyze_free_evaluation.py (T019); do not edit by hand", "\\begin{table}[t]",
         "\\caption{Main-sample size $N$ needed for at least $m'$ automatic assignments with probability 0.95, by the stratified predictive rule, under \\emph{assumed} pilot outcomes (coverage $c$ in every stratum, pilot of 100, 100 and 50 cases; frame 7,938, 8,260, 1,123 and 9 blocks, XL a census). This is a planning illustration and not data.}",
         "\\label{tab:exp-planning}", "\\centering", "\\footnotesize", "\\begin{tabular}{@{}rrrrr@{}}", "\\toprule", "$c$ & $m'$ & $N$ (Jeffreys) & $N$ (uniform) & $N$ (lower bound) \\\\", "\\midrule"]
    for r in plan["rows"]:
        L.append(f"{r['assumed_coverage']:.2f} & {r['m_prime']} & {r['N_jeffreys'] if r['N_jeffreys'] else '$>$2500'} & {r['N_uniform'] if r['N_uniform'] else '$>$2500'} & {r['N_lower_bound'] if r['N_lower_bound'] else '$>$2500'} \\\\")
    L += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--tex-dir", type=Path, required=True)
    a = ap.parse_args()
    res = {name: analyze(name) for name in DATASETS}
    plan = planning()
    a.out_dir.mkdir(parents=True, exist_ok=False); a.tex_dir.mkdir(parents=True, exist_ok=True)
    with open(a.out_dir / "results.json", "x", encoding="utf-8") as f:
        f.write(json.dumps({"label_basis": "benchmark-derived (provisional ORCID agreement); NOT independently verified", "datasets": res, "planning": plan}, indent=1, sort_keys=True) + "\n")
    for fname, text in (("exp_outcomes.tex", tex_outcomes(res)), ("exp_retrieval.tex", tex_retrieval(res)), ("exp_selective.tex", tex_selective(res)), ("exp_planning.tex", tex_planning(plan))):
        with open(a.tex_dir / fname, "x", encoding="utf-8") as f:
            f.write(text)
    print(json.dumps({k: {s: v["scopes"][s]["selective"]["C1|selective_policy_v2"] for s in v["scopes"]} for k, v in res.items()}, indent=1)[:1800])


if __name__ == "__main__":
    main()
