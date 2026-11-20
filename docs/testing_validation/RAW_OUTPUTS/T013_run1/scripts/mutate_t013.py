"""T013 mutation sanity check on hammer_pilot/paper_tables.py (run from backend/); the caller restores the file."""
import sys
f = "hammer_pilot/paper_tables.py"
s = open(f, encoding="utf-8").read()
MUTS = {
 "W1 unspecified parameters no longer block final tables": ('if unspecified and not draft:', 'if False:'),
 "W2 verified table shows rates even when verification is incomplete": ('if not sv["scoring"]["verification_complete"]:', 'if False:'),
 "W3 underscores not escaped": ('("_", r"\\_"), ', ''),
 "W4 pooled interval always shown as withheld": ('    if p.get("interval"):\n        return base + interval(p["interval"])', '    if False:\n        return base + interval(p["interval"])'),
 "W5 draft marker removed": ('cap = esc(caption) + (r" \\textbf{DRAFT: parameters not yet frozen.}" if draft else "")', 'cap = esc(caption)'),
 "W6 audit table drops the not-a-correction-factor statement": ('It describes this frame only and is not a correction factor.', 'It describes this frame only.'),
 "W7 benchmark retrieval caption loses its not-verified label": ('(ORCID agreement, not independently verified)', '(ORCID agreement)'),
 "W8 accounting total column wrong": ('[str(acc["outcome_counts"][o])] for o in acc["outcome_counts"]]', '[str(acc["n_primary"])] for o in acc["outcome_counts"]]'),
}
if sys.argv[1] == "--list":
    print("\n".join(MUTS)); sys.exit(0)
old, new = MUTS[sys.argv[1]]
assert s.count(old) == 1, (sys.argv[1], s.count(old))
open(f, "w", encoding="utf-8").write(s.replace(old, new, 1))
