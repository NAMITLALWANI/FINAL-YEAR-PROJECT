# HAMMER — Research Claim Verification Matrix

**Document ID:** HAMMER_RESEARCH_CLAIM_VERIFICATION.md  
**Audit Date:** 2026-11-02  
**Auditor:** Independent AI Research & Verification Auditor  
**System:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Target:** Verification of Research Paper Claims vs. Empirical Evidence  

---

## 1. Executive Summary

This audit scrutinizes every primary research claim intended for the HAMMER research paper, classifying each claim into one of five rigorous academic audit categories:
- **Verified:** Supported by both complete implementation and reproducible benchmark data.
- **Partially Verified:** Implemented and empirically tested, but with documented boundary exceptions or scope limits.
- **Implementation-Only:** Fully implemented in source code and unit-tested, but lacks large-scale external benchmark data.
- **Unsupported:** Claimed in discussions or concept documents but lacks implementation or empirical validation.
- **Incorrect:** Refuted by empirical data or code inspection.

---

## 2. Research Claims Audit Matrix

| Research Claim | Implementation Evidence | Experimental Evidence | Status | Safe Wording for Research Paper |
|---|---|---|---|---|
| **"Zero False Merges in Deduplication"** | `backend/pipeline/deduplicate.py` uses blocking and weighted fuzzy matching (0.6 title + 0.3 author + 0.1 year). | Benchmark on 50 pairs produced **2 False Positives** (Sutton 1st vs 2nd edition, Hinton acoustic modeling papers). | **Incorrect** (as an absolute claim) | *"HAMMER achieves 94.1% precision in publication deduplication, with false merges restricted to multi-edition works and serial workshop papers sharing identical authorship."* |
| **"Zero Hallucinations in Scholarly Summaries"** | `backend/services/scholarly_retrieval.py` enforces `responseSchema` and drops claims citing non-retrieved documents. | Citation validator dropped 100% of synthetic invalid/hallucinated document citations across 9 safety test cases. | **Partially Verified** (Referential containment verified; semantic entailment unverified) | *"HAMMER enforces strict citation referential integrity, eliminating hallucinated external document identifiers by requiring all generated claims to cite local retrieved records."* |
| **"Fully Offline Operation"** | Local SQLite storage, local ChromaDB vector store, local `all-MiniLM-L6-v2` embeddings, deterministic template fallback. | System operates with zero network connectivity when LLM and OpenAlex harvesters are disabled. 55/55 pytest tests pass offline. | **Verified** | *"HAMMER supports complete offline execution across ingestion reconciliation, vector search, and deterministic template explanation, requiring network access only for optional live OpenAlex and Gemini queries."* |
| **"Complete Author Disambiguation"** | Multi-signal evidence scoring (affiliation, coauthors, venues, topics, temporal) in `author_resolution/`. | In 100-query benchmark, 52% required manual review, 35% were unresolved, and 13% were auto-selected. | **Incorrect** (as "complete"); **Verified** as *"Human-in-the-Loop Disambiguation"* | *"HAMMER implements a conservative human-in-the-loop author resolution architecture, resolving 13% of distinctive profiles automatically while safely deferring 87% of ambiguous cases to expert review."* |
| **"Citation Correctness"** | Citation post-processor validates that `doc_id in retrieved_hit_ids`. Replaces summary if citations are invalid. | Live Gemini test cited 3/3 documents present in hit set; 9/9 safety test cases passed. | **Partially Verified** (Structural citation validity verified; textual entailment unverified) | *"HAMMER guarantees citation containment by rejecting any claim citing document IDs outside the retrieved candidate set, though natural language semantic entailment remains an evaluation limitation."* |
| **"High Semantic Retrieval Effectiveness"** | ChromaDB with `all-MiniLM-L6-v2`, cosine metric, and 0.35 similarity floor. | 20-query evaluation yielded 100% recall on in-corpus queries, 100% gibberish rejection, and 16.7% out-of-domain false acceptance. | **Partially Verified** (Binary query recall verified; per-document MAP/NDCG unverified) | *"HAMMER achieves 100% retrieval recall on in-corpus queries while a 0.35 cosine similarity floor suppresses nonsensical and out-of-domain queries."* |
| **"Publication Reconciliation Accuracy"** | Multi-source canonical record schema, DOI priority matching, provenance tracking in `source_records`. | Production database contains 2,053 source records reconciled into 454 canonical publications across 960 duplicate groups. | **Verified** | *"HAMMER reconciles heterogeneous multi-source academic records into canonical publications with full source provenance tracking, resolving 2,053 harvested records into 454 canonical entities."* |
| **"Automated Institutional Affiliation Clustering"** | Schemas exist for `author_affiliations` and `author_aliases`. | Both tables contain **0 rows** in the production database. Logic relies on ephemeral OpenAlex candidate metadata. | **Implementation-Only** | *"HAMMER specifies relational schemas for institutional affiliations and author aliases, utilizing live candidate metadata for real-time evidence scoring."* |

---

## 3. High-Risk Claims to Strictly Avoid in Viva and Paper

1. **DO NOT CLAIM:** *"HAMMER completely solves author name disambiguation."*
   - **Reality:** Author disambiguation is an NP-hard unsupervised clustering problem. HAMMER correctly auto-resolves only 13% of distinctive cases and routes 87% to human review.
2. **DO NOT CLAIM:** *"Zero hallucinations under LLM synthesis."*
   - **Reality:** HAMMER guarantees that cited *document IDs* exist in the retrieved hit set. It does not formally verify that the generated text is semantically entailed by the paper's contents.
3. **DO NOT CLAIM:** *"100% test coverage."*
   - **Reality:** The suite contains 55 passing tests, but line coverage was not measured via coverage tools.
4. **DO NOT CLAIM:** *"Deduplication was tested on 960 pairs."*
   - **Reality:** 960 is the number of rows in the `duplicate_groups` table. The empirical benchmark evaluated 50 curated pairs (48 decided).

---

## 4. Verification Summary

Every research claim has been assigned safe, scientifically defensible phrasing. Incorporating these calibrated formulations protects the research paper from reviewer rejection and prepares the candidate for viva defense.
