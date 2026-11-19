# HAMMER — Stage 0/1 Research Ideation Proposal

**Status:** Proposed; owner approval required before Stage 2  
**Audit basis:** committed Git HEAD d41378c on main, 19 November 2026  
**Scope:** Repository/artifact inspection only. No application code was changed; tests and benchmarks were not run.

## Recommendation

Position HAMMER as an **applied systems paper** on provenance-preserving scholarly metadata integration with conservative, evidence-guided identity decisions. Its defensible contribution is architectural and methodological: separate publication matching from author identity resolution, retain source evidence, and allow abstention. Do not claim a new foundational ML algorithm.

Make **author candidate generation and selective author resolution (RQ2)** the primary empirical question. Keep **publication deduplication (RQ1)** as a secondary question only after its implementation and historical results are reconciled. Describe retrieval and LLM explanation as supporting system features; defer RQ3/RQ4 as research questions because current evidence does not establish ranking quality or semantic claim support.

## Stage 0 — Audit findings

The audited Git checkout is Documents/COLLEGE WORK/YEAR LONG PROJECT/SYSTEM/FINAL-YEAR-PROJECT, commit d41378c, branch main tracking origin/main. The working tree has local modifications, including backend/database.py; its working copy removes author-resolution ORM classes present at HEAD. Per the owner’s instruction, committed HEAD is the intended baseline. I left local changes untouched and based implementation descriptions on HEAD. Modified .DS_Store and __pycache__ files also remain untouched.

The repository contains a FastAPI/SQLAlchemy backend, React frontend, scholarly-source ingestion, V1/V2 publication deduplication, OpenAlex author candidates and deterministic evidence scoring, Chroma dense retrieval, and optional Gemini explanation. It also contains evaluation scripts, historical JSON results, a 100-query author benchmark, experiment notes, claim and reference audits, figure material, and a dataset protocol with review/split templates.

No Word manuscript, BibTeX library, or LaTeX manuscript was found. The current revised draft is Markdown. Preserve the existing draft, claim matrix, and reference audit; this proposal does not replace them.

### Findings that block strong claims

1. **Dedup results conflict.** The Phase 4 aggregate reports V2 as TP=33, FP=0, TN=15, FN=0 over 48 scored pairs; two pairs are uncertain. Earlier verification reports V1 as 32/2/13/1, while later notes report V2 as 33/0/15/0. The aggregate JSON does not contain per-pair predictions for both versions. Replay both against the same frozen labels before claiming improvement.
2. **Committed edition detector defect.** backend/deduplication/engine.py contains U+0008 backspace characters in the edition regex where word-boundary escapes appear intended. Ordinary edition strings will not match this detector. Correct and re-evaluate before claiming edition-conflict protection. This is source inspection, not a test result.
3. **Author claim overstates accuracy.** The sealed 100-query benchmark has 13 auto-selected cases: 12 Confirmed and 1 Probable. The existing claim matrix’s “13/13 strictly accurate” wording is too strong. Keep label category and denominator explicit.
4. **Retrieval formula documentation is stale.** The Chroma collection is configured for cosine distance and _search uses 1 − d. The header in backend/rag/retrieval.py describes Euclidean distance and 1 − d/2. Align docs and establish the application call path before publishing an equation or threshold result. Retrieval implementation is present in both rag/retrieval.py and explanation/synthesis.py, so architecture figures need a resolved source path.
5. **Gemini runtime is not pinned.** backend/.env.example names gemini-2.5-flash, but the runtime reads GEMINI_MODEL from the environment. The example does not prove which model generated historical results.
6. **Existing DB/index paths need a canonical identity.** Use the Git version and existing manifest/hash evidence to identify the intended snapshot. Do not create another checkout or unmanaged copy.

## Positioning and contribution

**Problem:** inconsistent, incomplete metadata across scholarly providers can create duplicate publication records and mistaken author links, damaging search and downstream analytics. HAMMER combines aggregation, provenance, matching, author review, and discovery in one application.

**Existing work:** record linkage, publication deduplication, author disambiguation, lexical/dense retrieval, and retrieval-grounded generation are established areas. The repo’s reference audit is a starting point, not a completed literature review. Do not claim that no system already integrates these capabilities or that familiar components become a novel algorithm merely by combination.

**Defensible project-specific gap:** evaluate how publication equivalence and author identity are kept as separate decisions in one provenance-aware workflow, and whether conservative decision gates change error/coverage behavior on curated benchmarks. This is a bounded study focus, not a field-wide absence claim.

**Potential contributions, if verified:**

- Integration architecture retaining provider provenance and separating publication records from author decisions.
- Paired evaluation of legacy similarity matching against deterministic safeguards.
- Staged author retrieval and identity decision with review/unresolved outcomes.
- Reproducible artifacts and explicit limits on evidence and claims.

These are architectural, methodological, and empirical contributions. There is no supported algorithmic novelty claim.

## Research questions

| Question and recommendation | Features, data, baselines, metrics, confounders, feasibility |
|---|---|
| **RQ1 — Deduplication:** Do deterministic safeguards reduce errors versus the legacy weighted-similarity baseline? **Keep conditionally as secondary.** | The implementation and V1 baseline exist. Historical set: 50 pairs, 48 binary-scored and 2 uncertain. Replay both versions on identical pairs. Report precision, recall, F1, false-positive rate, paired disagreements, error categories, and exact denominators. The small, curated set risks rule overfitting; conflicting V1 records and the edition-regex defect make the reported delta unverified. |
| **RQ2 — Author retrieval/resolution:** How effectively are gold profiles retrieved, and how do evidence gates trade automatic coverage against precision? **Retain as primary; keep retrieval and decision metrics separate.** | OpenAlex candidates and five-signal scoring/gates exist. Historical V3: 100 queries, 56 gold (50 Confirmed, 6 Probable), plus controls. Compare exact/normalized-name retrieval with supported candidate strategies; compare always-top-1 or name-only with evidence gates on identical frozen candidates. Retrieval: Recall@1/5/10, MRR, candidate count. Decision: auto precision/coverage, review/unresolved rates, selective risk, Confirmed vs Probable. Gold and candidates are OpenAlex-derived, potentially inflating coverage; the query set is not random. |
| **RQ3 — Retrieval ranking:** Does dense/hybrid search improve discovery over lexical search? **Defer as an RQ.** | Dense retrieval exists; the current evaluation is a 20-query in-corpus/out-of-domain threshold check, not ranking relevance. No BM25 baseline or graded relevance pool was found. A valid study needs frozen queries, blinded judgments, development/test separation, BM25/dense/hybrid runs, nDCG@k, MRR, Recall@k, and latency. Keep the feature; do not claim improved ranking. |
| **RQ4 — Evidence-grounded explanations:** Do validation mechanisms reduce unsupported claims? **Defer as an RQ; describe only tested structural safeguards.** | Nine adversarial cases test behaviors such as identifier containment and malformed outputs. They do not measure semantic support. A study needs human claim-to-source judgments (supported/partial/unsupported/contradicted), agreement reporting, controlled prompts/models, and comparison conditions. Identifier membership is not entailment. |

## Testable hypotheses

- **H1 (RQ1):** On the same 48 binary pairs, V2 will produce fewer false-positive merges than V1 without reducing recall. Reject if paired replay does not show fewer false positives or recall falls beyond a pre-registered tolerance. Report the two uncertain pairs separately; do not generalize beyond this challenge set.
- **H2a (RQ2 retrieval):** On a frozen identity-group split, normalized/multi-strategy retrieval will improve Recall@k or MRR over exact-name retrieval. Reject if held-out differences are non-positive or too uncertain to support the expected effect.
- **H2b (RQ2 decision):** On frozen candidate pools, evidence gates will improve precision among auto-decisions over always-top-1, at lower coverage. Reject if precision does not improve or the result depends on counting Probable as Confirmed. Tune thresholds on development data only.
- RQ3/RQ4 hypotheses are out of current scope until their missing datasets and comparisons exist.

## Essential experiments and changes

1. **Dedup replay:** Correct the edition detector; freeze the 50 pairs, labels, and provenance; replay V1/V2; retain per-pair predictions and report 48 decided plus 2 uncertain cases. Expand only if independent labels can be obtained.
2. **Author study:** Freeze candidate snapshots, document gold-label provenance, sample without viewing predictions, split by author identity, and report retrieval recall separately from selective precision/coverage with uncertainty and error review. docs/evaluation/dataset.md and its templates are a useful protocol base; completed independent held-out judgments are not evident in that directory.
3. Do not add BM25/hybrid or human claim-support experiments to the core paper unless scope expands; they are substantial new studies.

Necessary research-integrity work: fix/replay the dedup rule; reconcile V1/V2 records; align retrieval documentation and choose one canonical implementation path; pin model/version in run metadata; correct author-accuracy wording. These do not justify new services or providers.

**Retain:** Git architecture, source provenance, SQLite record store, rebuildable Chroma index, separate publication/author decisions, abstention/review, evaluation scripts, dataset protocol, and existing audits. Reuse existing claim/reference registers.

**Do not claim:** universal zero false merges, universal author accuracy, hallucination-free generation, dense search outperforming lexical search, or retrieval changing author-resolution decisions.

**Main validity threats:** small hand-curated samples; potential tuning on evaluation examples; OpenAlex-derived gold/candidates; no blind multi-annotator relevance or claim-support judgments; code/document/result drift; multiple DB/index paths and runtime overrides; denominator or Probable/Confirmed conflation.

## Recommended paper structure

1. Introduction and bounded problem  
2. Related work: linkage, author disambiguation, review/abstention  
3. Architecture and provenance model  
4. Methods: deduplication and staged author resolution  
5. Evaluation protocol, data, baselines, metrics  
6. Results: RQ1 if reconciled, then RQ2 retrieval and selective decisions  
7. Error analysis/discussion  
8. Limitations, reproducibility, conclusion  

Describe retrieval and citation-ID checking as system capabilities with bounded evidence. Draft the abstract after results and approved claims.

## Proposed workspace and Word workflow

Use one research workspace inside the existing docs/research/ in this Git checkout; do not create another checkout. Reuse the existing claim matrix, reference audit, and draft notes. Proposed additions, pending approval:

~~~text
docs/research/
  HAMMER_STAGE0_STAGE1_IDEATION_PROPOSAL.md
  decisions/DECISION_REGISTER.md
  protocols/
  datasets/                 # manifests/labels; one canonical snapshot identity
  experiments/<run-id>/     # config, commit, inputs, metrics, raw outputs
  figures/figure-register.csv and source/
  tables/table-register.csv
  equations/equation-register.md
  references/HAMMER.bib
  CLAIM_EVIDENCE_MATRIX.md  # reuse existing file
  revision-history.md
  manuscript/HAMMER_research_paper.docx  # one living manuscript
  exports/                  # release exports only
~~~

No DOCX or BibTeX library currently exists. If approved, the DOCX becomes the single living manuscript, built section by section with approval and a revision log. Keep the existing Markdown draft as historical material, not a second live manuscript. Use Git history for revisions and generate a PDF only for an approved release; do not create versioned manuscript copies.

## Decision brief — approval before Stage 2

**Recommended direction:** RQ2 primary; RQ1 secondary only after its implementation/results are reconciled; defer RQ3 and RQ4 as research questions. This supports a coherent systems paper on safe scholarly metadata integration while retaining retrieval and explanation as supporting features.

Please approve or revise this direction. After approval, Stage 2 should settle final RQs, hypotheses, denominators, and dataset protocol before new experiments or manuscript sections begin.

