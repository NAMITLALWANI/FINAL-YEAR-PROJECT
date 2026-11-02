# HAMMER — Final Experimental Verification Audit

**Document ID:** HAMMER_FINAL_EXPERIMENTAL_VERIFICATION.md  
**Audit Date:** 2026-11-02  
**Auditor:** Independent AI Research & Verification Auditor  
**System:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Status:** **AUDIT COMPLETE — ALL CLAIMS CALIBRATED**  

---

## 1. Executive Summary & Audit Mandate

Before committing any numerical results or technical descriptions to the final BTech research paper, an exhaustive experimental verification audit was conducted across all six subsystems of HAMMER:
1. Publication Deduplication
2. Semantic Retrieval & Vector Indexing
3. Author Candidate Generation & Disambiguation
4. Gemini LLM Integration & Citation Safety
5. Automated Test Suite & Isolation
6. Research Paper Claims & Scientific Wording

The audit strictly separated **measured empirical results** from **implementation descriptions** and **mocked test executions**.

---

## 2. Master Verification Dashboard

| Subsystem | Metric / Claim | Verified Measured Value | Evidence Source | Status |
|---|---|---|---|---|
| **Deduplication** | Precision | **94.12%** (32 / 34) | 50-pair benchmark (48 decided) | **Verified** |
| **Deduplication** | Recall | **96.97%** (32 / 33) | 50-pair benchmark (48 decided) | **Verified** |
| **Deduplication** | F1 Score | **95.52%** | Recalculated confusion matrix | **Verified** |
| **Deduplication** | False Merges | **2 pairs** (multi-edition / serial) | Benchmark error trace | **Documented** |
| **Vector Retrieval** | Distance Metric | **Cosine Distance** (`hnsw:space: cosine`) | ChromaDB collection metadata | **Verified** |
| **Vector Retrieval** | Score Formula | `score = 1.0 - distance` (exact cosine similarity) | Source code inspection | **Verified** |
| **Vector Retrieval** | In-Corpus Recall | **100.0%** (14 / 14 queries) | 20-query live benchmark | **Verified** |
| **Vector Retrieval** | Gibberish Rejection | **100.0%** (3 / 3 queries rejected) | 20-query live benchmark | **Verified** |
| **Vector Retrieval** | Threshold Floor | **0.35 Cosine Similarity** | Live threshold evaluation curve | **Verified** |
| **Author Resolution** | Candidate Recall@5 | **71.43%** (40 / 56 gold queries) | 100-query benchmark dataset | **Verified** |
| **Author Resolution** | MRR | **0.6152** | 100-query benchmark dataset | **Verified** |
| **Author Resolution** | Manual Review Rate | **52.0%** (52 / 100 queries) | 100-query benchmark dataset | **Verified** |
| **Author Resolution** | Unresolved Rate | **35.0%** (35 / 100 queries) | 100-query benchmark dataset | **Verified** |
| **Author Resolution** | Auto-Selected Rate | **13.0%** (13 / 100 queries) | Engine decision output | **Verified** |
| **Gemini Integration** | Provider Status | **HTTP 200 OK** | Live network call to Google | **Verified** |
| **Gemini Integration** | Model Identifier | `gemini-3.5-flash` | Live network call to Google | **Verified** |
| **Gemini Integration** | Citation Containment | **100.0%** (All cited IDs in hit set) | Live evidence search response | **Verified** |
| **Gemini Integration** | Deterministic Fallback | **Functional** (100% offline fallback) | Test suite + code inspection | **Verified** |
| **Test Suite** | Passing Tests | **55 / 55 passed** (0 failed, 0 skipped) | Live pytest execution (20.3s) | **Verified** |
| **Test Suite** | Production DB Impact | **Zero** (100% in-memory / disposable) | Test code inspection | **Verified** |

---

## 3. Key Technical Insights & Discrepancy Resolutions

### 3.1 Deduplication: The 48 vs 50 Pair Resolution
The previous evaluation report stated $N=50$ with TP=32, FP=2, TN=13, FN=1. The sum of these confusion matrix cells is 48. Independent code audit revealed that **2 pairs** were labeled `"uncertain"` in ground truth due to ambiguous subtitle variations. The evaluation harness correctly skipped uncertain pairs when computing TP/FP/TN/FN but reported the container length (50). The research paper must explicitly state:
$$\text{Total Curated Pairs} = 50, \quad \text{Evaluated Pairs} = 48, \quad \text{Reserved Boundary Pairs} = 2$$

### 3.2 Author Resolution: The `auto_resolved: 0.0%` vs `13 auto_selected` Resolution
In `docs/audit/phase4/results/author_resolution_benchmark_100.json`, the metrics table reported `auto_coverage: 0.0%`, while the decisions table reported `auto_selected: 13`. This was caused by an internal naming discrepancy: `backend/services/author_resolution.py` defines `AUTO_RESOLVED = "auto_selected"`. The decision engine outputs `"auto_selected"`, but the summary script looked for `"auto_resolved"`. The true automatic selection rate is **13.0%**, while **87.0%** of queries are safely deferred to human review or marked unresolved.

### 3.3 Semantic Retrieval: Verification of the 0.35 Floor
Inspection of the active ChromaDB vector index (`scholarly_records_v1`, 449 documents) confirmed that the collection space is configured as `hnsw:space: cosine`. The formula `score = 1.0 - distance` accurately converts Chroma's cosine distance into standard cosine similarity in $[-1.0, 1.0]$. The 0.35 floor is genuinely a cosine similarity threshold, not an arbitrary unscaled distance.

### 3.4 Gemini: Structural Containment vs Semantic Entailment
Live execution confirmed that `gemini-3.5-flash` authenticates, generates structured JSON claims, and strictly cites document IDs from the local retrieved hit set. However, the system checks **structural containment** (whether `doc_id in hit_ids`), not **semantic entailment** (whether the abstract logically entails the claim text). This distinction is documented as an evaluation limitation.

---

## 4. Prioritized Action List Before Academic Submission

Before updating `docs/research-paper.md` or presenting at the final viva examination, the following prioritized items must be addressed:

### Priority 1: Research Paper Text Corrections (Immediate)
1. **Correct Deduplication Sample Size:** Replace any claim of "50 pairs evaluated" with "50 curated pairs, 48 evaluated, 2 reserved boundary pairs". Precision = 94.1%, Recall = 97.0%, F1 = 95.5%.
2. **Remove Unsubstantiated Absolute Claims:**
   - Change *"Zero false merges"* to *"94.1% precision with false merges restricted to multi-edition publications"*.
   - Change *"Zero hallucinations"* to *"Guaranteed citation referential containment with zero hallucinated document identifiers"*.
   - Change *"Complete author disambiguation"* to *"Conservative human-in-the-loop resolution routing 87% of cases to review"*.
3. **Harmonize ChromaDB Collection Name:** Update paper architecture diagrams to reference `scholarly_records_v1` (the actual persistent collection name) rather than the conceptual name `publications`.

### Priority 2: Technical & Experimental Documentation (Pre-Viva)
4. **Document Author Resolution Split-Profile Artifacts:** Explain that OpenAlex contains fragmented entity IDs for top authors (e.g. Demis Hassabis has 2 distinct OpenAlex IDs), explaining why raw ID matching against a single gold ID understates candidate entity quality.
5. **Acknowledge Semantic Entailment Future Work:** Explicitly include a paragraph in the paper's Limitations section stating that natural language semantic entailment verification remains an open direction.

### Priority 3: Codebase Cleanliness (Post-Paper Submission)
6. **Harmonize Engine Status Constants:** Unify `AUTO_RESOLVED` and `auto_selected` across `author_resolution.py` and evaluation scripts to eliminate reporting confusion.
7. **Run Formal Pytest Coverage Report:** Execute `pytest --cov=backend` to establish a defensible, measured line-coverage percentage for viva examiners.

---

## 5. Verification Deliverables Index

The complete suite of 7 audit verification reports is available in `docs/finalisation/verification/`:
1. `HAMMER_DEDUP_VERIFICATION.md` — Deduplication benchmark & confusion matrix audit
2. `HAMMER_RETRIEVAL_VERIFICATION.md` — ChromaDB configuration & retrieval threshold audit
3. `HAMMER_AUTHOR_RESOLUTION_VERIFICATION.md` — Author resolution 100-query benchmark reconciliation
4. `HAMMER_GEMINI_VERIFICATION.md` — Live Gemini provider trace & citation safety audit
5. `HAMMER_TEST_EVIDENCE_AUDIT.md` — Test suite categorization, isolation & mocking audit
6. `HAMMER_RESEARCH_CLAIM_VERIFICATION.md` — Research claims verification matrix
7. `HAMMER_FINAL_EXPERIMENTAL_VERIFICATION.md` — Master executive synthesis & prioritized submission roadmap
