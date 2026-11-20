"""T004 mutation sanity check: apply one deliberate defect to hammer_pilot/metrics_c7.py (run from backend/); the caller restores the file."""
import sys
f = "hammer_pilot/metrics_c7.py"
s = open(f, encoding="utf-8").read()
MUTS = {
 "N1 impure group no longer a contradiction": ('    if case.group_purity == "impure":\n        reasons.append("impure_group")', '    if False:\n        reasons.append("impure_group")'),
 "N2 pure unresolved group counted as a contradiction": ('    return "consistent", [], None\n\n\ndef audit_label_error', '    return ("contradicted", ["impure_group"], None) if case.label_state == "unresolved" else ("consistent", [], None)\n\n\ndef audit_label_error'),
 "N3 numerator counts reasons, not cases": ('errors, consistent, indeterminate = n["contradicted"], n["consistent"], n["indeterminate"]', 'errors, consistent, indeterminate = sum(reason_counts.values()), n["consistent"], n["indeterminate"]'),
 "N4 cannot-tell on a mapped candidate counted as an error": ('if any(j.get(i) == "different" for i in case.pool_ids if i in case.mapped_ids):', 'if any(j.get(i) in ("different", "cannot_tell") for i in case.pool_ids if i in case.mapped_ids):'),
 "N5 HAMMER abstentions removed from verified retrieval": ('elif c.label_state == "unresolved":\n            counts["ground_truth_unresolved"] += 1', 'elif c.label_state == "unresolved" or c.outcome in ("manual", "unresolved", "no_score"):\n            counts["ground_truth_unresolved"] += 1'),
 "N6 ground-truth unresolved no longer excluded": ('elif c.label_state == "unresolved":\n            counts["ground_truth_unresolved"] += 1', 'elif False:\n            counts["ground_truth_unresolved"] += 1'),
 "N7 no-matching-candidate claimed without every candidate judged": ('if case.pool_judgments is not None and set(case.pool_judgments) == set(case.pool_ids) and all(j == "different" for j in case.pool_judgments.values()):', 'if case.pool_judgments is not None and not any(j == "same" for j in case.pool_judgments.values()):'),
 "N8 cannot-verify automatic case reported as Verified": ('if case.outcome == "auto" and score_automatic(case)[0] == UNCERTAIN:', 'if False:'),
 "N9 replay builder takes the R0 pool": ('if r["arm"] == "R2"}', 'if r["arm"] == "R0"}'),
 "N10 audit consistency claimed without every candidate judged": ('if case.label_state == "resolved" and case.pool_ids and set(j) != set(case.pool_ids):', 'if False:'),
 "N11 verified miss claimed without every candidate judged": ('elif c.pool_ids and (c.pool_judgments is None or set(c.pool_judgments) != set(c.pool_ids)):', 'elif False:'),
}
if sys.argv[1] == "--list":
    print("\n".join(MUTS))
    sys.exit(0)
old, new = MUTS[sys.argv[1]]
assert s.count(old) == 1, (sys.argv[1], s.count(old))
open(f, "w", encoding="utf-8").write(s.replace(old, new, 1))
