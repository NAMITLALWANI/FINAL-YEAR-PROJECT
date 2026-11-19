# RQ1 — Deduplication Replay Protocol

**Status:** Conditional secondary study; no source code, labels, or results were changed
**Replay baseline:** committed Git HEAD d41378cf4781a9bec8738ff60899ecec43227b6f

## Current benchmark audit

The 50-pair list is in backend/scripts/run_remaining_evaluations.py. Its labels are 33 same, 15 different, and 2 uncertain. Committed category counts are:

| Category | Pair count |
|---|---:|
| Exact DOI | 10 |
| DOI conflict | 5 |
| Identical title | 10 |
| Punctuation difference | 4 |
| Subtitle difference | 7 |
| Author order | 4 |
| Similar title / different publication | 10 |
| **Total** | **50** |

Older verification prose reports different category sizes and category-level outcomes than the current committed pair list. Historical aggregates state an earlier V1 outcome of TP=32, FP=2, TN=13, FN=1 and a later V2 aggregate of TP=33, FP=0, TN=15, FN=0 over 48 decided pairs. The later aggregate does not preserve pair-level predictions for both versions, so the improvement is not a paired replay result. The labels are hand-authored challenge labels; row-level external bibliographic evidence and independent dual review are not established in the source list. This is not a representative production sample.

The edition regex at backend/deduplication/engine.py line 91 contains two literal U+0008 BACKSPACE characters inside a raw regular expression. This is source inspection, not a test result. The proposed minimal repair replaces those control characters with literal backslash-b word-boundary escapes. No code change was made.

## Preconditions before reporting RQ1

1. Freeze the exact 50 pair inputs, labels, categories, script hash, and Git SHA. Emit a canonical pair-level file and hash only after approval; do not edit the current source list in this design task.
2. Have two reviewers verify each pair's work-identity label against bibliographic records and stable DOI/publisher metadata, blind to predictions. Adjudicate disagreements and retain uncertain labels. If artificial or inaccurate DOI/title examples cannot be validated, retain the set as a software challenge only.
3. Reconcile the current pair list with category tables in prior reports. Do not copy category metrics until pair IDs and labels match exactly.
4. Record the precise legacy V1 algorithm and exact repaired V2 source. Any repair must be a minimal versioned change in the existing Git checkout, with old code represented in Git history; do not create another project checkout or overwrite earlier reports.
5. Produce one row for every pair and every implementation, including pair hash, gold label, merge/non-merge decision, reason/features, source version, and run ID. Keep uncertain rows visible.
6. Review paired outputs before calculating summary metrics.

## Replay arms

If preconditions pass, run the same frozen pair data through:

- **Legacy V1 baseline** as defined by its preserved implementation and historical specification.
- **Committed V2 at HEAD** only if needed to reconcile the historical aggregate; label this defect-preserving result diagnostic.
- **V2 with minimal edition-regex correction** as the candidate corrected implementation.

Use one checkout and Git history for version traceability. Do not use mutable application database rows as benchmark inputs. This proposal does not authorize a replay.

## Metrics and interpretation

For the 48 adjudicated binary pairs, report TP, FP, TN, FN; precision, recall, F1, decided-pair accuracy, and exact denominators. Report the two uncertain pairs separately with each implementation's merge/non-merge behavior; do not count them as correct or incorrect. Report decision coverage as binary-labeled pairs / 50 and provide a paired V1-versus-corrected-V2 disagreement table and per-pair error list.

Do not infer a population error rate or make broad claims from this curated challenge set. Avoid significance testing unless a method is registered and justified. The bounded result is behavior on these named challenge cases and whether the edition fix changes relevant outcomes.

## Claim gate

RQ1 may appear as a conditional secondary result only after input/label reconciliation and paired replay. If label verification or pair-level provenance fails, report implementation inspection and the challenge-set limitation without a performance claim. Historical confusion matrices remain historical reports until reproduced under this protocol.
