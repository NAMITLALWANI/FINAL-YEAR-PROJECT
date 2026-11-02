# HAMMER — Author Resolution V1 Scoring & Evidence Review

## 1. Executive Summary

This report evaluates the mathematical rigor, evidence signals, dynamic weight renormalization, and decision policy implemented in **Author Resolution V1** (`author_evidence.py`, `author_scoring.py`, and `author_resolution.py`).

### Key Conclusion: Safe Against Sparse Evidence False Positives
The audit confirms that the Author Resolution V1 engine **does NOT allow sparse evidence (such as a name match alone) to produce an automatic identity resolution**. Even though dynamic weight renormalization scales available signals to 1.0, the decision policy explicitly mandates:
1. `top_score >= 0.75` (Score Threshold)
2. `available_signals >= 2` (**Minimum Signal Diversity Constraint**)
3. `margin >= 0.15` (Separation from Runner-Up)
4. `dominance >= 1.35` (Ratio over Runner-Up)

If a candidate has only a name match (1 available signal), `available_signals < 2` unconditionally fails the automatic resolution check and routes the candidate safely to **`manual_selection_required`**.

---

## 2. Signal Extractors & Availability Mechanics

Author Resolution V1 extracts 5 orthogonal signals for every candidate profile:

| Signal Name | Baseline Weight | Extractor Logic | Availability Condition | Missing Evidence Handling |
| :--- | :--- | :--- | :--- | :--- |
| **`name_similarity`** | **0.35** | `fuzz.token_sort_ratio` against candidate display name and aliases | Available if query text and candidate names exist | Marked `unavailable` if query is empty; returns score `None` |
| **`institution_similarity`** | **0.25** | `fuzz.token_set_ratio` against candidate affiliation history | Available only if user supplies `institution_hints` AND candidate has affiliations | Marked `unavailable` if hint is omitted or profile has no affiliations |
| **`publication_overlap`** | **0.20** | Intersection of exact DOIs and normalized titles against seed publications | Available only if query context includes sample publications | Marked `unavailable` if publication context is missing |
| **`coauthor_overlap`** | **0.10** | Overlap of normalized coauthor names | Available only if coauthors are provided in context | Marked `unavailable` if coauthor context is missing |
| **`temporal_compatibility`** | **0.10** | Overlapping publication years between query range and OpenAlex counts | Available only if `active_year_start/end` are provided | Marked `unavailable` if date bounds are missing |

---

## 3. Dynamic Weight Renormalization Analysis

When certain signals are missing (e.g., the user did not provide an institution hint or coauthors), HAMMER renormalizes the active signals using `author_scoring.py`:

```python
active_weights = {
    sig: weight for sig, weight in AUTHOR_SCORE_WEIGHTS.items()
    if sig in available_evidence
}
available_sum = sum(active_weights.values())
if available_sum == 0:
    return CandidateScore(score=None, ...)

renormalization_factor = 1.0 / available_sum
effective_weights = {
    sig: weight * renormalization_factor
    for sig, weight in active_weights.items()
}
final_score = sum(
    evidence[sig].normalized_score * effective_weights[sig]
    for sig in active_weights
)
```

### Mathematical Example: Name-Only Candidate
- User queries `"Geoffrey Hinton"` without institution, coauthor, or publication hints.
- Only `name_similarity` is available (`normalized_score = 1.00`).
- `available_sum = 0.35`.
- `renormalization_factor = 1.0 / 0.35 = 2.857`.
- `effective_weight = 0.35 * 2.857 = 1.00`.
- **Calculated candidate score = 1.00**.

### Why This Does NOT Cause False-Positive Auto-Resolution
While the mathematical score is 1.00, the decision function `decide()` in `author_resolution.py` enforces:

```python
strong = (
    top >= AUTHOR_AUTO_SCORE_THRESHOLD                         # 1.00 >= 0.75  (PASS)
    and ranked[0].score.available_signals >= AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO  # 1 >= 2 (FAIL!)
    and (second is None or (margin >= AUTHOR_AUTO_MARGIN_THRESHOLD and (dominance is None or dominance >= AUTHOR_AUTO_DOMINANCE_THRESHOLD)))
)
```
Because `available_signals` is **1**, `strong` is **`False`**.
The resolver proceeds to the next condition:
```python
if top >= AUTHOR_MANUAL_SCORE_THRESHOLD:  # 1.00 >= 0.45 (PASS)
    return MANUAL_REVIEW, top, second, margin, dominance, "Candidate evidence is plausible but not sufficiently separated for automatic resolution."
```
**Decision: `MANUAL_REVIEW` (`manual_selection_required`)**.
Automatic resolution is strictly prevented.

---

## 4. Multi-Candidate Competition & Disambiguation

When a common name (e.g. `"John Smith"`) generates multiple OpenAlex profiles:
1. **Candidate Margin:** $\Delta = 	ext{Score}_{	ext{top}} - 	ext{Score}_{	ext{runner-up}}$.
   - Must be $\ge 0.15$ for auto-resolution. If two profiles score 0.85 and 0.80 ($\Delta = 0.05$), auto-resolution is aborted.
2. **Dominance Ratio:** $ho = rac{	ext{Score}_{	ext{top}}}{	ext{Score}_{	ext{runner-up}}}$.
   - Must be $\ge 1.35$. If $ho = rac{0.85}{0.80} = 1.06$, auto-resolution is aborted.
3. **Audit Trail Persistence:** Every decision persists signal-by-signal raw JSON values, normalized scores, effective weights, and source URLs in `author_resolution_evidence`.

---

## 5. Potential Risk Areas & Recommendations

1. **Two-Signal False Positives:**
   - If an author has an exact name match (0.35) and an overlapping publication year span (0.10), `available_signals = 2`.
   - If no runner-up exists, this candidate could achieve `score = 1.00` and `available_signals = 2`, triggering auto-resolution.
   - **Recommendation:** Increase `AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO` from `2` to `3` for queries without institutional hints, or require `institution_similarity` or `publication_overlap` as a mandatory positive signal for auto-resolution.
2. **Preserve Current Code:**
   - In accordance with audit instructions, no threshold modifications have been applied during preflight.
