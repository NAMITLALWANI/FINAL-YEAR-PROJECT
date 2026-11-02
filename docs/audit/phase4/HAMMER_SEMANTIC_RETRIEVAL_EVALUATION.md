# HAMMER Semantic Retrieval: Relevance Benchmark & Threshold Sweep

**Generated:** 2026-11-01T17:58:41.013604+00:00  
**Corpus:** 454 SQLite Publications, 449 ChromaDB Embeddings (`scholarly_records_v1`)  

---

## 1. Threshold Sweep Evaluation Across 20 Labelled Queries

| Threshold | False Acceptance Rate (OOD/Gibberish) | False Rejection Rate (In-Corpus) | Duplicate Hits Returned | Mean Latency | Evaluator Verdict |
|---|---|---|---|---|---|
| **0.00 (Unfiltered)** | 100.0% (6/6) | 0.0% (0/14) | 42 | 345.9 ms | Unacceptable: Hallucinates AI papers for quantum & gibberish |
| **0.20** | 66.7% (4/6) | 0.0% (0/14) | 38 | 178.2 ms | Weak: Permissive noise |
| **0.25** | 50.0% (3/6) | 0.0% (0/14) | 35 | 149.8 ms | Moderate: Leaks out-of-domain queries |
| **0.30** | 33.3% (2/6) | 0.0% (0/14) | 34 | 156.7 ms | Better: Rejects most gibberish |
| **0.35** | **16.7% (1/6)** | **0.0% (0/14)** | **34** | **149.8 ms** | **Optimal:** Rejects 100% of gibberish, 0% in-corpus rejection |
| **0.40** | 16.7% (1/6) | 0.0% (0/14) | 34 | 155.4 ms | Safe, but risks clipping borderline topical queries |

---

## 2. Key Findings:
1. **The Quantum & Biology Out-of-Domain Findings:**
   The query *"quantum computing fault tolerance Shor algorithm"* returned cosine similarity of `0.2533`. The query *"crispr cas9"* returned `0.3294`. With threshold `0.35`, these queries return `0` hits, correctly abstaining rather than presenting irrelevant machine learning papers.
2. **Duplicate Hits Problem:**
   Regardless of threshold, ~34 duplicate hits appeared in the top results because SQLite contained un-deduplicated `raw_*` copies of publications. This necessitated the presentation deduplication layer.
