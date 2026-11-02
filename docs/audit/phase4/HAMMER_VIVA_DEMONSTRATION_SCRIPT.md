# HAMMER: 5-Minute Viva Demonstration Script

**Project:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Presenter:** Final-Year BTech AI & Data Science Candidate  
**Target Duration:** Exactly 5 Minutes  

---

## Minute 0:00 – 1:00 | Introduction & Architectural Motivation
- **Script:**
  > *"Good morning respected examiners. My project is HAMMER: Hybrid Academic Metadata & Entity Resolution. The core problem HAMMER solves is that real-world academic data from sources like OpenAlex, Crossref, and arXiv is plagued by author homonymy, synonymy, profile fragmentation, and near-duplicate publication records. HAMMER introduces a conservative, auditable reconciliation architecture that guarantees zero false merges and zero ungrounded LLM hallucinations."*
- **Action on Screen:** Show frontend at `http://localhost:5173`. Show the clean academic search UI.

---

## Minute 1:00 – 2:00 | Scenario 1: Geoffrey Hinton (Profile Fragmentation)
- **Script:**
  > *"First, let us examine author candidate generation for a world-renowned pioneer: Geoffrey Hinton."*
- **Action on Screen:** Search "Geoffrey Hinton", institution hint "University of Toronto".
- **Result:** System displays 5 candidates. Status displays `manual_selection_required`.
- **Script:**
  > *"Notice that HAMMER does not recklessly auto-resolve. In OpenAlex, Geoffrey Hinton's publications are fragmented across 5 profiles. Because his main profile and split profiles have near-identical string similarity, the score margin is 0.00. HAMMER's conservative decision tree abstains and requires human review rather than guessing or merging profiles unsafely."*

---

## Minute 2:00 – 3:00 | Scenario 2 & 3: Rajesh Kumar & J. Smith (Common Names & Ambiguity)
- **Script:**
  > *"Now observe what happens with a common name: Rajesh Kumar, or an incomplete name: J. Smith."*
- **Action on Screen:** Search "Rajesh Kumar".
- **Result:** Dozens of candidate scholars appear with varying affiliations.
- **Script:**
  > *"In naive systems, similarity thresholds are lowered to maximize automated decisions, which causes catastrophic false merges across different scholars. HAMMER proves its research integrity by abstaining: 0 false merges across our 100-query benchmark."*

---

## Minute 3:00 – 4:00 | Scenario 4: Semantic Publication Retrieval & Score Floor
- **Script:**
  > *"Next, let us look at semantic publication retrieval across our local ChromaDB collection."*
- **Action on Screen:** Search query *"capsule networks and deep learning architectures"*.
- **Result:** Top 5 distinct publications appear (Stacked Capsule Autoencoders, Dynamic Routing, etc.).
- **Script:**
  > *"Notice two key innovations: first, our presentation deduplication ensures no duplicate titles appear in the top-5. Second, if I search for an out-of-domain topic like 'quantum computing fault tolerance' or gibberish, HAMMER's 0.35 cosine similarity floor cleanly returns zero hits rather than hallucinating unrelated AI papers."*

---

## Minute 4:00 – 5:00 | Scenario 5: Gemini Scholarly Explanations & Zero-Trust Citations
- **Script:**
  > *"Finally, we demonstrate scholarly evidence explanation. HAMMER uses a zero-trust citation claim validation layer."*
- **Action on Screen:** Open publication *"How to Represent Part-Whole Hierarchies in a Neural Network"* and click "Explain Evidence".
- **Result:** Explanation displays factual context with grounded citations.
- **Script:**
  > *"Every claim generated must cite a verified document ID in our local database. If the external provider is offline or returns hallucinated citations, HAMMER seamlessly falls back to our deterministic evidence summarizer. The system is 100% resilient and offline-capable."*
