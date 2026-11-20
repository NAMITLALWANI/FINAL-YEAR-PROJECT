"""T005 mutation sanity check: apply one deliberate defect to hammer_pilot/metrics_c7.py (run from backend/); the caller restores the file."""
import sys
f = "hammer_pilot/metrics_c7.py"
s = open(f, encoding="utf-8").read()
MUTS = {
 "P1 pure unresolved group treated as consistent again": ('    if case.label_state == "unresolved":\n        return "indeterminate", [], "label_unresolved_pure_group"', '    if False:\n        return "indeterminate", [], "label_unresolved_pure_group"'),
 "P2 unresolved group purity treated as consistent": ('    if case.group_purity == "unresolved":\n        return "indeterminate", [], "purity_unresolved"', '    if False:\n        return "indeterminate", [], "purity_unresolved"'),
 "P3 uncertain case with an impure group pulled into the definite denominator": ('    if case.label_state in ("uncertain", "unverifiable"):\n        return "indeterminate", [], f"label_{case.label_state}"', '    if False:\n        return "indeterminate", [], f"label_{case.label_state}"'),
 "P4 impure groups outside the definite denominator not reported": ('impure_by_label["uncertain"] + impure_by_label["unverifiable"]', '0'),
 "P5 impure-group rate denominator includes unresolved purity": ('_rate(purity["impure"], purity["pure"] + purity["impure"])', '_rate(purity["impure"], purity["pure"] + purity["impure"] + purity["unresolved"])'),
 "P6 conditional denominator includes cannot-tell-only cases": ('mapped = [(a, b) for a, b in used if a]', 'mapped = [(a or b, b) for a, b in used if b]'),
 "P7 judgment categories swapped": ('"cannot_tell_only" if either else "verified_no_match"', '"verified_no_match" if either else "cannot_tell_only"'),
 "P8 overall retrieval adjusted by verified label": ('    mapped = lambda c: first_rank(c) is not None\n', '    mapped = lambda c: first_rank(c) is not None and c.label_state not in ("uncertain", "unverifiable")\n'),
 "P9 cannot_tell accepted again as a purity state": ('PURITY = ("pure", "impure", "unresolved")', 'PURITY = ("pure", "impure", "unresolved", "cannot_tell")'),
 "P10 uncertainty bracket loses indeterminate cases": ('"all_wrong": {"errors": errors + indeterminate', '"all_wrong": {"errors": errors'),
}
if sys.argv[1] == "--list":
    print("\n".join(MUTS))
    sys.exit(0)
old, new = MUTS[sys.argv[1]]
assert s.count(old) == 1, (sys.argv[1], s.count(old))
open(f, "w", encoding="utf-8").write(s.replace(old, new, 1))
