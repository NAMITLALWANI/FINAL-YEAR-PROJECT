# Decision B: audit dossier design, blinding and reviewer-time pilot (proposal)

**Date:** 20 November 2026. **Status:** B1 to B7 approved by the research director as recommended (see section 6). **Read-only:** no dossier, packet, capture, seed, code or manuscript file was created or changed; the only new file is this one. Decision A is approved (`DECISION_A_LABEL_STRATEGY_RECORD.md`, revision 2); Decision C is open. Facts marked *verified* were read from the smoke-run artifacts in `research_data/lagos_and_v2/`; no gold ORCID value was printed.

## 1. What the existing artifacts show
| Finding (verified) | Consequence for the dossier |
|---|---|
| Every captured OpenAlex author object carries `orcid`, `ids.orcid` and a field `observed_orcids`; 129 of 231 objects hold a value, and 524 ORCID-URL strings occur across the 231 objects | ORCID leaks through at least three fields per candidate, so redaction by field name alone is fragile |
| Author objects also carry `relevance_score`, `block_key`, `raw_author_names`, `full_name`, `works_api_url`, `ids.openalex`, creation and update dates | `relevance_score` reveals provider rank; `works_api_url` and `ids.openalex` allow a reviewer to open the live profile, which shows the ORCID. The meaning of `observed_orcids` and `block_key` should be confirmed from provider documentation before relying on them |
| Works responses (C1x look-ups) list authorships with `author.orcid`: 141 such entries in the 50 look-ups | Works material needs the same redaction |
| The captures hold **no list of each candidate's works**; the works responses cover only the designated DOI | Reviewers have no capture-backed evidence about what a candidate has published |
| Benchmark rows (`selected_block_rows.csv`) include the ORCID, `pid`, block name, split flag and source row | All of these must be dropped from any Stage A packet |
| Group paper counts per case: minimum 2, median 6.5, maximum 260; 18 of 50 groups have more than 20 | A Stage A packet needs a cap |
| R2 pool sizes: minimum 1, median 6.5, maximum 10; 306 candidate profiles over 50 cases | Stage B is roughly six candidate judgments per case |

## 2. Decisions

### B1. Review process
| | B1a. Static single packet | B1b. Single packet, free browsing | **B1c. Two-stage blinded (recommended)** |
|---|---|---|---|
| Stage A | none | none | Identity first: from the group's papers and external evidence, decide who the person is and whether the group is pure. No candidate profile is shown |
| Stage B | one pass | one pass | Per-candidate judgment against the Stage A identity, on a shuffled pool under opaque IDs |
| Strength | cheapest | highest chance to settle a case | the identity judgment cannot be tilted by a candidate list; matches the earlier protocol |
| Risk | many *uncertain* | uncontrolled evidence and ORCID exposure | two passes of work |

**Group purity is part of Stage A.** The benchmark asserts that a group's papers belong to one person. Stage A must test that claim against evidence outside the benchmark labels, such as publisher author lists and institutional pages. A group judged impure is labelled *uncertain* or *unverifiable*, never forced.

### B2. Where candidate evidence comes from
| | B2a. Stored author object only | B2b. Reviewers browse OpenAlex live | **B2c. Additional bounded, hashed capture of each candidate's works (recommended)** |
|---|---|---|---|
| Evidence | name variants, affiliations, topics, yearly counts, works count | anything on the live profile | a capped list per candidate (title, DOI, year, venue, author names), saved and hashed like every other response |
| Problem | too little to separate common names | the live page shows the ORCID; content drifts over time; not reproducible | needs new provider requests (not made yet) and a redaction step |

Cost is small: the smoke run's 92 requests cost $0.047, so roughly six candidate-works requests per verified case is a minor cost. It still requires provider calls, so it needs your approval and a request budget at implementation time, and it must follow the same save-and-hash discipline.

### B3. Blinding and ORCID leakage
**Build packets by an allow-list, not a deny-list.** Only named fields enter a packet. A deny-list fails silently when the provider adds a field such as `observed_orcids`.

| Packet | Allowed | Always excluded |
|---|---|---|
| Stage A | printed query name; up to $K$ group papers (title, DOI, year, venue, author names, affiliation, coauthor names); the designated paper always included | ORCID, `pid`, block name, split flag, source row, any HAMMER output |
| Stage B | per candidate under an opaque ID: display name and variants, affiliations with years, topics, works count, capped works list from B2c | every ORCID field and URL (`orcid`, `ids.orcid`, `observed_orcids`, works `author.orcid`), `ids.openalex`, `works_api_url`, `relevance_score`, provider order, HAMMER scores, ranks, signal sets, the selected candidate, pool statistics that reveal rank |

Further controls:
1. **Shuffle** candidates with a hash-seeded order, independent of provider rank and HAMMER rank.
2. **Opaque IDs** per case, with the mapping in a separate file that reviewers cannot open and that is held by a person who is not a reviewer.
3. **Automated leak scan before release:** a packet is released only if a scan finds zero ORCID patterns, zero provider IDs and URLs, and none of the HAMMER field names. The scan result is stored with the packet hash.
4. **Residual leakage cannot be eliminated.** Reviewers' own searches may show an ORCID on a publisher page. They are told not to use ORCID as evidence, and they record whether they encountered one. Results are reported separately for cases where they did.
5. **Verification of automatic assignments** uses exactly the same packet as any other case: the full shuffled pool, and no sign of which case came from the automatic set.

### B4. Group-paper cap $K$ (Stage A)
Median 6.5, maximum 260 papers. Proposal: $K=10$, the designated paper plus up to nine others chosen by a hash order; cases with fewer papers show all. $K$ is checked in the pilot and frozen before the audit. **Decision needed: accept $K=10$ or set another value.**

### B5. Recording, agreement and adjudication
The earlier single-row review template (`identity_review.csv`: one status and one gold author ID per case) does not fit a two-stage, per-candidate design, so a new schema is needed.
- **Stage A, one row per reviewer per case:** status (resolved, unresolved, uncertain, unverifiable), confidence 1 to 5, group-purity judgment, rationale, evidence references, searches performed, ORCID-encountered flag, minutes.
- **Stage B, one row per reviewer per case per candidate:** judgment (same, not same, cannot tell), confidence, evidence references, ORCID-encountered flag, minutes.
- **Independence:** reviewers do not discuss before submitting. The adjudicator sees both reviewers' rows and the dossier, and records a final label with a rationale. Where evidence still does not settle a case, the label is *uncertain* or *unverifiable*, per Decision A.
- **Agreement:** raw agreement and Cohen's kappa for Stage B judgments, with counts, and a caution that kappa is unstable at small numbers and when one category dominates.

### B6. Who reviews
| | B6a. Outside peers as reviewers, faculty member as adjudicator | B6b. Project members who have not seen HAMMER output | B6c. External volunteers |
|---|---|---|---|
| Independence | strong | weak: shared knowledge of the system and the benchmark | strong |
| Practicality | needs recruitment and a short briefing | easiest | hardest to schedule |

Required whichever option is chosen: each reviewer states in writing that they have not seen HAMMER outputs or the benchmark ORCID labels for the audited cases; the person who builds packets and holds the mapping is neither a reviewer nor the adjudicator; reviewers are calibrated on the pilot cases. **Recommendation: B6a, or B6b only with those attestations and the limitation stated in the paper.** I cannot judge from the repository who is available, so the names are yours to supply.

### B7. Reviewer-time pilot (sets the audit size under Decision A)
Purpose: measure the effort and the failure modes before fixing the audit size.
- **Cases:** a small number from the existing 50 smoke seeds, chosen by a deterministic rule stratified by pool size and group size. Smoke cases carry no confirmatory role, so using them costs nothing in validity. They are excluded from the audit sample. The pilot needs B2c captures for those cases only.
- **What it measures:** minutes per Stage A pass; minutes per candidate in Stage B; the share of cases and candidates labelled uncertain or unverifiable; how often an ORCID was encountered; dossier defects (missing evidence, leaks found by reviewers); indicative agreement.
- **How it sets the size:** with total reviewer time $H$ hours per reviewer and measured mean minutes $t_A$ per case for Stage A and $t_B$ per candidate, with $\bar k$ candidates per case, the affordable number of audited cases is about $N=\lfloor 60H/(t_A+\bar k\,t_B)\rfloor$ per reviewer, less adjudication time and the number of automatic assignments that must be verified first. The audit sample is what remains. No time has been measured yet, so this memo gives no figure.
- **Decision needed:** the number of pilot cases (I suggest about six, enough to see the range of pool and group sizes without a large commitment) and the reviewer hours available.

## 3. Decision checklist
| # | Decision | Recommended |
|---|---|---|
| B1 | Process | Two-stage blinded (B1c), with group purity checked in Stage A |
| B2 | Candidate evidence | Bounded hashed capture of candidate works (B2c); approve a request budget later |
| B3 | Blinding | Allow-list packets, shuffle, opaque IDs, separate mapping, zero-match leak scan, ORCID-encounter logging |
| B4 | Group-paper cap | $K=10$, to be checked in the pilot |
| B5 | Records | New two-stage schema; independent rows; adjudication by a third person; agreement reported with counts |
| B6 | Reviewers | Outside peers and a faculty adjudicator, or project members with written attestations; names to be supplied |
| B7 | Pilot | About six smoke cases; measure minutes, uncertainty, ORCID encounters; set the audit size from the formula |

## 4. Dependencies
- B2c needs new provider requests, so it waits for your approval of a request budget. Nothing is requested now.
- The audit size (Decision A) waits for B7.
- Decision C (one case per block) fixes how many cases exist to verify, so it should be settled after the pilot gives a per-case cost.
- The leak scan and the packet builder are implementation work and have not been started.

## 5. What has not been done
No dossier or packet was generated, no provider request was made, no capture was changed, and the manuscript, seeds and code are untouched. The evaluation remains unfrozen.

## 6. Approval record (20 November 2026)
The research director approved B1 to B7 as recommended in section 3. Approval covers the design, not the following items, which stay open:
| Open item | Status |
|---|---|
| Reviewer and adjudicator names; B6a or B6b | To be supplied by the director. If B6b, written attestations and the stated limitation are required |
| Reviewer hours $H$ | To be supplied |
| Pilot case count | About six recommended; to be confirmed with the pilot case list |
| $K=10$ | Accepted as the starting value; checked in the pilot and frozen before the audit |
| B2c request budget | Not approved. Needs a separate approval with a stated request count and cost ceiling before any provider call |
| Packet builder and leak scan | Not implemented. Not started until the director says so |
| Audit size (Decision A) and sample size (Decision C) | Wait for the pilot |

**Personnel deferral (director, 20 November 2026).** Every requirement involving people outside the project is postponed to the very end and will be settled together with the other external dependencies: reviewer and adjudicator names, recruitment, external attestations, and assumptions about reviewer availability or hours. B6a stays the preferred design with its personnel requirements unresolved. B6b is not adopted merely to avoid recruitment. The "Reviewer names", "Reviewer hours" and "Pilot case count" rows above are therefore deferred, not pending. Internal protocol work (schema, packet design, leak-scan specification) may continue.

Nothing was generated or frozen on approval. The manuscript is not edited, including the Decision A wording and any Decision B text for Section 5.
