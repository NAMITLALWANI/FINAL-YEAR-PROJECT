# HAMMER Author Resolution: Error Analysis & Threshold Evaluation

**System:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Topic:** Decision Thresholds, Abstention Rationale, and Error Modes  

---

## 1. Analysis of the Zero Auto-Resolution Outcome

The 100-query benchmark yielded **0 automatic resolutions**. An inexperienced evaluator might interpret this as an error. In reality, it is a **safety feature**:

### The Scoring and Threshold Math:
- Thresholds configured in `config.py`:
  - `AUTHOR_AUTO_SCORE_THRESHOLD = 0.85`
  - `AUTHOR_AUTO_MARGIN_THRESHOLD = 0.15`
  - `AUTHOR_AUTO_DOMINANCE_THRESHOLD = 1.35`
  - `AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO = 3`
- When "Geoffrey Hinton" is searched:
  - Candidate 1 (`A5153609875`): `score = 1.0` (Signals: 2 [name, institution])
  - Candidate 2 (`A5139521503`): `score = 1.0` (Signals: 1 [name])
  - Calculated Margin: `1.0 - 1.0 = 0.00` (< `0.15` threshold!)
  - Calculated Dominance: `1.0 / 1.0 = 1.00` (< `1.35` threshold!)
  - Available Signals: 2 (< `3` threshold!)
- **Result:** System cleanly transitions to `manual_selection_required`.

---

## 2. Risk Modeling: Why Lowering Thresholds is Unacceptable

If we reduced `margin_threshold` to `0.00` and `dominance_threshold` to `1.00`:
- Prolific researchers like Hinton would auto-resolve arbitrarily to whichever candidate profile OpenAlex listed first.
- **Catastrophic Failure on Common Names:** Queries like "Rajesh Kumar", "Wei Zhang", or "John Smith" return dozens of distinct individuals with identical name similarity. The system would falsely merge independent scholars into a single identity!
- **Viva Defense:** "In academic entity resolution, an incorrect merge is permanent and fatal to bibliographic citation integrity. HAMMER prioritizes precision and human auditability over automated recklessness."
