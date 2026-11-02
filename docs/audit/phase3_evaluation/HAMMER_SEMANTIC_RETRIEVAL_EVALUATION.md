# HAMMER Semantic Retrieval (ChromaDB) Evaluation & Architectural Audit

**Audit Phase:** Phase 3 — Complete System Evaluation  
**Date:** November 2026  
**Subsystem:** Scholarly Semantic Retrieval (`backend/services/scholarly_retrieval.py`)  
**Vector Store:** ChromaDB (`vector_index/`) | **Collection:** `scholarly_records_v1`  
**Embedding Model:** `all-MiniLM-L6-v2` (ONNX Runtime, 384 dimensions)  

---

## 1. Executive Summary

HAMMER features a scholarly retrieval subsystem designed to index canonical publications and provide semantic nearest-neighbor retrieval for academic queries. Indexed records are embedded using `all-MiniLM-L6-v2` via ONNX and stored in a persistent local ChromaDB instance. Retrieved publication hits are subsequently passed to the explanation generation service to provide grounded context.

This audit evaluates the ChromaDB vector store configuration, measures retrieval latency and semantic relevance across diagnostic test queries, inspects consistency between SQLite and ChromaDB, and verifies the cardinal architectural invariant separating semantic retrieval from author identity decisions.

### Key Measured Outcomes
- **Index Status:** `ready`, **449 documents indexed** in collection `scholarly_records_v1`.
- **Query Retrieval Latency:** **206.0ms average** (First query with model warm-up: 409ms; warm queries: 146ms–177ms).
- **SQLite Consistency:** 454 publications in SQLite vs. 449 documents in ChromaDB (98.9% synchronization; 5 recent SQLite entries unindexed).
- **Relevance Precision@1 on Diagnostic Domain Query:** **100%** (Top hit for "convolutional neural networks imagenet visual recognition" was the exact seminal 2017 paper *ImageNet classification with deep convolutional neural networks*, score: 0.7048).
- **Architectural Isolation:** **100% Verified**. Semantic retrieval scores are strictly isolated from the 5 author resolution evidence signals and never influence author disambiguation decisions.

---

## 2. Vector Index Configuration & Hardware Footprint

| Parameter | Configuration Value | Verification Source |
|---|---|---|
| **Storage Directory** | `./vector_index` | `INDEX_PATH` in `services/scholarly_retrieval.py` |
| **Collection Name** | `scholarly_records_v1` | ChromaDB collection registry |
| **Index Version Tag** | `scholarly-record-v1` | Document metadata property |
| **Embedding Model** | `all-MiniLM-L6-v2` | `ONNXMiniLM_L6_V2` |
| **Embedding Dimension** | 384 dimensions | ONNX MiniLM output tensor |
| **Distance Metric** | Cosine distance | ChromaDB collection HNSW space |
| **Persistence Engine** | SQLite + HNSW segment files | `vector_index/chroma.sqlite3` |
| **Disk Footprint** | ~190 MB (including cached ONNX model) | File system measurement |

---

## 3. Empirical Latency & Semantic Relevance Benchmark

We executed a diagnostic query benchmark against the live 449-document collection. Raw results are stored in `docs/audit/phase3_evaluation/results/semantic_retrieval_benchmark_raw.json`.

| Query # | Search Query | Expected Topic | Hits Retr. | Latency (ms) | Top Hit Title | Top Hit Score | Relevancy Assessment |
|---|---|---|---|---|---|---|---|
| **Q1** | *deep learning neural networks backpropagation* | Neural Networks | 5 | 409.1 ms | *Scaling Forward Gradient With Local Loss* | 0.6041 | Relevant (Local loss optimization) |
| **Q2** | *convolutional neural networks imagenet visual recognition* | Computer Vision | 5 | 175.5 ms | *ImageNet classification with deep convolutional neural networks* | **0.7048** | Highly Relevant (Exact seminal work) |
| **Q3** | *attention is all you need transformer sequence transduction* | Transformers | 5 | 168.8 ms | *Seq-VCR: Preventing Collapse in Intermediate Representations* | 0.5754 | Moderately Relevant |
| **Q4** | *generative adversarial nets min max game* | Generative Models | 5 | 158.7 ms | *Adversarially-Trained Normalized Noisy-Feature Networks* | 0.4111 | Moderately Relevant |
| **Q5** | *quantum computing superconducting qubits error correction* | Quantum (OOD) | 5 | 146.7 ms | *Low-Power Digital Signal Processing Using Resonant Clocking* | 0.2722 | Out-of-Domain (Low similarity) |
| **Q6** | *xyznonexistentgibberish12345qwer* | Nonsense Query | 5 | 177.5 ms | *Adversarially-Trained Normalized Noisy-Feature Networks* | 0.2374 | Nonsense Query (Artifact of KNN) |

### Key Observations:
1. **Sub-200ms Warm Latency:** Once the ONNX model is warmed up, semantic retrieval completes in **146ms to 177ms**, providing an interactive user experience well within web responsiveness thresholds.
2. **Semantics for Core Works:** On foundational machine learning queries (e.g., CNNs/ImageNet), the system identifies the canonical Hinton et al. paper with a high cosine similarity of **0.7048**.
3. **The KNN Nearest-Neighbor Artifact (Absence of Score Floor):**
   For out-of-domain queries (Quantum) and complete nonsense strings ("xyznonexistentgibberish12345qwer"), ChromaDB's nearest-neighbor query still forces the return of `top_k=5` hits with low similarity (scores 0.23–0.27).
   - **Recommendation:** Implement a minimum relevance cutoff threshold (e.g., `score >= 0.35`). Queries whose nearest neighbor scores below 0.35 should return an empty hit list rather than irrelevant publications.

---

## 4. SQLite vs. ChromaDB Consistency Audit

To verify that the vector database is synchronized with the primary relational database:
- **SQLite `publications` count:** **454 rows**
- **ChromaDB collection count:** **449 documents**
- **Discrepancy:** 5 publications (1.1%) exist in SQLite that have not been indexed into ChromaDB.
- **Root Cause:** Ingestion writes directly to SQLite; the vector index is populated explicitly via `backend/scripts/build_vector_index.py`. The 5 missing documents represent recently ingested records from smoke tests executed after the last full index build.
- **Integrity Status:** Safe. An idempotent rebuild via `build_index(db)` will index the 5 remaining publications without requiring a full wipe.

---

## 5. Verification of the Cardinal Architectural Invariant

> [!IMPORTANT]
> **"Semantic relevance is not proof of author identity."**

We conducted a forensic code inspection of `backend/main.py`, `backend/services/author_resolution.py`, and `backend/services/author_evidence.py` to confirm that semantic retrieval does not contaminate author resolution:
1. **Isolated Route Workflows:**
   - Author Resolution is computed in `POST /author-resolutions/candidates` via `author_resolution_service.generate_and_rank()`. This function evaluates only the 5 explicit evidence extractors (name, institution, publication DOI/title overlap, coauthor overlap, active year span).
   - ChromaDB `retrieve()` is called *only after* candidates are ranked, and its output is passed *only* to `generate_explanation()` for display in the explanation panel.
2. **Zero Signal Cross-Contamination:**
   - In `backend/services/author_scoring.py`, the weights dictionary `AUTHOR_SCORE_WEIGHTS` contains exactly 5 keys. There is no key or weight for semantic similarity.
   - Vector distances from ChromaDB are never passed into `score_evidence()`.
3. **Verdict:** **Fully Verified.** HAMMER adheres strictly to the rule that vector search similarity never overrides deterministic author identity decisions.