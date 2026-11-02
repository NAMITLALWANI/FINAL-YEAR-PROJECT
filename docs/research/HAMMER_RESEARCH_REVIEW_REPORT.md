# HAMMER — Research Paper Critical Peer Review & Scientific Rigour Audit

**Document ID:** HAMMER_RESEARCH_REVIEW_REPORT.md  
**Audit Date:** 2026-11-02  
**Role:** Critical Senior Peer Reviewer (Information Retrieval, Digital Libraries, and Data Engineering)  
**Subject:** Scientific audit and publication-readiness assessment of the revised research manuscript for **HAMMER (Hybrid Academic Metadata Aggregator and Evidence-Guided Author Entity Resolution System)**.

---

## 1. Skeptical Reviewer Examination (Answers to the 12 Critical Questions)

### 1. What is the actual research contribution?
**Assessment:** The genuine research contribution of HAMMER is **architectural and methodological**, rather than a novel foundational machine learning algorithm. Specifically, HAMMER contributes:
- A formally decoupled architecture enforcing SQLite as the authoritative transactional system of record and ChromaDB as a derived, rebuildable retrieval index.
- A deterministic deduplication engine (V2) that wraps heuristic string metrics in five domain-specific veto guards (DOI divergence, edition keywords, multi-year gaps, prefix matching, and title floors), empirically eliminating false positive merges on boundary-condition challenge pairs.
- An evidence-guided author resolution workflow that uses non-linear margin and dominance gates to prioritize precision over recall, intentionally treating safety abstention (`manual_selection_required` and `unresolved`) as a valid, high-value outcome to protect downstream academic graphs from irreversible entity corruption.
- A syntactic citation containment validator that deterministically rejects hallucinated or unverified document attributions in LLM-generated summaries.

### 2. Is the novelty sufficiently distinguished from existing work?
**Assessment:** **Yes, when framed accurately.** HAMMER does not claim to outperform offline machine learning disambiguation frameworks (e.g., S2AND, WhoIsWho) on web-scale static graphs. Instead, it distinguishes itself as an **online, operational, human-in-the-loop streaming architecture** designed for production environments where false merges carry asymmetric real-world penalties and external API integrations require strict provenance tracking.

### 3. Are the research questions answerable using the experiments?
**Assessment:** **Yes, within their revised, strictly scoped boundaries:**
- *RQ1 (Semantic Retrieval Filtering):* Fully answered regarding gibberish and out-of-domain rejection thresholds ($\tau = 0.35$ on 20 queries), but explicitly acknowledged as not constituting a scaled comparative benchmark against BM25.
- *RQ2 (Candidate Retrieval vs. Decision Gates):* Fully answered using Benchmark V3 Sealed (100 queries). The experiments cleanly prove that candidate generation achieves 100% recall on confirmed queries, while decision gates achieve 100% precision by abstaining on 87% of ambiguous cases.
- *RQ3 (Generative Synthesis Attribution):* Answered at the *syntactic citation containment* level (9 adversarial attack vectors blocked/sanitized), while explicitly noting that *semantic entailment* remains unproven without human annotation.

### 4. Are the datasets sufficiently described?
**Assessment:** **Yes.** The revised manuscript provides exact, granular breakdowns:
- Deduplication benchmark: 50 pairs across 7 categories (33 duplicates, 15 distinct, 2 uncertain).
- Benchmark V3 Sealed: 100 queries (56 gold profiles: 50 Confirmed, 6 Probable; 44 controls).
- Semantic benchmark: 20 queries (14 in-corpus, 6 out-of-domain controls).
- Citation safety suite: 9 adversarial prompt and injection scenarios.

### 5. Are the metrics correctly interpreted?
**Assessment:** **Yes. Critical conflations have been eliminated:**
- Candidate harvesting recall (100% on confirmed queries) is no longer conflated with automatic resolution accuracy.
- Deduplication precision and recall (100% across 48 decided pairs) explicitly document the neutral exclusion of the 2 boundary pairs.
- Automatic selection rate (13%) is correctly reported as a measure of conservative coverage rather than a system failure.

### 6. Are the results reproducible?
**Assessment:** **Yes.** All underlying experimental artifacts, evaluation scripts (`evaluate_benchmark.py`, `run_phase4_evaluations.py`), and frozen benchmark files (`author_resolution_benchmark_100_v3_sealed.json`, `deduplication_evaluation_50.json`) are cryptographically sealed with SHA-256 hashes in `docs/finalisation/week1/reproducibility_manifest_v3.json` and committed to the Git repository.

### 7. Are the comparisons fair?
**Assessment:** **Yes.** Deduplication Engine V2 is compared directly against the legacy V1 baseline on the exact same challenge dataset, clearly detailing why V1 failed on Sutton & Barto (edition conflict) and Deng & Yu (keyword overlap) while V2 succeeded.

### 8. Are the conclusions supported by results?
**Assessment:** **Yes.** The revised conclusions claim only what is empirically demonstrated: elimination of false merges on the tested benchmark pairs, high candidate retrieval coverage, conservative precision-first resolution, and syntactic citation defense.

### 9. Are the limitations adequately disclosed?
**Assessment:** **Exemplary.** The manuscript dedicates Section 7 to an unvarnished analysis of sample size constraints, dependence on OpenAlex graph cleanliness, the absence of multi-annotator graded IR pools, and scraper brittleness.

### 10. Could a reviewer reproduce the main experiments?
**Assessment:** **Yes.** By executing the frozen evaluation scripts against the sealed JSON datasets in the repository, any reviewer can reproduce the exact tables and metrics reported in the paper.

### 11. Are any claims stronger than their supporting evidence?
**Assessment:** **No.** All prohibited claims (e.g., "zero hallucinations", "100% solved disambiguation", "absolute zero false merges guarantee") have been rigorously excised and replaced with bounded, verifiable statements.

### 12. Does the paper distinguish engineering implementation from research findings?
**Assessment:** **Yes.** Architectural decisions (FastAPI routes, SQLite ORM schemas, circuit breakers) are presented as software infrastructure supporting the empirical research questions, rather than masquerading as algorithmic novelties.

---

## 2. Category Ratings (Scored out of 10)

| Evaluation Category | Score (1–10) | Reviewer Rationale & Justification |
|---|:---:|---|
| **Problem Significance** | **8.5 / 10** | Metadata fragmentation and author entity corruption are major, pervasive problems in digital scholarship, institutional analytics, and bibliometrics. |
| **Novelty** | **6.5 / 10** | The core algorithms rely on established techniques (Jaro-Winkler, S-BERT embeddings, heuristic rules). The novelty lies in the *system synthesis, deterministic veto logic, and human-in-the-loop abstention architecture*. |
| **Technical Depth** | **8.0 / 10** | Comprehensive mathematical formulation of deduplication vetoes, multi-signal scoring, non-linear decision gates, and cryptographic state management. |
| **Methodological Rigour**| **8.5 / 10** | Clean experimental separation between deduplication, candidate recall, decision gates, vector retrieval, and LLM containment; complete eradication of metric conflation. |
| **Experimental Quality** | **7.0 / 10** | High precision and excellent forensic failure analysis, but constrained by modest sample sizes (50 dedup pairs, 100 author queries, 20 semantic queries). |
| **Reproducibility** | **9.5 / 10** | Outstanding. Sealed JSON datasets, automated pytest suite (78 passing tests), and cryptographic SHA-256 manifests ensure exact verification. |
| **Literature Review** | **8.0 / 10** | Foundational and modern works correctly cited (Fellegi-Sunter, S2AND, WhoIsWho, RAG, S-BERT, OpenAlex); all 9 DOIs/URLs independently verified. |
| **Writing Quality** | **8.5 / 10** | Formal, precise academic prose; free of marketing superlatives; consistent terminology and clear architectural descriptions. |
| **Overall Research Maturity**| **8.0 / 10** | A rock-solid, methodologically sound applied research manuscript that sets a benchmark for undergraduate engineering projects. |

---

## 3. Venue Suitability Assessment

### A. Final-Year BTech Evaluation / Viva Examination
**Rating: OUTSTANDING (10 / 10)**  
The paper represents an exceptionally strong final-year BTech project. It far exceeds typical undergraduate projects by demonstrating end-to-end full-stack software engineering, deep architectural discipline, rigorous empirical benchmarking, failure forensic analysis, and comprehensive automated testing (78 tests). It is fully defensible before any academic viva panel.

### B. Internal Academic Presentation / Departmental Colloquium
**Rating: HIGHLY RECOMMENDED (9.5 / 10)**  
The clear problem formulation, architectural diagrams, and ablation comparisons between V1 and V2 provide an ideal narrative for departmental presentations and academic seminars.

### C. Student Research Conference (e.g., IEEE/ACM Student Research Competition)
**Rating: READY FOR SUBMISSION (8.5 / 10)**  
The manuscript is immediately competitive for student research tracks and regional computer science conferences. Its emphasis on safety through abstention and reproducible benchmarking provides strong competitive differentiation.

### D. Premier Peer-Reviewed Conference / Journal (e.g., JCDL, CIKM, SIGIR)
**Rating: BORDERLINE / WORK-IN-PROGRESS (6.5 / 10)**  
While methodologically sound, a top-tier international conference would require expanding the empirical datasets from tens/hundreds of samples to thousands, conducting double-blinded human relevance evaluations (for nDCG@k), benchmarking against S2AND models on the same data, and conducting multi-annotator human factuality evaluations on LLM summaries.

---

## 4. Five Highest-Priority Actions for Premier Publication Readiness

1. **Scale the Deduplication Benchmark:** Expand the current 50-pair challenge dataset to at least 500–1,000 diverse publication pairs across multiple academic disciplines (e.g., PubMed, IEEE, SSRN).
2. **Double-Blinded Human Relevance Judgments:** Create a 50-query semantic retrieval pool with multi-annotator graded relevance labels (0, 1, 2) to compute standard Information Retrieval metrics (nDCG@10, MAP).
3. **Blinded Human Factuality Evaluation:** Conduct a blinded multi-annotator study over 100 LLM-generated synthesis summaries to quantify genuine semantic claim entailment and hallucination rates beyond syntactic ID containment.
4. **Comparative Machine Learning Baselines:** Implement and compare HAMMER's deterministic resolver against an established machine-learned baseline (such as S2AND's pairwise classifier or an agglomerative S-BERT clusterer) on the same evaluation dataset.
5. **Cross-Domain Generalization Testing:** Evaluate candidate generation and deduplication performance on non-CS corpora (e.g., biomedical literature with complex consortium authorship) to prove cross-domain robustness.
