# HAMMER Stage 2 — Decision Register

**Baseline:** committed Git HEAD d41378cf4781a9bec8738ff60899ecec43227b6f
**Purpose:** Separate accepted direction from proposed experimental choices

Status values: **Approved** means carried forward from the user's accepted Stage 0/1 direction or explicit task constraints. **Proposed** means a Stage 2 protocol choice awaiting review. No item authorizes implementation or experimentation.

| ID | Decision | Status | Rationale / next gate |
|---|---|---|---|
| D01 | RQ2 author candidate retrieval and selective author resolution is the primary empirical question. | Approved | Accepted Stage 0/1 direction. |
| D02 | RQ1 deduplication is conditional secondary work after defect and historical result reconciliation. | Approved | Accepted Stage 0/1 direction. |
| D03 | RQ3 retrieval ranking and RQ4 semantic explanation remain supporting capabilities, not current performance questions. | Approved | Judgment sets are insufficient. |
| D04 | Establish intended-person truth before candidate generation from external non-OpenAlex evidence; OpenAlex IDs are profile IDs, not gold-person truth. | Approved | Two reviewers and adjudication address source circularity. |
| D05 | Map candidates to gold people in a separate blinded review after truth and split freeze. | Approved | Separates label creation from provider-profile evaluation. |
| D06 | Reuse current identity templates; add a candidate-to-gold crosswalk only after schema review if required. | Proposed | Do not overload source-scoped gold IDs or change templates now. |
| D07 | Retrieval arms are raw input, NFC/whitespace normalization, and committed cleaner plus initials fallback. | Proposed | Describe search procedures honestly; none is literal exact lookup. |
| D08 | Use full-evidence forced top-1 and selective gates on the same pool; retain name-only only if exact offline reproduction is verified. Null top score means no assignment and a separate no-score outcome. | Approved | No application change; omit name-only if verification fails. |
| D09 | Pilot is 10 resolved identities and 5 unresolved controls; reassess main-study size after pilot. | Approved | Original 40/20/60 split is deferred, not approved. |
| D10 | Use resolved, unresolved, uncertain; unresolved is not nonexistence. Do not introduce a separate Probable grade initially. | Approved | Historical V3 Probable is never encoded as resolved. |
| D11 | Do not adopt a 10% pass/fail coverage floor; report actual coverage with selective risk. | Approved | Freeze thresholds before any sealed-test evaluation. |
| D12 | Report Recall@1/5/10 and MRR separately from auto precision/risk, coverage, review, unresolved, and source failures. | Proposed | Exact formulas and denominators are in METRIC_DEFINITIONS.md. |
| D13 | Pilot reporting is descriptive: exact counts, denominators, suitable intervals; no accuracy claim, minimum auto-decision count, or pass criterion. | Approved | Any main-study objective is revisited after pilot. |
| D14 | Correct the dedup regex only as a separately approved minimal change, then replay the same frozen pairs through legacy V1 and corrected V2. | Proposed | Defect is source-inspected; no fix or replay here. |
| D15 | Treat V3 and historical dedup aggregates as exploratory until independent labels, aligned snapshots, and pair-level outputs exist. | Proposed | Label/run provenance is incomplete or misaligned. |
| D16 | No application modifications, benchmark changes, labels, threshold changes, replay, or experiments in this Stage 2 design task. | Approved | Explicit task constraint. |
| D17 | Preserve one existing Git checkout and pre-existing local modifications; do not create another project copy. | Approved | Explicit user instruction. |
| D18 | Do not replace Stage 0/1 documents, existing claim matrix, reference audit, or paper draft. | Approved | Stage 2 records are additive. |
| D19 | Bibliographic cleanup is outside this write; reference files remain untouched. | Approved | Any corrections need a later scoped edit and source verification. |

## Owner decision record — 19 November 2026

Approved: 10-resolved/5-unresolved workflow pilot; descriptive reporting only; statuses resolved/unresolved/uncertain; no separate Probable grade; no 10% coverage floor; no assignment on a null top score; conditional name-only arm; Stage A/Stage B blinding and identity-disjoint leakage safeguards. The full 40/20/60 design is deferred pending actual pilot feasibility evidence. The pilot is not an experiment or performance evaluation.
