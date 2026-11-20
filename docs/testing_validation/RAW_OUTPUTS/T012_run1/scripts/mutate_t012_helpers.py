"""T012 mutation sanity check on hammer_pilot/run_helpers.py (run from backend/); the caller restores the file."""
import sys
f = "hammer_pilot/run_helpers.py"
s = open(f, encoding="utf-8").read()
MUTS = {
 "X1 counts ignore the condition and policy": ('if r["condition"] == condition and r["policy"] == policy]', 'if True]'),
 "X2 audit frame takes every seeded case, secondary included": ('primary = [c["case_id"] for c in manifest["cases"]]', 'primary = list(strata)'),
 "X3 seeded case without a prediction is not refused": ('if missing:\n        raise HelperError(f"{len(missing)} seeded case(s) have no prediction row")', 'if False:\n        raise HelperError("")'),
 "X4 duplicate prediction rows not refused": ('if len(out) != len(rows):', 'if False:'),
 "X5 automatic counted by any outcome": ('d["automatic"] += outcomes[cid] == "auto"', 'd["automatic"] += outcomes[cid] != "provider_failed"'),
}
if sys.argv[1] == "--list":
    print("\n".join(MUTS)); sys.exit(0)
old, new = MUTS[sys.argv[1]]
assert s.count(old) == 1, (sys.argv[1], s.count(old))
open(f, "w", encoding="utf-8").write(s.replace(old, new, 1))
