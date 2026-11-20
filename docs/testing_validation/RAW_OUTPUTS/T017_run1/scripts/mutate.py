"""T015-T017 mutation sanity check: insert one deliberate defect at a time, require the module's tests to fail, restore byte-identically. Run from backend/."""
import hashlib, os, subprocess, sys
from pathlib import Path
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "DATABASE_URL": "sqlite+aiosqlite:///:memory:"}
M = [
 ("Y1", "hammer_pilot/freeze.py", 'hexdigest()[:8], 16)', 'hexdigest()[:7], 16)', "tests/test_freeze.py"),
 ("Y2", "hammer_pilot/freeze.py", 'OVERRIDE_PREFIXES = ("AUTHOR_", "ENABLE_AUTHOR_", "DEDUP_")', 'OVERRIDE_PREFIXES = ("AUTHOR_", "ENABLE_AUTHOR_")', "tests/test_freeze.py"),
 ("Y3", "hammer_pilot/freeze.py", "elif sha256_file(p) != want:", "elif False:", "tests/test_freeze.py"),
 ("Y4", "hammer_pilot/freeze.py", '"working_tree_dirty": bool(status.strip()),', '"working_tree_dirty": False,', "tests/test_freeze.py"),
 ("G1", "hammer_pilot/guarded_transport.py", "self.spent >= self.limit", "self.spent > self.limit * 5", "tests/test_guarded_transport.py"),
 ("G2", "hammer_pilot/guarded_transport.py", "        else:\n            self.consecutive_failures = 0", "        else:\n            pass", "tests/test_guarded_transport.py"),
 ("G3", "hammer_pilot/guarded_transport.py", "response.status_code >= 500", "response.status_code >= 400", "tests/test_guarded_transport.py"),
 ("G4", "hammer_pilot/guarded_transport.py", "self.consecutive_failures >= self.max_failures", "self.consecutive_failures > self.max_failures", "tests/test_guarded_transport.py"),
 ("R1", "hammer_pilot/report_assembly.py", "found.group(1) == gold", "found.group(1) != gold", "tests/test_report_assembly.py"),
 ("R2", "hammer_pilot/report_assembly.py", "if stratum[c] != info[\"stratum\"]:", "if False:", "tests/test_report_assembly.py"),
 ("R3", "hammer_pilot/report_assembly.py", '"is_primary": c.case_id in primary}', '"is_primary": True}', "tests/test_report_assembly.py"),
 ("R4", "hammer_pilot/report_assembly.py", "len(done) == len(auto)", "len(done) >= 0", "tests/test_report_assembly.py"),
 ("R5", "hammer_pilot/report_assembly.py", "if fields and c.case_id not in primary:", "if False:", "tests/test_report_assembly.py"),
 ("D1", "hammer_pilot/review_driver.py", "if c not in primary or outcome[c] == \"auto\"", "if c not in primary", "tests/test_review_driver.py"),
 ("D2", "hammer_pilot/review_driver.py", "if set(case_inputs) != set(flags):", "if False:", "tests/test_review_driver.py"),
 ("D3", "hammer_pilot/review_driver.py", "not author_id.startswith(\"A\") or not author_id[1:].isdigit()", "False", "tests/test_review_driver.py"),
 ("D4", "hammer_pilot/review_driver.py", "if cid and cid not in seen:", "if cid:", "tests/test_review_driver.py"),
 ("D5", "hammer_pilot/review_driver.py", "if e and e.get(\"body_file\") and e.get(\"status\") and e[\"status\"] < 400:", "if e and e.get(\"body_file\"):", "tests/test_review_driver.py"),
 ("D6", "hammer_pilot/review_driver.py", "if r[\"condition\"] == condition and r[\"policy\"] == policy and r[\"case_id\"] in primary", "if r[\"case_id\"] in primary", "tests/test_review_driver.py"),
]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ok = 0
for mid, f, old, new, t in M:
    src = Path(f); orig = src.read_text(); h0 = sha(f)
    assert orig.count(old) == 1, f"{mid}: pattern count {orig.count(old)}"
    src.write_text(orig.replace(old, new))
    try:
        r = subprocess.run([".venv/bin/python", "-m", "pytest", t, "-p", "no:cacheprovider", "-q", "--no-header", "-x"], env=ENV, capture_output=True, text=True, timeout=300)
    finally:
        src.write_text(orig)
    assert sha(f) == h0
    detected = r.returncode != 0
    ok += detected
    print(f"{mid} {f} -> {'DETECTED' if detected else 'SURVIVED'}")
print(f"{ok} of {len(M)} mutants detected; all files restored byte-identically")
