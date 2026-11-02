# HAMMER Semantic Retrieval: Implementation of Score Floor & Presentation Dedup

**System:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Files Modified:** `backend/services/scholarly_retrieval.py`, `backend/tests/test_scholarly_retrieval.py`  

---

## 1. Concrete Improvements Implemented

1. **Cosine Similarity Floor (`min_score = 0.35`):**
   Chroma distance is converted to similarity `score = max(-1.0, min(1.0, 1.0 - float(distance)))`. Hits with `score < min_score` are dropped immediately. Gibberish and out-of-domain queries return `0` hits.
2. **Multi-Key Presentation Deduplication:**
   When iterating through nearest neighbors, documents are deduplicated by:
   - `canonical_id`
   - `doi` (normalized lower case)
   - `norm_title` (stripped punctuation and collapsed whitespace)
   This eliminates duplicate versions of the same paper from appearing repeatedly in the top-5 results.
3. **Candidate Pool Sizing:**
   Query size is increased to `n_query = min(max(top_k * 4, 10), 50)` so that after deduplication and score filtering, the user receives up to `top_k` distinct, high-relevance publications.

---

## 2. Verification Evidence

A regression test `test_retrieval_similarity_floor_and_title_dedup` was added to `backend/tests/test_scholarly_retrieval.py`.
- **Pre-fix:** Querying "capsule networks" returned 3 identical copies of "Stacked Capsule Autoencoders".
- **Post-fix:** Querying "capsule networks" returns 5 distinct papers (Stacked Capsule Autoencoders, Dynamic Routing Between Capsules, Class-Conditional Capsules, Canonical Capsules, Deep Learning for AI).
- **Test Results:** 13/13 tests pass in `test_scholarly_retrieval.py`.
