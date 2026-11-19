# Pilot Stage A Annotation Protocol

**Status:** Draft for owner review; no cases selected, evidence gathered, or labels recorded.  
**Scope:** Approved workflow pilot of 10 resolved identities and 5 unresolved controls. Stage A establishes intended-person labels independently before candidate capture.  
**Purpose:** Assess evidence availability, rubric clarity, reviewer agreement, and annotation workload. This is not a performance evaluation and cannot support author-resolution accuracy claims.

## Unit and outcomes

The unit is one independently sampled identity or unresolved control, represented by an opaque pilot case ID. A query string, provider profile, or candidate ID is not identity truth. Keep one underlying person in one case; aliases and variants are not separate identities.

- **`resolved`** — external evidence supports one intended person and reviewers can assign a stable project-local person key. An external identifier is supporting evidence, not the definition of truth.
- **`unresolved`** — the query/context does not support one uniquely intended person after the approved external search procedure. This does not imply the person does not exist or lacks a provider profile.
- **`uncertain`** — evidence is insufficient, contradictory, or cannot safely distinguish one intended person. Do not force an uncertain case into resolved to meet the pilot count.

The required 10 resolved / 5 unresolved composition is approved. What to do if a proposed control is adjudicated uncertain, including whether it counts toward the five or is replaced, remains an owner decision.

## Independent evidence and source hierarchy

Establish the intended person before candidate generation. Reviewers must not use HAMMER predictions, resolver outcomes, candidate pools, candidate-source IDs/profiles, rank, scores, or historical V3 labels. OpenAlex candidate evidence is excluded from Stage A. Do not access `docs/evaluation/pilot_predictions.json` during selection or labeling.

The approved author-benchmark protocol calls for independent evidence classes: (1) a person-level source such as an official institutional/laboratory profile, personal academic page, or externally administered researcher record; and (2) publication-level evidence connecting the person to works, preferably two DOI-resolvable publisher or repository records. ORCID or another externally administered person identifier can support a match but should be corroborated by publications. A name-only match, single self-entered identifier, LLM answer, search snippet, or candidate-provider profile is insufficient by itself.

The hierarchy below restates approved source classes, not new authorization:

1. **Person-level primary evidence:** official institutional, laboratory, employer, or author academic page; externally administered researcher record where available.
2. **Work-level corroboration:** DOI-resolvable publisher or repository records whose authorship and metadata connect the work to the person.
3. **Supporting context:** other independently sourced records that corroborate name variants, affiliation, or chronology; these do not replace person-level plus work-level evidence.

No source tier automatically determines a label. Whether one publication record can suffice when a second is unavailable, how conflicting official sources are ranked, and which additional registries are acceptable remain open. Record unavailable evidence; never invent a source or locator.

## Evidence recording

1. Assign an opaque case ID. Keep personal details out of Git unless an owner-approved data policy allows them.
2. Record source name/type, URL or persistent reference, access date, evidence date/period when stated, and a concise locator. Reuse the existing evidence-packet field conventions or the pilot CSV; do not alter benchmark templates.
3. Record what each item supports and any contradictory evidence. Distinguish direct identity evidence from material merely consistent with a name or affiliation.
4. Reviewers record their decision, evidence references, rationale, uncertainty/confidence rationale, and effort independently. For unresolved controls, record the sources/searches checked and why they did not establish a unique target.
5. Preserve captures only in an owner-approved secure workspace and where source terms permit. Git may contain permitted references and concise locators, not restricted or private captures.
6. Freeze Stage A labels and identity groups before candidate capture. Do not overload existing evaluation fields with a provider ID as gold-person truth; the storage representation remains open.

## Ambiguity, exclusion, and escalation

- Conflicting or insufficient evidence is `uncertain`; send disagreements to an independent adjudicator with the same candidate-blind packet.
- `unresolved` requires the owner-approved search boundary. It is not an assertion of nonexistence.
- Defer/exclude a proposed case if evidence is inaccessible/restricted, provenance cannot be recorded, or it duplicates another pilot identity. Record the reason; never replace it based on system behavior.
- Escalate identity-group overlap, shared decisive publications, possible duplicate people, and reviewer conflicts before labels freeze.
- If adjudication cannot settle a conflict, retain `uncertain`; apply the owner-approved replacement rule without changing 10/5 silently.

## Reporting boundary

Report workflow observations with exact counts, denominators, and suitable uncertainty intervals. Record evidence availability, reviewer agreement/disagreement, adjudication, and time. Do not calculate resolver accuracy or baseline superiority, set a pass criterion, require a minimum automatic-decision count, or impose a coverage floor.

## Open decisions before annotation

1. Minimum sufficient publication evidence when a second record is unavailable.
2. Source ranking for conflicting official/authoritative sources and any additional permitted registries.
3. Search scope/stopping rule for unresolved controls.
4. Treatment/replacement of an adjudicated uncertain control within the five-control quota.
5. Confidence-scale anchors; the existing CSV field has no pilot-specific anchors.
6. Secure storage, access, retention, and source-capture policy.
7. Representation of independent `gold_person_id` and any later candidate-source crosswalk without changing benchmark templates.
