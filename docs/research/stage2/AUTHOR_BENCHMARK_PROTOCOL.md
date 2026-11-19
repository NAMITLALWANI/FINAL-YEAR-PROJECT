# Author Identity Benchmark Protocol

**Status:** Proposed; no benchmark rows, labels, or templates have been changed
**Purpose:** Establish intended author identities independently of HAMMER predictions and OpenAlex candidate generation

## Benchmark target and source independence

The target is the person intended by the query and supplied context, not an author profile ID returned by the system. Establish the identity label before candidate generation.

Assign each independently identified person a stable local gold_person_id. Where available, record an ORCID or another externally administered person identifier as evidence; otherwise use a project-local opaque ID linked to documented institutional or author-profile sources. Never define primary gold identity as an OpenAlex author ID.

For each Confirmed identity, collect at least two independent evidence classes:

- one person-level source, such as an official university/laboratory profile, personal academic page, or externally administered researcher record;
- publication-level evidence, preferably at least two DOI-resolvable publisher or repository records whose author lists and metadata connect to that person.

Record exact URLs or persistent IDs, capture dates, evidence type, and locator notes. A name match alone, an OpenAlex profile, an LLM answer, or a single self-entered identifier is insufficient by itself. ORCID can support a match but should be corroborated by publication records. Preserve local source captures where permitted; do not commit restricted or private material.

## Two-stage blind review

### Stage A — Intended-person labeling

1. Select query seeds and context from a documented sampling frame before calling OpenAlex or exposing system output.
2. Give two reviewers the query text, resolver context, and external evidence packet only. Hide candidate IDs, candidate names not present in the packet, candidate rank, scores, resolver status, and prior V3 labels.
3. Each reviewer independently selects exactly one supported status: resolved, unresolved, or uncertain. Reviewers record confidence, rationale, and evidence references.
4. A distinct adjudicator resolves disagreements from evidence. If evidence cannot establish a unique target, retain uncertain. Never force a positive label to increase benchmark size.
5. Freeze final labels and identity groups before candidate generation.

Reuse docs/evaluation/templates/identity_query_seed.csv, identity_evidence_packet.csv, identity_labels.csv, and identity_adjudication.csv, plus the workflow in docs/evaluation/dataset.md. In the current schema, encode primary Confirmed as final status resolved, no-supported-match as unresolved, and insufficient/conflicting evidence as uncertain. The source-scoped gold ID may be an external identifier or approved local opaque person ID; the person-group key and candidate-source mapping are distinct concepts. V3's Probable label is not a supported final status and remains excluded from resolved labels. Do not add a separate Probable sensitivity grade in the initial study.

### Stage B — Candidate-source mapping

Only after Stage A labels and split membership are frozen, prepare a separate candidate mapping review.

- Include the full frozen candidate pool, shuffle candidates independently per query, and hide API rank, HAMMER scores, decisions, and baseline names.
- Ask reviewers to map each OpenAlex author ID to a Stage A gold_person_id, mark a verified different person, or mark evidence insufficient.
- Use independently documented identifiers and work records, such as ORCID links and DOI/publisher author records, to establish mapping. Candidate display names and OpenAlex profile data are objects being evaluated; they must not retroactively establish Stage A truth.
- Adjudicate mapping disagreements independently. Preserve ambiguous mappings; do not choose the highest-ranked candidate.
- A candidate is a retrieval hit only if mapping is Confirmed to the intended gold_person_id. A split OpenAlex profile can map to the same person only when external evidence establishes it. Report profile fragmentation separately.
- After candidate pools are frozen, a separate source-coverage audit may look for an OpenAlex profile using independent identity evidence. This determines source-mappability; it must not alter the identity label or query context.

This mapping needs a companion crosswalk with query ID, source author ID, gold person ID, mapping status, reviewer IDs, evidence references, and adjudication status. This schema is a proposal only; do not add or populate it before approval. The frozen candidate manifest and resolver-prediction templates remain the run record.

## Label meanings

- **resolved:** external evidence establishes one intended person and review establishes a canonical gold_person_id. This is the primary positive evaluator status; “Confirmed” is explanatory shorthand.
- **uncertain:** reviewers cannot settle identity using available evidence. This includes evidence historically called V3 “Probable”; never encode it as resolved. A separate optional grade is not recommended for the first study unless a sensitivity question justifies the added schema and review work.
- **unresolved:** the supplied query and context do not establish a uniquely supported intended person. This does not assert that no such person exists. A confident automatic assignment is a false acceptance for this query.
- **Synthetic control:** use only for explicit implementation checks. Do not mix fictitious entities with population performance metrics, and do not claim an unindexed or absent OpenAlex profile proves nonexistence.

The primary benchmark is resolved/Confirmed intended identities plus adjudicated unresolved cases for decision safety. Uncertain cases are counted and excluded from primary rates. Retrieval Recall@k uses only Confirmed people for whom the post-freeze source-coverage audit establishes at least one externally mapped OpenAlex profile.

## Sampling frame and proposed scale

The approved protocol pilot contains 10 resolved identities and 5 unresolved controls. Use it only to assess evidence availability, rubric clarity, reviewer agreement, candidate-pool sizes, candidate-to-person mapping difficulty, and annotation workload. It is not a performance evaluation and must not support author-resolution accuracy claims. Reassess main-study size after the pilot. Use one preregistered primary query per group for primary metrics; aliases and additional contexts are secondary analyses and remain grouped. Sample across common/distinctive names, initials/name variants, transliteration where relevant, affiliation change, multiple institutions, fragmented profiles, and sparse histories. Keep every alias and repeated query for one person in the same identity group. Record inclusion/exclusion reasons in the sampling ledger.

Before owner decisions, the proposed full split entailed 160 primary cases: 120 resolved identities and 40 unresolved controls. With two independent Stage A reviews per case, that is 320 case reviews before adjudication. Assuming three evidence checks per resolved identity (one person-level source plus two publication records), 120 identities require about 360 checks. Unresolved cases need documented searches, whose effort is not estimated. Candidate mapping depends on pool sizes: at the verified default cap of 10, 160 pools yield at most 1,600 query-profile mappings, or 3,200 judgments if double-reviewed. These are workload counts, not time estimates. A protocol pilot is recommended.

## Existing V3 disposition

The V3 sealed file has 100 rows: 50 Confirmed, 6 Probable, and 44 controls, including 4 negative-control-pair rows. Its positive rows point to 33 unique OpenAlex IDs. The canonical-evidence sidecar has 28 entries, of which 24 overlap those IDs; nine positive IDs have no sidecar entry. V3 rows do not include per-row external URLs and blinded reviewer evidence sufficient to audit independence. Its labels are historical/exploratory for the proposed primary question.

The 56 positive rows and 100 total rows also include prior hand inspection and use OpenAlex IDs as labels. Do not move V3 identities into the new sealed test. If reused for method development, mark it as exposed historical data and exclude it from validation and test estimates.
