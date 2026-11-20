"""T007 mutation sanity check on hammer_pilot/selector_c1c.py (run from backend/); the caller restores the file."""
import sys
f = "hammer_pilot/selector_c1c.py"
s = open(f, encoding="utf-8").read()
MUTS = {
 "R1 seed ignored in the ordering key": ('return hashlib.sha256("|".join([str(seed), role, *map(str, parts)]).encode("utf-8")).hexdigest()', 'return hashlib.sha256("|".join([role, *map(str, parts)]).encode("utf-8")).hexdigest()'),
 "R2 primary case is the largest hash instead of the smallest": ('groups = sorted(catalog[block]["case_groups"], key=lambda o: key(seed, "primary", block, o))', 'groups = sorted(catalog[block]["case_groups"], key=lambda o: key(seed, "primary", block, o), reverse=True)'),
 "R3 smoke exclusion ignored in the pilot frame": ('frame = eligible_frame(catalog, split=split, exclude_blocks=smoke_blocks)\n    drawn = _draw(frame["strata"], per_stratum, seed, "pilot")', 'frame = eligible_frame(catalog, split=split)\n    drawn = _draw(frame["strata"], per_stratum, seed, "pilot")'),
 "R4 pilot blocks not removed from the post-exclusion frame": ('post = eligible_frame(catalog, split=split, exclude_blocks=list(smoke_blocks) + pilot_blocks)', 'post = eligible_frame(catalog, split=split, exclude_blocks=list(smoke_blocks))'),
 "R5 ORCID written into the manifest case record": ('primary.append({"case_id": cid, "block_id": block,', 'primary.append({"orcid": groups[0], "case_id": cid, "block_id": block,'),
 "R6 person inclusion probability ignores the group count": ('_fraction(Fraction(n_h, big_n * g))', '_fraction(Fraction(n_h, big_n))'),
 "R7 main sample ignores the pilot exclusion": ('frame = eligible_frame(catalog, split=split, exclude_blocks=list(smoke_blocks) + list(pilot_blocks))\n    if set(floors)', 'frame = eligible_frame(catalog, split=split, exclude_blocks=list(smoke_blocks))\n    if set(floors)'),
 "R8 pilot and main share the ordering role": ('drawn = _draw(frame["strata"], per_stratum, seed, "main")', 'drawn = _draw(frame["strata"], per_stratum, seed, "pilot")'),
 "R9 audit order uses the case id instead of the hash": ('take = sorted(members, key=lambda c: key(seed, "audit", c))[: alloc[g]]', 'take = sorted(members)[: alloc[g]]'),
 "R10 audit allocation not proportional (equal split)": ('alloc = allocate(n_audit, validate_frame(sizes), {g: 0 for g in sizes})', 'alloc = {g: n_audit // len(sizes) + (1 if i < n_audit % len(sizes) else 0) for i, g in enumerate(sizes)}'),
 "R11 manifest hash not recomputed on verification": ('return manifest.get("manifest_sha256") == hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()', 'return "manifest_sha256" in manifest'),
 "R12 audit merging rule ignored": ('group_of = {s: (merge_rule or {}).get(s, s) for s in original}', 'group_of = {s: s for s in original}'),
}
if sys.argv[1] == "--list":
    print("\n".join(MUTS)); sys.exit(0)
old, new = MUTS[sys.argv[1]]
assert s.count(old) == 1, (sys.argv[1], s.count(old))
open(f, "w", encoding="utf-8").write(s.replace(old, new, 1))
