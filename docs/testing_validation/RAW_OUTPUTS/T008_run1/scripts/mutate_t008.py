"""T008 mutation sanity check on hammer_pilot/dossier.py (run from backend/); the caller restores the file."""
import sys
f = "hammer_pilot/dossier.py"
s = open(f, encoding="utf-8").read()
MUTS = {
 "S1 candidate allow-list also copies the ORCID field": ('return {"display_name": _text(item.get("display_name")),', 'return {"orcid": item.get("orcid"), "display_name": _text(item.get("display_name")),'),
 "S2 designated paper not forced into the Stage A packet": ('chosen = [designated[0]] + others[: k - 1]', 'chosen = others[:k]'),
 "S3 candidates keep provider order": ('order = sorted(range(len(candidates)), key=lambda i: key(seed, "stage_b", case_id, ids[i]))', 'order = list(range(len(candidates)))'),
 "S4 Stage A cap K ignored": ('chosen = [designated[0]] + others[: k - 1]', 'chosen = [designated[0]] + others'),
 "S5 scan ignores forbidden keys": ('if FORBIDDEN_KEY_RE.search(str(item)):', 'if False:'),
 "S6 scan ignores ORCID-shaped strings": ('for name, rx in (("orcid_pattern", ORCID_RE), ("orcid_url", ORCID_HOST_RE),', 'for name, rx in (("orcid_url", ORCID_HOST_RE),'),
 "S7 hand-edit check always passes": ('return report.get("released") is True and report.get("packet_sha256") == sha256_text(canonical(packet))', 'return report.get("released") is True'),
 "S8 crosswalk written into the reviewer directory": ('with open(protected_dir / name, "x", encoding="utf-8") as f:', 'with open(reviewer_dir / name, "x", encoding="utf-8") as f:'),
 "S9 works cap ignored": ('key(seed, "works", opaque, w["doi"] or w["title"])))[:works_cap]', 'key(seed, "works", opaque, w["doi"] or w["title"])))'),
 "S10 opaque id built from the provider id": ('opaque = "K-" + key(seed, "candidate", case_id, ids[i])[:10]', 'opaque = "K-" + ids[i]'),
 "S11 release gate bypassed": ('    if not report["released"]:\n        raise LeakFound(report)', '    if False:\n        raise LeakFound(report)'),
 "S12 gold value scan disabled": ('if any(g in text for g in gold):', 'if False:'),
}
if sys.argv[1] == "--list":
    print("\n".join(MUTS)); sys.exit(0)
old, new = MUTS[sys.argv[1]]
assert s.count(old) == 1, (sys.argv[1], s.count(old))
open(f, "w", encoding="utf-8").write(s.replace(old, new, 1))
