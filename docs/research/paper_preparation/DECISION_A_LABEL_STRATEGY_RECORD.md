# Decision A: main-evaluation label strategy (record and proposed manuscript wording)

**Date:** 20 November 2026. **Status:** Decision A approved by the research director with corrections (this is revision 2 of the record). Decisions B and C are open and the evaluation is unfrozen. This file is new. It does not edit the earlier decision register in `docs/research/stage2/`, the manuscript, any seed, dataset or evaluation artifact. The LaTeX in section 4 is **proposed wording for review and has not been applied** to `paper/`.

## 1. The five statements the record must carry
1. The primary condition-policy pair is **C1 with the full selective policy** (`selective_policy_v2`).
2. **Only that pair** defines the primary automatic-assignment verification population. Forced top-one, the threshold-gate ablation, C0 and C1x never enlarge it.
3. The random audit draws from the **entire non-automatic frame** of that pair. The frame includes cases with no mapped profile and is defined without benchmark identity labels or any knowledge of whether a candidate is correct.
4. The measured label-error rate **is not transferable** to automatic assignments, to other conditions or to other policies.
5. Any **stratum-merging rule is specified before the draw**, before the selected cases or their labels are seen. The original stratum counts are kept and reported even when strata are merged for sampling.

## 2. Decision register (as approved)
| Item | Decision |
|---|---|
| Label strategy | **A3**: benchmark-derived labels are provisional; independent verification where a claim depends on it |
| Primary pair | C1 + `selective_policy_v2` |
| Automatic assignments of the primary pair | Independently verify **every one** |
| Random audit frame | **All non-automatic cases** of the primary pair, including cases with no mapped profile |
| Audit timing | Drawn only after capture and replay under frozen thresholds, weights, code and policy |
| Audit sampling | Proportional stratified draw by LAGOS block size; **largest-remainder rounding**; deterministic SHA-256 hash order within each stratum |
| Selection | Predeclared audit seed; frozen case manifest recording seed, dataset version, manifest hash, original stratum sizes, any merged strata, selection probabilities and selected case IDs |
| Stratum merging | Allowed only if allocation would leave a stratum inadequately represented; rule fixed before the draw; original counts preserved and reported |
| Audit size | **Pending** the reviewer-time pilot under Decision B (the memo's 30 cases is an illustration only) |
| Label-error estimate | Describes only the sampled non-automatic primary-pair frame. Reported alongside its benchmark-derived results with its interval. **Never used to correct metrics. Never attached to automatic assignments, other conditions or other policies** |
| Other conditions and policies | Reported as **benchmark-derived**. Verified precision for any other policy would need its own verification design |
| Label states | Resolved, unresolved, uncertain, unverifiable |
| Uncertain and unverifiable | Visible in reporting; excluded from primary rates; sensitivity-tested (all wrong, all right) |
| Reporting classes | Each case in exactly one: `Verified (n = …)`, `Uncertain (n = …)`, `Unverifiable (n = …)`, `Benchmark-derived (n = …)`; an audited case is Verified (or Uncertain or Unverifiable), never also Benchmark-derived; never one pooled accuracy figure |
| Unresolved controls | Measure **dropped** unless a separate independently labelled control set is built |
| Blinding for verifying automatic assignments | Full shuffled candidate pool, opaque IDs, no HAMMER selection, rank, score or decision visible; identity-to-candidate mapping held separately. A condition of A, not only of B |
| Scope qualification | The audit estimates benchmark-label validity in the sampled frame. It does not establish the correctness of every benchmark-derived retrieval result and does not replace verification of automatic assignments |

### Clarifications approved in principle (previously proposed)
| # | Clarification | Outcome |
|---|---|---|
| 1 | Definition of automatic | **Corrected**: primary pair C1 + `selective_policy_v2`; others benchmark-derived; the audit's error rate is not attached to them (this removes the earlier inconsistency with clarification 5) |
| 2 | Audit timing | Approved |
| 3 | One reporting class per case | Approved |
| 4 | Allocation rule | Approved with refinement: largest-remainder rounding, hash order, merging rule fixed in advance, original counts reported |
| 5 | No extrapolation | Approved, now extended to automatic assignments, other conditions and other policies |

## 3. Not decided and not adopted
- Reusing a verified case label for other policies on the same pool. It is technically possible, because C0, C1 and C1x share one R2 pool, but the decision is to report other policies as benchmark-derived. Revisit only with its own design.
- Which RQ2a retrieval results the audit estimate may accompany. **Resolved by the director's review of Decision C (20 November 2026), recorded in `DECISION_C_STATISTICAL_DESIGN_PROPOSAL.md` (C6):** none. Overall retrieval is reported as benchmark-derived ORCID agreement with its denominator; verified retrieval is reported separately for the cases actually verified; the audit's label-error rate describes only the non-automatic frame of the primary pair and is never applied to retrieval results.

## 4. Proposed manuscript wording (not applied)

### 4.1 Section 5: replace the second paragraph of the label-audit subsection and add a label-strategy subsection
```latex
\subsection{Label Strategy and Verification}
\label{sec:labels}
Two kinds of identity label are kept apart throughout. A \emph{benchmark-derived} label is the provisional ORCID-based mapping of Section~\ref{sec:benchmark}. It is never described as independently verified ground truth. A \emph{verified} label is reached by independent reviewers from evidence outside the benchmark labels (Section~\ref{sec:audit}).

The primary population is defined by one condition-policy pair: condition C1 under the full selective policy. An automatic assignment is an assignment made by that pair, and only that pair defines which assignments are verified. Every such assignment is verified independently. A pre-specified random sample of the remaining, non-automatic cases of the same pair is audited. The audit frame is the entire non-automatic set, including cases in which no candidate was mapped to the expected person, so that label problems, profile fragmentation and retrieval failure are not excluded. The frame is built after capture and replay under frozen thresholds, weights, code and policy, and it uses no benchmark identity label and no knowledge of whether a candidate is correct. The sample is stratified by block size with proportional allocation (largest-remainder rounding) and is drawn by a deterministic SHA-256 hash order under a predeclared seed. If strata must be merged, the rule is fixed before the draw, and the original stratum counts are still reported. The frozen manifest records the seed, the dataset version, the manifest hash, the original and merged stratum sizes, the selection probabilities and the selected case identifiers. The audit size is set after a reviewer-time pilot.
% TODO: audit size and the stratum-merging rule must be fixed before this text is frozen.

When a reviewer verifies an automatic assignment, the reviewer receives the complete candidate pool, shuffled and under opaque identifiers, and cannot see HAMMER's selected candidate, ranking, score or decision. Otherwise the verification would confirm the system's own choice. The mapping from identifiers to candidates is held separately.

Each case is labelled \emph{resolved}, \emph{unresolved}, \emph{uncertain} or \emph{unverifiable}. Uncertain and unverifiable cases remain visible in every table, are excluded from the primary rates, and are bracketed by a sensitivity analysis that counts them all as wrong and then all as right. Every case belongs to exactly one reporting class, \emph{Verified}, \emph{Uncertain}, \emph{Unverifiable} or \emph{Benchmark-derived}, each reported with its case count, and an audited case is never counted as benchmark-derived as well. Verified and benchmark-derived observations are never combined into one accuracy figure.

Conditions and policies other than the primary pair, namely C0, C1x, the threshold-gate ablation and forced top-one, are reported with benchmark-derived labels only. Their selections are not verified, and the audit described here does not validate them. Verified precision for another policy would need its own verification design.

The error rate of the benchmark-derived labels, estimated from the audit sample with its interval, describes only the sampled non-automatic frame of the primary pair. It is reported alongside the benchmark-derived results of that frame. It is not used to correct them, because a correction would require assumptions about how label errors affect outcomes, and it is not applied to automatic assignments, to other conditions or to other policies. The audit does not establish the correctness of every benchmark-derived retrieval result, and it does not replace the verification of automatic assignments.

The benchmark contains only resolved identities, and all 50 smoke seeds are labelled resolved. False acceptance on unresolved queries is therefore not measured, and that measure is omitted from the main evaluation unless a separate, independently labelled control set is built.
```
Two existing Section 5 statements then need a one-line edit for consistency: the last sentence of the label-audit subsection ("no main-evaluation claim will rest on unaudited ORCID equality alone") should point to Section~\ref{sec:labels}, and the definition of a false automatic assignment on an unresolved control in the metrics subsection should state that the measure is omitted.

### 4.2 Section 8: label-related threats (Section 8 is currently a stub)
```latex
\subsection{Label Validity}
The expected identity is derived from ORCID values, and OpenAlex profiles may carry ORCID values from overlapping sources, so benchmark agreement is not independent verification. Independent verification covers every automatic assignment of the primary pair and an audit sample of its non-automatic cases. Results for non-audited cases, and all results for other conditions and policies, rest on benchmark-derived labels. The audited error rate describes only the sampled frame, is reported but not used for correction, and is not transferable to other frames, conditions or policies. Uncertain and unverifiable cases are excluded from primary rates and may concentrate among hard cases, so primary rates may be optimistic; the sensitivity analysis bounds this effect.

\subsection{Unresolved Queries}
The benchmark and the smoke seeds contain no ambiguous queries. Neither measures how often HAMMER would assign automatically when no unique intended person exists, and no claim about false acceptance on unresolved queries is made.
```

## 5. Still open (unchanged)
Decision B (dossier contents, reviewers, reviewer-time pilot) and Decision C (one case per block, clustered inference, sample size). The audit size depends on B. Nothing is frozen, no dossiers exist, and no implementation has begun.
