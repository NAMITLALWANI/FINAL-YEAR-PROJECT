# HAMMER Stage 2 — Research Design

**Status:** Design proposal for owner review; no new labels or experiments were created
**Audit baseline:** committed Git HEAD d41378cf4781a9bec8738ff60899ecec43227b6f, 19 November 2026
**Repository:** the existing FINAL-YEAR-PROJECT checkout

## Accepted direction

The paper is an applied systems study of provenance-aware scholarly metadata integration and conservative author identity decisions.

- **Primary empirical question:** RQ2, author candidate retrieval and selective author resolution.
- **Conditional secondary question:** RQ1, publication deduplication, only after the edition-detector defect and historical result conflicts are reconciled.
- **Supporting system capabilities:** RQ3 retrieval and RQ4 generated explanations. They are not independent performance questions because their judgment sets are absent.
- No algorithmic novelty, universal safety, or application-scale performance claim is planned.

See the [Stage 0/1 proposal](../HAMMER_STAGE0_STAGE1_IDEATION_PROPOSAL.md), [historical evidence timeline](../HISTORICAL_EVIDENCE_TIMELINE.md), [claim/evidence matrix](../CLAIM_EVIDENCE_MATRIX.md), and [evaluation dataset protocol](../../evaluation/dataset.md).

## Current evidence that shapes Stage 2

The sealed V3 author benchmark contains 100 rows: 50 Confirmed, 6 Probable, and 44 controls. Its 56 positive rows refer to 33 distinct OpenAlex author IDs. The sidecar canonical-evidence file covers 24 of those 33 IDs; nine have no matching sidecar entry. V3 rows include free-text notes but no row-level external evidence links or blinded annotation trail. OpenAlex is both the candidate source and the gold-ID namespace. V3 is useful for historical software shakedown, but not a confirmatory independent test set.

The stored V3 outcomes and the Day 5 candidate artifact are not a single aligned experiment: their top candidate differs on 30 of 56 positive rows. Recalculation of Recall@k from the Day 5 candidate IDs against the later V3 labels is exploratory and must not be described as an end-to-end resolver result.

The dedup benchmark is a hand-authored 50-pair challenge set in backend/scripts/run_remaining_evaluations.py: 33 same, 15 different, and 2 uncertain. Historical reports disagree on category counts and system outputs; the current aggregate has no pair-level predictions for both historical implementations. The committed edition detector contains two U+0008 backspace characters where word-boundary escapes appear intended. See the [dedup replay protocol](DEDUP_REPLAY_PROTOCOL.md).

## RQ2 and hypotheses

### RQ2a — Candidate retrieval

**Question:** On independently identified test people with at least one externally verified OpenAlex profile at the evaluation cutoff, how often does each frozen query strategy retrieve a profile for the intended person, and how high does it rank that profile?

**H2a:** The committed normalized/multi-strategy procedure will improve candidate Recall@k or MRR over raw-input search on the same identity-disjoint test queries. Report by Confirmed identity group. A result is inconclusive when intervals are wide or captured provider responses are inadequate for replay.

The retrieval unit is a query/identity group. Candidate rank is the source-returned order before HAMMER evidence scoring. Resolver ranking and assignment are evaluated separately.

### RQ2b — Selective author resolution

**Question:** On one identical, frozen candidate pool per query, do HAMMER's five-signal evidence ranking and decision gates reduce erroneous automatic assignments versus simpler policies while retaining useful automatic coverage?

Compare three policies over precisely the same candidate IDs, payloads, query context, and evidence snapshot:

1. **Name-only forced top-1:** rank by name similarity alone and select the first candidate whenever the pool is nonempty.
2. **Full-evidence forced top-1:** use the committed five-signal ranking and select its first candidate whenever the pool is nonempty.
3. **Full-evidence selective policy:** use the same ranking and the committed automatic/manual/unresolved gates.

The comparison between policies 2 and 3 isolates the effect of abstention gates. The comparison between policies 1 and 2 describes the effect of additional evidence while forcing a choice. No decision baseline may use a different candidate pool.

**H2b (main study, after pilot):** At frozen thresholds, compare selective risk and coverage for full-evidence selective resolution and full-evidence forced top-1 on the same pool. The pilot does not test this hypothesis or support accuracy claims. No minimum coverage floor is adopted.

Candidate retrieval strategies naturally produce different pools; that is the retrieval comparison. For resolution, all policies use the one frozen committed-strategy pool. Candidate-source failures and successful empty responses are tracked separately and are never recoded as resolver abstentions.

## Proposed benchmark and test split

First conduct the approved protocol pilot with 10 resolved identities and 5 unresolved controls. Its purpose is evidence availability, rubric clarity, reviewer agreement, pool sizes, mapping difficulty, and workload only. It is not a performance evaluation. Reassess the main-study size after the pilot using observed workload and data availability. The prior 40/20/60 split is not approved. Preserve identity-disjoint splits and blinding in any later study.

The pilot reports descriptive workflow counts only. It must not report author-resolution accuracy or use a statistical pass criterion. Any later main-study precision estimate must identify its actual automatic-decision denominator and uncertainty.

For a future main study, freeze query seeds, independent labels, identity-disjoint split membership, thresholds, and metric formulas before candidate requests or prediction outputs are inspected. This split is a proposal; the current benchmark is unchanged.

## Frozen order of operations

1. Freeze questions, source cutoff, label rubric, sampling frame, baseline definitions, split rules, metric formulas, coverage floor, and claim limits.
2. Sample query seeds without examining predictions or candidate lists.
3. Establish independent labels with two reviewers and adjudication. Seal label and split hashes.
4. Freeze the software baseline, environment, resolver/scoring configuration, and exact thresholds.
5. Capture every retrieval arm's request, raw API response, timestamp, payload, and ordered candidate IDs. Do not rely on a future live API call for replay.
6. Freeze a common committed-strategy candidate pool and all resolver inputs.
7. Produce per-query predictions for every baseline against that same pool; hash inputs and outputs.
8. Unseal the test once, calculate predeclared metrics, and preserve failures, empty results, abstentions, and exclusions.
9. Any test-informed change requires a new version and a new sealed test.

## Reproducibility record

Each run identifies Git SHA and dirty state, Python/runtime and packages, configuration and thresholds, code hashes, query/label/split hashes, strategy, source request parameters, UTC times, raw response hashes, candidate IDs and payload hashes, evidence/database snapshot hashes, prediction hashes, metric version, and run ID. Because OpenAlex is live, captured responses—not an assertion of a provider-wide historical snapshot—are the replay source. Record the source cutoff and API response metadata. A source failure retains its error code and is never treated as an empty successful result.

Reuse the current templates and validator under docs/evaluation/templates and backend/scripts where schemas fit. Any new candidate-to-gold crosswalk or multiple strategy manifests is a later, separately reviewed data/tooling change; this proposal does not edit those artifacts.

## Claim boundary

A successful independent test supports only a bounded statement about the frozen HAMMER version, source, cohort, and thresholds. It cannot establish universal author accuracy or safety, generalize to every scholarly source, prove OpenAlex IDs are people, or show semantic retrieval changes identity decisions. V3 and the current dedup challenge can support historical or software-shakedown descriptions only until independence, alignment, and provenance gaps are addressed.

See [metric definitions](METRIC_DEFINITIONS.md), [split/leakage plan](DATA_SPLIT_AND_LEAKAGE_PLAN.md), [RQ2 experiment protocol](EXPERIMENT_PROTOCOL_RQ2.md), [author benchmark protocol](AUTHOR_BENCHMARK_PROTOCOL.md), and [updated claim/evidence matrix](UPDATED_CLAIM_EVIDENCE_MATRIX.md).
