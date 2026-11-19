# HAMMER research gap and positioning

**Status:** Research-preparation assessment for ChatGPT (research director) and the owner. It recommends; it does not decide, and it changes no approved methodology.  
**Commit inspected:** `bee7eabfba2d88c4a03c12d227ac6b04624fb8c8`.  
**Evidence base:** the existing repository literature audit, a limited extension described in `LITERATURE_SEARCH_LOG.md`, and static reading of the code (`PAPER_IMPLEMENTATION_FACTS.md`). **No source was read in full.** Reference keys are in `LITERATURE_MASTER_INVENTORY.md`.

## Bottom line

1. The *narrow* gap is **plausible but not established**. It is a gap in what is **evaluated and reported jointly**, not a gap in what exists as a technique.
2. Every individual ingredient (candidate retrieval, multi-signal scoring, human review, abstention-like decisions) has prior art. A novelty claim on any ingredient is **not justified**.
3. The most honest contribution is an **applied systems study with a careful evaluation protocol**. Whether even the protocol is novel depends on reading work I could only skim (CONNA, WhoIsWho, AMiner HITL, HUMO).
4. A newly found implementation fact weakens the "evidence-guided, five-signal" description: in the committed live-candidate path only **two** signals can be available (three if the caller supplies active years). This must shape how RQ2 is framed. See section 9.

## 1. RQ2 (primary; unchanged)

> How effectively does HAMMER retrieve author candidates, and how do its evidence-guided decision gates balance automatic assignment precision against coverage?

Approved sub-structure (from `STAGE2_RESEARCH_DESIGN.md`): **RQ2a** candidate retrieval (R0/R1/R2 query strategies; Recall@k, MRR); **RQ2b** selective resolution on one frozen pool (name-only forced top-1, full-evidence forced top-1, full-evidence selective). Hypotheses H2a and H2b are as approved. Nothing here alters them.

## 2. RQ1 (conditional; unchanged)

> How reliably does HAMMER identify duplicate scholarly publication records while preserving distinct publications?

Remains conditional. The edition-regex defect **is still present at the inspected commit** (two U+0008 bytes in `_EDITION_RE`, `backend/deduplication/engine.py:90-93`; byte count verified). No paired V1/V2 replay exists. Therefore RQ1 must **not** be presented as a confirmed contribution. Prior work for context: `fellegi1969recordlinkage`, `forbes2024deduplicator`, and (metadata-only) `elmagarmid2007duplicate`, `kopcke2010frameworks`.

## 3. Synthesis of the relevant literature

### 3.1 Author name disambiguation is a mature field with several task forms
- A literature review organises methods into grouping (similarity/clustering) and assignment (classification) families (`rodrigues2024andreview`, per prior audit). Surveys exist for the general field and graph-based methods (`ferreira2012brief`, `debonis2023graph`, `sanyal2021review`; titles verified, content not read).
- Large-scale systems exist: PubMed Computed Authors (`tian2024pubmedcomputedauthors`), AMiner with clustering, maintenance and human annotators (`zhang2018aminerhitl`), and AggAND (`zhang2021aggand`).

### 3.2 Benchmarks and ground truth are recognised weaknesses
- Models trained on one AND dataset often transfer poorly to others, because each covers a narrow slice (`subramanian2021s2and`, abstract-level).
- Benchmarks exist at scale (`chen2023whoiswho`, >1 M papers) and from ORCID/DOI evidence (`zhang2023lagosand`). Data-set quality has been analysed (`muller2017datasets`, metadata only; `kim2018dblp`, metadata only).
- GSD1900 is a pairwise MEDLINE gold standard (`vishnyakova2019gsd1900`), not a candidate-ranking set.

### 3.3 Candidate generation and assignment
- Blocking/filtering is a studied stage of entity resolution (`papadakis2020blocking`, metadata only).
- Real-time *assignment* of a new paper to candidate authors is an explicit task in WhoIsWho (`chen2023whoiswho`, abstract plus a search summary). CONNA matches a paper to the best existing person and then decides whether to assign or create a new person (`chen2020conna`, abstract-level).
- **Not found:** an AND paper that reports Recall@k (or equivalent) for an author-candidate stage *separately* from the final assignment. This is an absence in four searches and one skim, not a finding about the field.

### 3.4 Evidence-based resolution
- Prior systems combine name, coauthor, title/venue and affiliation evidence (`boukhers2024deepdblp`, `zhang2021aggand`, `choi2024heterogeneoussites`, `tian2024pubmedcomputedauthors`).
- Metadata-conditioned scheme choice exists (`choi2024heterogeneoussites`).
- Probabilistic combination of evidence is established (`fellegi1969recordlinkage`; `tang2012unified`, metadata only). HAMMER's fixed-weight heuristic is not a validated probabilistic model.
- Institution linking is a separate, tool-supported task (`duran-silva-etal-2024-affilgood`, `kallipoliti2025affro`).

### 3.5 Selective prediction, abstention and human review
- Reject-option and selective classification are established general frameworks, with risk-coverage as the standard evaluation language (`chow1970reject`, `elyaniv2010foundations`, `geifman2017selective`, `geifman2019selectivenet`, `hendrickx2024reject`; most metadata-only).
- Human-in-the-loop AND is deployed (`zhang2018aminerhitl`). Human/machine workload splitting with precision/recall targets exists for entity resolution generally (`chen2018humo`, `hou2018rhumo`, `wang2012crowder`).
- **Not found:** an AND paper reporting automatic-decision precision against automatic coverage (a risk-coverage curve) with an explicit manual-review and unresolved split. Again, a statement about a limited search.

### 3.6 Metadata integration and provenance
- Multi-source aggregation for AND is prior art (`zhang2021aggand`, `choi2024heterogeneoussites`, `priem2022openalex`). Source coverage differs and is task-dependent (`culbert2025openalexcoverage`, `gerasimov2024datasetcoverage`). Provenance has a formal vocabulary (`buneman2001whyandwhere`).

## 4. Comparison of prior approaches (what is and is not comparable)

| Dimension | Typical prior work | HAMMER | Comparable? |
|---|---|---|---|
| Unit of task | Clustering of mentions (S2AND, WhoIsWho), pairwise (GSD1900), or assign-to-person (CONNA, WhoIsWho online) | A query name (plus optional institution) against a provider's author-profile search; candidates are OpenAlex author profiles | Not directly. HAMMER resolves a *query to a provider profile*, not mentions to clusters. |
| Evaluation metric | B3 F1, pairwise accuracy, per-author F1 | Recall@k, MRR; automatic precision, coverage, selective risk | Different families. Do not compare numbers across them. |
| Learned vs rule-based | Often learned (neural, random forest, probabilistic) | Fixed-weight heuristic plus thresholds | Different; HAMMER's weights are unvalidated. |
| Open-world / new author | Handled by CONNA's new-person decision; flagged as a limitation in DBLP work | `unresolved` outcome; candidate pool restricted to OpenAlex | Partially. `unresolved` does not mean the person is absent. |
| Human review | AMiner annotators; HUMO workload splitting | `manual_selection_required` plus a review UI | Concept shared; HAMMER has no quality guarantee. |
| Ground truth | Curated data sets, ORCID/DOI-derived labels | Planned: independent Stage A labels, blinded Stage B mapping (proposed, not done) | Only after annotation is completed. |

## 5. What the literature already establishes

- Author disambiguation is hard, mature and multi-formed; single-dataset results transfer poorly.
- Multi-signal, multi-source evidence, new-author handling, online assignment and human-in-the-loop operation all exist in published systems.
- Selective prediction with risk-coverage evaluation is a standard general framework.
- Affiliation-to-organisation linking is an established subtask.

## 6. What remains insufficiently evaluated or addressed (hypotheses, not findings)

All of the following are **"Not established from the sources inspected"**, i.e. I did not find it, and a fuller search could overturn it:

1. A report that evaluates **candidate retrieval** (Recall@k/MRR) and **selective assignment** (automatic precision at stated coverage) **on the same frozen candidate pool**, with unresolved and manual-review outcomes counted explicitly.
2. A conservative-assignment evaluation in which the **denominator includes provider failures and empty pools**, so that coverage is not inflated by dropping hard cases.
3. A *small, applied, openly protocolled* evaluation of this kind for a **scholarly metadata aggregator** (as opposed to a web-scale system).

## 7. The narrowest defensible research gap

> Published author-disambiguation work evaluates grouping or assignment accuracy with F1-style measures; general selective-prediction work supplies risk-coverage evaluation but not for author identity; and published human-in-the-loop systems describe review workflows. **It is not established from the sources inspected that prior work reports retrieval-stage recall and selective automatic-assignment precision-versus-coverage jointly, on one frozen candidate pool, with manual-review, unresolved and provider-failure outcomes counted in the denominator.**

This is a statement about *reporting and evaluation design*, not about a new technique. It must be re-tested by the follow-up searches in `LITERATURE_SEARCH_LOG.md` section 9 before it appears in the paper as anything stronger than "to our knowledge, within the sources we reviewed".

## 8. How HAMMER addresses that gap (design, not results)

- The approved Stage 2 protocol separates retrieval from decision (`STAGE2_RESEARCH_DESIGN.md`, `METRIC_DEFINITIONS.md`) and keeps provider failures and empty pools in the end-to-end denominator.
- The code distinguishes `auto_selected`, `manual_selection_required` and `unresolved`, and persists scores, margins and per-signal evidence (`PAPER_IMPLEMENTATION_FACTS.md` section 9-10).
- The protocol requires one frozen pool, identity-disjoint splits and independent labels. **None of this has been executed.** There is no result.

## 9. What HAMMER does not establish (and a code-level caveat)

- No result. No pilot, no annotation, no frozen dataset, no experiment manifest exists in the repository.
- No evidence that HAMMER's weights or thresholds are good, calibrated or better than a name-only or learned baseline.
- No evidence about semantic retrieval, explanation quality or citation faithfulness.
- **Caveat on "five-signal":** static reading shows that in the committed live-candidate path, `sample_publications` and `coauthor_summary` are always `None` (`candidates.py:265,267`), so `publication_overlap` and `coauthor_overlap` are `unavailable` for every live candidate. The app UI and the Day 5 evaluation script send only name and institution (`frontend/src/services/api.js:62`; `backend/scripts/run_day5_e2e_evaluation.py:92`). Temporal compatibility needs `active_year_start/end` in the request context. So the effective evidence is **two signals** (name, institution), or three with caller-supplied years. This is a reading of the code, not a run, and must be confirmed by Codex before the paper says "five signals" without qualification. It does not change any approved decision, but it changes what the paper may honestly call "evidence-guided".
- Stage 2 protocol text says evidence inputs include local database/index state for publication, coauthor and temporal evidence (`EXPERIMENT_PROTOCOL_RQ2.md`). The code reads none of that for evidence (`evidence.py`). This is a protocol/code discrepancy for the owner to settle.

## 10. Potential contribution statements (candidates only; none approved)

Ordered from safest to riskiest. Each is a *hypothesis for ChatGPT to review*.

| Tier | Contribution statement | Type | Status |
|---|---|---|---|
| A | A provenance-retaining pipeline that keeps work-level matching separate from person-level resolution and exposes a three-outcome decision with persisted per-signal evidence. | **Engineering** | Describable now (implementation exists; no performance claim). |
| B | A frozen-pool evaluation protocol that reports retrieval recall and selective automatic precision/coverage separately, counting failures and empty pools. | **Methodological (applied)** | Protocol approved; unexecuted. |
| C | An empirical estimate of HAMMER's automatic-assignment precision and coverage on an independently labelled set. | **Empirical** | Impossible until annotation and a main study exist. |
| D | Evidence that selective gates reduce risk versus forced top-1 at useful coverage. | **Empirical (H2b)** | Impossible until a main study exists. |
| Avoid | Novel algorithm; first multi-source resolver; first HITL AND; zero false merges; semantic retrieval improves identity decisions. | n/a | Unsupported or contradicted. |

**Engineering contribution vs research contribution:** A is engineering. B is a modest methodological contribution. C and D would be the research contribution and do not exist yet. The paper must not let A be read as C or D.

## 11. Novelty risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| CONNA-type "assign vs new person" decision stage | Direct precedent for a decision after candidate ranking | Read CONNA fully; describe HAMMER's gates as a conventional rule-based variant. |
| HUMO / r-HUMO / CrowdER | Quality-controlled human/machine splitting exists for entity resolution | Do not claim the manual-review pathway is new; claim only what is measured. |
| WhoIsWho online assignment | Assignment of a new paper to candidates is already a benchmark task | Position HAMMER's task as query-to-provider-profile resolution, not paper assignment. |
| Selective prediction is general ML | Risk-coverage is standard | Cite as framework; contribution is application and reporting only. |
| Search was limited | An existing joint-reporting paper could exist | Do the follow-up searches before any novelty wording. |
| Effective signals are fewer than five | "Evidence-guided, five-signal" may be challenged | State effective signals per query; report availability rates. |
| OpenAlex both candidate source and gold namespace | Circularity risk | Already addressed by the Stage A/B protocol; must be executed. |
| Heuristic score read as probability | Misleading | Use "heuristic score"; cite calibration literature only as caution. |
| Tiny pilot, small main study | Wide uncertainty | Report counts, denominators and exact intervals only (approved). |

## 12. Suggested related-work subsection structure

Consistent with `PROPOSED_RELATED_WORK_STRUCTURE.md` (kept; not replaced), reordered around RQ2:

1. **Author name disambiguation: task forms and benchmarks** (clusters 1-2): `rodrigues2024andreview`, `subramanian2021s2and`, `chen2023whoiswho`, `vishnyakova2019gsd1900`, `zhang2023lagosand`. State what is not comparable to HAMMER.
2. **Candidate generation and assignment** (cluster 3): `papadakis2020blocking`, `chen2020conna`, `chen2023whoiswho`, `priem2022openalex`.
3. **Evidence signals and weighting** (cluster 4): `boukhers2024deepdblp`, `zhang2021aggand`, `choi2024heterogeneoussites`, `fellegi1969recordlinkage`; affiliation sub-paragraph `duran-silva-etal-2024-affilgood`, `kallipoliti2025affro`.
4. **Abstention, selective prediction and human review** (cluster 5): `chow1970reject`, `geifman2019selectivenet`, `hendrickx2024reject`, `zhang2018aminerhitl`, `chen2018humo`.
5. **Metadata integration, provenance and publication deduplication** (cluster 6): `culbert2025openalexcoverage`, `buneman2001whyandwhere`, and (only if RQ1 is retained) `forbes2024deduplicator`.
6. **Gap and study focus**: the section 7 statement, with the "within the sources reviewed" qualifier.

Do not include `petroni2021kilt`, `guo2017calibration` or `gerasimov2024datasetcoverage` unless an argument in the paper needs them.

## 13. Claims to avoid

- "HAMMER is novel", "first", "state of the art", "outperforms".
- "92% top-1", "0% false merge", "88% abstention" (unsupported October figures).
- "52/56 top-1" or "MRR 0.9286" as a result (historical re-scoring, not a controlled run).
- "13/13 accurate" (12 Confirmed + 1 Probable; keep categories).
- "Zero false positives/negatives" for deduplication.
- "Five-signal evidence resolver" without the effective-signals qualification.
- "Calibrated confidence" or "probability" for the score; the API's `High/Medium/Low` label (`main.py:218`) is a hard-coded threshold, not calibrated.
- "Semantic retrieval improves identity resolution" or "faithful citations".
- "Cosine/Euclidean `1 - d/2`" (stale documentation); the code uses cosine distance with `1 - d`.
- "Gemini 2.5 Flash was used" (model is read from environment).
- Any statement that a literature absence proves a gap.

## 14. Supporting references by argument

| Argument | References |
|---|---|
| AND is mature, multi-formed | `rodrigues2024andreview`, `ferreira2012brief`, `debonis2023graph` |
| Benchmarks vary and transfer poorly | `subramanian2021s2and`, `chen2023whoiswho`, `zhang2023lagosand`, `muller2017datasets` |
| GSD1900 is pairwise, not HAMMER | `vishnyakova2019gsd1900`, `tian2024pubmedcomputedauthors` |
| Multi-source/multi-signal AND has prior art | `zhang2021aggand`, `choi2024heterogeneoussites`, `boukhers2024deepdblp` |
| Assign-or-new-person decision exists | `chen2020conna`, `chen2023whoiswho` |
| Human-in-the-loop exists | `zhang2018aminerhitl`, `chen2018humo`, `wang2012crowder` |
| Selective prediction framework | `chow1970reject`, `elyaniv2010foundations`, `geifman2017selective`, `geifman2019selectivenet`, `hendrickx2024reject` |
| Score is heuristic, not probability | `fellegi1969recordlinkage` (contrast), `guo2017calibration` (caution) |
| Affiliation linking is a distinct task | `duran-silva-etal-2024-affilgood`, `kallipoliti2025affro` |
| Source coverage and provenance | `priem2022openalex`, `culbert2025openalexcoverage`, `buneman2001whyandwhere` |
| Work-level dedup differs from person-level | `fellegi1969recordlinkage`, `forbes2024deduplicator` |

Every row above must be re-checked against the actual paper text before a specific claim is attributed to it.
