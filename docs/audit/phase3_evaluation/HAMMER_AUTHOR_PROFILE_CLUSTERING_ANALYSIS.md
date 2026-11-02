# HAMMER Author Profile Duplication & Entity Clustering Feasibility Analysis

**Audit Phase:** Phase 3B — Author Resolution Deep-Dive  
**Date:** November 2026  
**Auditor:** Entity Disambiguation & Machine Learning Systems  
**Status:** Investigation Completed; Entity Clustering Evaluated (Not Implemented)  

---

## 1. Executive Summary

Phase 3 established that Author Resolution V1 achieved a **0.0% automatic resolution coverage rate** across 10 evaluation queries, routing 9 out of 10 queries (90%) to human manual review. Even for world-famous, distinctive Turing Award laureates (Geoffrey Hinton, Yoshua Bengio, Yann LeCun) with explicit institutional hints, HAMMER refused to auto-resolve.

This investigation determined the exact empirical root cause: **OpenAlex author profile entity fragmentation**.

Because OpenAlex contains multiple split candidate records for the same real-world researcher, HAMMER's margin (`0.15`) and dominance (`1.35`) thresholds correctly detect that candidate #1 and candidate #2 are tied or near-tied. The resolver, lacking cross-candidate entity awareness, assumes candidate #2 is a distinct competing human being and safely abstains.

---

## 2. Empirical Candidate Profile Investigation

We queried OpenAlex directly for the three canonical Turing laureates. Below is the exact entity breakdown returned by OpenAlex:

### 1. Geoffrey Hinton (5 Candidate Profiles in OpenAlex)

| Candidate # | OpenAlex ID | Display Name | Works | Citations | Affiliations | Years Active | Nature of Profile |
|---|---|---|---|---|---|---|---|
| **1** | `A5108093963` | *Geoffrey E. Hinton* | 556 | 531,769 | Univ. of Toronto, Microsoft, Google, CIFAR | 1976–2026 | **Canonical Primary Profile** |
| **2** | `A5098035523` | *James A. Anderson and Geoffrey E. Hinton* | 1 | 50 | *(None)* | 2013–2025 | Compound Author Name Error in OpenAlex |
| **3** | `A5153609875` | *Geoffrey Hinton* | 4 | 0 | **University of Toronto** | 2019–2026 | **Fragment Split Entity of Geoffrey Hinton** |
| **4** | `A5160214549` | *Professor Geoffrey Hinton* | 1 | 0 | *(None)* | 2024–2024 | Honorific Prefix Split Entity |
| **5** | `A5139521503` | *Hinton Geoffrey* | 1 | 0 | *(None)* | 2026–2026 | Inverted Name Split Entity |

### 2. Yoshua Bengio (4 Candidate Profiles in OpenAlex)

| Candidate # | OpenAlex ID | Display Name | Works | Citations | Affiliations | Years Active | Nature of Profile |
|---|---|---|---|---|---|---|---|
| **1** | `A5086198262` | *Yoshua Bengio* | 1,560 | 520,034 | Mila, CIFAR, Microsoft | 1987–2026 | **Canonical Primary Profile** |
| **2** | `A5129842707` | *Yoshua Bengio* | 5 | 0 | **Université de Montréal** | 2020–2026 | **Fragment Split Entity of Yoshua Bengio** |
| **3** | `A5160219784` | *Professor Yoshua Bengio* | 1 | 0 | *(None)* | 2024–2024 | Honorific Prefix Split Entity |
| **4** | `A5132658158` | *Dr. Yoshua Bengio\nUniversité de Montréal* | 1 | 0 | *(None)* | 2024–2024 | Malformed Title/Affiliation String Split |

### 3. Yann LeCun (2 Candidate Profiles in OpenAlex)

| Candidate # | OpenAlex ID | Display Name | Works | Citations | Affiliations | Years Active | Nature of Profile |
|---|---|---|---|---|---|---|---|
| **1** | `A5001226970` | *Yann LeCun* | 545 | 269,392 | Meta, Courant Institute, ENS | 1985–2026 | **Canonical Primary Profile** |
| **2** | `A5153612811` | *Yann LeCun* | 4 | 1 | **New York University** | 2022–2026 | **Fragment Split Entity of Yann LeCun** |

---

## 3. The Mathematics of Resolution Failure

When a user searches *"Geoffrey Hinton"* with institution hint *"University of Toronto"*:
- **Candidate 1 (`A5108093963`):** Matches name (1.0), matches institution hint via historical affiliation (1.0), matches active years (1.0). Renormalized score: **1.0000**.
- **Candidate 3 (`A5153609875`):** Matches name (1.0), matches institution hint as sole affiliation (1.0), active years (0.75). Renormalized score: **0.9643**.

### Evaluation of Thresholds:
```python
score_top = 1.0000
score_second = 0.9643

margin = score_top - score_second           # 1.0000 - 0.9643 = 0.0357 (Required: >= 0.15 ❌)
dominance = score_top / score_second        # 1.0000 / 0.9643 = 1.0370 (Required: >= 1.35 ❌)
```
Because the margin is **0.0357** (far below 0.15) and dominance is **1.037** (far below 1.35), HAMMER's decision logic in `services/author_resolution.py` triggers:
```python
if top >= AUTHOR_MANUAL_SCORE_THRESHOLD:
    return MANUAL_REVIEW, top, second, margin, dominance, "Candidate evidence is plausible but not sufficiently separated for automatic resolution."
```

**The decision logic executed flawlessly according to its engineering specification.** It did not fail. Rather, the assumption that each OpenAlex candidate ID maps to a unique human being is violated by OpenAlex's real-world database.

---

## 4. Evaluation of Entity Clustering (Pre-Resolution Grouping)

Can entity clustering safely group duplicate external profiles *before* computing margin and dominance?

### Proposed Conceptual Design:
Before scoring candidates against each other:
1. Construct an undirected graph where nodes are candidate profiles.
2. Add an edge between Candidate $i$ and Candidate $j$ if:
   - Normalized name similarity $\ge 0.95$, **AND**
   - At least one of the following holds:
     a. Primary affiliations overlap ($	ext{sim} \ge 0.85$).
     b. Shared coauthors $\ge 1$.
     c. Citation count ratio exceeds $100:1$ and the smaller profile has $\le 5$ works with overlapping active years.
3. Compute Connected Components (Union-Find) to form **Candidate Entity Clusters**.
4. Merge each cluster into a single composite candidate (preserving all source IDs and taking the maximum works/citation counts).
5. Compute margin and dominance *between clusters*, not individual candidate rows.

### Safety Analysis & Risks:
- **Risk 1 (False Merges on Common Names):** On "Rajesh Kumar" or "Wei Zhang", two distinct people frequently share an institution (e.g. "IIT Delhi" or "Tsinghua University"). An aggressive clustering heuristic would erroneously merge two different scholars before resolution.
- **Risk 2 (Father / Son Researchers):** Researchers in the same family sharing a last name and initial at the same institution (e.g., J. Smith and J. Smith).
- **Compliance Status:** **Not Implemented.** Per strict Phase 3B rules, entity clustering was evaluated conceptually but not implemented.

---

## 5. Methodological Critique: Ground-Truth Dataset & Recall@K

The Phase 3 benchmark summary reported:
- *"Candidate Recall@1 = 100% on distinctive author names."*
- *"Candidate Recall@5 = 100%."*

### Why These Metrics Cannot Currently Be Justified:
In academic literature (e.g., S2AND, WhoIsWho), Recall@K is defined as:
$$	ext{Recall}@K = rac{1}{|Q|} \sum_{q \in Q} \mathbb{I}(	ext{gold\_author\_id}_q \in 	ext{top\_K\_candidates}_q)$$

1. **Absence of Ground-Truth Labels:** In this repository, `docs/evaluation/templates/identity_labels.csv` contains only column headers. There is no independent, adjudicated mapping between query strings and verified OpenAlex author IDs.
2. **Ambiguity of Target Identity:** For "Geoffrey Hinton", is the gold target `A5108093963` or `A5153609875`? Without an adjudicated label set defining equivalence classes, claiming that Candidate #1 is the "correct" target is an informal heuristic observation, not an objective research measurement.
3. **Correct Scientific Standard:** Until the 100-query benchmark is populated with double-reviewed ground-truth targets, HAMMER must report candidate retrieval as:
   - *"Qualitative verification on 10 seed queries confirmed that prominent candidate profiles were retrieved in top-3 rankings, but formal Recall@K metrics await gold dataset annotation."*