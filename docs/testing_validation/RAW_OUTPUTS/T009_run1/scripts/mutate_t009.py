"""T009 mutation sanity check on hammer_pilot/review_records.py (run from backend/); the caller restores the file."""
import sys
f = "hammer_pilot/review_records.py"
s = open(f, encoding="utf-8").read()
MUTS = {
 "U1 two-distinct-reviewers requirement removed": ('if len(reviewers) != 2 or len(a) != 2:', 'if False:'),
 "U2 adjudicator independence removed": ('if final["adjudicator_id"] in reviewers or final["adjudicator_id"] == builder_id or not final.get("adjudicator_id"):', 'if not final.get("adjudicator_id"):'),
 "U3 Stage B completeness removed": ('if cand_set and set(judged) != cand_set:', 'if False:'),
 "U4 chance agreement ignored in kappa": ('pe = sum((ca[c] / n) * (cb[c] / n) for c in cats)', 'pe = 0.0'),
 "U5 builder-as-reviewer check removed": ('if builder_id in reviewers:', 'if False:'),
 "U6 crosswalk not applied in the C7 conversion": ('judgments = {crosswalk[c]: j for c, j in final_label["candidate_judgments"].items()}', 'judgments = dict(final_label["candidate_judgments"])'),
 "U7 purity disagreement ignored": ('ra["status"] != rb["status"] or ra["group_purity"] != rb["group_purity"] or any(', 'ra["status"] != rb["status"] or any('),
 "U8 affordable cases ignores candidate time": ('math.floor(60 * h / (t_a + k * t_b))', 'math.floor(60 * h / t_a)'),
 "U9 ORCID encounters in Stage B ignored": ('cases = {r["case_id"] for r in list(stage_a) + list(stage_b) if _bool(r["orcid_encountered"])}', 'cases = {r["case_id"] for r in list(stage_a) if _bool(r["orcid_encountered"])}'),
 "U10 resolved adjudication may skip candidates": ('(cand_set and set(judgments) != cand_set and final["final_status"] == "resolved")', 'False'),
 "U11 degenerate kappa reported as perfect": ('kappa = None if math.isclose(pe, 1.0) else (po - pe) / (1 - pe)', 'kappa = (po - pe) / (1 - pe) if not math.isclose(pe, 1.0) else 1.0'),
}
if sys.argv[1] == "--list":
    print("\n".join(MUTS)); sys.exit(0)
old, new = MUTS[sys.argv[1]]
assert s.count(old) == 1, (sys.argv[1], s.count(old))
open(f, "w", encoding="utf-8").write(s.replace(old, new, 1))
