"""T006 mutation sanity check: apply one deliberate defect to hammer_pilot/sizing_c9.py (run from backend/); the caller restores the file."""
import sys
f = "hammer_pilot/sizing_c9.py"
s = open(f, encoding="utf-8").read()
MUTS = {
 "Q1 search guard removed (smallest N that first meets the condition)": ('    guarded = None                     # smallest N whose whole suffix [N, n_max] satisfies the condition (None if N_max itself fails)\n    for n in reversed(grid):\n        if not ok[n]:\n            break\n        guarded = n\n', '    guarded = first\n'),
 "Q2 uniform sensitivity prior replaced by Jeffreys": ('"uniform": (1.0, 1.0)', '"uniform": (0.5, 0.5)'),
 "Q3 Bonferroni correction removed": ('level_tail = gamma / n_strata', 'level_tail = gamma'),
 "Q4 stratum without pilot data given a non-zero lower limit": ('out[h] = {"lower": 0.0, "no_pilot_data": True, "tail": level_tail}', 'out[h] = {"lower": 0.1, "no_pilot_data": True, "tail": level_tail}'),
 "Q5 floors no longer capped at the frame size (no census)": ('eff = {h: min(floors[h], frame[h]) for h in strata}', 'eff = {h: floors[h] for h in strata}'),
 "Q6 largest-remainder leftover dropped": ('allocation.update({h: floor_part[h] + (1 if i < leftover else 0) for i, h in enumerate(order)})', 'allocation.update({h: floor_part[h] for i, h in enumerate(order)})'),
 "Q7 tail probability off by one": ('return float(pmf[m_prime:].sum()) if m_prime < len(pmf) else 0.0', 'return float(pmf[m_prime + 1:].sum()) if m_prime < len(pmf) else 0.0'),
 "Q8 convolution skips the last stratum": ('    for p in pmfs:\n        out = np.convolve(out, p)', '    for p in list(pmfs)[:-1]:\n        out = np.convolve(out, p)'),
 "Q9 N_max may exceed the frame": ('    if n_max > sum(frame.values()):\n        raise SizingError', '    if False:\n        raise SizingError'),
 "Q10 an infeasible N counted as satisfying the condition": ('ok = {n: (prob[n] is not None and prob[n] >= target) for n in grid}', 'ok = {n: (prob[n] is None or prob[n] >= target) for n in grid}'),
 "Q11 primary search uses beta instead of 1 - beta": ('result = search(fn, _grid_start(frame, floors, m_prime), n_max, 1 - beta)\n    result.update({"method": "stratified beta-binomial', 'result = search(fn, _grid_start(frame, floors, m_prime), n_max, beta)\n    result.update({"method": "stratified beta-binomial'),
 "Q12 log-gamma difference restored for the pmf start (precision regression)": ('log0 = float(np.sum(np.log(beta + k) - np.log(alpha + beta + k)))', 'log0 = (math.lgamma(alpha) + math.lgamma(n + beta) - math.lgamma(alpha + n + beta)) - (math.lgamma(alpha) + math.lgamma(beta) - math.lgamma(alpha + beta))'),
 "Q13 posterior ignores the prior in alpha": ('"alpha": a0 + a,', '"alpha": a,'),
 "Q14 floor binding ignored": ('newly.update({h: eff[h] for h in unbound if h not in newly and share[h] < eff[h]})', 'newly.update({})'),
 "Q15 infeasible floors not rejected": ('    if sum(eff.values()) > total:\n        raise AllocationInfeasible', '    if False:\n        raise AllocationInfeasible'),
}
if sys.argv[1] == "--list":
    print("\n".join(MUTS))
    sys.exit(0)
old, new = MUTS[sys.argv[1]]
assert s.count(old) == 1, (sys.argv[1], s.count(old))
open(f, "w", encoding="utf-8").write(s.replace(old, new, 1))
