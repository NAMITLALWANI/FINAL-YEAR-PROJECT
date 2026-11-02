# HAMMER — Research Paper Revision Notes & Delta Rationale

**Document ID:** HAMMER_RESEARCH_PAPER_REVISION_NOTES.md  
**Audit Date:** 2026-11-02  
**Status:** Revision Specification & Change Log  
**Author:** Senior Technical Paper Editor & Methodology Reviewer

---

## 1. Summary of Structural and Scientific Changes

The original draft (`docs/research-paper.md`) served as an exploratory early description of HAMMER. While it accurately established several key architectural principles (such as SQLite as the system of record and the distinction between citation containment and semantic entailment), it lacked empirical depth, contained obsolete application database counts (citing 696 publications from an outdated run), referenced unadjudicated baseline numbers, and did not reflect the significant engineering and experimental achievements completed during Week 1 (Days 1–7).

The revised manuscript (`docs/research/HAMMER_RESEARCH_PAPER_REVISED_DRAFT.md`) transforms the paper into a scientifically rigorous, defensible, and methodologically precise conference-grade draft.

---

## 2. Key Sections Rewritten vs. Retained

| Section | Treatment | Rationale & Specific Modifications |
|---|---|---|
| **Title & Abstract** | **Completely Rewritten** | Expanded to explicitly reflect the hybrid architecture: multi-source aggregation, deterministic entity resolution, semantic retrieval, and provenance-aware synthesis. Incorporates exact empirical findings (100% precision on 48 decided dedup pairs, 100% confirmed author recall, 13 automatic decisions). |
| **Problem Statement & Motivation** | **Substantially Expanded** | Sharply distinguished publication-level deduplication (document identity) from author-level entity resolution (real-world personhood). Formulated the risk asymmetry between false merges and false splits in scholarly citation indices. |
| **Research Questions (RQ1–RQ3)** | **Critically Re-scoped** | Re-aligned RQs with verifiable empirical evidence: RQ1 addresses semantic cosine filtering thresholds (20 queries); RQ2 evaluates multi-signal candidate generation and conservative resolution (100 queries, sealed Benchmark V3); RQ3 evaluates structural citation containment defense against hallucination. |
| **System Architecture** | **Rewritten & Standardized** | Formalized the separation between the authoritative relational store (SQLite `academic_search.db`) and downstream derived vector indices (ChromaDB `scholarly_records_v1`). Defined transactional lifecycle and rebuild synchronization. |
| **Publication Normalization & Deduplication (V1 vs. V2)** | **Completely Rewritten** | Fully documented the mathematical formulation of legacy V1 and the 5 deterministic safeguards introduced in V2 (DOI conflict veto, edition keyword conflict, multi-year divergence, prefix-aware matching, and title similarity floor). Documented the adversarial failure cases (Sutton & Barto edition merge, Hinton & Deng distinct paper merge, Silver et al. subtitle truncation). |
| **Author Candidate Generation & Resolution** | **Completely Rewritten** | Replaced speculative descriptions with exact implementation formulas from `backend/services/author_*.py`. Detailed Unicode NFC normalization, compound surname handling, 5 weighted evidence signals, and the non-linear decision gates (score >= 0.75, margin >= 0.15, dominance >= 1.35). Framed manual review and unresolved states as intentional safety mechanisms. |
| **Experimental Results** | **Completely Rewritten with Primary Data** | Replaced preliminary estimates with frozen artifacts: Benchmark V3 sealed dataset (100 queries, 56 gold, 50 confirmed, 6 probable), deduplication benchmark (50 pairs: 33 TP, 15 TN, 0 FP, 0 FN, 2 uncertain), semantic retrieval evaluation (20 queries), and citation containment matrix (9 test vectors). |
| **Threats to Validity & Limitations** | **Newly Authored** | Added an uncompromising discussion of sample size constraints, synthetic label heritage in early phases, OpenAlex profile splitting, lack of human semantic entailment judgments, and live scraper brittleness. |
| **References & Related Work** | **Reconciled & Expanded** | Corrected duplicate index entries; added primary literature citations for OpenAlex (Priem et al.) and S-BERT (Reimers & Gurevych); verified all 9 DOIs and URLs. |

---

## 3. Discrepancies Resolved & Claims Deliberately Weakened

1. **Database Inventory Clarification:**  
   - *Previous Text:* Stated 696 publications and 2,186 source records.  
   - *Audit Finding:* Active application database contains 396 publications and 1,801 source records. The frozen experimental benchmark snapshot contains 454 publications and 2,053 source records.  
   - *Resolution:* Both numbers are explicitly defined and decoupled in the manuscript to prevent reviewer confusion.
2. **Deduplication Confusion Matrix Accounting:**  
   - *Previous Ambiguity:* Manifest cited 35 TP, 0 FP, 15 TN, 0 FN (50 total pairs), while evaluation scripts reported 33 TP, 15 TN, 2 uncertain.  
   - *Resolution:* Grounded in `run_phase4_evaluations.py`. The 50-pair dataset contains 33 positive pairs, 15 negative pairs, and 2 boundary pairs (`uncertain`: GLOM subtitle variant and Simon Prince textbook edition). Across the 48 decided pairs, V2 achieves 100% precision (33/33) and 100% recall (33/33). The 2 uncertain pairs are explicitly documented as intentional neutral abstentions.
3. **Candidate Recall vs. Identity Resolution Accuracy:**  
   - *Deliberate Correction:* In earlier drafts, 100% candidate recall on confirmed queries was occasionally conflated with author resolution accuracy. The revised draft strictly distinguishes:
     - **Candidate Harvesting Recall:** 100% (50/50 confirmed), 92.86% (52/56 all gold).
     - **Automatic Decision Precision:** 100% (13/13 automatic decisions match ground truth).
     - **Decision Coverage:** 13% automatic, 52% manual review, 35% unresolved.
4. **Removal of Unsubstantiated "Zero Hallucination" Language:**  
   - Replaced all marketing phrasing with precise technical descriptions of the **Citation ID Containment Validator**, acknowledging that semantic entailment and factual correctness require future blinded human evaluation.
5. **Decoupling Semantic Retrieval from Author Resolution:**  
   - Confirmed that dense vector embeddings in ChromaDB do not alter V1 author resolution decisions. The manuscript presents semantic retrieval as an independent publication discovery aid.

---

## 4. Priority Evidence Still Required for Peer-Reviewed Publication

While the revised manuscript provides a rock-solid, defensible baseline for a final-year BTech dissertation and viva examination, submission to a major peer-reviewed conference (e.g., JCDL, SIGIR, or CIKM) will require addressing the following five empirical gaps:
1. **Scaled Deduplication Benchmark:** Expanding the 50-pair test suite to 500–1,000 diverse publication pairs across multiple academic domains.
2. **Double-Blinded Human Relevance Judgments:** Constructing a 50-query retrieval pool with graded relevance labels (0, 1, 2) to compute formal IR metrics (nDCG@10, MAP).
3. **Human Factuality & Entailment Evaluation:** Conducting blinded multi-annotator reviews of 100 LLM-generated summaries to evaluate semantic faithfulness and factual correctness beyond simple ID containment.
4. **Comparative Baseline Experimentation:** Benchmarking HAMMER's deterministic author resolver against established machine learning baselines (e.g., S2AND or S-BERT clustering) on the same dataset.
5. **Cross-Domain Generalization Testing:** Testing candidate generation and deduplication on humanities, medical (PubMed), and social science corpora beyond computer science and machine learning.
