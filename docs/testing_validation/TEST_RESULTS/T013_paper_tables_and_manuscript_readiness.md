# T013: result-table generator and readiness of the manuscript for the final protocol

**Test ID:** T013 (run 1) | **Date:** 20 November 2026 | **Type:** unit tests; mutation sanity check; static validation of proposed manuscript changes on a scratch copy | **Status:** PASS (10 tests; 8 of 8 mutants detected; proposed changes pass the static checks) | **The manuscript text was not changed.**

> T001 to T012 and all their raw outputs are preserved unchanged.

## 1. Question and reason
Every number in the Results section must be traceable to a frozen artifact. Can the tables be generated directly from a C7 report, and can the manuscript be updated to the final protocol without breaking its references, labels or the rule that no result is stated?

## 2. Expected behaviour
The generator renders tables only from a report; refuses final tables while any protocol parameter is unspecified (a `--draft` flag marks the output); shows a placeholder, not a rate, when verification is incomplete; prints a withheld interval with its reason and a computed interval exactly as in the report; keeps verified and benchmark-derived tables separate with their caveats; escapes LaTeX; and is deterministic. The proposed manuscript text (Section 5 final protocol, Section 6 scaffold with guarded `\IfFileExists` inputs, Section 8 limitations) uses only cited keys that exist in `references.bib`, defines every label it references, and states no result.

## 3. Environment
Python 3.12.5, pytest 8.4.2, git `6d31cbe`, dirty tree. SHA-256: `backend/hammer_pilot/paper_tables.py` `fbf02d3e8fbaa995b3b9102b2efd2d040567dbd2f31715c2a64ba9952996b7de`; `backend/tests/test_paper_tables.py` `d407fe979fc3c7fbdae7fa50582a4a9a6edda534fa9564512bd52a4d343677b8`; `paper/HAMMER_IEEE_PAPER/tools/make_result_tables.py` `58ba6ac0e975381839f1015065a29740671940f036d3d9805ded0b1755fca5a0`; proposed Section 5 tail `docs/research/paper_preparation/proposed/SECTION5_tail_final_protocol.tex` `2ac387dee06c8828d36073e4006443b8a5498158fc25026a8d1d92086e2a870b`; apply script `2ad0a9e095f631f32330892f3b51049fe50be1732cef7d4283b657080f341726`.

## 4. Data
A synthetic report built from hand-made cases (four strata, one a census). No real result exists.

## 5. Results
| Check | Expected | Actual |
|---|---|---|
| `test_paper_tables.py` | all pass | **10 passed**, 1.35 s |
| Refusal and draft marking | final tables refused with unspecified parameters; draft tables marked | as expected |
| LaTeX form | balanced environments, column counts, escaped underscores, no ORCID | as expected for all 7 tables |
| Traceability | table cells equal the report values | accounting totals, a retrieval cell and the pooled estimate, the audit counts and a pooled bootstrap interval match the report exactly |
| Caveats | not independently verified; not verified accuracy; never pooled; not a correction factor | present |
| Command-line script | writes new files only; refuses unspecified parameters | as expected |
| Mutants W1 to W8 | each detected | **8 of 8** (the first pass detected 7; a test of a printed pooled interval was added) |
| Proposed manuscript changes, applied to a scratch copy | static checks pass | **PASS**: the five new references resolve, labels are defined, braces balance; the guarded table inputs are reported as optional warnings after a one-line change to the checker |
| Current manuscript | static checks pass | PASS (unchanged text) |

## 6. What was and was not changed in `paper/`
Changed: `references.bib` (five verified statistical references, added on 20 November 2026 and logged in `REFERENCE_VERIFICATION.md`), the new tool `tools/make_result_tables.py`. A figure edit made during this work was reverted so that the figure and the current Section 5 text agree. **Not changed:** every `sections/*.tex` file and `main.tex`. A command that would have rewritten Section 5 was denied by the environment's permission check and was not retried by other means; the proposed text is instead in `docs/research/paper_preparation/proposed/` with a script that applies it only when run with `--apply` (it backs up the originals first).

## 7. Interpretation and limitations
The Results can be filled mechanically from a frozen report, and the manuscript can be moved to the final protocol in one reviewed step. Static checks are not a compile: LaTeX has not been run (no TeX installation, by instruction), so the user's single Overleaf upload is still the compile test. The table layout (cell format) has not been seen in a rendered page.

## 8. Artifacts
`RAW_OUTPUTS/T013_run1/`: `pytest_paper_tables_verbose.txt`, `pytest_full_suite.txt` (550 passed), `mutation_check_t013.txt`, `check_manuscript_current_manuscript.txt`, `scripts/`. Hashes: `RAW_OUTPUTS/SHA256SUMS.txt`.

## 9. Addendum (20 November 2026, after the user approved applying the changes)
The proposed changes were applied with `apply_proposed_manuscript_changes.py --paper-dir paper/HAMMER_IEEE_PAPER --apply`. `main.tex` gained the `\tbd` placeholder macro; `sections/05_experimental_design.tex` now follows the final protocol (Label Strategy and Verification, Blinded Review Procedure, Sampling Design, Coverage Pilot and Sample Size, Evaluation Metrics, Statistical Inference, Validation of the Evaluation Tooling, Affiliation Cleaning, Status of the Main Evaluation); `sections/06_results.tex` is a scaffold with guarded table inputs and states no result; `sections/08_threats_limitations.tex` holds the limitations. The pipeline figure was regenerated from the proposed script. Original files are in `paper/HAMMER_IEEE_PAPER/_backup_before_final_protocol/`. Static check after applying: PASS (optional table inputs are warnings until a frozen evaluation generates them). LaTeX has not been compiled. Sections 1 to 4, 7 and 9 and the Abstract are unchanged.
