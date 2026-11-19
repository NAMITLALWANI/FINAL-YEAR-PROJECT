# Data Split and Leakage Plan

**Status:** Proposed; no split manifest has been populated or frozen
**Purpose:** Prevent identity, work, candidate, and tuning information from crossing the test boundary

## Approved pilot and deferred main split

The approved pilot has 10 resolved identities and 5 unresolved controls. Keep identities distinct and preserve Stage A label review before Stage B blinded candidate mapping. Pilot cases are workflow-only and cannot be reported as a performance evaluation. The prior full split (40/20/60 plus 10/10/20 controls) is not approved; reassess its feasibility after observing actual evidence, agreement, pool-size, mapping, and workload data. For any future main study, assign all aliases and variants of one identity to one split.

| Split | Confirmed identity groups | Unresolved control groups | Use |
|---|---:|---:|---|
| Development | 40 | 10 | Develop annotation rubric and permitted analysis; any calibration belongs here |
| Validation | 20 | 10 | Check protocol consistency and frozen implementation |
| Sealed test | 60 | 20 | One-time evaluation, subject to sample-size and interval limits |

Use one preregistered primary query per group for primary metrics. Additional aliases, initials, affiliation contexts, and repeated queries remain with the same person and split and are secondary analyses. Stratify Confirmed groups across distinctive/common names, initials or spelling variants, multiple/changed affiliations, fragmented profiles, and sparse history. Keep unresolved controls out of the Confirmed retrieval denominator.

No 10% automatic-coverage floor is adopted. In a future main study, report actual automatic coverage together with selective risk; do not tune thresholds on test results.

## Assignment and freezing

1. Create query seeds from the sampling frame before candidate generation.
2. Establish and adjudicate person labels without system predictions or OpenAlex candidates.
3. Assign a stable identity_group_id to each intended person or control cluster.
4. Assign groups using a recorded deterministic procedure and seed, stratified only on predeclared case characteristics.
5. Ensure one external gold person ID and all aliases/variants appear in exactly one split.
6. Freeze query, evidence, label, group, and split files; hash them before candidate requests.
7. Capture candidates and score only after the split is sealed. Never move an inconvenient case after seeing output.

Reuse docs/evaluation/templates/split_manifest.csv and split_freeze.json, and the existing validator/sealer described in docs/evaluation/dataset.md. If the tool schema cannot represent independent gold identity and a separate OpenAlex crosswalk, document a versioned companion artifact rather than overloading OpenAlex IDs as truth. Such a schema change is not part of this proposal.

## Leakage rules

- **Person leakage:** No identity group, external person ID, alias, or query variant may cross splits.
- **Publication leakage:** DOI, work ID, or publication evidence used to identify one person must not be shared across splits in a way that reveals labels or resolver context. Group shared evidence before assignment; duplicate DOI rows are not independent examples.
- **Candidate leakage:** Candidate pools, OpenAlex IDs, response ranks, scores, selected candidates, or V3 labels cannot select queries, establish Stage A truth, tune rules, or assign splits.
- **Evidence leakage:** Do not feed gold-only URLs, reviewer notes, adjudication rationales, or mapping decisions into resolver context unless they are natural query inputs identically available at inference time.
- **Threshold leakage:** Freeze effective thresholds and score weights before unsealing test results. If calibrated, use development only, document tried configurations, then freeze one choice before validation/test.
- **Provider-time leakage:** Capture raw API results and timestamps. A live API is not a historical snapshot; do not replay by issuing another request. Use captured responses and report the cutoff.
- **Artifact leakage:** Keep test labels and reviewer evidence separate from predictions until test unsealing. Record hashes and access chronology in the manifest.
- **Post-test leakage:** No test-guided rule changes followed by re-evaluation on the same test. A modified method needs a new sealed test set.

## Current data disposition

V3 and prior Day 5 outputs have already been inspected. Treat them as exposed development/history only. None of their people, labels, or candidate pools can enter the new sealed test. Their candidate mismatch also prevents them from serving as one aligned frozen experiment.

## Reproducibility and privacy

Preserve only allowed source references and hashes in Git. Store source captures containing personal or restricted material in an approved secure workspace; do not commit private data. Record dataset version, capture dates, hashes, reviewer identifiers, adjudication, split seed, Git SHA, code/config hashes, and run ID. Use a new dataset version rather than overwriting a prior freeze.
