# HAMMER Stage 2.1 — Protocol and Statistical Review

**Status:** Pilot approved; main-study design remains open  
**Baseline:** committed HEAD d41378cf4781a9bec8738ff60899ecec43227b6f  
**Scope:** Corrections to Stage 2 protocol documents only

## Problems identified

1. The draft paired 80 primary test cases (60 resolved identities plus 20 unresolved controls) with a claim that at least 60 automatic decisions were needed. Identity count and automatic-decision count are different. At a hypothetical 10% coverage, 80 cases would yield about eight decisions in expectation, if that rate generalized.
2. Ten percent coverage had been introduced as a pass/fail floor without an operational requirement or empirical basis.
3. Label prose used Confirmed/Probable alongside evaluator statuses resolved/unresolved/uncertain, creating an unsupported ambiguity.
4. The name-only arm did not specify its feature implementation, tie-breaking, null scores, or whether committed ranking supports custom weights. Retrieval arms did not state request limits, fallback failures, or ordering.
5. The proposed 160-case annotation workload was not quantified. Productivity or duration estimates are unavailable and have not been invented.

## Corrections made

- Distinguished total identity/query groups from observed automatic decisions throughout the sample and metric documents.
- Replaced the fixed “60 automatic decisions or exploratory” rule with actual-denominator intervals and explicit exploratory language when estimates are imprecise.
- Added the exact-binomial interval framework. With n independent automatic decisions and zero errors, the one-sided 95% upper risk bound is 1 − 0.05^(1/n). For n=8 this is about 31%; this assumes independent Bernoulli outcomes and is not a guarantee about a curated or selectively assigned sample.
- Recorded the owner's decision to adopt no 10% pass/fail floor; report actual coverage with selective risk.
- Recorded primary statuses resolved, unresolved, uncertain; V3 Probable remains outside resolved and no separate Probable grade is approved initially.
- Inspected committed candidate, evidence, resolver, and configuration code. Added verified request/ranking behavior and separated it from protocol choices still needing approval.
- Added workload counts under explicit assumptions and recommended a staged pilot.

## Statistical assumptions and limits

Selective risk alone can look favorable if the resolver auto-assigns only a tiny fraction of cases; coverage shows how often it makes an automatic assignment. Coverage alone does not show correctness. Report each operating point as the pair (automatic coverage, selective risk), with automatic-decision n and uncertainty, plus manual review, unresolved, empty-pool, and source-failure rates. The threshold is frozen before sealed-test evaluation; do not tune it to test results.

The binomial interval treats each automatic decision as an independent Bernoulli outcome from a target population. That assumption may not hold exactly for a curated cohort or when the resolver selectively auto-assigns particular subgroups. With repeated queries, use one primary query per identity group; variants are secondary. For paired policy differences, use identity-level paired outcomes and an interval method fixed before unsealing.

For a simple planning objective of a two-sided 95% proportion interval with approximately ±10 percentage-point half-width at worst-case p=0.5, the usual normal approximation gives about 97 independent automatic decisions. This is a planning approximation, not a guarantee and not a required target. At an assumed 10% automatic coverage it would imply roughly 970 eligible test cases in expectation; actual needs depend on the unknown coverage and error rate. A ±5 point objective would require about 385 automatic decisions under the same assumptions. These numbers illustrate why an 80-case test cannot support precise risk estimates at low coverage; they do not justify a specific project sample without owner priorities and feasibility.

If zero errors are observed, 59 independent automatic decisions are needed for a one-sided exact 95% upper risk bound just below 5%. Any observed errors require a different bound and generally more observations. This does not mean that 59 identity groups guarantee 59 automatic decisions or reliable coverage.

## Annotation workload under the original proposal

The original split contains 120 resolved identities and 40 unresolved controls, 160 primary cases total.

- **Evidence collection assumption:** one person-level source plus two DOI/publisher work records per resolved identity = three checks each, or about 360 evidence checks. Unresolved cases need documented searches; their number of source checks is not fixed here.
- **Independent Stage A reviews:** two reviewers on all 160 cases = 320 case reviews, before adjudication. Disagreement rate and adjudication load are unknown.
- **Candidate mapping:** the committed default cap is 10 candidates per query and one API page. At that upper bound, 160 pools could produce up to 1,600 query-profile mapping items. Two reviewers per item would mean up to 3,200 mapping judgments, before adjudication. Actual pool sizes are unknown.
- **Time:** no reviewer speed data exists, so no hours or completion date is estimated.

These counts make the full proposal substantial for a final-year project, especially the candidate mapping stage.

## Owner-approved sample design

The owner approved a staged design:

1. Run a protocol pilot on 10 resolved identities and 5 unresolved controls, with the same external-evidence standard, two independent reviewers, blinded candidate mapping, and adjudication. This assesses evidence availability, rubric clarity, reviewer agreement, candidate-pool sizes, mapping difficulty, and annotation workload only; it is not a performance evaluation.
2. After the pilot, record actual case-review time, disagreement rate, candidate-pool size distribution, mapping time, and failure rate. Revise the protocol before freezing a main study.
3. The prior 40/20/60 plus 10/10/20 design is deferred and not approved. Reassess after the pilot using observed evidence availability, agreement, pool sizes, mapping effort, and workload.
4. If a narrow risk objective is required, plan the test size from the chosen confidence/precision objective and observed development coverage; keep test identities sealed. The needed cohort could be much larger than the current proposal.

Blinding and identity independence remain mandatory at every size. The pilot must not be merged into the sealed test after its candidates or outcomes are inspected.

## Verified implementation facts and open protocol choices

At committed HEAD, candidate requests apply outer trimming; clean_query_name performs NFC normalization, whitespace collapse, and a narrow Le/La join. Candidate parsing drops missing source IDs or blank display names. Default max_candidates is 10, one page is requested, and there is no pagination. Duplicate source IDs are removed in first-seen order; fallback IDs append. API order is the retrieval rank. Resolver order is by score availability, score, then source ID, sorted in reverse order, making ID ties descending. Name similarity uses RapidFuzz token_sort_ratio/100 after casefold/trim/whitespace normalization, taking the best display-name/alias score. Missing signals are omitted and weights renormalized; no available score is null.

The resolver thresholds and weights can be overridden by environment/configuration. The default thresholds are auto score 0.75, margin 0.15, dominance 1.35, manual score 0.45, and two signals; weights are 0.35/0.25/0.20/0.10/0.10. A future run must freeze effective values and overrides.

The current rank_candidates function has no custom-weight argument. The name-only baseline can be constructed in an offline evaluator from the existing name evidence and score_evidence(weights={name_similarity: 1.0}); the wrapper must be reviewed and must not alter application code. If it cannot reproduce the existing name signal exactly, omit the arm. Before sealing, decide what forced-top-1 does when the top score is null; the recommendation is no assignment.

R0, R1, and R2 are search strategies, not exact-name lookup. They share the author endpoint and per-page cap. R0 applies no normalization beyond common outer trimming; R1 adds NFC and whitespace normalization; R2 uses committed clean_query_name and its initial-only search fallback after successful empty filter results. Retrieval rank is API order. Fallback results append only unseen IDs. Primary failures return failed; successful empty results return empty. A fallback exception can leave the final status empty, so record each request outcome separately.

## Remaining open decisions

The main-study sample size and confirmatory objective remain open until pilot workload and evidence availability are measured. The original 40/20/60 split is not approved. The name-only arm remains conditional on exact offline reproduction. No operational coverage floor is adopted. Any future main study still requires frozen inputs, thresholds, independent labels, identity-disjoint splits, and the existing leakage safeguards.

## Owner approval checklist

- [x] Pilot: 10 resolved identities and 5 unresolved controls.
- [x] Purpose: workflow assessment only, not performance evaluation.
- [x] Descriptive reporting with exact counts, denominators, and suitable intervals; no accuracy claim or minimum-decision/pass criterion.
- [x] No 10% coverage pass/fail floor; report coverage with risk.
- [x] Statuses: resolved, unresolved, uncertain; no separate Probable grade initially.
- [x] Null top score: no assignment, separately recorded as no-score.
- [x] Name-only baseline conditional on exact offline reproduction and deterministic tie-breaking.
- [x] Main-study size deferred until pilot evidence and workload are known.
- [x] Stage A/Stage B separation, identity-disjoint splits, and leakage safeguards preserved.

**No implementation, benchmark data, labels, templates, thresholds, evaluation outputs, candidate results, or experiments were changed or created in this review.** The research direction remains RQ2 primary and conditional RQ1 secondary. The pilot decisions are recorded; any main-study design remains subject to further owner approval.
