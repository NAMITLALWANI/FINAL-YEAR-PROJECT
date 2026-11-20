"""T012 mutation sanity check on hammer_pilot/seeds_from_manifest.py (run from backend/); the caller restores the file."""
import sys
f = "hammer_pilot/seeds_from_manifest.py"
s = open(f, encoding="utf-8").read()
MUTS = {
 "V1 designated citation is the largest hash": ('designated = min(pool, key=lambda k: _key(seed, "cite", orcid, k))', 'designated = max(pool, key=lambda k: _key(seed, "cite", orcid, k))'),
 "V2 ORCID leaked into the seeds file": ('seeds.append({"case_id": cid, "query_text": cite["author_name"],', 'seeds.append({"case_id": cid, "gold_orcid": orcid, "query_text": cite["author_name"],'),
 "V3 non-designated DOIs registered as both": ('dois.append({"case_id": cid, "doi": doi, "purpose": "gold_evidence", "registered_by": "dataset_orcid_link", "justification_if_both": ""})', 'dois.append({"case_id": cid, "doi": doi, "purpose": "both", "registered_by": "dataset_orcid_link", "justification_if_both": ""})'),
 "V4 complete-block check removed": ('if len(rows) != catalog[block]["raw_rows"]:', 'if False:'),
 "V5 identity-map block mismatch ignored": ('if ident is None or ident["block"] != block:', 'if ident is None:'),
 "V6 manifest hash not bound in the freeze file": ('"manifest_sha256": manifest["manifest_sha256"], "role"', '"manifest_sha256": "", "role"'),
 "V7 affiliation-less citations allowed to be designated first": ('pool = with_aff or cites', 'pool = cites'),
}
if sys.argv[1] == "--list":
    print("\n".join(MUTS)); sys.exit(0)
old, new = MUTS[sys.argv[1]]
assert s.count(old) == 1, (sys.argv[1], s.count(old))
open(f, "w", encoding="utf-8").write(s.replace(old, new, 1))
