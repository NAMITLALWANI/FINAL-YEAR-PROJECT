# Hybrid Academic Metadata Aggregator and Evidence-Guided Author Entity Resolution System

**Research-in-progress draft â updated 15 October 2026**

**Author(s):** [Student name], [Supervisor] Â· **Affiliation:** [Institution]

## Abstract

Scholarly publication metadata is distributed across providers whose records overlap but differ in identifiers, names, affiliations, and completeness. These inconsistencies complicate both publication consolidation and author identity review. This work presents a working academic metadata application that ingests records from OpenAlex, DBLP, Crossref, and arXiv; normalizes and deduplicates publications; and preserves source provenance in a relational database. A persistent Chroma index over canonical publications supplies semantic evidence to an existing deterministic OpenAlex author-candidate workflow. Optional Gemini-generated explanations are constrained to cite retrieved document identifiers, while citation filtering, deterministic fallback, manual review, and unresolved outcomes preserve a boundary between evidence presentation and authoritative identity decisions. The backend database currently contains 696 canonical publications and 2,186 source records; these are mutable application data, not an evaluation corpus. The project also implements blinded annotation preparation, adjudication, frozen-snapshot validation, read-only V1 replay, and separate identity and retrieval metrics. A 10-query annotation pilot and a minimum 100-query independently reviewed identity dataset are specified but not yet completed. Retrieval relevance judgments and human assessments of generated claims are also absent. Engineering verification demonstrates application and tooling behavior, not research performance. Thus, the system and evaluation workflow are implemented, while whether semantic retrieval improves evidence retrieval or author-candidate decisions remains an open empirical question.

**Keywords:** scholarly metadata; author name disambiguation; entity resolution; semantic retrieval; evidence provenance; human review; abstention.

## 1. Introduction

Researchers often encounter publication records assembled from multiple bibliographic services. The services may describe the same publication using different or incomplete metadata, and may disagree about author names, venue, date, identifiers, or affiliations. A system that aggregates these records must therefore preserve both the canonical representation it uses for search and the source evidence from which that representation was constructed.

Author entity resolution adds a distinct risk. A query may match multiple candidate profiles, and incomplete records can make the correct profile difficult to establish. Semantic similarity can help locate publications about a topic, but topical relevance does not establish that the publication belongs to the person named in a query. Likewise, a generated explanation that cites a retrieved record can still misinterpret what that record supports. An applied system should make this distinction visible, retain provenance, and allow a reviewer to select a candidate or leave identity unresolved when evidence is insufficient.

This project combines an existing deterministic OpenAlex candidate resolver with a persistent semantic search over canonical publication records. Retrieval is presented as review context; it does not change the V1 resolver's scores or identity statuses. The implemented work is paired with an evaluation workflow intended to test retrieval and identity decisions separately rather than treating the combined interface as evidence of improved accuracy.

The research questions are:

1. **Evidence retrieval:** Does semantic retrieval provide more useful query-to-publication evidence than a defined metadata or identifier baseline on an independently judged publication pool?
2. **Identity decisions:** Does a separately implemented retrieval-enhanced resolver improve candidate quality while avoiding an unacceptable rate of false automatic selections compared with V1?
3. **Explanation support:** Are claims from the optional generator adequately supported by their cited records under human review?

The first and third questions require real annotations and, for the third, a live provider run. The second additionally requires a separately versioned resolver variant: the current system cannot answer it because retrieved evidence does not affect V1 decisions.

## 2. Related work and research positioning

Record linkage studies how evidence across records should be combined when fields agree, disagree, or are missing. The FellegiâSunter framework provides a classical statistical foundation for linkage decisions [1]. Scholarly author-name disambiguation specializes this problem: publication assignments depend on interacting evidence such as author mentions, coauthors, affiliations, topics, and time.

S2AND harmonizes multiple author-disambiguation datasets and provides a shared evaluation system [2]. WhoIsWho provides a large-scale benchmark and toolkit for academic name disambiguation [3]. These resources make clear that performance depends on dataset construction, identity grouping, and evaluation protocol; a small operational application history is not a substitute for independent benchmark labels. The present work addresses a narrower application question: whether retrieval over a locally aggregated, canonicalized scholarly corpus supplies useful, source-traceable evidence in a conservative candidate-review workflow.

Retrieval-augmented generation (RAG) conditions generation on retrieved non-parametric evidence [4]. Provenance is also an explicit concern in knowledge-intensive evaluation, as illustrated by KILT [5]. Here, retrieval supports evidence inspection and the optional generator provides explanatory text; neither is authorized to assign identity. Chroma persistent storage and Sentence Transformers embeddings are implementation choices [6], while Gemini is an optional external generation provider [7]. These are not proposed as new algorithms. The literature review is targeted and preliminary; a broader review with a documented search date, inclusion criteria, and search log remains in progress. No claim is made that prior work has ignored evidence retrieval for author review.

## 3. Contributions and scope

### 3.1 Completed engineering contributions

1. A multi-source scholarly metadata application with normalization, publication deduplication, canonical relational storage, and source provenance.
2. A persistent semantic index over canonical publications, using stable document identifiers, content hashes, index/model version metadata, and explicit rebuild operations.
3. An evidence retrieval workflow integrated with author-candidate review, while leaving deterministic V1 identity scores, rankings, and statuses unchanged.
4. An optional Gemini explanation path with bounded retrieved context, citation-ID validation, deterministic fallback, and no authority over identity decisions.
5. An evaluation toolchain for blinded reviewer packets, independent annotation merges, adjudication, dataset and snapshot validation, read-only frozen V1 replay, and separately denominated identity/retrieval metrics.

### 3.2 Ongoing empirical contribution

The planned empirical contribution is a controlled evaluation of evidence retrieval, V1 identity decisions, and generated claim support on independently annotated data. This work has not yet produced a valid frozen dataset or research results. Results will be reported only after labels, snapshots, and versioned predictions are available and traceable.

## 4. System design and implementation

The system separates source ingestion, canonical publication storage, evidence retrieval, candidate resolution, and optional explanation. The relational database remains authoritative; Chroma is a rebuildable projection. Candidate profiles are resolved by V1 independently of semantic retrieval.

![Figure 1. Application architecture. Retrieved and generated evidence is shown to the reviewer and does not feed the V1 identity decision.](figures/system-architecture.png)

### 4.1 Metadata aggregation and canonical storage

Connectors obtain records from OpenAlex, DBLP, Crossref, and arXiv. The existing pipeline normalizes publication fields and compares records for deduplication, preserving raw source records and canonical publications in SQLAlchemy-backed relational tables. The canonical record supports application search, while source records and provider identifiers retain traceability. The database is the source of truth for publications, provenance, candidates, and resolution decisions.

At the read-only check for this draft, `backend/academic_search.db` contained **696 publications** and **2,186 source records**, with SQLite integrity check `ok`. These counts describe mutable local application state and are not a frozen research dataset. A separate root-level SQLite file contains a different history and must not be substituted for the backend database.

![Figure 2. Current local backend database inventory. These are mutable engineering data counts, not benchmark size or performance results.](figures/database-inventory.png)

### 4.2 Persistent semantic evidence retrieval

An explicit builder projects canonical publications into Chroma collection `scholarly_records_v1`. The current document schema is `scholarly-record-v1`; the default local embedding model is `all-MiniLM-L6-v2`. Indexed text includes available title, abstract, author list, venue, year, source-reported topics/concepts, and publication-level affiliation mentions. Affiliation mentions are not linked to individual authors. Metadata retains canonical and relational identifiers, source providers and source-record identifiers, DOI, URL, content hash, abstract provenance, embedding model, and index version.

Document IDs are stable hashes derived from canonical IDs. Content hashes incorporate the normalized indexed representation and version information so an explicit rebuild can update changed documents, retain unchanged ones, and remove stale entries. At query time, semantic top-k retrieval can be combined with exact DOI, year, or primary-source filters. Returned hits include rank, ranking score, and provenance. Cosine-derived similarity is a ranking signal, not a calibrated probability of relevance or identity.

### 4.3 Author candidate resolution and review

Author Resolution V1 generates OpenAlex candidate profiles and scores available name, institution, publication-overlap, coauthor-overlap, and temporal signals. Configurable heuristic rules select among `auto_selected`, `manual_selection_required`, and `unresolved`. The scores and thresholds are engineering settings, not calibrated probabilities. Evidence provenance and decision status are persisted. Failed candidate-source requests are distinct from a successful empty result; source failure must not be treated as an unresolved identity.

Retrieved publications are displayed as supporting context in the review interface. They do not change V1 scores, candidate order, or status. Reviewers can select a profile when required or explicitly record an unresolved outcome. The system preserves this human decision boundary because relevant publications may still be authored by a different person with a similar name.

### 4.4 Optional explanation generation

When configured, the explanation layer calls Gemini's native `generateContent` API with a bounded query and at most eight retrieved records. The instructions treat metadata as untrusted input, prohibit identity decisions, and request claims that cite supplied document IDs. The parser drops claims with absent or unknown IDs, and the display summary is assembled from claims that pass this identifier-membership check. If the provider is missing or fails, deterministic evidence text remains available; no-hit queries abstain.

Identifier membership does not establish semantic entailment: a cited document may not support the claim made about it. Human claim-to-source review is required to assess faithfulness. Gemini request construction, parsing, failure fallback, and citation filtering have mock-based test coverage. The live provider integration has not been verified in the active environment, so no live generation-quality result is reported.

## 5. Research progress and evaluation status

| Work area | Current status | Evidence and interpretation |
|---|---|---|
| Metadata pipeline and canonical storage | Implemented and verified | Read-only database check: 696 publications, 2,186 source records; integrity `ok`. Counts are application-state figures. |
| Persistent semantic retrieval | Implemented and verified | Persistent index was built and locally API-checked over 696 canonical records, as recorded in project evaluation documentation. No relevance labels exist. |
| Evidence provenance | Implemented and verified | Canonical IDs, provider/source-record metadata, content hashes, and index version are represented and tested. |
| Explanation integration | Implemented but not live-verified | Gemini native request path and deterministic fallback have mock coverage; no live Gemini call has been verified. |
| Engineering verification | Implemented and verified | Current backend suite: 52 passing tests. The frontend production build was previously successful. These checks establish implementation behavior, not research performance. |
| Annotation packet and adjudication tooling | Implemented and verified | Blinded packet/merge/validation workflows are covered by synthetic tests; synthetic fixtures are not labels. |
| Independent identity annotation | Planned or in progress | No source-verified, double-reviewed identity labels are present. |
| Frozen research dataset | Planned or in progress | No sealed manifest or frozen development/test membership exists. |
| Retrieval relevance evaluation | Planned or in progress | No independently graded query-publication pool is present. |
| Identity-resolution evaluation | Planned or in progress | No valid labelled benchmark replay or held-out result exists. |
| Human evaluation of generated claims | Planned or in progress | Requires live provider output and independent claim-support review. |

Historical manual choices are operational application history. They have not been independently verified, may include repeated queries, and are excluded from the benchmark labels and primary results. The evaluation scripts have not been run against a valid real-data manifest. No research result is inferred from unit tests, index size, latency of a local build, or user selections.

## 6. Evaluation workstream

The evaluation is divided into distinct data collection and analysis tasks so that evidence retrieval, identity decisions, and explanation support are not collapsed into one âRAG accuracyâ measure.

### 6.1 Identity labels and protocol pilot

First, prepare a **10-query annotation pilot** sampled without viewing resolver outputs. Two reviewers independently inspect source-level evidence before seeing each other's judgments or candidate rankings. Each records a label, a 1â5 confidence value, rationale, and evidence references with source, persistent URL or source-scoped identifier, capture time, and evidence type. A third reviewer adjudicates disagreements. If evidence is contradictory or inadequate, retain `uncertain` rather than force a match. Record rubric changes and re-review pilot cases affected by the final rubric. The pilot develops the protocol; it is not part of held-out evaluation.

The main identity set must contain at least **100 author queries**, including common and rare names, variants/transliterations where relevant, affiliation or discipline changes, sparse/conflicting evidence, and cases that may be unresolved. A `resolved` label requires a specific source-scoped author identifier; `unresolved` indicates no uniquely supported target; `uncertain` records inadequate or contradictory evidence. Preserve sampling and exclusion notes. The current templates and merge tool require exact query coverage, distinct reviewers, evidence references, confidence, and adjudication consistency.

### 6.2 Retrieval relevance judgments

Create a separate retrieval query set and freeze a documented publication pool for each query before judgment. The pool should cover known relevant publications and the union of results from each compared retrieval system. Reviewers receive blinded query-publication pairs without system, rank, or similarity attribution and independently assign 0 (not relevant), 1 (relevant), or 2 (strongly relevant), with evidence notes. Adjudicate disagreements; missing judgments are incomplete, not irrelevant. The frozen pool must cover every returned publication in each evaluated prediction file.

This benchmark measures whether retrieval finds relevant publication evidence. It does not label author identity: publication topical relevance or author-list appearance alone is not a cross-source identity link.

### 6.3 Frozen snapshots, splits, and replay

Use checkpointed copies of the relational database and persistent index. Record canonical snapshot identifiers, file/tree hashes, database revision and counts, Chroma collection, index/model versions, and index count in a sealed manifest. Candidate snapshots must exist in the selected database and match the normalized query. Do not add synthetic evaluation rows to the application database or run replay against it.

Assign `identity_group_id` by person so spelling variants and repeated queries cannot cross splits. Freeze training, development, and test membership before predictions. Use training/development only for design decisions and threshold tuning; reserve test for the final report. Replay V1 against frozen candidate snapshots and an immutable read-only database, saving non-overwriting, versioned predictions bound to manifest and code/configuration hashes. The current tooling validates these controls, but no real manifest or prediction set has been created.

![Figure 3. Planned annotation and evaluation workflow. All dataset counts shown are protocol targets; no real annotation phase is complete.](figures/evaluation-workflow.png)

### 6.4 Comparisons and interpretation

For RQ1, compare semantic retrieval with a specified metadata/identifier baseline on identical queries and the same complete, blinded relevance pool. For RQ2, compare V1 with a separately implemented and versioned retrieval-enhanced resolver on the same independently labelled identity queries. That variant does not exist yet; the current application alone cannot answer RQ2. Report both improvements and regressions, especially incorrect automatic selections and changes in abstention/coverage. For RQ3, first verify a live Gemini request using synthetic non-sensitive evidence, then collect generated explanations for the evaluation corpus under a documented run configuration and have reviewers assess claim-to-source support. A successful smoke call alone is not a faithfulness evaluation.

The retrieval hypothesis would be supported only if the semantic system improves pre-specified retrieval metrics on the held-out relevance set with all predictions covered by judgments. The identity hypothesis would require better pre-specified candidate/decision measures without an unacceptable false-selection trade-off on the frozen test set. It would be weakened or remain inconclusive if improvements are absent, inconsistent across slices, or accompanied by unsafe automatic errors. For explanations, citation membership alone is insufficient; human support judgments determine whether claims are grounded. Negative and inconclusive results will be reported with the same denominators and dataset-version traceability as positive outcomes.

## 7. Measures and denominators

For identity decisions, report counts as well as rates. Exclude `uncertain` from primary resolved/unresolved denominators but report its count. Define:

- **Selective accuracy:** correct automatic source-scoped IDs / all automatic decisions.
- **Automatic coverage:** automatic decisions / all adjudicated resolved plus unresolved queries.
- **Resolved-target automatic recall:** correct automatic decisions / all adjudicated resolved queries; wrong selections and abstentions are misses.
- **Top-1 candidate accuracy:** queries whose highest-ranked candidate exactly matches the gold source-scoped ID / all adjudicated resolved queries.
- **Unresolved recall:** correctly unresolved queries / all adjudicated unresolved queries.
- **False-merge rate:** incorrect automatic selections / all automatic decisions.

Also report manual-review, unresolved, candidate-source-failure, and combined abstention counts/rates separately. Coverage and selective accuracy must be shown together so abstention cannot be hidden by accuracy among the few automatic cases. Where a denominator is zero, report the measure as undefined rather than zero.

For retrieval, report Recall@k, MRR, precision@k, empty-result rate, and latency. Relevant means an adjudicated grade greater than zero. Recall@k and MRR use only queries with at least one judged relevant publication; recall denominator is the number of relevant publications in that query's judged pool. Precision@k uses fixed denominator k, including unfilled positions. Empty-result rate uses all fully judged queries. Explain query-level averaging and denominators in every result artifact. Generation measures include citation-ID validity, human-rated claim support, unsupported-claim rate, completeness/relevance, abstention, provider failures, latency, and cost where observable.

## 8. Current evidence and planned experiments

No comparative identity, retrieval, or generation-quality results are available. The repository has no independent identity labels, frozen split, sealed manifest, or relevance judgments; therefore, no benchmark evaluator has run on valid research data. The 12 historical manual selections are not treated as ground truth and are not reported as a benchmark result.

The current engineering evidence is **52 passing backend tests**; the frontend production build also passed in the preceding application verification. The tests cover application workflows and evaluation-tool safeguards with isolated/synthetic fixtures. They show that code paths behave as tested, not that candidate identities are correct, that retrieved publications are relevant, or that generated claims are faithful. The local persistent retrieval index and API workflow have been verified in project checks, but no judged retrieval experiment has been completed. Live Gemini integration and human review of generated claims remain outstanding.

The next empirical outputs are: (1) pilot and adjudication records documenting the final identity rubric; (2) at least 100 independently reviewed identity queries and identity-group split freeze; (3) a separate fully judged retrieval pool; (4) immutable database/index snapshot identifiers and a sealed dataset manifest; (5) versioned V1 and, if implemented, retrieval-enhanced predictions; and (6) metrics and error analysis traceable to those exact predictions and labels. No performance table is populated until these artifacts exist.

## 9. Limitations, threats to validity, and ethics

The local corpus was accumulated through application use and is not a representative sample of scholarly literature. Provider coverage and metadata quality vary. Canonicalization can merge records incorrectly or leave duplicates, and missing fields can influence both retrieval and resolver evidence. An index built from this corpus cannot retrieve records absent from it. Semantic similarity can favor topical matches that are irrelevant to a specific information need, and neither similarity nor a valid citation ID establishes identity or semantic support.

Identity labels can be difficult when authoritative sources conflict or disappear. Independent reviewers and adjudication reduce but do not eliminate interpretation error. Identity-group splits reduce leakage, but small or imbalanced strata may limit precision and generalizability. Retrieval pools can be incomplete; the protocol therefore requires complete judgments for every result returned by evaluated systems. The optional Gemini provider may vary across model versions and service conditions, and no live output has yet been reviewed. Heuristic V1 thresholds are not statistically calibrated. These limitations will be reflected in any final analysis rather than hidden by aggregate metrics.

The system processes public scholarly metadata, but provider terms, attribution, rate limits, and redistribution restrictions still apply. Source references and captures should be stored in an approved research workspace; private or restricted evidence must not be committed. API credentials must remain outside source code and frontend bundles. Identity outcomes should remain reviewable and reversible, especially when evidence is sparse or ambiguous.

## 10. Reproducibility and research artifacts

The current retrieval configuration uses collection `scholarly_records_v1`, document/index version `scholarly-record-v1`, embedding model `all-MiniLM-L6-v2`, cosine distance, and default top-k 5. Index building is explicit; ordinary requests do not rebuild the collection. Evaluation scripts and templates are documented in `docs/evaluation.md` and `docs/evaluation/dataset.md`.

For every future run, preserve the dataset manifest, annotation and split hashes, database and index snapshot identifiers, candidate manifest, source-code revision, resolver/scoring/threshold configuration, model and embedding versions, raw versioned predictions, and metric output. The V1 replay opens only the frozen database snapshot in immutable read-only mode. Prediction and manifest tools refuse silent overwrite. This provides an auditable path from labels and snapshots to reported metrics; it does not create research labels or guarantee external replication without the same data and provider access.

## 11. Conclusion

The project has progressed beyond a metadata aggregation prototype: it includes canonical provenance-aware storage, persistent semantic publication retrieval, a review interface, optional citation-filtered Gemini explanation, and tooling for a controlled evaluation. Its central design boundary is deliberate: retrieved evidence can inform a human reviewer but cannot override the existing deterministic V1 identity decision. The backend contains 696 canonical publications and 2,186 source records, and current engineering checks pass, but these facts are implementation progress rather than evidence of research effectiveness.

The empirical work is now concretely specified but remains incomplete. Independent annotation, adjudication, frozen identity-group splits, a separate publication relevance set, immutable snapshots, valid evaluator runs, a retrieval-enhanced resolver variant, and human claim-support review are still required for the respective research questions. Until saved labels and predictions support controlled comparisons, the project makes no claim that semantic retrieval, Gemini, or RAG improves author resolution.

## References

1. I. P. Fellegi and A. B. Sunter, âA Theory for Record Linkage,â *Journal of the American Statistical Association*, vol. 64, no. 328, pp. 1183â1210, 1969. [doi:10.1080/01621459.1969.10501049](https://doi.org/10.1080/01621459.1969.10501049).
2. S. Subramanian, D. King, D. Downey, and S. Feldman, âS2AND: A Benchmark and Evaluation System for Author Name Disambiguation,â in *Proceedings of the ACM/IEEE Joint Conference on Digital Libraries (JCDL)*, 2021, pp. 170â179. [doi:10.1109/JCDL52503.2021.00029](https://doi.org/10.1109/JCDL52503.2021.00029); [paper](https://arxiv.org/abs/2103.07534); [dataset and license notes](https://github.com/allenai/S2AND).
3. B. Chen, J. Zhang, F. Zhang, T. Han, Y. Cheng, X. Li, Y. Dong, and J. Tang, âWeb-Scale Academic Name Disambiguation: the WhoIsWho Benchmark, Leaderboard, and Toolkit,â in *Proceedings of the 29th ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD â23)*, 2023, pp. 3817â3828. [doi:10.1145/3580305.3599930](https://doi.org/10.1145/3580305.3599930); [paper](https://arxiv.org/abs/2302.11848).
4. P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. KÃ¼ttler, M. Lewis, W.-t. Yih, T. RocktÃ¤schel, S. Riedel, and D. Kiela, âRetrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,â in *Advances in Neural Information Processing Systems 33*, 2020. [NeurIPS proceedings](https://papers.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html); [arXiv:2005.11401](https://arxiv.org/abs/2005.11401).
5. F. Petroni, A. Piktus, A. Fan, P. Lewis, M. Yazdani, N. De Cao, J. Thorne, Y. Jernite, V. Karpukhin, J. Maillard, V. Plachouras, T. RocktÃ¤schel, and S. Riedel, âKILT: a Benchmark for Knowledge Intensive Language Tasks,â in *Proceedings of NAACL-HLT 2021*, pp. 2523â2544. [doi:10.18653/v1/2021.naacl-main.200](https://doi.org/10.18653/v1/2021.naacl-main.200); [ACL Anthology](https://aclanthology.org/2021.naacl-main.200/).
6. Chroma, âEmbedding Functionsâ and âPersistent Client,â official documentation. [Embedding functions](https://docs.trychroma.com/docs/embeddings/embedding-functions); [Python client](https://docs.trychroma.com/reference/python).
7. Google, âGemini API: Generate content,â official API documentation. [GenerateContent REST API](https://ai.google.dev/api/generate-content); [structured output](https://ai.google.dev/gemini-api/docs/generate-content/structured-output).
7. Google, âGemini API: Generate content,â official API documentation. [GenerateContent REST API](https://ai.google.dev/api/generate-content); [structured output](https://ai.google.dev/gemini-api/docs/generate-content/structured-output).