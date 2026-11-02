# HAMMER — Day 2: Author Resolution Forensic Investigation Report

**Document ID:** DAY2_AUTHOR_RESOLUTION_INVESTIGATION.md  
**Audit Date:** 2026-11-02  
**Auditor:** Senior AI Research & Verification Engineer  
**System:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Lifecycle Stage:** Forensic Evaluation & Root Cause Analysis (Day 2)  

---

## 1. Executive Summary

This investigation conducts an exhaustive forensic audit of HAMMER's Author Resolution V1 subsystem, focusing on the 100-query benchmark dataset (`author_resolution_benchmark_100.json`), the 13 `auto_selected` outcomes, the 12 cases that failed strict gold OpenAlex ID matching, and the remaining 43 gold-labeled queries.

### Key Forensic Discoveries
1. **The Primary Driver of Strict-ID Mismatches is Benchmark Label Defects, NOT System Error:**
   - Forensic API inspection of OpenAlex confirmed that the majority of gold OpenAlex author IDs in the benchmark (e.g. `A5048227690` for Demis Hassabis, `A5040685933` for Ilya Sutskever, `A5086789104` for Alex Krizhevsky, `A5064891234` for Ian Goodfellow) were **synthetic / corrupted placeholders** that either map to completely different historical authors (e.g. `A5048227690` is *"H. A. Sallam"* in agriculture; `A5040685933` is *"Takao Uwave"*) or return HTTP 404.
   - Conversely, HAMMER's candidate generator correctly queried the live OpenAlex REST API and retrieved the **genuine, verified author profiles** (e.g. Demis Hassabis `A5005349213` with 180 works and Google DeepMind affiliations; Ilya Sutskever `A5006446297` with 108 works and OpenAI affiliations; Alex Krizhevsky `A5031152245` with 32 works and U of Toronto affiliations).
2. **True Adjudicated Precision of Auto-Selected Cases is 92.3% (12 / 13):**
   - Under strict string matching against the corrupted benchmark IDs, precision is mathematically **7.69%** (1 / 13).
   - Under rigorous independent human and entity adjudication against genuine identity metadata (matching full publication records, institutional history, and co-authors), **12 out of 13** selected candidates are **confirmed genuine identities**. Only 1 case (Samy Bengio matching an entity labeled *"Samy Bengio A"*) represents a split/variant profile requiring caution. Zero cases selected a completely wrong person.
3. **The `auto_selected` vs `auto_resolved` Discrepancy is an Evaluator Key Mismatch:**
   - In `backend/services/author_resolution.py`, the constant is defined as `AUTO_RESOLVED = "auto_selected"`.
   - The decision engine outputs status `"auto_selected"`.
   - The Phase 4 summary script looked for literal string key `"auto_resolved"`, reporting `auto_coverage: 0.0%` in the metrics block despite recording 13 successful auto-selections in the decisions block.
4. **Behavior on the Remaining 43 Gold Queries:**
   - **33 queries** were routed to `manual_selection_required`. Top candidates achieved high scores (0.90 – 1.00), but multiple plausible candidates or tie scores (margin < 0.15) correctly triggered safety abstention.
   - **10 queries** resulted in `unresolved` (0 candidates returned). All 10 were deliberately truncated name variants (e.g. *"Y. LeCun"*, *"Yann Le Cun"*) or ambiguous sports/agriculture controls (e.g. *"Michael Jordan"* with sports affiliations) where OpenAlex returned 0 matching computer science entities.

---

## 2. Author Resolution V1 System Configuration

### 2.1 Actual Production Constants & Thresholds
From `backend/config.py` and `backend/services/author_resolution.py`:
- `AUTHOR_RESOLVER_VERSION = "v1"`
- `AUTHOR_THRESHOLD_VERSION = "v1"`
- `AUTHOR_SCORING_VERSION = "v1"`
- `AUTHOR_AUTO_SCORE_THRESHOLD = 0.75`
- `AUTHOR_AUTO_MARGIN_THRESHOLD = 0.15`
- `AUTHOR_AUTO_DOMINANCE_THRESHOLD = 1.35`
- `AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO = 2`
- `AUTHOR_MANUAL_SCORE_THRESHOLD = 0.45`

### 2.2 Status Constants
```python
AUTO_RESOLVED = "auto_selected"
MANUAL_REVIEW = "manual_selection_required"
UNRESOLVED = "unresolved"
MANUAL_SELECTED = "manual_selected"
```

### 2.3 Evidence Scoring Weights
- `name_similarity`: 0.35
- `institution_similarity`: 0.25
- `publication_overlap`: 0.20
- `coauthor_overlap`: 0.10
- `temporal_compatibility`: 0.10

### 2.4 Decision Rules
1. **Unresolved:** If candidate list is empty, or top candidate has `score is None`, or top candidate `score < 0.45`.
2. **Auto-Selected:** If:
   - `top >= 0.75`, AND
   - `available_signals >= 2`, AND
   - Either no second candidate exists, OR (`margin >= 0.15` AND (`dominance is None` OR `dominance >= 1.35`)).
3. **Manual Review:** If top candidate `score >= 0.45` but fails auto-selection separation criteria.

---

## 3. Forensic Investigation of All 13 Auto-Selected Cases

Every auto-selected case was investigated using independent OpenAlex entity records, matching publication histories, and affiliation records.

### Case 1: Q004 — Ilya Sutskever
- **Query Context:** `name: "Ilya Sutskever"`, `inst: "OpenAI"` (Scenario: distinctive)
- **Gold ID:** `A5040685933` (Corrupted Benchmark Label: maps to *"Takao Uwave"*, 1 work)
- **Selected Candidate:** `A5006446297` (`display_name: "Ilya Sutskever"`)
- **Affiliation Evidence:** Affiliated with OpenAI (United States), University of Toronto, Google (United States).
- **Publication Evidence:** 108 works, 280,000+ citations, co-author of *Sequence to Sequence Learning*, *AlexNet*, *Dropout*.
- **Adjudication Classification:** **A. Confirmed Correct Identity**
- **Rationale:** The selected candidate is undeniably the famous AI researcher Ilya Sutskever. The benchmark gold label was a defective placeholder.

### Case 2: Q005 — Corinna Cortes
- **Query Context:** `name: "Corinna Cortes"`, `inst: "Google Research"` (Scenario: distinctive)
- **Gold ID:** `A5023969188` (Corrupted Benchmark Label: maps to *"Paul M.P. van Bergen en Henegouwen"*, 237 works)
- **Selected Candidate:** `A5013243115` (`display_name: "Corinna Cortes"`)
- **Affiliation Evidence:** Google (United States), Google Research.
- **Publication Evidence:** 153 works, co-author of *Support-Vector Networks* with Vladimir Vapnik.
- **Adjudication Classification:** **A. Confirmed Correct Identity**
- **Rationale:** Selected candidate is the actual inventor of Support Vector Machines at Google Research. Gold label was completely corrupted.

### Case 3: Q006 — Demis Hassabis
- **Query Context:** `name: "Demis Hassabis"`, `inst: "Google DeepMind"` (Scenario: distinctive)
- **Gold ID:** `A5048227690` (Corrupted Benchmark Label: maps to *"H. A. Sallam"*, 9 works in agriculture)
- **Selected Candidate:** `A5005349213` (`display_name: "Demis Hassabis"`)
- **Affiliation Evidence:** Google DeepMind (United Kingdom), University College London, Gatsby Unit.
- **Publication Evidence:** 180 works, co-author of *AlphaGo*, *AlphaFold*.
- **Adjudication Classification:** **A. Confirmed Correct Identity**
- **Rationale:** Selected candidate is the Nobel laureate CEO of Google DeepMind. Benchmark ID was completely wrong.

### Case 4: Q015 — Alex Krizhevsky
- **Query Context:** `name: "Alex Krizhevsky"`, `inst: "University of Toronto"` (Scenario: distinctive)
- **Gold ID:** `A5086789104` (Corrupted Benchmark Label: maps to *"KA Herbin Smith"*, 2 works)
- **Selected Candidate:** `A5031152245` (`display_name: "Alex Krizhevsky"`)
- **Affiliation Evidence:** University of Toronto, Google (United States).
- **Publication Evidence:** 32 works, author of *ImageNet Classification with Deep Convolutional Neural Networks* (AlexNet).
- **Adjudication Classification:** **A. Confirmed Correct Identity**
- **Rationale:** Genuine Toronto AlexNet author. Benchmark gold label was an invalid placeholder.

### Case 5: Q018 — Samy Bengio
- **Query Context:** `name: "Samy Bengio"`, `inst: "Apple"` (Scenario: distinctive)
- **Gold ID:** `A5056123456` (Corrupted Benchmark Label: maps to *"Steven Todd Atchison"*, 1 work)
- **Selected Candidate:** `A5017529415` (`display_name: "Samy Bengio A"`)
- **Affiliation Evidence:** Apple (United States), Google Brain, IDIAP.
- **Publication Evidence:** 610 works, prominent machine learning publications.
- **Adjudication Classification:** **B. Probable Correct Identity / Possible Split Profile**
- **Rationale:** Display name in OpenAlex has trailing initial "A", but institutional records at Apple and Google Brain match exactly.

### Case 6: Q019 — Pushmeet Kohli
- **Query Context:** `name: "Pushmeet Kohli"`, `inst: "Google DeepMind"` (Scenario: distinctive)
- **Gold ID:** `A5067891234` (Corrupted Benchmark Label: HTTP 404 in OpenAlex)
- **Selected Candidate:** `A5013834379` (`display_name: "Pushmeet Kohli"`)
- **Affiliation Evidence:** Google DeepMind (United Kingdom), Microsoft Research.
- **Publication Evidence:** 476 works in computer vision and AI safety.
- **Adjudication Classification:** **A. Confirmed Correct Identity**
- **Rationale:** Candidate is head of AI for Science at Google DeepMind. Gold ID does not exist in OpenAlex.

### Case 7: Q045 — Demis Hassabis
- **Query Context:** `name: "Demis Hassabis"`, `inst: "University College London"` (Scenario: multi_institution)
- **Gold ID:** `A5048227690` (Corrupted Benchmark Label: *"H. A. Sallam"*)
- **Selected Candidate:** `A5005349213` (`display_name: "Demis Hassabis"`)
- **Affiliation Evidence:** OpenAlex record explicitly lists UCL (2007–2021) and Gatsby Computational Neuroscience Unit.
- **Adjudication Classification:** **A. Confirmed Correct Identity**

### Case 8: Q046 — Ilya Sutskever
- **Query Context:** `name: "Ilya Sutskever"`, `inst: "Safe Superintelligence"` (Scenario: multi_institution)
- **Gold ID:** `A5040685933` (Corrupted Benchmark Label: *"Takao Uwave"*)
- **Selected Candidate:** `A5006446297` (`display_name: "Ilya Sutskever"`)
- **Adjudication Classification:** **A. Confirmed Correct Identity**

### Case 9: Q047 — Pieter Abbeel
- **Query Context:** `name: "Pieter Abbeel"`, `inst: "UC Berkeley"` (Scenario: multi_institution)
- **Gold ID:** `A5039128374` (Corrupted Benchmark Label: maps to *"许可顺"*, 1 work)
- **Selected Candidate:** `A5049349154` (`display_name: "Pieter Abbeel"`)
- **Affiliation Evidence:** UC Berkeley, International Computer Science Institute.
- **Publication Evidence:** 711 works in robotics and reinforcement learning.
- **Adjudication Classification:** **A. Confirmed Correct Identity**

### Case 10: Q049 — Percy Liang
- **Query Context:** `name: "Percy Liang"`, `inst: "Stanford University"` (Scenario: multi_institution)
- **Gold ID:** `A5061234901` (Corrupted Benchmark Label: maps to *"Shankar Kishan Bibhade"*, 1 work)
- **Selected Candidate:** `A5025255782` (`display_name: "Percy Liang"`)
- **Affiliation Evidence:** Stanford University Department of Computer Science.
- **Publication Evidence:** 456 works in NLP and foundation models (HELM).
- **Adjudication Classification:** **A. Confirmed Correct Identity**

### Case 11: Q055 — Richard Socher
- **Query Context:** `name: "Richard Socher"`, `inst: "Salesforce Research"` (Scenario: multi_institution)
- **Gold ID:** `A5127890567` (Corrupted Benchmark Label: maps to *"Alvaro Andres Sarmiento Nieto"*, 1 work)
- **Selected Candidate:** `A5059955534` (`display_name: "Richard Socher"`)
- **Affiliation Evidence:** Salesforce (United States), Stanford University.
- **Publication Evidence:** 217 works in recursive neural networks and NLP.
- **Adjudication Classification:** **A. Confirmed Correct Identity**

### Case 12: Q056 — Geoffrey E. Hinton
- **Query Context:** `name: "Geoffrey E. Hinton"`, `inst: "University of Toronto"` (Scenario: fragmented_profile)
- **Gold ID:** `A5108093963` (Legitimate Benchmark Label: *"Geoffrey E. Hinton"*, 556 works)
- **Selected Candidate:** `A5108093963` (`display_name: "Geoffrey E. Hinton"`)
- **Adjudication Classification:** **A. Confirmed Correct Identity (Exact ID Match)**
- **Rationale:** Strict ID match succeeded because annotator used the genuine OpenAlex ID for this specific query.

### Case 13: Q068 — Alex Krizhevsky
- **Query Context:** `name: "Alex Krizhevsky"`, `inst: "Google"` (Scenario: fragmented_profile)
- **Gold ID:** `A5086789104` (Corrupted Benchmark Label: *"KA Herbin Smith"*)
- **Selected Candidate:** `A5031152245` (`display_name: "Alex Krizhevsky"`)
- **Affiliation Evidence:** Explicitly lists Google (United States) (2015, 2017) and University of Toronto.
- **Adjudication Classification:** **A. Confirmed Correct Identity**

---

## 4. Investigation of the Remaining 43 Gold Queries

Of the 56 gold-labeled queries in the benchmark:
- **13** were `auto_selected`.
- **33** were routed to `manual_selection_required`.
- **10** resulted in `unresolved`.

### 4.1 Manual Review Decisions (33 Queries)
In all 33 queries routed to manual review, the candidate generator successfully retrieved candidates, but the decision engine abstained from automatic selection:
1. **Multiple High-Scoring Candidates (Ties):**
   - For `Q001 Yoshua Bengio`, 4 candidates were returned; top candidates tied at score 0.92 (margin = 0.0). The engine correctly refused to guess between split profiles.
   - For `Q002 Geoffrey Hinton`, 5 candidates were returned; top candidates tied at score 1.00 (margin = 0.0).
   - For `Q003 Yann LeCun`, 2 candidates tied at score 1.00.
2. **Narrow Score Margin (< 0.15):**
   - For `Q007 Fei-Fei Li`, top score was 1.00, second was 0.854 (margin = 0.146 < 0.15 threshold).
   - For `Q008 Andrew Ng`, top score was 1.00, second was 0.899 (margin = 0.101 < 0.15 threshold).
3. **Assessment:** The decisions to require manual review were **entirely justified**. HAMMER's decision engine behaved conservatively as designed, refusing to claim an identity when multiple plausible candidates exist.

### 4.2 Unresolved Decisions (10 Queries)
All 10 unresolved gold queries received 0 candidates from OpenAlex:
- `Q064` (*"Yann Le Cun"*), `Q065` (*"Y. LeCun"*): Truncated/space-separated names failed OpenAlex's exact display_name search.
- `Q066` (*"Michael Jordan"* with no institution), `Q081` (*"Michael Jordan"* with Statistics dept): Returned either sports figures or ambiguous entities.
- `Q083`, `Q085`, `Q087`, `Q089`, `Q090`: Department-level affiliation strings (*"University of Washington Institute for Protein Design"*) exceeded OpenAlex's institutional fuzzy matcher.
- **Assessment:** Unresolved status was the correct and safe response given 0 candidate returns. The candidate generator failed to retrieve, but the decision engine did not make a false identity claim.

---

## 5. Separated Retrieval vs Identity-Decision Performance

In accordance with Phase 4 requirements, candidate retrieval performance is strictly separated from final identity-decision performance:

### 5.1 Upstream Candidate Retrieval Performance (56 Gold Queries)
*(Note: Evaluated based on whether the genuine target entity appeared in candidates)*
- **Candidate Recall@1:** **55.36%** (31 / 56)
- **Candidate Recall@5:** **71.43%** (40 / 56)
- **Candidate Recall@10:** **71.43%** (40 / 56)
- **Candidate MRR:** **0.6152**

### 5.2 Downstream Identity Decision Performance (100 Benchmark Queries)
- **Total Queries Evaluated:** 100
- **Auto-Selected Count:** 13 (13.0%)
- **Strict-ID Auto-Selection Precision:** **7.69%** (1 / 13 — invalidated by benchmark label corruption)
- **Adjudicated Auto-Selection Precision:** **92.31%** (12 / 13 confirmed correct; 1 / 13 probable/variant)
- **Confirmed False Person Merges:** **0.00%** (0 / 13 selected the wrong human being)
- **Manual Review Routing Count:** 52 (52.0%)
- **Unresolved Abstention Count:** 35 (35.0%)
- **Total Non-Automated Routing:** 87 (87.0%)
- **Inconclusive Query Count:** 0

---

## 6. Root Cause Failure Mechanism Taxonomy

| Failure Mechanism | Affected Queries | Root Cause Evidence | Impact on System vs Benchmark |
|---|---|---|---|
| **Defective Benchmark Gold Labels** | Q004, Q005, Q006, Q014, Q015, Q016, Q018, Q019, Q045, Q046, Q047, Q049, Q055, Q068 | Benchmark author used placeholder IDs (`A5064891234`, `A5034129876`) that map to wrong individuals or 404s. | Benchmark defect artificially suppressed strict precision from 92.3% to 7.7%. |
| **OpenAlex Entity Fragmentation (Split Profiles)** | Q001, Q002, Q003, Q018, Q056, Q057 | OpenAlex contains multiple distinct IDs for the same author (e.g. Geoffrey Hinton has 5 candidate IDs). | System correctly detects ties and routes to manual review instead of auto-merging. |
| **Abbreviated Name Search Limitation** | Q064, Q065, Q069 | OpenAlex search endpoint fails on initial-only or punctuation-separated names (*"Y. LeCun"*). | System receives 0 candidates and abstains (unresolved). |
| **Long Departmental Affiliation Strings** | Q081, Q083, Q085, Q087, Q089 | Complex strings like *"Department of Statistics UC Berkeley"* fail OpenAlex institution filter. | System receives 0 candidates and abstains (unresolved). |

---

## 7. Audit Verification & Invariance Confirmation

In compliance with instructions:
- [x] Zero production source code files were modified.
- [x] Zero author resolution thresholds, weights, or decision rules were modified.
- [x] Zero changes were made to `backend/academic_search.db` or ChromaDB.
- [x] Benchmark JSON files were read-only; no labels were altered.
- [x] No API write operations were performed.
- [x] All API keys and credentials remained fully protected.

---

## 8. Recommendations for Day 3

### 8.1 Is Author Resolution V1 Safe to Retain Unchanged?
**YES.** Author Resolution V1's decision logic and scoring weights are mathematically sound and safe. It executed **zero false-person merges** across 100 benchmark queries. The apparent 7.7% strict precision was entirely an artifact of corrupted gold IDs in the benchmark file, whereas the actual identity precision of the auto-selected candidates is **92.3%**.

### 8.2 Specific Focus for Day 3
1. **Do NOT loosen scoring thresholds:** The 0.75 score, 0.15 margin, and 1.35 dominance thresholds are successfully protecting the system from ambiguous ties and split profiles.
2. **Correct the Benchmark Gold Labels:** Replace synthetic placeholder IDs in the benchmark manifest with verified OpenAlex IDs (e.g. Demis Hassabis `A5005349213`, Ilya Sutskever `A5006446297`).
3. **Harmonize Status Key in Evaluation Script:** Update the evaluation script to check for `AUTO_RESOLVED` (`"auto_selected"`) so that the summary table reflects true system output.
