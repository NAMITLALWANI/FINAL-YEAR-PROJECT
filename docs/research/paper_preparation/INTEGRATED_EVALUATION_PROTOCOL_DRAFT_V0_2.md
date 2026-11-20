# HAMMER — Integrated Evaluation Protocol and Open-Items Register

**Document type:** Internal research protocol
**Version:** draft v0.2, 20 November 2026 (supersedes draft v0.1, which is kept unedited in `INTEGRATED_EVALUATION_PROTOCOL_DRAFT_V0_1.md`)
**Status:** Accepted by the research director on 20 November 2026 as the working integrated protocol. Not frozen. Operational parameters in section 8 remain open, and nothing in section 10 is authorised.
**Scope:** Integration of Decisions A, B and C
**Authority:** The three decision records (`DECISION_A_LABEL_STRATEGY_RECORD.md` rev 2, `DECISION_B_DOSSIER_DESIGN_PROPOSAL.md`, `DECISION_C_STATISTICAL_DESIGN_PROPOSAL.md` rev 3 with its clarification addendum). This document consolidates them. It does not supersede or amend them. Changes from v0.1 are listed in section 12 and justified in `INTEGRATED_PROTOCOL_CONSISTENCY_REVIEW.md`.

---

## 1. Purpose and governing principles

This document integrates the approved design decisions for the HAMMER evaluation into one protocol: the order of activities, the relation between independent labels and benchmark-derived labels, the blinded review, the sampling and statistical design, and the outstanding operational decisions.

The protocol preserves these principles:

1. Work-level publication matching and person-level author identity resolution remain separate tasks.
2. Retrieval quality and selective-resolution quality are evaluated separately.
3. Benchmark-derived ORCID agreement is not represented as independent ground truth.
4. Verified results and benchmark-derived results are reported separately.
5. Candidate retrieval, resolver decisions, reviewer judgments and adjudicated labels retain separate provenance.
6. Automatic assignment, manual review, unresolved outcomes, empty retrieval, provider failure and no-defined-score outcomes remain distinguishable.
7. Every provisional parameter is selected and documented before the freeze to which it belongs.
8. No outcome-informed change is made once evaluation outputs have been inspected. A changed protocol requires a new version and an appropriately independent evaluation.
9. Resolver predictions are frozen and hashed before any reviewer judgment exists.

## 2. Decision authority and status

| Decision | Subject | Status | Governing rule |
|---|---|---|---|
| A | Label strategy and audit population | Approved with corrections (revision 2) | Use the approved label strategy and audit design |
| B | Evidence dossiers, blinding and independent review | Approved as recommended (B1 to B7) | Use the two-stage blinded design and its leakage controls |
| C | Sampling, estimands, inference and coverage-based sizing | Locked as revision 3 | Apply C1 to C9 as written; thresholds and operational parameters stay provisional |

If integration reveals an apparent conflict, it is entered in the register (section 8) and resolved by an explicit clarification or amendment to the relevant record. Clarifications X-02 and X-03 are recorded in the Decision C addendum and were confirmed by the director on 20 November 2026.

## 3. Evaluation populations and label basis

### 3.1 Primary evaluation pair
- **Condition:** C1 (institution plus a one-year range; no DOIs).
- **Policy:** `selective_policy_v2`.

Only automatic assignments of this pair define the primary automatic-assignment population for verified precision. Other conditions and policies (C0, C1x, the threshold-gate ablation, forced top-one) are secondary or exploratory, are reported as benchmark-derived, and are never substituted for the primary pair.

### 3.2 Label states and reporting classes
Two separate vocabularies are used, as in Decision A.

**Label states** (what the independent review concludes about a case):
- **Resolved:** the reviewers identified a definite intended person.
- **Unresolved:** the reviewers determined that no unique intended person exists.
- **Uncertain:** the review could not reach a sufficiently definite conclusion.
- **Unverifiable:** the independent evidence needed could not be accessed or established.

**Reporting classes** (each case in exactly one, always with its case count): Verified, Uncertain, Unverifiable, Benchmark-derived. An audited case is never also Benchmark-derived. Verified and benchmark-derived observations are never combined into one accuracy figure.

Uncertain and unverifiable cases stay visible in case accounting and are excluded from primary verified rates. Every verified rate is bracketed by counting those cases all wrong and then all right. Benchmark-derived ORCID agreement is never described as independently verified accuracy.

### 3.3 Benchmark scope
The frame consists of eligible LAGOS-AND blocks. Eligibility (verified in `backend/hammer_lagos/prep.py`) requires: at least two ORCID groups; at most eight ORCID groups; no DOI shared across ORCID groups; at least one group with two unique DOIs; a single source split.

The study therefore concerns a restricted, benchmark-defined population of ambiguous author blocks. It does not establish performance across all author names, nor on the most ambiguous names that the cap excludes.

### 3.4 Retrieval and identity resolution
- **Retrieval:** did the candidate pool contain a profile that can be mapped to the intended person?
- **Resolution:** did HAMMER select that person automatically, send the case to manual review, or leave it unresolved?

A retrieval failure is never reclassified as a resolver abstention. Successful empty retrieval and provider failure remain separate outcomes.

## 4. Decision A — label strategy and audit

### 4.1 Verification and audit populations
- **Verified precision:** every automatic assignment of the primary pair is independently verified.
- **Audit frame:** all non-automatic cases of the primary pair, including cases with no mapped profile, defined after capture and replay under frozen thresholds, weights, code and policy, and without any benchmark identity label.
- **Audit sample:** a random sample drawn from that frame, proportional and stratified by block size, with largest-remainder rounding and a SHA-256 hash order within each stratum. Its size is set after the reviewer-time pilot. If strata must be merged, the rule is fixed before the draw and the original stratum counts are still reported. The case manifest records the predeclared audit seed, dataset version, manifest hash, original and merged strata, selection probabilities and selected case identifiers. (A census of the frame is the limiting case if the audit size equals the frame size. Neither record plans or excludes it.)

### 4.2 Interpretation limits
The audit's label-error estimate describes only the sampled non-automatic frame of the primary pair. It is never used to correct metrics and is not transferred to automatic assignments, other conditions, other policies, overall retrieval results or the full benchmark. It is reported alongside the benchmark-derived results of that frame, with its interval.

### 4.3 Scope qualification
The audit estimates benchmark-label validity in its frame. It does not establish the correctness of every benchmark-derived retrieval result and does not replace the verification of automatic assignments. The measure of false acceptance on unresolved queries is omitted, because the benchmark contains only resolved identities and no independently labelled control set exists.

## 5. Decision B — blinded evidence dossiers and review

### 5.1 Review design
**Stage A, identity.** Reviewers decide who the person is from the benchmark group's publication evidence (up to *K* papers, starting value *K* = 10, with the designated paper always included) and external evidence, before seeing any candidate profile. Stage A also tests group purity: an impure group is labelled uncertain or unverifiable, never forced.

**Stage B, candidates.** Reviewers judge each shuffled, redacted candidate against the Stage A identity as same person, different person, or cannot tell. Cases with no pool (provider failure, empty retrieval) receive Stage A only.

### 5.2 Dossier construction and leakage controls
1. **Allow-list construction.** Only named fields enter a packet. A deny-list is not used, because it fails silently when a provider adds a field.
2. **Stage A allows:** printed query name; capped group papers (title, DOI, year, venue, author names, affiliation, coauthor names).
3. **Stage B allows, per candidate under an opaque identifier:** display name and variants, affiliations with years, topics, works count, and the capped works list from the candidate-works capture (B2c).
4. **Always excluded:** every ORCID field and URL (`orcid`, `ids.orcid`, `observed_orcids`, works `author.orcid`); `pid`; block name, split flag and source row; `ids.openalex` and `works_api_url`; `relevance_score` and provider order; HAMMER scores, ranks, signal sets, the selected candidate and any decision; pool statistics that reveal rank.
5. **Shuffle** candidates in a hash-seeded order independent of provider and HAMMER rank.
6. **Opaque identifiers** with the crosswalk held separately by a person who is neither a reviewer nor the adjudicator.
7. **Packets are built by a reproducible script and never edited by hand.**
8. **Leak scan before release:** a packet is released only if a scan finds no ORCID pattern, no provider ID or URL and no HAMMER field name. The scan result is stored with the packet hash.
9. **Identical presentation:** automatic cases being verified and audited non-automatic cases use the same packet form, the full shuffled pool, and a mixed queue order, so nothing shows which came from the automatic set.
10. **Residual leakage** is recorded: reviewers' own searches may reveal an ORCID. They are told not to use an ORCID as evidence and they record whether they encountered one. Results are reported separately where they did.

### 5.3 Evidence sources and logging
- **Stage A:** external evidence is permitted (for example publisher author lists and institutional pages). The exact list of permitted sources is open (B-O9).
- **Stage B:** judgments rest on the captured, redacted dossier. Live browsing of OpenAlex profile pages is excluded, because it exposes the ORCID and drifts over time.
- Reviewers record evidence references, searches performed, confidence, rationale, whether they encountered an ORCID, and minutes.

### 5.4 Records, independence and adjudication
Reviewers work independently, and their judgments are stored separately. The schema is two-stage: Stage A has one row per reviewer per case; Stage B has one row per reviewer per case per candidate. A third person, the adjudicator, sees both reviewers' rows and the dossier and records a final label with a rationale. The final label never overwrites the original judgments. Report raw agreement and Cohen's kappa with counts, cautiously where *n* is small.

### 5.5 Reviewer independence (personnel deferred)
Design B6a is preferred: outside peers as reviewers and a faculty member as adjudicator. B6b is not adopted merely to avoid recruitment. Each reviewer states in writing that they have not seen HAMMER outputs or the benchmark ORCID labels for the audited cases, and the person who builds packets and holds the crosswalk is neither reviewer nor adjudicator. Names, recruitment, attestations, availability, hours and capacity are deferred (section 7, step 3). This protocol assumes none of them.

## 6. Decision C — sampling and statistical design

### 6.1 Sampling unit
One hash-selected primary case per eligible block (the case-eligible group with the smallest `sha256(seed|block|orcid)`). Other case-eligible groups of the block are secondary, benchmark-derived and used only for C8. The manifest preserves the sampling unit and each case's inclusion probability.

### 6.2 Estimands and weights
E1 (block level, primary) has weight *N_h*/*n_h*. E2 (person level, secondary) has weight (*N_h*/*n_h*)·*g_i*. Each estimate is labelled with its estimand.

### 6.3 Strata and allocation
Fixed S, M, L and XL bands by unique DOIs (0 to 9, 10 to 49, 50 to 199, 200 or more). Proportional allocation with floors, census caps, iterative redistribution and largest-remainder rounding, as in C3. No boundary or rule changes after outcomes are seen.

### 6.4 Evaluation frame
Eligible test blocks excluding the 23 smoke blocks and the reserved coverage-pilot blocks (whole blocks). A new main seed is declared at the appropriate freeze point. Sampling is without replacement and no drawn case is replaced. Exact frame counts and selected cases are not yet computed.

### 6.5 Inference
- **R1:** Clopper–Pearson interval per stratum, as a conservative superpopulation approximation, with the sampling fraction reported as a diagnostic.
- **R2:** pooled, frame-weighted estimate with a stratified percentile bootstrap, where the quantity and stratum sizes support it.
- **R3:** sparse automatic precision as counts and exact intervals, with no bootstrap, and never a bootstrap on zero errors.
- A stratum too small to resample gets its estimate and counts without a bootstrap interval. The pooled interval is withheld by default, unless a negligible-weight rule is predeclared and the pooled estimand relabelled.
- All numerical thresholds are provisional and must be stated before freeze.
- The beta-binomial sizing is a superpopulation approximation; its lower-tail conservatism is to be checked, not assumed.

### 6.6 Endpoints, denominators and scoring against a verified label
Every drawn primary case stays in the case accounting and falls in exactly one outcome category: automatic, manual, unresolved, empty retrieval, provider failure, or no defined score. A case need not be in every metric's denominator. Denominators are those of Decision C7.

**Primary endpoints:** automatic coverage and verified automatic precision of the primary pair (RQ2b), always together; and, benchmark-derived, end-to-end success@1 and @10 and the candidate-pool mapping rate (RQ2a). Conditional Recall@*k*, conditional and end-to-end MRR, other conditions and policies, C1x, R0 versus R2 and E2 are secondary. Conditional and end-to-end retrieval measures are always reported together, and a conditional measure is never substituted for an end-to-end one. The evaluation is estimation with intervals, not pass or fail.

**Scoring one automatic assignment against its verified label:**
| Verified status | Selected candidate | Scored as | In the precision denominator |
|---|---|---|---|
| Resolved | judged the same person | correct | yes |
| Resolved | judged a different person | incorrect | yes |
| Resolved, and no candidate in the pool is the person | any candidate | incorrect | **yes** |
| Unresolved (no unique intended person) | any candidate | incorrect | **yes** |
| Uncertain or unverifiable at case level, or reviewers cannot tell for the selected candidate | | not scored; counted and bracketed | no, but visible |

Only uncertain and unverifiable cases leave the denominator.

**Verified retrieval** is reported separately for the automatic assignments and for the random audit sample, never pooled with each other or with benchmark-derived retrieval.

### 6.7 Secondary block-level analysis
C8 applies to the secondary cases only: block-level cluster bootstrap, leave-one-block-out check, reported distribution of automatic assignments across blocks. The 20-block figure is a warning, not a validity threshold. The analysis is exploratory, benchmark-derived and never merged with the primary estimates.

### 6.8 Coverage pilot and predictive sizing
- **Source:** disjoint eligible test blocks reserved for the pilot, drawn by the same one-case-per-block hash rule with a separate pilot seed, stratified by the four bands. Per stratum, train or validation blocks are a fallback only, with the transfer assumption reported.
- **Label-free:** the pilot estimates coverage of C1 with `selective_policy_v2` from decision categories only, and scores no correctness.
- **Post-exclusion counts:** the post-exclusion *N_h* depend only on which blocks were reserved, so they are computed right after the pilot draw and before sizing (clarification X-02).
- **Feasibility:** the pilot reservation is checked against *N*_max, because *N* is unknown when the pilot is drawn (clarification X-03).
- **Sizing:** stratified beta-binomial predictive sizing for the smallest *N* with probability at least 1−β of reaching *m′* automatic assignments, plus the lower-bound sensitivity check.
- **No tuning:** a pilot result never changes thresholds, weights, code or policy. A change after seeing pilot output needs a new freeze and a new pilot on fresh blocks.
- The pilot is not authorised for execution here. Its size, allocation, budget, seed and the sizing parameters remain open.

## 7. Integrated order of operations
This is a dependency plan, not permission to perform any step.

| # | Activity | Required output or condition |
|---|---|---|
| 1 | Resolve integration items (X-02, X-03) and non-capacity parameters | thresholds, priors, β, γ, *N*_max, bootstrap minimum, negligible-weight rule, provider budget, cost ceiling, stop rules |
| 2 | Build and test internal tooling, each piece separately authorised | selector, manifest builders, packet builder and leak scan, sizing script, analysis code |
| 3 | Resolve personnel requirements | reviewer and adjudicator names, independence attestations, availability and capacity. This is the first step needing people outside the project |
| 4 | Reviewer-time pilot (B7) on about six smoke cases, with candidate-works capture for those cases | minutes per stage, share uncertain, ORCID encounters, defects; check *K* and the schema; needs budget |
| 5 | Fix *m*, *m′*, the audit size, the merging rule and the audit seed | from reviewer capacity and step 4 |
| 6 | Freeze software, resolver policy and weights, configuration, dossier tooling and protocol versions | versioned manifest |
| 7 | Draw the coverage pilot (whole blocks, own seed); compute post-exclusion *N_h* | pilot manifest; outcome-free counts |
| 8 | Run the label-free coverage pilot | separately authorised; captured outcomes and artifacts |
| 9 | Stratified predictive sizing; freeze *N*, allocation and the sizing result | calculation, assumptions and sensitivity result |
| 10 | Draw the main sample with the main seed | main manifest: strata, weights, inclusion probabilities, secondary cases |
| 11 | Capture retrieval for all *N* cases | raw responses, hashes, ceilings, stop rules |
| 12 | Replay under the frozen policy; **freeze and hash predictions** | before any review |
| 13 | Define the verification population and the audit frame; draw the audit sample | predeclared seed and merging rule; audit manifest |
| 14 | Capture candidate works for the selected cases (B2c) | hashed capture; budget |
| 15 | Build packets by script, leak-scan and hash them; Stage A and Stage B reviews in a mixed queue; adjudication | reviewer rows, adjudicated labels, agreement |
| 16 | Freeze labels and analysis inputs; analyse as predeclared | tables, intervals, exclusions and brackets |
| 17 | Update the manuscript from frozen artifacts | claims traceable to frozen outputs and approved denominators |

## 8. Open-items register

### 8.1 Cross-decision items
| ID | Item | Status |
|---|---|---|
| X-01 | Audit "entire non-automatic frame" versus "random audit sample" | **Closed, no conflict.** Frame = all non-automatic cases; audit = random sample from it (section 4.1) |
| X-02 | Order of C9: post-exclusion *N_h* before sizing | **Closed.** Clarification recorded in the Decision C addendum and confirmed by the director (20 November 2026) |
| X-03 | Pilot reservation feasibility checked at *N*_max | **Closed.** Clarification recorded in the Decision C addendum and confirmed by the director (20 November 2026) |
| C7-R | Five rulings on C7 ambiguities (derived audit error, Uncertain class, ground-truth unresolved versus HAMMER abstention, R2 pool, complete-judgment rule) | **Closed.** Recorded in the Decision C addendum, implemented in `metrics_c7.py` and validated in test record T004. Four follow-up points await the director (T004 section 11) |
| C7-C | Four clarifications on group validity and verified retrieval (pure unresolved indeterminate; group impurity reported apart from the definite-label error rate; overall retrieval never adjusted; conditional verified retrieval categories) | **Closed.** Recorded in the Decision C addendum, implemented in `metrics_c7.py` and validated in test record T005. Three follow-up points await the director (T005 section 11) |

### 8.2 Decision A items
| ID | Item | Status |
|---|---|---|
| A-O1 | Audit size | Open; waits for step 4 |
| A-O2 | Stratum-merging rule | Open; fixed before the audit draw |
| A-O3 | Predeclared audit seed | Open; distinct from the pilot and main seeds |
| A-O4 | Size bands that stratify the audit | Confirm they are the C bands S/M/L/XL |
| A-O5 | Reporting audit estimates unweighted over the sampled frame | Confirm; the main allocation is disproportionate under P3 |

### 8.3 Statistical and sampling parameters
| ID | Item | Status |
|---|---|---|
| C-O1 | Minimum stratum size for bootstrap resampling | Open; no provisional value |
| C-O2 | Negligible-weight rule for the pooled estimand | Open; if adopted, predeclared and the estimand relabelled |
| C-O3 | Sampling-fraction diagnostic (about 0.10) | Provisional |
| C-O4 | Sparse automatic-count warning (about 30) | Provisional |
| C-O5 | Sparse error-count warning (about 5) | Provisional |
| C-O6 | C8 contributing-block warning (about 20) | Provisional |
| C-O7 | Pilot size and allocation by stratum | Open |
| C-O8 | Main sample size *N* | Open |
| C-O9 | Target *m* and adjusted *m′* | Open; waits for step 4 |
| C-O10 | Sizing probability parameter β | Open |
| C-O11 | Lower-bound sensitivity parameter γ | Open |
| C-O12 | Floors and census inputs | Open where not fixed by the C3 algorithm |
| C-O13 | Predictive prior and sensitivity prior | Open (Jeffreys and uniform proposed) |
| C-O14 | Search maximum *N*_max | Open |
| C-O15 | Pilot and main seeds | Open; recorded at the freeze |
| C-O16 | Exact eligible test-frame counts and allocation | **Pre-pilot counts computed (T011):** S 8,039, M 8,363, L 1,173, XL 12; after the 23 smoke blocks S 8,038, M 8,360, L 1,173, XL 9. Final post-exclusion counts depend on the pilot draw (X-02); allocation open |
| C-O17 | Feasibility rule for pilot reservation, evaluated at *N*_max | Open; X-03 is confirmed, and the check is applied at the freeze once counts exist |

### 8.4 Dossier and review operations
| ID | Item | Status |
|---|---|---|
| B-O1 | Reviewer and adjudicator names | Deferred (step 3) |
| B-O2 | Written independence attestations | Deferred (step 3) |
| B-O3 | Reviewer availability and capacity | Deferred (step 3) |
| B-O4 | Reviewer time and workload feasibility | Deferred (steps 3 and 4) |
| B-O5 | Pilot review cases and workflow feasibility | Open; no cases selected |
| B-O6 | Packet builder and automated leak scan | **Implemented and validated (T008).** No real dossier generated |
| B-O7 | Final two-stage schema and validation | **Implemented and validated (T009).** Director to confirm the adjudication reading (T009 section 9) |
| B-O8 | Group-paper cap *K* (starting value 10) | Checked in the pilot, frozen before the audit |
| B-O9 | Evidence sources allowed in Stage A | Open |
| B-O10 | Affiliation-normaliser version; raw affiliations preserved | Open |

### 8.5 Provider and execution budget
| ID | Item | Status |
|---|---|---|
| P-O1 | Provider-request budget | Open |
| P-O2 | Monetary cost ceiling | Open |
| P-O3 | Request-count ceiling and per-case assumptions | Open |
| P-O4 | Candidate-works capture scope and page limits | Open |
| P-O5 | Stop conditions for errors, rate limits and unexpected cost | Specified before any authorised capture |

### 8.6 Implementation
| ID | Item | Status |
|---|---|---|
| I-O1 | One-case-per-block selector | **Implemented and validated on synthetic catalogues (T007).** Not run on the real archive |
| I-O2 | Sizing script (stratified beta-binomial and lower-bound check) | **Implemented and validated on synthetic inputs (test record T006).** Not run on real inputs; frozen with the manifest only at the freeze |
| I-O3 | Pilot, main and audit manifest builders | **Implemented and validated on synthetic data (T007)** |
| I-O4 | Analysis code for the C5 regimes and C7 denominators | Not written |

### 8.7 Manuscript integration
| ID | Item | Status |
|---|---|---|
| M-O1 | Integrate the final protocol into the methodology and design sections | Not started |
| M-O2 | Align metric definitions and denominators with C7 | Not started |
| M-O3 | State the benchmark scope and label-circularity limitations | Not started |
| M-O4 | Document the audit population and its limited interpretation | Not started (no longer blocked by X-01) |
| M-O5 | Report all thresholds and parameters actually frozen | Blocked until values are selected |
| M-O6 | Write results, discussion and claims only from frozen artifacts | Not started |
| M-O7 | Section 5 edits: *R* defined as "the audited cases", the unresolved-control measure, the four-row scoring definition, the label-strategy and sampling-design subsections, the scope statement | Not applied |

## 9. Freeze requirements
The evaluation is not described as frozen until the relevant prerequisites are complete and recorded. The freeze package identifies:
- protocol and decision-record versions, including the Decision C addendum;
- eligible frame, exclusions, and post-exclusion counts per stratum;
- strata, allocation, inclusion probabilities and weights;
- pilot, main and audit seeds, manifests and selected cases, and the separation of pilot, smoke and main blocks;
- reviewer and adjudicator arrangements, label rubric, adjudication procedure and the permitted evidence sources;
- dossier tooling version, allow-list, leak-scan results and packet hashes;
- software revision, dirty state, dependencies and effective configuration;
- resolver thresholds, weights and policy;
- provider-request, cost and stop limits;
- hashes of raw responses and evidence snapshots;
- the hashed, frozen predictions (before any label exists);
- metric definitions, denominators, scoring table and interval procedures;
- the sizing calculation, assumptions and sensitivity result.
A freeze does not retroactively authorise earlier work. Every action has its own approval where required.

## 10. Explicitly not authorised by this document
Writing or running the selector; computing test-frame counts; drawing pilot, main or audit samples; making provider requests; generating dossiers or packets; recruiting or assigning reviewers; changing code, thresholds, weights or resolver policy; changing the benchmark or labels; editing the manuscript; starting the main evaluation; declaring the evaluation frozen.

## 11. Change control
This document consolidates Decisions A, B and C and replaces none. When an open item is resolved, record the value, rationale, date and approving authority. A change to a locked design goes through an explicit amendment of that record, with its earlier version preserved. A locked decision is never edited by changing only this document.

## 12. Change log from v0.1
| v0.1 location | Change in v0.2 | Review ID |
|---|---|---|
| 1 (principles) | "Sealed" and "test-informed" replaced by "frozen" and "outcome-informed"; principle 9 added | R-15 |
| 2 | Status wording matches the records; Decision A is "approved with corrections" | |
| 3.2 | Label states and reporting classes separated | R-08 |
| 3.3 | Five eligibility rules listed | R-17 |
| 4.1 to 4.3 | Frame versus sample stated; audit mechanics added; X-01 closed | R-13 |
| 5.2 | Allow-list, excluded fields, leak scan, *K*, crosswalk holder, mixed queue | R-09, R-10 |
| 5.3 | Evidence sources by stage; live OpenAlex excluded | R-11 |
| 5.5 | Written attestations, builder independence | R-16 |
| 6.6 | C7 scoring table; endpoint wording | R-07, R-14 |
| 6.8 | Pilot details, X-02 and X-03 | R-03, R-18 |
| 7 | Order of operations rebuilt: B7 pilot, audit draw, B2c, predictions frozen after replay, review after capture, *m* after capacity | R-01, R-02, R-03, R-04, R-05, R-06 |
| 8 | Register additions A-O, B-O8 to B-O10, C-O17, I-O, M-O7 | R-12 |
| 9 | Freeze package adds audit manifest, pre-label prediction freeze, tooling and leak-scan hashes | R-02 |

---
**Current status:** Decisions A, B and C are settled designs; C is locked as revision 3. Operational parameters remain open. No selector, pilot, provider capture, dossier generation, manuscript integration or evaluation freeze has been authorised or performed.
