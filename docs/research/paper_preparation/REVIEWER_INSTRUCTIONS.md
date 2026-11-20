# Reviewer instructions (Decision B; to be given to each independent reviewer)

**Status:** ready to use; no reviewer has been recruited, named or contacted. These instructions contain nothing about how any system performed.

## Your task
For each case you receive two kinds of packet. Judge only from the packet and from sources you search yourself, **excluding any ORCID identifier** (see rule 3).

**Stage A (identity).** You see a printed author name and a set of publications that a dataset groups under one person. Decide:
1. `status`: `resolved` (you can identify one definite person), `unresolved` (no single intended person exists, for example the papers belong to several people and none is the one meant), `uncertain` (you could not decide with reasonable effort), `unverifiable` (the evidence needed does not exist).
2. `group_purity`: `pure` (all shown publications belong to one person), `impure` (they belong to more than one), or `unresolved`.
3. `confidence` 1 to 5, a short `rationale`, the `evidence_refs` you relied on (URLs, DOIs, institutional pages) and the `searches` you ran.

**Stage B (candidates).** You see a list of candidate author profiles under opaque identifiers, in an arbitrary order. For **every** candidate record `same` (the same person as in Stage A), `different`, or `cannot_tell`, with a confidence and evidence references. Judge every candidate; a pool may not be called "no matching candidate" until each one has been judged.

## Rules
1. Work independently. Do not discuss a case with the other reviewer or the adjudicator before both of you have submitted.
2. The order of candidates carries no meaning. Do not infer anything from it.
3. **Do not use an ORCID as evidence.** If you meet an ORCID anyway (for example on a search result), set `orcid_encountered` to `true` for that row; this is recorded and reported, not penalised.
4. Do not look for, and do not ask for, any information about how a case was selected or what any automated system decided. If you think you can tell, say so in the rationale of that row.
5. Record the minutes you spent on each Stage A case and each Stage B candidate; the totals set the size of the audit.
6. `cannot_tell` and `uncertain` are legitimate answers. Never guess to avoid them.

## Forms
CSV templates are produced by `review_records.write_templates` (Stage A, Stage B and adjudication). Fields:
Stage A `case_id, reviewer_id, status, group_purity, confidence, rationale, evidence_refs, searches, orcid_encountered, minutes`;
Stage B `case_id, reviewer_id, candidate, judgment, confidence, evidence_refs, orcid_encountered, minutes`.

## Adjudicator (a third person, neither a reviewer nor the packet builder)
Only for cases where the two reviewers disagree. Record `final_status`, `final_group_purity`, the final judgment for each candidate (`opaque_id:judgment;...`) and a rationale. Reviewer rows are never overwritten.
