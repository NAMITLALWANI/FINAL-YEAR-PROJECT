# HAMMER Author Profile Clustering Design: Non-Destructive Association Layer

**System:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Topic:** Resolving Upstream Profile Fragmentation Without Data Loss  

---

## 1. Problem Statement & Upstream Profile Fragmentation

Phase 3B and Phase 4 empirical evaluations revealed that authoritative academic databases (specifically OpenAlex) exhibit severe profile fragmentation:
- **Geoffrey Hinton:** 5 distinct OpenAlex profiles (`A5108093963` [556 works], `A5153609875` [4 works], `A5160214549` [1 work], `A5139521503` [1 work], `A5098035523` [1 work]).
- **Yoshua Bengio:** 4 distinct OpenAlex profiles (`A5058729352`, `A5088219437`, `A5013098379`, `A5012586738`).
- **Yann LeCun:** 2 distinct OpenAlex profiles (`A5004945511`, `A5048227690`).

Because multiple profiles describe the same underlying scholar, string and institution similarity scores produce near-identical values (e.g. `score1 = 1.0`, `score2 = 1.0`, margin = `0.00`). The conservative resolver strictly requires `margin >= 0.15` and `dominance >= 1.35`, and therefore abstains with `manual_selection_required`.

Lowering thresholds to force automatic resolution would cause disaster: it would trigger catastrophic false merges on common names like "Rajesh Kumar" or "Wei Zhang".

---

## 2. Non-Destructive Profile Association Architecture

To solve this without modifying thresholds or mutating source entities, HAMMER defines a **Non-Destructive Profile Association Layer**:

```
[OpenAlex Profile A5108093963] ──┐
[OpenAlex Profile A5153609875] ──┼──> [Proposed Cluster CLUST_HINTON] ──> [Canonical Scholar Entity]
[OpenAlex Profile A5139521503] ──┘         (Status: Proposed / Approved)
```

### Guiding Architectural Principles:
1. **Preserve Source IDs:** Original OpenAlex IDs (`source_author_id`) are never overwritten or deleted.
2. **Reversible Linkage:** Links are stored in an association table (`author_profile_clusters`), which can be reviewed, confirmed, or revoked by a human reviewer.
3. **Multi-Signal Clustering Evidence:**
   - **Shared DOI Overlap:** Two profiles coauthoring or authoring the same DOI.
   - **Coauthor Graph Overlap:** High Jaccard similarity of coauthors across profiles.
   - **Chronological & Topic Continuity:** Shared OpenAlex concepts/topics and contiguous active publication years.
4. **Separation of Concerns:** Semantic text similarity alone never triggers profile clustering.
