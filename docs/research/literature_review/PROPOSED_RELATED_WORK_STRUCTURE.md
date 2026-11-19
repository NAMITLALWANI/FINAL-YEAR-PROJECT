# Proposed related-work and paper structure

**Status:** Research-development proposal, not final manuscript text. The user has accepted the RQ2-first direction in principle and requested literature foundation work. No experiments or application changes are part of this note.

## Suggested related-work order

### 1. Scholarly metadata graphs and cross-source provenance

Introduce open and proprietary scholarly data sources as sources with different scope, coverage and metadata completeness. Cite OpenAlex’s resource paper, Culbert et al.’s shared-corpus reference-coverage study, Gerasimov et al.’s task-specific dataset-citation comparison, and AggAND’s use of external sources in PubMed author disambiguation.

**Argument boundary:** Cross-source aggregation is established. The paper’s contribution cannot be “we combine sources for the first time.” Frame any project value around retaining source-level provenance and separating work records from author decisions, if the committed implementation and experiment trail support it.

### 2. Work-level matching and author identity resolution

Explain that publication-record equivalence and person identity are distinct linkage targets. Use Fellegi–Sunter for record linkage foundations and Forbes et al. for an applied duplicate-record workflow. Then introduce author name disambiguation as assigning mentions or papers to people, citing the Rodrigues et al. review and systems such as DBLP deep AND, AggAND and PubMed Computed Authors.

**Argument boundary:** Do not merge deduplication and author resolution into a single accuracy number or use a duplicate-work score as evidence of person identity.

### 3. Evidence signals, benchmarks and generalization

Summarize evidence used in prior work: name variants, coauthors, titles/research topics, affiliations, temporal/publication metadata and external identifiers. Cite Boukhers & Asundi, AggAND, Choi et al. and PubMed Computed Authors. Then describe benchmark availability and transfer concerns using GSD1900, S2AND, WhoIsWho and LAGOS-AND.

**Argument boundary:** HAMMER’s five weighted signals are an implementation choice; source literature does not show those weights are optimal. Use identity-group splits, a fixed candidate snapshot, explicit label provenance and stratification by confirmed/probable/negative cases.

### 4. New identities, abstention and human review

Review the new-author limitation discussed in the DBLP paper, large online/daily assignment in WhoIsWho, human annotators and maintenance in AMiner, and selective prediction/reject-option work such as SelectiveNet. Explain why an identity resolver may need three outcomes: assign automatically, route for human judgment, or retain unresolved.

**Argument boundary:** Abstention and HITL have prior art. A possible empirical contribution is a measured error/coverage/reviewer-workload trade-off for HAMMER’s gates on a bounded, well-described set.

### 5. Affiliation parsing and organization linking

Separate author affiliation evidence from organization entity linking. Cite AffilGood’s span/entity/ROR tasks and AffRo’s raw-string-to-organization-ID method and dataset.

**Argument boundary:** Describe HAMMER’s current institution compatibility feature accurately. Do not say the field lacks institution disambiguation or imply a token-overlap signal resolves departments.

### 6. Bounded study focus

Close with the project-specific question: whether a provenance-retaining scholarly metadata workflow can separate work matching from author identity decisions and, under an audited candidate pool, how deterministic evidence gates alter automatic precision/coverage relative to a simple ranked choice.

That is a **proposed** contribution and must be validated by paired baselines and independently reviewed labels. It is not a claim that HAMMER’s system combination is unprecedented.

## Recommended overall paper outline

1. Introduction: scholarly metadata quality, distinct work and person linkage tasks, bounded aims.
2. Related work: source graphs/provenance; work-level linkage; AND methods/signals/benchmarks; selective decisions and human review; affiliation linking.
3. System: committed architecture, data provenance, candidate generation, evidence features, thresholds and decision states.
4. Methods: frozen data, candidate snapshots, label adjudication, identity-level splits, baselines, exact denominators and metrics.
5. Results: RQ2 candidate retrieval first, then selective decision risk/coverage; RQ1 only if replay is repaired and comparable.
6. Error analysis: common names, sparse metadata, probable labels, misses, controls, source-specific errors.
7. Discussion: implications for review workload and provenance; comparison only where tasks align.
8. Limitations and reproducibility: small/curated sample, OpenAlex-derived candidate/gold risks, source drift, human-review cost and versioned artifacts.
9. Conclusion.

Write the abstract after the protocol and results are approved. Treat semantic search and optional generation as supporting application features unless separate relevance/support experiments are conducted.

## Recommended source-reading order

1. GSD1900 original and PubMed Computed Authors, to reconcile the October result card.
2. S2AND, WhoIsWho, LAGOS-AND and AMiner, to define realistic benchmark, candidate-generation and human-review context.
3. DBLP deep AND and AggAND, to ground signals and external metadata.
4. Choi et al., AffilGood and AffRo, to narrow heterogeneous-site and affiliation claims.
5. SelectiveNet and the record-linkage/deduplication work, to ground decision coverage and conditional RQ1.

## Unresolved decisions for the project owner

1. Can the original GSD1900 subset, HAMMER prediction rows and calculation script behind slide 10 be located? If not, preserve the cards as historical unverified claims and exclude them from the paper.
2. Is the probable one of the 13 V3 auto-selected identities allowed in the “correct” numerator, or should the primary result be 12/12 Confirmed only?
3. Should GSD1900 remain a proposed benchmark, given it is pairwise and biomedical, or should LAGOS-AND/S2AND be evaluated for the author-query task after schema/license/leakage review?
4. Is RQ1 retained only after fixing the edition regex and producing paired V1/V2 predictions on identical frozen pairs?
5. Does the user want the future bibliography to use BibTeX keys from HAMMER_REFERENCES.bib as canonical for the manuscript?

These decisions do not block the literature inventory and can be answered when the paper protocol is reviewed.

