# Updated Claim / Evidence Matrix

**Status:** Evidence-bound paper guidance; not an approved manuscript
**Audit baseline:** committed Git HEAD d41378cf4781a9bec8738ff60899ecec43227b6f

| Proposed statement | Current evidence | Evidence status | Allowed use now | Gate for a result claim |
|---|---|---|---|---|
| HAMMER integrates scholarly metadata and retains source provenance in its architecture. | Committed backend/frontend code and architecture documents. | Implementation inspection. | Describe the implemented workflow and components; do not imply evaluated user benefit. | Confirm exact code path and source behavior against final Git SHA. |
| HAMMER separates publication deduplication from author identity resolution. | Separate committed modules, data models, and workflows. | Implementation inspection. | Describe architectural separation. | Verify final architecture diagram and data flow. |
| Candidate generation creates hypotheses; a source author ID is not proof of intended identity. | Candidate module boundary and OpenAlex profile structure. | Supported design boundary. | State that source-profile IDs are candidates. | No additional gate for this bounded design statement. |
| Evidence ranking and gates use five configured signals and automatic/manual/unresolved outcomes. | Committed scorer, resolver, and configuration. | Software behavior, not empirical safety. | Describe method and record effective values. | Independent frozen test for accuracy, precision, or safety claims. |
| OpenAlex candidate retrieval has measured recall of a stated percentage. | V3 labels and candidates are OpenAlex-derived; Day 5 outputs do not align with V3 top candidates on 30/56 positive rows. | Exploratory and misaligned. | At most describe historical artifacts and limitations. | Independent non-OpenAlex truth, separate source mapping, captured pools, sealed split, same-run metrics. |
| V3's recorded automatic decisions are accurate. | 13 V3 auto rows (12 Confirmed, one Probable), but labels are not independently auditable per row and candidate artifacts are misaligned. | Not supported as primary accuracy. | Do not say “13/13 accurate” or combine Probable with Confirmed. | Independent external labels and candidate mappings on a sealed test with exact denominators and intervals. |
| Evidence gates reduce selective risk at useful coverage. | No aligned frozen baseline comparison on independent labels. | Not measured. | State only as a hypothesis. | Compare risk and coverage at frozen thresholds on one pool; show actual automatic-decision n and interval. Identity count is not decision count. |
| Normalized/multi-strategy retrieval improves Recall@k or MRR. | Candidate code exists; no independent sealed retrieval comparison. | Not measured. | State only as H2a. | Frozen retrieval arms, independent mappings, response snapshots, identity-disjoint test. |
| Retrieval ranking improves paper discovery. | No complete blinded relevance pool or evaluated BM25/dense/hybrid comparison for this question. | Not supported. | Describe retrieval as a system capability only. | Separate relevance dataset, ranked baselines, and relevance metrics. |
| Generated explanations are semantically supported by cited papers. | Citation filtering and adversarial behavior checks do not establish entailment or factual support. | Not supported. | Describe structural safeguards only, not semantic correctness or hallucination-free behavior. | Blinded claim-to-source judgments, agreement, controlled versions, and predeclared evaluation. |
| Dedup V2 improves over V1 on the 50-pair benchmark. | Historical aggregates conflict; committed pair categories differ from one audit table; no paired per-pair outputs. Edition regex contains U+0008 characters. | Unreconciled and unverified. | Describe defect and need for replay; no improvement claim. | Verify labels, correct defect in versioned change, paired replay with per-pair outputs. |
| Deduplication achieves universal zero false merges or prevents all bad merges. | Curated 50-pair challenge cannot establish a universal rate; historical results are not paired. | Not supported. | Do not use. | No finite curated benchmark supports a universal claim; use bounded test language. |
| The project introduces a novel author-disambiguation algorithm. | Implementation uses established evidence signals, deterministic scoring, and decision gates; no novelty study supports the claim. | Not supported. | Position as applied systems/methodology research. | Separate literature-backed novelty question and evaluation. |

## Safe wording after the proposed protocol

The approved pilot supports workflow feasibility observations only, not author-resolution accuracy. If a later independent main study supports hypotheses, scope claims to the frozen HAMMER version, captured OpenAlex responses, specified cohort, and registered thresholds. Include the number of independent identity groups, source-mappable positives, automatic decisions, wrong automatic decisions, unresolved controls, source failures, coverage, and uncertainty intervals.

If sample size is insufficient, report a pilot with exact counts and descriptive intervals. Zero observed errors is not evidence of zero risk. Keep sub-Confirmed/Probable evidence out of the primary status and never substitute a provider profile ID for independently established person identity.

## Supporting references and bibliography state

The repository bibliography includes core author-name disambiguation and selective-prediction sources such as S2AND, WhoIsWho, LAGOS-AND, AMiner, GSD1900, SelectiveNet, and Fellegi–Sunter. Use the existing literature matrix and reference verification report; do not create another bibliography in Stage 2. The AMiner BibTeX entry lacks page metadata in the current file and should be checked against its proceedings record before final citation. No bibliography file was modified.
