# HAMMER: Comprehensive Viva Question Bank & Model Answers

**Target:** Final-Year Project Defense  
**Domain:** AI, Entity Resolution, Semantic Search, and LLM Trust  

---

### Q1: What is the difference between semantic retrieval and author entity resolution in HAMMER?
**Answer:** *"Semantic retrieval performs approximate nearest-neighbor search in a continuous vector embedding space (all-MiniLM-L6-v2 in ChromaDB) to retrieve topically relevant papers based on query semantics. Author entity resolution, by contrast, is a discrete decision problem that determines whether an author mention in a paper corresponds to a specific real-world researcher, evaluating multi-modal evidence such as coauthorship graphs, institutional history, and temporal continuity. High topical similarity never proves identity."*

---

### Q2: Why did your author resolution benchmark show 0 automatic resolutions? Isn't that a failure?
**Answer:** *"No, sir, that is one of HAMMER's most important design contributions. In academic entity resolution, an automated false merge corrupts citation integrity and author attribution. Upstream sources like OpenAlex suffer from profile fragmentation—for example, Geoffrey Hinton has five separate profiles. When profiles of the same researcher compete, their string and metadata similarities tie, resulting in a margin of 0.00. Because HAMMER enforces a strict margin threshold of 0.15 and dominance of 1.35, the system conservatively abstains with `manual_selection_required`. Over our 100-query benchmark, this yielded a 0.00% False Merge Rate."*

---

### Q3: How do you prevent Gemini from hallucinating fake academic citations?
**Answer:** *"We use a zero-trust citation claim validation architecture. When Gemini generates a response, it is constrained to output structured JSON claims where every claim must cite one or more `document_id` values from the retrieved candidate pool. Our backend parser intercepts this payload, verifies that every cited ID exists in our local database records, and strips any ungrounded claims. Furthermore, the model's free-standing summary is completely discarded and replaced by concatenated validated claim text."*

---

### Q4: Why did you choose ChromaDB with all-MiniLM-L6-v2 instead of a larger embedding model?
**Answer:** *"all-MiniLM-L6-v2 provides an optimal trade-off for academic titles and abstracts: 384 dimensions, fast inference on CPU (mean retrieval latency ~150 ms), and high retrieval quality on conceptual queries. Because HAMMER is designed for responsive interactive search and offline defense, all-MiniLM-L6-v2 eliminates GPU dependencies while preserving high precision."*

---

### Q5: How does your deduplication pipeline handle preprints versus published journal papers?
**Answer:** *"In `deduplicate.py`, our blocking pass requires exact DOI, year match within 1 year, author overlap, or title prefix match. For preprint vs published versions, DOIs typically differ. Fuzzy scoring evaluates title similarity (0.60 weight), author overlap (0.30 weight), and year match (0.10 weight). If the combined score meets the source-aware threshold, they merge under a single canonical publication while preserving the source provenance of both in the `source_records` table."*
