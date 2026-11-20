# HAMMER: final completion report and manuscript/evidence audit

**Date:** 20 November 2026 (updated after the no-spend instruction; see section 11) | **Git:** branch `main`, HEAD `6d31cbe`, dirty working tree, **nothing staged, committed, reset, stashed, cleaned or reverted** (`git diff --cached` is empty). One tracked file was modified: `backend/scripts/capture_hammer_pilot.py` (adds `--cost-ceiling-usd` and the stop guard). All other changes are new untracked files.

## 1. Headline
The paper, tooling and evaluation preparation are as complete as they can be **without two external inputs**: an OpenAlex API credential (none exists in the environment, and none may be pasted into chat or a file) and independent human reviewers (deferred by the director and never simulated). Consequently **no performance result exists and none is reported.** Results, the Abstract and the verified-results sections are pending by design, not by omission. A LaTeX compile was not possible (no TeX installation; none was installed without consent).

## 2. What was completed in this run
| Item | Status | Evidence |
|---|---|---|
| Inspection of repo, manuscript, protocol, tooling, register | done | this report; git state above |
| Dataset year-range discrepancy | **resolved**: 1870 to 2022 is the full-archive range; 1963 to 2022 was a 16,710-row prefix | T014 |
| Evaluation freeze (code hashes, configuration, adopted parameters, derived seeds) | done, verified | `research_data/lagos_and_v2/eval_F2/freeze_F2.json`, T015 |
| Parameters adopted from the ratification sheet (except m, m', audit size, personnel) | done, documented | `PARAMETERS_ADOPTED_F2.json` |
| Coverage-pilot draw (250 blocks, label-free) and capture inputs | done offline | `eval_F2/pilot/`, T015 |
| Capture stop conditions (cost stop level, 3 consecutive 5xx) | built, tested | T017 |
| Candidate-works capture and blinded packet release driver | built, tested, dry-run on smoke data in scratch | T017 |
| C7 report assembly from replay, manifest, mapping, verified labels | built, tested | T016 |
| Reviewer instructions, human-dependency list with exact commands | written | `REVIEWER_INSTRUCTIONS.md`, `HUMAN_DEPENDENCIES_AND_NEXT_ACTIONS.md` |
| Claim-level check of S2AND, WhoIsWho, CONNA, HUMO/r-HUMO, LAGOS-AND | done (LAGOS-AND partly: journal paper unreadable) | T018, `REFERENCE_VERIFICATION.md` |
| Manuscript: Sections 1, 2, 5, 7, 9 and the literature table updated; Discussion and Conclusion written from supported content only | done | `paper/HAMMER_IEEE_PAPER/` (zip rebuilt) |
| Testing register, methodology, viva summary, reports T014 to T018, raw outputs and hashes | done | `docs/testing_validation/` |
| Full backend suite | **585 passed** | `RAW_OUTPUTS/T017_run1/pytest_full_suite.txt` |

## 3. Experiments actually run
- Real: the full-archive year scan (T014); the offline pilot draw and capture-input build on the real catalogue and archive (T015). **No provider request was made in this run.**
- Earlier and still the only real provider data: the 50-case smoke capture (92 responses, USD 0.047), used only as an operational check.
- Synthetic: all unit tests, mutation checks, the end-to-end rehearsal and the Monte Carlo validation (T001 to T013, T015 to T017).
- **Not run:** the coverage-pilot capture and replay, sample-size computation on real pilot counts, the main sample draw and capture, the audit draw, the reviewer-time pilot, the blinded review, the C7 report on real data, the result tables.

## 4. Exact dataset and sample sizes
Archive 743,558,936 bytes (SHA-256 `a0ac028b...6840`); 1,476,550 rows; 80,294 blocks; 244,564 identity groups; years 1870 to 2022; 70,351 eligible blocks. Test-split frame after the smoke exclusion: S 8,038, M 8,360, L 1,173, XL 9 (17,580). Pilot drawn: 100 S, 100 M, 50 L, 0 XL blocks (250 primary cases, 264 uncaptured secondary cases); frame after the pilot: S 7,938, M 8,260, L 1,123, XL 9. Smoke: 50 cases from 23 blocks.

## 5. Main findings, denominators and uncertainty
**There are no main findings.** The only real-data counts are the smoke diagnostics (50 cases, 23 related blocks; expected ORCID in the R2 pool for 38; C1 selective policy 4 automatic and 46 manual), which are benchmark-derived, operational, and carry no interval. Tooling and methodology results (all synthetic): estimators unbiased; per-stratum Clopper–Pearson coverage 0.96 to 0.97; pooled bootstrap 0.935 against 0.95; predictive sizing 0.899 (matched prior) and 0.881 (mismatched prior, small pilot); lower-bound check 0.998; plug-in rule 0.55 to 0.68. These describe procedures, not HAMMER.

## 6. Benchmark-derived versus independently verified
Everything real is benchmark-derived (provisional ORCID agreement). **Nothing is independently verified.**

## 7. What depends on people (not simulated)
Independent blinded reviewers (at least two), an adjudicator, a packet builder, the reviewer-time pilot (sets m' and the audit size), the research director's confirmation of the adopted parameters, an OpenAlex API key in the user's own shell, and a cost ceiling. Exact commands: `HUMAN_DEPENDENCIES_AND_NEXT_ACTIONS.md`.

## 8. Unresolved methodological and technical limitations
Provisional ORCID labels; the weak membership hint in the designated-citation context; coauthor evidence unobservable on this benchmark; one provider whose content can drift; minimal affiliation cleaning; pooled bootstrap slightly under-covers; sizing conditional on a finite pilot and on an unset m'; the works capture has never contacted OpenAlex and assumes the response shape of the candidate capture; the freeze identifies code by file hashes because the tree is dirty and may not be committed; CONNA's TKDE year (arXiv 2020, Crossref 2022) and r-HUMO's venue rest on Crossref.

## 9. Manuscript and evidence audit
| Check requested | Result |
|---|---|
| Outdated or inconsistent sample sizes and counts | none found; smoke 50 and 23, frame and pilot counts checked against T011 and T015 |
| Dataset year range | corrected provenance added (T014) |
| Metric definitions and denominators | consistent with C7 and T005 (Table of measures; six outcome categories) |
| C1, C1x, R0, R2 descriptions | consistent with code and protocol |
| Resolver safeguards | consistent (B1 to B5, G0 to G3, M, F) |
| Claim that all five signals were observed | none; at most four, coauthor unavailable (Sections 4, 5) |
| ORCID agreement as independent truth | none; stated as provisional throughout |
| Synthetic results as accuracy; smoke as main evaluation | none; explicitly separated (Section 5, Discussion, Conclusion) |
| Claim that human review occurred | none; stated as not performed and not simulated |
| Algorithmic novelty | none claimed |
| Statements not supported by code | spot-checked: authorship table unpopulated; failed initials fallback swallowed in the application; both stated in the manuscript |
| Reference claims | S2AND, WhoIsWho, CONNA, HUMO/r-HUMO supported; LAGOS-AND partly; four wording corrections made |
| Draft notes and placeholders | removed where resolvable. **Remaining by design:** the Abstract, the results tables (guarded placeholders), `\tbd` for m' and the audit size, and the author-order and e-mail confirmation comment (needs the four authors) |
| Compile, visual page check | **not done**: no TeX; the static checker passes (optional result tables are warnings) |
| Venue, publication, acceptance, copyright | none invented |

## 10. Deliverable paths
Manuscript `paper/HAMMER_IEEE_PAPER/` (zip `paper/HAMMER_IEEE_PAPER.zip`); references `paper/HAMMER_IEEE_PAPER/references.bib`, verification `REFERENCE_VERIFICATION.md`; figure and table generators `figures/make_figures.py`, `tools/make_result_tables.py`; freeze, pilot manifest and capture inputs `research_data/lagos_and_v2/eval_F2/`; tooling `backend/hammer_pilot/{freeze,guarded_transport,review_driver,report_assembly}.py` and `backend/scripts/{freeze_evaluation,assemble_c7_report,prepare_review_release}.py`; reports `docs/testing_validation/TEST_RESULTS/T014 to T018`; register `TESTING_MASTER_REGISTER.md`; instructions and dependencies `docs/research/paper_preparation/`. Outside the repository, never to be committed: `LAGOS_SOURCE/` (archive, catalogue) and `LAGOS_SOURCE/protected/` (identity map, gold register, pilot specs).
The Word white book (`whitebook/`) was **not** regenerated: it still says 550 tests and no freeze; regenerate it only after you have filled in your copy, or edit those two figures by hand.


## 11. Update after the instruction "do not spend money or use a key; complete the paper"
**What changed.** A keyless OpenAlex request is free (shared USD 0.10 daily quota), so a real exploratory capture was run without payment. It found and fixed two integration defects (T019), ended on HTTP 429 after **18 complete cases**, and was analysed together with the 50 smoke cases (benchmark-derived, exploratory). The manuscript is now complete in every section: the Abstract, Results (Section 6), Discussion and Conclusion were written from these observations; Sections 1, 5 and 8 were updated; the pending protocol results remain visible placeholders.
**Main findings (all benchmark-derived, exploratory; no verified result):** expected ORCID in the R2 pool for 38 of 50 (76%) and 13 of 18 (72%); provider first candidate agrees for 22 of 50 and 7 of 18; HAMMER top-1 under C1 agrees for 17 of 50 and 6 of 18; automatic assignments under C1 with the full policy 4 of 50 (3 agree) and 0 of 18, the same as without the safeguards; under C1x 7 of 50 and 3 of 18 with the safeguards against 26 and 8 without; binding gate conditions were margin and dominance (not score; median top score 0.88). Planning range for a verified phase at the observed coverage: about 435 to 950 primary cases for 32 automatic assignments.
**Still not done (cannot be done without people or access):** independent verification; the coverage pilot (needs about three free daily quotas or a free key); a confirmatory sample (new freeze id; exclude the 50 exploratory blocks); the LaTeX compile (no TeX installed).
**Evidence:** `TEST_RESULTS/T019_*`; tests 591 passed; freeze F4; failed attempts kept (F2 refusal, F3 70 decoding errors). The earlier statements in sections 1, 3 and 5 of this report that "no result exists" refer to verified results; benchmark-derived exploratory results now exist as stated above.

## 12. Compilation (T020)
Tectonic 0.17.0 was installed (with consent, scratch directory only) and the manuscript compiled to **22 pages with 0 undefined citations or references**. All pages were inspected; four defects were found and fixed (a table overlapping the right column, a math-mode placeholder printing as italic text, a cramped table header, and an inaccurate freeze-history sentence). The compiled proof is `paper/HAMMER_IEEE_PAPER.pdf`; the source zip `paper/HAMMER_IEEE_PAPER.zip` was rebuilt after the fixes. Limitation: tectonic has no bold Times shapes, so bold run-in headings print regular in the proof; Overleaf will render them bold. The compile section of this report supersedes the earlier statement that the paper was not compiled.
