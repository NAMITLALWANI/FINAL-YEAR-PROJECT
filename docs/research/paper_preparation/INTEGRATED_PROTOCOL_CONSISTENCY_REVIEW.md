# Consistency review of the integrated protocol draft v0.1

**Date:** 20 November 2026. **Reviewed:** `INTEGRATED_EVALUATION_PROTOCOL_DRAFT_V0_1.md` (saved verbatim and unedited) against `DECISION_A_LABEL_STRATEGY_RECORD.md` (rev 2), `DECISION_B_DOSSIER_DESIGN_PROPOSAL.md` (approved, with section 6) and `DECISION_C_STATISTICAL_DESIGN_PROPOSAL.md` (locked, rev 3). **Read-only.** No locked record, manuscript, code or artifact was changed. Nothing here amends a decision. Proposed changes are for the director's approval.

**Overall verdict.** The draft is faithful in its principles and in sections 3 to 6, and its authority, change-control and not-authorised sections are sound. Its section 7 (order of operations) has sequencing errors that conflict with Decisions A, B and C, and it drops several controls and register items. One of the sequencing problems comes from my own Decision C wording and needs an explicit clarification.

## 1. Findings
Severity: **High** changes what the evaluation could validly claim or do; **Medium** drops a locked control or open item; **Low** wording.

| ID | Sev. | Draft location | Finding | Proposed change |
|---|---|---|---|---|
| R-01 | **High** | 7, stages 10 and 11 | Stage A identity review is placed **before** the retrieval capture. Decision A defines both the verification population (every automatic assignment of the primary pair) and the audit frame (its non-automatic cases) only after capture and replay under frozen thresholds. Before capture nobody knows which cases are automatic, so which cases need review is undefined | Capture and replay first; review only the verification population and the drawn audit sample |
| R-02 | **High** | 7, stage 13 | Predictions are frozen **after** the reviews. They must be frozen and hashed before the audit draw and before any reviewer judgment exists, so that no label can influence what the system is said to have predicted | Move the freeze of replayed decisions to immediately after replay |
| R-03 | **High** | 7, stages 7 and 8 | Sizing (stage 7) precedes defining the post-exclusion frame (stage 8), but the locked sizing uses the post-exclusion *N_h* in its allocation step. **This inconsistency originates in my Decision C wording** (the C9 order of operations lists "compute the sizing" before "define the main frame, recompute *N_h*", while the sizing procedure itself uses the post-exclusion *N_h*). The post-exclusion counts need no outcomes, only the pilot draw | Clarification to C9 (see section 3, X-02): compute the post-exclusion *N_h* immediately after the pilot draw, before sizing; only the main draw waits for *N* |
| R-04 | **High** | 7 (missing) | The Decision B **reviewer-time pilot** (B7, about six smoke cases) is absent. It measures reviewer minutes, which set the audit size (Decision A) and constrain *m* (Decision C9 step 1). It also needs the packet builder and the candidate-works capture for those cases | Add as a stage before *m* and the audit size are fixed |
| R-05 | **High** | 7, stages 2 and 3 | Stage 2 resolves "sizing inputs" before stage 3 resolves reviewer capacity. *m* is chosen once reviewer capacity and the precision bound are known, so *m* cannot be fixed in stage 2 | Split inputs: non-capacity parameters in stage 2; *m*, *m′* and the audit size after personnel and the B7 pilot |
| R-06 | Medium | 7 (missing) | The audit draw (predeclared audit seed, merging rule fixed before the draw, manifest) and the candidate-works capture (B2c) for the selected cases are not stages | Add both |
| R-07 | Medium | 6.6 | The C7 table that scores an automatic assignment against its verified label is not carried. Its key rule: a resolved case with no matching candidate, and an unresolved case, count as **incorrect** and stay in the precision denominator; only uncertain and unverifiable cases leave it | State the rule in 6.6 or point to C7 explicitly |
| R-08 | Medium | 3.2 | The list mixes the four *label states* (resolved, unresolved, uncertain, unverifiable) with the four *reporting classes* (Verified, Uncertain, Unverifiable, Benchmark-derived). "Resolved" and "unresolved" are missing, and the scoring in R-07 depends on them | List the four label states and the four reporting classes separately, as in Decision A |
| R-09 | Medium | 5.2 | Leakage controls are written as removals (a deny-list). Decision B requires an **allow-list**, because deny-lists fail silently when a provider adds a field. Also missing: exclusion of `ids.openalex`, `works_api_url` and `relevance_score`; the zero-match leak scan before release, stored with the packet hash; the hash-seeded shuffle; the cap on group papers (*K* = 10, checked in the pilot); and that the person who builds packets and holds the crosswalk is neither a reviewer nor the adjudicator | Add each |
| R-10 | Medium | 5.2 | Decision A requires that verifying automatic assignments use the same packet as any other case, with no sign of which came from the automatic set. The draft does not say that automatic and audited cases are presented identically, in a mixed order | Add |
| R-11 | Medium | 5.3 | "Limited external research is permitted" is open-ended. Decision B did not adopt live browsing of OpenAlex profiles (B2b), which expose the ORCID and drift over time. Stage A uses external evidence; Stage B relies on the captured, redacted dossier. Reviewers must also be told not to use an ORCID as evidence | State the permitted evidence sources per stage, and that live OpenAlex profile pages are excluded |
| R-12 | Medium | 8 | Register omissions (section 2 below) | Add |
| R-13 | Low | 4.3 and 8.1 | See X-01: not a conflict | Close X-01 |
| R-14 | Low | 6.6 | Primary endpoints say "end-to-end retrieval measures". Decision C6 names end-to-end success@1 and @10 and the mapping rate; conditional Recall@*k* and MRR are secondary. "Must remain separate" should read "always reported together, never substituted", per the paper's design | Align the wording |
| R-15 | Low | 1.8 and 7 | "Sealed evaluation", "test-informed" and "unseal" introduce a sealing concept that no decision defines, and "test" is ambiguous with the test split | Use "frozen" and "outcome-informed", or define the seal |
| R-16 | Low | 5.5 | The written attestation by each reviewer that they have not seen HAMMER outputs or the benchmark ORCID labels, and the adjudicator's independence from the packet builder, are not stated (B-O2 covers confirmations only by title) | Add |
| R-17 | Low | 3.3 | "Eligibility criteria" is not listed | List the five verified rules: at least two ORCID groups, at most eight, no DOI shared across groups, a group with two unique DOIs, a single source split |
| R-18 | Low | 6.8 | The pilot paragraph omits the one-case-per-block hash rule with a separate pilot seed, the label-free property, and the per-stratum train-or-validation fallback with its transfer assumption | Add |

## 2. Register additions proposed
| New ID | Item | Why |
|---|---|---|
| A-O1 | Audit size | Decision A: pending the reviewer-time pilot |
| A-O2 | Stratum-merging rule | Decision A: must be fixed before the draw |
| A-O3 | Predeclared audit seed | Decision A; distinct from the pilot and main seeds in C-O15 |
| A-O4 | Which size bands stratify the audit | A says "block size"; confirm these are the C bands S/M/L/XL |
| A-O5 | Whether audit estimates are reported unweighted over the sampled frame | A restricts them to the sampled non-automatic frame, and the main allocation is disproportionate under P3 |
| B-O8 | Group-paper cap *K* (starting value 10) | Decision B4 |
| B-O9 | Evidence sources allowed in Stage A | Open item in the earlier decision memo |
| B-O10 | Affiliation-normaliser version and preservation of raw affiliations | Earlier memo and director's note |
| C-O17 | Feasibility rule for pilot reservation, evaluated at *N*_max | See X-03 |
| I-O1 | One-case-per-block selector | Does not exist |
| I-O2 | Sizing script (stratified beta-binomial convolution and lower-bound check) | Must be frozen with the manifest |
| I-O3 | Pilot and main manifest builders | |
| I-O4 | Analysis code for the C5 regimes and the C7 denominators | |
| M-O7 | Section 5 edits: *R* defined as "the audited cases", the unresolved-control measure, the four-row scoring definition, the label-strategy and sampling-design subsections, the scope statement | Recorded in Decisions A and C as not applied |

## 3. Cross-decision items
- **X-01 (draft item) is not a conflict. Proposed resolution: close it with no amendment.** Decision A states that "the random audit draws from the entire non-automatic frame" and lists the frame ("all non-automatic cases of the primary pair") separately from the sampling ("proportional stratified draw by LAGOS block size"). Decision C refers to a random audit sample. Both say the same thing: the *frame* is all non-automatic cases and the *audit* is a random sample drawn from it, with its size pending. A census is the limiting case if the audit size equals the frame size, which neither record excludes or plans.
- **X-02 (new): clarify the C9 order of operations.** Post-exclusion *N_h* is computed right after the pilot draw and before sizing. This corrects my wording, not the substance. It needs a recorded clarification to the locked Decision C record, and I have not made it.
- **X-03 (new): pilot feasibility is checked before *N* is known.** C9 requires the pilot reservation to leave the main allocation feasible, but the main allocation depends on *N*. The census cap in C3 already handles a small stratum, so this is not a validity problem. Check feasibility at *N*_max, or accept that reserved blocks may shrink a census stratum, and state which.
- **Personnel dependency (for your awareness).** Personnel can be postponed to the end of the design and tooling work, but not past the B7 pilot. B7 is the first activity needing people, and it sets the audit size and constrains *m*.

## 4. Proposed corrected order of operations (for approval; not authorising any stage)
| # | Activity | Notes |
|---|---|---|
| 1 | Resolve integration items X-02 and X-03 and the non-capacity parameters | thresholds, priors, β, γ, *N*_max, bootstrap minimum, negligible-weight rule, budget and cost ceiling, stop rules |
| 2 | Build and test internal tooling, each separately authorised | selector, packet builder and leak scan, sizing script, analysis code |
| 3 | Resolve personnel requirements | the first point where people outside the project are needed |
| 4 | B7 reviewer-time pilot on about six smoke cases, with candidate-works capture for those cases | measures minutes; checks *K* and the schema; needs budget |
| 5 | Fix *m*, *m′*, the audit size, the merging rule and the audit seed | from reviewer capacity and B7 |
| 6 | Freeze software, resolver policy and weights, configuration, dossier tooling and protocol versions | |
| 7 | Draw the coverage pilot (whole blocks, own seed) and compute the post-exclusion *N_h* | outcome-free counts |
| 8 | Run the label-free coverage pilot | separately authorised; budget |
| 9 | Stratified predictive sizing: *N* and the lower-bound check; freeze *N* and allocation | |
| 10 | Draw the main sample (new seed) and write the manifest | |
| 11 | Capture retrieval for all *N* cases | ceilings and stop rules |
| 12 | Replay under the frozen policy; **freeze and hash predictions** | before any review |
| 13 | Define the verification population and the audit frame; draw the audit sample | predeclared seed and merging rule; manifest |
| 14 | Capture candidate works for the selected cases (B2c) | budget |
| 15 | Build packets by script, leak-scan and hash them; Stage A and Stage B reviews in a mixed queue; adjudication | |
| 16 | Freeze labels and analysis inputs; analyse as predeclared | with the all-wrong and all-right brackets |
| 17 | Update the manuscript from frozen artifacts | |

## 5. What was not done
The draft was saved verbatim and not corrected. No decision record, manuscript, code or seed was changed, and nothing was computed, requested or frozen. If you approve the changes above, I would produce draft v0.2 as a new file and leave v0.1 intact, and record X-02 and X-03 as explicit clarifications to the Decision C record.
