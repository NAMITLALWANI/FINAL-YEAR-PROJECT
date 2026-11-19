# Pilot Case Selection Protocol

**Status:** Draft for owner review; no pilot identities or controls selected.  
**Approved size:** 10 resolved identities and 5 unresolved controls. The pilot is workflow-only.

## Sampling frame

Before selection, document the eligible source population, time window, query/context source, inclusion rules, and frame preparer. Those choices are not settled in approved documents; obtain owner review before constructing/sampling the frame. Never create a frame from resolver output, candidate lists, scores, confidence, or observed system success.

## Resolved identities

Select ten cases without inspecting HAMMER or candidate-source predictions. Eligibility requires independent evidence that can support one intended person under the Stage A protocol. Evidence diversity may be considered only if the owner approves characteristics; there are no approved strata or quotas. Record selection reasons before candidate generation.

## Unresolved controls

Select five query/context cases independently of system behavior where the intended person is not uniquely established under the approved external evidence process. An unresolved control does not imply nonexistence or absence from a provider. An empty/difficult candidate search cannot establish an unresolved label. The external search boundary and stopping rule are open and must be approved before selection.

If Stage A adjudicates a proposed control as `uncertain`, do not relabel or replace it silently. The owner must decide whether it counts toward five or whether a documented replacement is allowed.

## Identity independence and leakage

- Assign one opaque case ID and one identity-group key per underlying person/control group.
- A person, alias set, spelling variant, or repeated query may occur in only one pilot case. Merge or exclude duplicates before selection freezes.
- Detect and record shared decisive DOI/work evidence that could let one case reveal another.
- No Stage B candidate ID, API rank, HAMMER score, resolver decision, or candidate profile may establish, select, exclude, or replace a Stage A case.
- V3/Day 5 artifacts are exposed history. Their identities' eligibility for a workflow-only pilot is unspecified; decide this without inspecting predictions. Do not access prediction files to resolve the question.

## Selection record

For included and excluded frame items, record opaque case ID, frame/version reference, selection date, eligibility, evidence availability, identity-group/deduplication check, inclusion/exclusion reason, and independent provenance. Keep identifiers and restricted material in an owner-approved secure location, not this Git document. Freeze the selection record before candidate capture. Do not populate it in this task.

## Open decisions before selection

1. Eligible population, time window, context fields, and sampling frame.
2. Desired diversity characteristics, if any; no quotas are approved.
3. External search scope/stopping rule for unresolved controls.
4. Treatment of uncertain outcomes and any replacement process.
5. Eligibility of identities already exposed in V3/Day 5 or other project artifacts.
6. Selection ledger format/location and access controls.
