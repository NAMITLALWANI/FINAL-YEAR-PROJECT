# Pilot Stage A Reviewer Guide

**Status:** Draft for owner review; reviewer assignments and cases do not yet exist.  
**Stage:** Independent intended-person labeling only; candidate mapping is a later, separate Stage B activity.

## Roles

Two Stage A reviewers independently assess every case using the same approved evidence packet. A separate adjudicator reviews disagreements/conflicts. Record distinct reviewer IDs. Reviewer assignment, conflict screening, and adjudicator availability must be confirmed before readiness.

## Blinding

Reviewers may see only query/context and approved independent external evidence. Do not provide or open candidate IDs/profiles, candidate pools, rank, HAMMER scores, predicted statuses, resolver explanations, or historical V3 labels. Do not access `docs/evaluation/pilot_predictions.json` during selection, review, adjudication, or replacement. Keep Stage B materials inaccessible until Stage A labels are frozen.

## Independent review

1. Inspect each source/locator and note inaccessible or contradictory material.
2. Choose `resolved`, `unresolved`, or `uncertain` under `PILOT_STAGE_A_ANNOTATION_PROTOCOL.md`. Do not force a positive label or infer nonexistence from missing search results.
3. Independently record status, evidence references, concise rationale, confidence/uncertainty rationale, and effort/time in the pilot template or an owner-approved identity-review format. Do not discuss the case or inspect another review before submitting.
4. For `resolved`, record the independent person key and external identifier only as allowed by the data policy. Never use an OpenAlex candidate ID as person truth.
5. For `unresolved`, record approved searches/sources checked and why the supplied context did not identify one person. For `uncertain`, specify missing or conflicting evidence.

## Evidence/workload CSV row convention

The empty pilot CSV uses `record_type=evidence` for one source/evidence item, `record_type=review` for one reviewer decision per case, and `record_type=adjudication` for a disputed case's final decision. Put total review effort on the review row only so evidence rows do not duplicate workload. Record support and contradiction on evidence rows; keep adjudication fields on the adjudication row. This is a pilot-only draft format and is not a replacement for benchmark templates.

## Disagreement and adjudication

Compare reviews only after both are recorded. Report exact agreement counts and denominators descriptively; there is no agreement pass criterion. A separate adjudicator reviews the same candidate-blind packet and records final status/rationale. If evidence remains inadequate or conflicting, retain `uncertain`. Do not alter the 10/5 composition without the owner-approved uncertain/replacement rule.

## Data handling and separation

Use opaque case IDs. Store private/restricted captures only in an approved secure location; Git receives only permitted references and concise locators. Do not alter benchmark templates or populate labels in this preparation task. Freeze Stage A labels and identity groups before candidate capture. Stage B must use a separate blinded packet with rank/scores hidden.

## Open reviewer decisions

Reviewer identities and conflicts, adjudicator availability, confidence anchors, packet storage/sharing, time-measurement method, and whether reviewers may consult sources beyond the packet must be settled before annotation. This guide is not readiness approval.
