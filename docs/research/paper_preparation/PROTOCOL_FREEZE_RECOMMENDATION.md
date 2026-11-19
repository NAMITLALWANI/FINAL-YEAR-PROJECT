# HAMMER RQ2 protocol freeze recommendation

**Status:** Revised (Stage 2.1) to incorporate the research-director decisions of 19 November 2026 (items 1-13 below). Items marked **[Director-approved]** are approved; anything else remains a recommendation. Companion: `PILOT_DATASET_AND_ANALYSIS_SPEC.md`; tooling audit: `PILOT_TOOLING_COMPATIBILITY_AUDIT.md`.

**Director decisions incorporated:** RQ2 primary, split into RQ2a/RQ2b; R0 vs R2, R1 dropped; R2 = query normalisation + initials fallback only; pilot 10 resolved + 5 unresolved, descriptive; weights and thresholds unchanged; P4-P8 approved as conservative amendments labelled **implemented policy v2**; P3 approved provided all other safeguards still apply; token-sort institution matching approved provisionally (exact OpenAlex/ROR IDs preferred); ID-only coauthors approved; no minimum automatic count or coverage floor; V3, Day 5 and October excluded from confirmatory claims; Stage 1C sufficient for the live integration check; nothing committed in this task.  
**State inspected:** branch `main`, HEAD `bee7eabfba2d88c4a03c12d227ac6b04624fb8c8`, plus the uncommitted five-signal working-tree changes (47 status lines; none made by this task). Implementation facts come from the current code and `FIVE_SIGNAL_*` documents, not from older prose.  
**Labels used:** **[Approved]** earlier approved decision (Stage 2 decision register D01-D19 and owner record of 19 Nov 2026). **[Implemented]** what the code does now. **[Recommended]** this document's proposal. **[Amendment]** implemented behaviour that departs from an approved definition and needs approval.  
This is a pilot-readiness protocol. **The pilot is a workflow feasibility study, not a performance evaluation [Approved D09/D13].** No result exists.

## 1. Exact RQ2 wording and hypotheses

**RQ2 [Approved wording, kept].** How effectively does HAMMER retrieve author candidates, and how do its evidence-guided decision gates balance automatic assignment precision against coverage?

- **RQ2a (retrieval).** On independently identified resolved people who have at least one externally mapped OpenAlex profile, how often does each frozen query strategy return such a profile in its candidate pool, and at what rank (source order)?
- **RQ2b (selective resolution).** On one identical frozen candidate pool per query, how do the full-evidence selective policy and the forced top-1 policy differ in wrong-automatic-assignment risk, automatic coverage, manual-review rate and unresolved rate?

**Hypotheses [Approved H2a/H2b, operationalised here].**
- **H2a.** R2 has higher Recall@k or MRR than R0 on the same queries. Judged by paired per-identity differences with exact intervals; "inconclusive" if intervals are wide or captures are unusable. **Not testable in the pilot** (descriptive only).
- **H2b.** At frozen thresholds, the selective policy has lower selective risk than forced top-1 on the same pool, with coverage reported alongside. **Not testable in the pilot.** No minimum coverage is imposed.

**RQ1 [Approved].** Conditional on a valid paired deduplication replay on frozen labelled pairs. The edition-regex defect is corrected in the working tree (uncommitted), but no replay exists, so RQ1 is outside this protocol.

## 2. Decision table

| # | Decision | Existing approved definition | Actual implementation | Final definition | Reason | Approval |
|---|---|---|---|---|---|---|
| 1 | Retrieval arms | R0 raw; R1 NFC; R2 committed strategy | Only R2 logic is application code | **R0 vs R2; R1 dropped from the pilot** | No hypothesis uses R1 | **Director-approved** |
| 2 | R2 meaning | R2 is a retrieval strategy | Five-signal scoring is decision-stage | **R2 = `clean_query_name` + initials-only fallback only.** Five-signal scoring belongs to RQ2b | Separates retrieval from decision quality | **Director-approved** |
| 3 | Forced top-1 | Name-only and full-evidence arms (D08) | No forced-top-1 code | **One context-neutral baseline `forced_top1`, evaluated separately within C0 and C1.** In C0 it is *name-only* forced top-1 (only name is available); in C1 it ranks by the committed heuristic score over whatever signals are available. Null top score = no assignment, reported as no-score | Makes the name-only arm part of C0 rather than a separate option | Follows from approved items; confirm wording |
| 4 | Selective policy | "Committed gates" | Gates plus amendments | **Implemented policy v2** (section 4) | | **Director-approved** (P3-P8) |
| 5 | Context conditions | Not specified | Name always; others only if supplied | **C0 name-only; C1 preregistered institution + years (+ query-context DOIs / OpenAlex coauthor IDs only under section 6.1)**; seeds frozen before any candidate generation | Reports ordinary-UI behaviour and rich-context behaviour | Recommended; DOI rule needs approval |
| 6 | Institution matching | token-set (protocol text) | ID/ROR equality, else token-sort | **Token-sort provisionally; exact IDs preferred; limitations stated.** Not equivalent to the original token-set wording | | **Director-approved** |
| 7 | Coauthor evidence | Names or IDs | OpenAlex IDs only | **ID-only** | | **Director-approved** |
| 8 | Pilot size | 10 + 5 (D09) | n/a | Unchanged; descriptive, not a performance evaluation | | Approved |
| 9 | Labels | resolved/unresolved/uncertain (D10) | n/a | Unchanged | | Approved |
| 10 | Coverage floor / minimum automatic count | None (D11, D13) | None | None | | **Director-approved** |
| 11 | Baseline commit | `d41378c` (stale) | `bee7eab` + uncommitted | Freeze a new commit before any capture (owner action; not done here) | Reproducibility | Open |

## 3. Baselines: exact definitions and fairness limits

- **R0.** `GET https://api.openalex.org/authors?filter=display_name.search:{trimmed query}&per-page=10`, page 1 only, no normalisation, no fallback. Rank = provider order. **[Approved, proposed in protocol]; not implemented as application code**; implemented only in the capture script.
- **R2.** Same endpoint and parameters, query passed through `clean_query_name` (NFC, whitespace collapse, narrow "Le/La" join); if and only if the primary response succeeds with zero valid candidates **and** the query contains an initial token, one fallback request `search={query}`; unseen IDs appended. **[Implemented]**. Primary and fallback outcomes are recorded separately because a failed fallback is swallowed and can end as `empty` (known defect, not changed).
- **Forced top-1.** On the frozen R2 pool, rank by the committed heuristic score (ties by descending source ID); select rank 1 when its score is non-null; a null top score is "no score", reported separately. **[Approved]**.
- **Selective resolver.** `evaluate_decision` on the same pool and context. **[Implemented]**, subject to section 4.
- **Fair comparison R0 vs R2.** Fair only if both arms use the **same query strings, same provider, same capture window and same Stage B ground-truth mapping**. Live OpenAlex changes over time, so each arm's raw responses are captured once, hashed and replayed; the comparison is on captured responses, not on live calls. R0 and R2 differ only in query text for most queries (they are identical when normalisation changes nothing), so many pairs will be ties.
- **Limitation (must be stated in the paper).** Candidate scores built from different signal sets are not directly comparable, because the score is renormalised over available signals. This affects the ranking itself, forced top-1 and any margin computation. **No common-subset reranking and no new scoring formula is introduced.** Each pool's per-candidate signal set is reported.
- **Not a baseline:** historical V3, Day 5 and October numbers. They are development evidence and are excluded from confirmatory claims.

## 4. Decision policy: implemented policy v2

Inputs: the ranked pool, per-candidate evidence, and the context condition. Frozen thresholds: automatic score 0.75, margin 0.15, dominance 1.35, manual score 0.45, minimum 2 available signals; weights 0.35/0.25/0.20/0.10/0.10 renormalised over available signals. The score is a heuristic, not a probability.

| # | Rule | Status |
|---|---|---|
| P0 | Null top score (no usable signal) gives **unresolved** with reason "no score" | Approved (D08) |
| P1 | Automatic requires top score ≥ 0.75 and ≥ 2 available signals | Approved |
| P2 | With competitors: margin ≥ 0.15 and dominance ≥ 1.35 (dominance not evaluated when the second score is 0) | Approved |
| P3 | Single-candidate pool: P2 is not applicable. **P3 relaxes only P2. P1 and P4-P8 still apply in full** | **Director-approved**, on that condition |
| P4 | A competitor with no score blocks automatic | **Director-approved** amendment |
| P5 | The top candidate needs an observed, non-zero institution, publication or coauthor signal | **Director-approved** amendment; conservative design assumption that name and temporal agreement alone are insufficient, not an empirical finding |
| P6 | An observed signal scoring exactly 0.0 on the top candidate blocks automatic | **Director-approved** amendment |
| P7 | Competitors scored on a different signal set than the top candidate block automatic | **Director-approved** amendment |
| P8 | Any evidence-retrieval failure in the pool, or an unreadable candidate, blocks automatic | **Director-approved** amendment |
| P9 | Not automatic and top score ≥ 0.45 gives **manual review**; otherwise **unresolved** | Approved |
| P10 | Provider failure: no decision recorded (`provider_failed`, separate category). Successful empty pool: `unresolved` with reason "empty retrieval", counted separately | Implemented; consistent with "failed is not empty" |

**Policy variants reported (names fixed):**
- `selective_policy_v2`: P0-P10 (the implemented policy).
- `legacy_gates_plus_p3`: P0, P1, P2, P3, P9, P10 only; P4-P8 switched off. This is the original gates plus the single-candidate rule. **The name does not imply that P3 was historically approved**; it was implemented behaviour that the director has now approved. It is computed offline from the same snapshot so the amendments' effect is visible.
- `forced_top1`: top-ranked candidate by heuristic score (ties by descending source ID) whenever its score is non-null.

**C0 interpretation (structural, not empirical).** C0 supplies only the name, so only the name signal can be available. P1 needs two signals and P5 needs a non-name, non-temporal signal, so **automatic assignment under `selective_policy_v2` (and under `legacy_gates_plus_p3`, which still needs 2 signals) is structurally impossible in C0.** C0 is a **name-only abstention/control condition**; its automatic coverage is zero **by design**. That zero must not be read as evidence of safety or accuracy. C0 outcomes (manual review, unresolved, no-score, failures) and C0 `forced_top1` are reported descriptively. **C1** is the condition in which automatic coverage can be observed, if sufficient independent evidence is supplied and obtained.

The limitation that scores built from different signal sets are not directly comparable remains: it affects ranking, `forced_top1` and margin computation, and no common-subset ranking or new formula is introduced. The amendments only withhold automation; their effect on precision or coverage is unmeasured.

## 5. Signal definitions

| Signal | Query input | Candidate source | Score | Unavailable when |
|---|---|---|---|---|
| Name | Query name (+ optional aliases) | OpenAlex `display_name` and alternatives | RapidFuzz `token_sort_ratio`/100 on casefolded, whitespace-collapsed text; max over pairs. No diacritic folding or transliteration | Never for a valid candidate |
| Institution | Supplied institution (name, OpenAlex ID, ROR) | `last_known_institutions` + `affiliations` | ID/ROR equal ⇒ 1.0; different IDs ⇒ 0.0; else `token_sort_ratio`. **Token-sort is provisional** and mis-scores abbreviations ("MIT") and aliases ("Mila"); similarly named institutions can score high | No query input, or no candidate affiliations |
| Publication overlap | Supplied DOIs / OpenAlex work IDs (titles ignored) | Authorships of the query's own works from one OpenAlex works lookup | Matched ÷ comparable supplied works (comparable = resolved in OpenAlex with untruncated author list) | No input; lookup failed; lookup empty; all works unresolved or truncated; stored result belongs to another input set |
| Coauthor overlap | Supplied **OpenAlex author IDs only** | Coauthor IDs from the candidate's own works' authorships, bounded sample (≤200 works, 2 pages × 100), explicit sort `publication_date:desc,cited_by_count:desc`; own ID excluded | Matched IDs ÷ min(supplied IDs, candidate coauthors) | Name-only input (`unavailable_input_unresolvable`, count-only diagnostics); no sample; failed; **zero overlap in an incomplete sample is inconclusive, not 0.0** |
| Temporal | Supplied year range | Min/max year in author `counts_by_year` | Range overlap ÷ shorter span | No input; no candidate range; query range entirely before the candidate's observed range (inconclusive). Query range after the observed range scores 0.0 |

Every signal carries a status (`observed`, `unavailable_*`), provenance and retrieval time. Live verification (Stage 1C): the request shapes, explicit sort, paging, positive publication evidence and positive coauthor-ID evidence were confirmed for **one** author/work; many conditions remain unverified (429, API key, authors with >100 works, incomplete samples live, tie stability).

**Availability in the ordinary UI:** name only. Everything else needs user-supplied context, and coauthor evidence needs OpenAlex IDs. The paper must not say all five signals are used on every query.

## 6. Ground-truth and annotation protocol (pilot)

### 6.1 Separating gold evidence from query context (leakage control)
A DOI that establishes the gold identity must not also be silently supplied to HAMMER as query context, otherwise publication overlap would be partly answering its own ground truth.
1. **Two purposes, never merged by default.** Every DOI is registered with a purpose: `gold_evidence` (used by reviewers to establish identity) or `query_context` (supplied to HAMMER in C1), or `both` **only** with a written justification showing the overlap is legitimate (for example, the DOI is part of the real-world information a user would already have, and was chosen by the frame preparer before Stage A).
2. **Prefer disjoint sets.** Query-context DOIs are chosen by the frame preparer from sources independent of OpenAlex and of the reviewers' gold packet; gold DOIs are those the reviewers independently collect.
3. **Overlap check.** After Stage A, the intersection of reviewer gold DOIs and seed query-context DOIs is computed per case and recorded. It never edits the seed.
4. **If disjointness cannot be shown** for a case (intersection non-empty without an accepted justification), **publication-overlap results for that case are excluded from the primary pilot interpretation and reported as exploratory only** (condition `C1x`), while the case's C1 primary run omits the DOI context.
5. **Seeds frozen first.** The case seed (including all context) is hashed and frozen **before any HAMMER candidate generation or capture**. No context may be added or changed after any candidate, rank, score or outcome has been seen; a change creates a new dataset version.

### 6.2 Definitions and procedure

Builds on `AUTHOR_BENCHMARK_PROTOCOL.md` and the pilot protocols in `stage2/pilot/`; only choices not yet fixed are decided here.

**Definitions.** (Stage A identity verification is separate from the HAMMER query context of section 6.1.)
- **Resolved:** external evidence supports exactly one intended person: at least one person-level source (official institutional or lab page, authoritative researcher record, or personal academic page) **and** at least two DOI-resolvable publisher or repository records whose author lists and metadata connect to that person. ORCID may support but is not sufficient alone.
- **Unresolved:** the query plus its supplied context does not establish a unique intended person under the same evidence search (two documented search passes). It does **not** mean the person does not exist or is absent from OpenAlex.
- **Uncertain:** reviewers cannot settle the identity; excluded from primary rates and counted.

**Case selection [Recommended; the director must approve the frame].**
- Frame: researchers in a named domain with public institutional pages (suggest the owner's department/university plus public figures not in V3/Day 5/October material), prepared before any HAMMER output is seen. 10 resolved cases and 5 unresolved controls.
- Resolved cases: stratify nothing by outcome; aim to include at least one common-name case and one with name variants, chosen by the frame preparer without looking at OpenAlex results.
- Unresolved controls: construct from real ambiguous queries (e.g. a very common name plus insufficient context), **not** from empty provider results.
- Exclusions: any person in V3, Day 5, the October deck or the existing pilot artifact; duplicate persons or alias variants (one case per underlying person); persons whose evidence cannot be accessed without restricted material; minors/private individuals.

**Reviewers.** Two independent reviewers (A, B) plus an adjudicator (third person; if unavailable, the owner after both finish, recorded as such). Reviewers receive only: query text, query seed context, and the external evidence packet they themselves collect or are given. They may inspect public web sources, publisher pages and DOI records. They must **not** see HAMMER candidate lists, ranks, scores, resolver decisions, OpenAlex profile pages for the query, or each other's judgments, and no prior V3/Day 5 labels.

**Stage A (identity truth, before any candidate generation; reviewers also register each DOI they use as `gold_evidence`).** Each reviewer records status, confidence 1-5, rationale and evidence references for every case. Agreed ⇒ final. Disagreement ⇒ adjudicator records the final label with rationale; if evidence still does not settle it, `uncertain`.

**Stage B (candidate-to-gold mapping, after Stage A is frozen and R0/R2 captures are sealed).** Reviewers, blind to rank, score and system decision, mark which OpenAlex candidate profiles in the captured pools correspond to each resolved person (multiple mapped profiles allowed because of fragmentation) and label each candidate "same / not same / cannot tell" with evidence. Adjudication as in Stage A.

**Record structure and rules.** See the pilot spec. A system prediction is never ground truth. The pilot must not be merged into a later confirmatory test set after its candidates or outcomes were inspected.

## 7. Metrics and denominators

Population: pilot cases with final label resolved or unresolved; `uncertain` excluded and counted. Counts and denominators are always printed beside rates.

**Retrieval (RQ2a), per arm.** Let M be resolved cases with at least one mapped profile in the **union of the captured pools**; catalog coverage = M ÷ resolved cases (reported, because an OpenAlex omission is not a retrieval miss within that catalog).
- **Recall@k** (k = 1, 5, 10) = cases in M whose first mapped profile is within the first k of that arm's pool ÷ |M|. The pool is at most 10, so Recall@10 equals pool recall; where pools are shorter than k, use all returned.
- **MRR** = mean of 1/rank of the first mapped profile (0 if missed) over M.
- Pool size, empty-pool rate, provider-failure rate reported separately; failures stay in the denominator of end-to-end counts and are never relabelled as empty.
- Unresolved controls are **excluded** from retrieval metrics (no target).

**Selective resolution (RQ2b), on the frozen R2 pool and fixed context condition.** Denominator for rates = all eligible cases (resolved + unresolved), including provider failures and empty pools.
- **Correct automatic:** auto-selected profile maps to the case's resolved person.
- **Incorrect automatic:** auto-selected profile maps to someone else, lacks mapping evidence, or the case is an unresolved control.
- **Automatic coverage** = automatic ÷ eligible. **Automatic precision** = correct ÷ automatic. **Selective risk** = incorrect ÷ automatic = 1 − precision (undefined when there are zero automatic assignments; report "no automatic assignments", not 100%).
- **Manual-review rate**, **unresolved rate**, **no-score**, **provider-failure** and **empty-pool** rates = their counts ÷ eligible.
- **Unresolved controls:** an automatic assignment on one is a false acceptance; manual review or unresolved on one is the intended abstention (reported, not "correct"/"incorrect" in the precision formula).
- **Forced top-1 (`forced_top1`):** correct top-1 ÷ eligible resolved cases, computed **separately within C0 and C1**; a null score is "no score", not a miss and not a selection. In C0 this is name-only top-1.
- **C0 automatic coverage** is structurally 0 under policies that require ≥ 2 signals (section 4); report it as "0 by design", not as a result. Provider failure, successful empty retrieval, no-score, manual review and unresolved stay separate categories in every table.
- **Reported alongside:** the signal-set composition of each pool and of each top candidate, which safeguards blocked automation, and an error table by cause (retrieval miss, mapping gap, ranking error, gate withheld, conflicting evidence).

**Uncertainty.** Exact (Clopper-Pearson) two-sided 95% intervals for proportions, with n. Zero automatic assignments: precision is undefined; report coverage 0/n with its interval. Zero errors in n automatic assignments: one-sided 95% upper bound 1 − 0.05^(1/n) (n = 8 ⇒ about 31%). Paired R0-vs-R2 differences: report discordant counts (exact McNemar as description, not a test claim). Repeated queries: one primary query per identity; variants are secondary and clustered.

**Why the pilot is descriptive.** With 10 resolved and 5 unresolved cases, any rate has very wide intervals, automatic assignments will be few and the sample is curated and not random. The pilot cannot support accuracy, superiority, coverage or safety claims, and no pass/fail criterion is set.

## 8. Dataset and leakage controls
1. **Separation.** Pilot cases are permanently assigned to the pilot split; none may enter a later confirmatory test set after candidates or outcomes were seen. Main-study identities are drawn from a new frame, identity-disjoint from the pilot.
2. **Development exclusions.** V3 (56 identities, 33 OpenAlex IDs), Day 5, the October deck cases and `docs/evaluation/pilot_predictions.json` identities are excluded from the pilot and from confirmatory use. Their eligibility for tuning is moot because thresholds are frozen.
3. **Duplicate prevention.** One case per underlying person; alias/variant queries merged; the same OpenAlex profile cannot be a gold mapping for two cases. Shared decisive DOIs across cases are recorded and cases sharing one are merged or one is dropped.
4. **Overlap checks.** Author-ID and DOI overlap between pilot and development sets are computed and reported before unsealing.
5. **Versioning and freezing.** Seeds, labels, split membership, thresholds, code SHA and package versions are hashed and frozen before candidate capture; any later change creates a new dataset version.
6. **Frozen snapshots.** Raw R0/R2 responses (and enrichment responses) with timestamps, endpoints, parameters (without secrets) and hashes; replay uses captures, never later live calls.
7. **Missing provider data.** Failures keep their error code; empty is not failure; unavailable signals stay unavailable; none is imputed.
8. **Reproducibility.** Metrics regenerate from frozen files by script; notebooks are exploratory only.

## 9. Statistical planning
The main-study size is **not set here**. After the pilot, record: evidence availability, reviewer agreement, adjudication rate, pool-size distribution, mapping effort, observed automatic coverage under C0 and C1, and provider failure rate. The director then chooses a precision objective and derives the number of eligible cases from the observed coverage (cases needed ≈ automatic decisions needed ÷ coverage). Illustration only, **not a coverage requirement or target**: with zero errors, 59 independent automatic assignments give a one-sided 95% upper error bound just below 5% (1 − 0.05^(1/59) ≈ 4.95%); any observed error requires more.

## 10. Paper-readiness check (literature)
Existing coverage is adequate for background but **thin where RQ2 is most specific**; only these gaps matter:
1. **Candidate generation and assignment (cluster 3):** read CONNA, WhoIsWho and AMiner in full for how candidates are generated and whether retrieval recall is reported; add a blocking/candidate-generation reference actually read.
2. **Author-disambiguation-specific abstention (cluster 5):** read HUMO/r-HUMO and the AMiner human-in-the-loop work; run the follow-up searches in `LITERATURE_SEARCH_LOG.md` section 9.
3. **Ground-truth construction (cluster 2):** read S2AND, LAGOS-AND and Müller et al. for label quality and leakage; cite what is needed to justify the two-reviewer design.
4. **Evaluation methodology:** a verified citation for exact binomial intervals for small samples (not yet in the inventory; unverified lead only).
Most inventory rows are metadata-only and none was read in full; **specific claims must not be attributed before reading.**

**Conservative positioning.** An applied scholarly-metadata system; a heuristic evidence resolver with up to five signals whose availability depends on supplied context; an evaluation protocol that reports retrieval and selective resolution separately. Do not claim novelty, "first", state of the art, calibrated confidence, universal accuracy, zero false merges, or that the safeguards improve precision. A gap statement may say only "not established from the sources reviewed". Keep the agreed IEEE conference two-column LaTeX/Overleaf structure; no abstract or results until approved.

## 11. Contradictions and implementation limitations to state
- Stage 2 text calls institution matching token-set; the code uses token-sort (provisional).
- Stage 2 text says evidence uses local database/index state; the code uses only payload and request context.
- `docs/evaluation/dataset.md` still describes a 100-query minimum (marked historical).
- Existing capture/evaluation scripts in `backend/scripts` target semantic publication retrieval (`capture_retrieval_predictions.py` has a 100-query minimum); I did not find an author-candidate R0/R2 capture script, and whether `replay_frozen_resolver.py` accommodates enrichment and context was **not verified**. Codex must confirm before reuse.
- Ranking mixes signal sets (case H); the failed initials fallback is swallowed; tie order in the works sample is undocumented; live checks cover one author only.

## 12. Open decisions for the research director (remaining)
1. Approve the DOI-purpose rule of section 6.1 (including treatment of non-disjoint cases as exploratory `C1x`).
2. Approve the C0/C1 definitions and the per-case seed contents.
3. Approve the case frame and unresolved-control construction; assign Reviewer A, Reviewer B and the adjudicator (roles only; no names are assumed here).
4. Decide who commits the implementation baseline and when (the capture and replay tooling must first be made fit; see the audit).
5. Decide whether an uncertain unresolved control may be replaced.
6. Decide the future-implementation task order for the tooling gaps in `PILOT_TOOLING_COMPATIBILITY_AUDIT.md`.
