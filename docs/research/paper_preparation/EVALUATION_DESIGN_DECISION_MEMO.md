# Evaluation design decision memo: labels, dossiers, inference

**Date:** 20 November 2026. **Status:** decision support only. It changes no code, manuscript, seed, dataset or evaluation artifact, and it freezes nothing. Numbers below come from the repository artifacts or are computed from stated formulas; planning illustrations are marked as such.

## 0. Why these three decisions are one decision
The label strategy fixes how many cases can be verified. The dossier design fixes the cost and the validity of each verification. The inference design fixes how many independent units are needed, and therefore how many cases must be labelled. Deciding them separately risks a protocol that is statistically valid but unaffordable, or affordable but circular.

## 1. Facts that constrain the choice
| Fact | Source | Consequence |
|---|---|---|
| Identity groups are defined by ORCID; OpenAlex profiles also carry an `orcid` field, populated for 57.5% of returned candidates | schema and smoke reports | ORCID equality is a provisional label and cannot be used as truth without checking |
| In the 50-case smoke run the expected ORCID was found in 38 pools (R2); 7 pools lacked it, 5 had no ORCID values at all | smoke diagnostics | At least 12 of 50 cases cannot be labelled automatically, and the reason (catalog, fragmentation, label error) is unknown |
| 50 cases came from 23 blocks (1 to 5 cases per block); 10 cases repeated another case's printed name and therefore shared one provider response | smoke capture | Same-block cases can share an identical candidate pool: dependence is mechanical, not only statistical |
| All 50 seeds have status `resolved`; the benchmark contains no ambiguous-query controls | `seeds.csv` | False acceptance on unresolved controls cannot be measured from LAGOS alone |
| In the smoke run C1 gave 4 automatic outcomes in 50 (descriptive, not a forecast) | replay predictions | Few automatic decisions: precision will rest on a small $n$ |
| Of 80,294 blocks, 54,231 have exactly two ORCID groups; 70,351 are eligible for sampling | quality report | A one-case-per-block frame is large; small homonym blocks dominate it |
| Institution observed for the top candidate in 29 of 50 C1 cases; affiliation strings carry unhandled markers | smoke report | Affiliation cleaning can change automatic coverage and must precede the seed freeze |

## 2. Decision A: how every evaluation case receives an identity label

**Options**

| | A1. Benchmark-derived labels only | A2. Independent verification of every evaluated case | A3. Tiered: benchmark labels everywhere, independent verification where a claim depends on it |
|---|---|---|---|
| What | Label = ORCID equality between the dataset group and an OpenAlex candidate | Two reviewers plus adjudicator label every case from non-OpenAlex evidence | A1 as the screening layer. Independent verification of (i) every automatic assignment, (ii) a random audit sample of all other cases |
| Advantages | Cheap, scalable, reproducible | Strongest validity; no circularity | Spends review effort where precision depends on it; yields a measured label-error rate |
| Limitations | Circular; 57.5% ORCID coverage; label error unknown | Cost grows with $n$; sample limited to what reviewers can afford | Two label qualities in one study; needs careful reporting |
| Methodological risk | Any claim reads as agreement with ORCID, not identity accuracy | Small $n$ and wide intervals; reviewer fatigue and drift | Verifying only automatic cases biases recall-type metrics unless those use the random sample or the provisional labels with stated error |
| Claim it supports | "Agreement with ORCID-derived benchmark labels" | "Identity accuracy on verified cases" | Precision of automatic assignments on verified identities, plus retrieval metrics with a bounded label error |

**Verified labels versus benchmark-derived labels must be reported as separate columns, never merged.** Precision is determined by the automatic assignments, which are few, so A3 verifies exactly the cases that matter for RQ2b. Retrieval measures (RQ2a) need a mapping for every case. They use the provisional ORCID mapping plus the audit sample, which estimates its error rate with an exact interval (for example 0 errors in 30 audited cases gives a one-sided 95% upper bound of 9.5%; 3 of 30 gives a two-sided interval of 2.1% to 26.5%).

**Uncertain and unverifiable cases.** Keep four label states: *resolved*, *unresolved*, *uncertain* (reviewers disagree and adjudication cannot settle it), *unverifiable* (evidence not accessible). Uncertain and unverifiable cases are excluded from primary rates, counted, and bracketed by a sensitivity analysis (all counted as wrong; all counted as right). If they concentrate in hard cases, the primary rates are optimistic, and the paper must say so.

**Gap to decide.** LAGOS contains no ambiguous-query controls, so the unresolved-control false-acceptance measure cannot be computed. Either build a small, separate, independently labelled control set (more cost, a second benchmark) or remove that measure from the main evaluation and state the omission.

**Recommendation: A3.** It is the only option that supports a claim about identity accuracy at an affordable cost, and it keeps the benchmark-derived results honest by labelling them as such. Drop the unresolved-control measure unless the controls can be built cheaply.

**Decision needed (A):** (1) Choose A1, A2 or A3. (2) Choose to build unresolved controls or to drop that measure. (3) Approve the four label states and the sensitivity bracketing.

## 3. Decision B: audit dossier design, ORCID leakage and reviewer blinding

**Leakage channels to close.** Closing is best-effort; we record what could not be closed.
| Channel | Mitigation | Residual risk |
|---|---|---|
| Expected ORCID in dataset rows | Never in the dossier | None if the packet is script-built |
| `orcid` field of each OpenAlex candidate, and ORCIDs inside raw payloads and works authorships | Redact every ORCID string and URL from candidate material | Reviewers' own web searches may show an ORCID on a publisher page |
| HAMMER scores, ranks, signal sets, the selected candidate | Remove; shuffle candidates; assign opaque IDs | None if selection into verification is not disclosed |
| Dataset group structure (`pid`, block, split) | Remove | None |
| Provider order | Shuffle | Candidate attributes (works count) can still hint at prominence, which is benign |

**Options**

| | B1. Static packet | B2. Packet plus free external research | B3. Two-stage blinded process |
|---|---|---|---|
| What | Fixed dossier: query name, the group's papers (DOIs, titles, venues) without ORCID, and redacted candidate profiles | B1, and reviewers may browse any source | Stage A: identity from the group's papers and external evidence, before any candidate is shown. Stage B: judge each shuffled candidate against that identity |
| Advantages | Cheapest, most reproducible | Highest chance to settle hard cases | Separates "who is the person" from "which profile is theirs"; matches the earlier protocol; the identity judgment cannot be tilted by candidate lists |
| Limitations | May leave many cases uncertain | Uncontrolled evidence, ORCID leakage through publisher pages | Two passes per case |
| Risk | High uncertain rate biases the audit toward easy cases | Reproducibility weak | Cost; the group's papers come from the benchmark, so group purity must itself be checked |

**Group purity is part of the audit.** The group's papers are asserted by the benchmark to share one person. Stage A must therefore test it against independent evidence (publisher author lists, institutional pages), not assume it.

**Recording independent judgments.** One row per reviewer, per case (Stage A: status, confidence 1 to 5, rationale, evidence references, searches done) and per candidate (Stage B: same, not same or cannot tell, confidence, evidence references). Each reviewer also records whether they encountered an ORCID and the minutes spent. Reviewers work alone. A third person sees both judgments and records a final label with a rationale. Report raw agreement and Cohen's kappa, with caution at small $n$. The opaque-ID mapping stays in a separate file, held by someone who is not a reviewer. The packets are built by a script and are never edited by hand.

**Who reviews.** Reviewers should not be the people who built HAMMER or who have seen its outputs. This must be decided before the audit.

**Recommendation: B3, with B1's fixed packet as the starting material and limited external research allowed and logged.** Report the audit separately for cases where an ORCID was encountered.

**Decision needed (B):** (1) Choose B1, B2 or B3. (2) Name the reviewers and the adjudicator, and confirm they have not seen HAMMER outputs. (3) Approve the redaction rule and the logging of ORCID encounters. (4) Approve measuring reviewer minutes on the first cases before fixing the audit size.

## 4. Decision C: inference given block dependence

Dependence is partly mechanical. Cases in one block share a printed name and can share the identical candidate pool.

| | C1. One case per block | C2. Several cases per block, block-clustered inference | C3. C1 as primary, C2 as secondary |
|---|---|---|---|
| What | Draw one eligible group per block at random, by a pre-specified hash | Keep all sampled groups; resample or aggregate by block | Confirmatory sample is C1; the multi-case data is analysed as exploratory |
| Advantages | Units are independent by design; exact binomial intervals are defensible; no model needed | Uses more data from each block | Valid primary inference plus extra evidence |
| Limitations | Needs more blocks for the same $n$; discards within-block variation | With few blocks, cluster bootstrap is unstable; automatic decisions are rare, so few clusters contribute to precision | Two analyses to explain |
| Methodological risk | The estimand is per block: small two-group blocks dominate an unstratified frame | Too few clusters give optimistic intervals; effective sample size is unknown without an intra-block correlation estimate | Readers may confuse the two |

**If several cases per block remain.** Use a cluster bootstrap over blocks, which resamples whole blocks and recomputes precision as a ratio (correct automatic over all automatic, both summed within block), and add a leave-one-block-out check. Report the number of blocks and the number of blocks contributing at least one automatic decision. Do not call a design-effect adjustment reliable unless the intra-block correlation can be estimated. State that clustered intervals are unreliable below roughly 20 blocks that contribute automatic decisions; this is a rule of thumb to confirm.

**What the sample size must be driven by.** The precision of RQ2b depends on the number of automatic assignments $n_\text{auto}$, not on the number of cases. In the smoke run C1 gave 4 automatic outcomes in 50 cases. If a future sample behaved the same way (an illustration, not a forecast), 200 cases would give about 16 automatic assignments.

| Automatic assignments $n_\text{auto}$ | Zero errors: one-sided 95% upper bound on risk | Two-sided 95% interval, 0 errors | Two-sided 95% interval, 2 errors |
|---:|---:|---|---|
| 8 | 0.312 | 0.000 to 0.369 | not computed |
| 16 | 0.171 | 0.000 to 0.206 | 0.016 to 0.383 |
| 32 | 0.089 | 0.000 to 0.109 | not computed |
| 100 | 0.030 | not computed | not computed |

So even a sample of a few hundred blocks may only bound the risk loosely, and the paper must frame RQ2b as an estimate with explicit uncertainty, not a pass or fail. Stratify by block size, as the smoke sample did, and report per stratum before any pooled figure; decide whether a pooled figure is weighted by stratum size.

**Recommendation: C3.** One case per block is the confirmatory sample, chosen by a pre-specified hash; cluster bootstrap with leave-one-block-out is reported as a labelled secondary analysis. Do not fix the sample size until the audit cost (Decision B) and the expected automatic coverage under C1 are known.

**Decision needed (C):** (1) Choose C1, C2 or C3. (2) Choose whether the primary pooled figure is stratified, weighted or per stratum only. (3) Agree that the sample size is set from the target number of automatic assignments, after a minimum-detectable-bound is chosen.

## 5. Dependencies and order
1. **A before B.** The label strategy decides which cases need dossiers (all, only automatic ones, or a random sample), and therefore the workload.
2. **B before C.** The measured reviewer minutes per case fix how many cases can be verified, which caps the sample.
3. **C feeds back to A.** One case per block needs many blocks, so verifying every case (A2) may be unaffordable; A3 is robust to that. A hand-built control set needs its own independent labels.
4. **Affiliation cleaning precedes any seed freeze.** It can change institution availability (29 of 50 observed) and automatic coverage, so a new seed version and a new dataset version would follow; the 50 smoke seeds stay as they are.
5. **Thresholds, weights, policy and code revision are frozen only after A, B, C and the affiliation decision.**

## 6. Recommended package and open items
| Topic | Recommendation |
|---|---|
| Labels | A3: benchmark labels as provisional, independent verification of every automatic assignment plus a random audit sample; four label states; sensitivity bracketing; drop the unresolved-control measure unless controls are built |
| Dossiers | B3 two-stage, script-built, ORCID-redacted, shuffled and opaque; reviewers independent of the HAMMER developers; third-person adjudication; ORCID encounters logged |
| Inference | C3: one case per block (hash-chosen) as primary; cluster bootstrap as secondary; sample size set from the target automatic count |

**Open items not covered by the three decisions:** who the reviewers are and whether the adjudicator can be independent of the team; whether to build unresolved controls; the affiliation-normalizer version; the audit sheet template; the exact evidence sources allowed in Stage A.

**What stays true whatever you decide:** there is no main evaluation, no validated precision, and no accuracy claim until labels exist and the protocol is frozen.
