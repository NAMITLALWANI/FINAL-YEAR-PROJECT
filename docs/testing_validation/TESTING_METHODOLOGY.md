# HAMMER testing methodology

A plain-language account of how HAMMER is tested, written so that a technical examiner can follow it without reading the code. Individual results are in `TESTING_MASTER_REGISTER.md` and `TEST_RESULTS/`.

## 1. What is tested
HAMMER retrieves candidate author profiles for a name, scores each with up to five evidence signals (name, institution, publication overlap, coauthors, temporal compatibility), and then decides: assign automatically, send to manual review, or leave unresolved. Provider failures, empty results and unscorable cases are separate outcomes. The tested components are:
- **Candidate retrieval and normalisation:** turning provider responses into candidate records, without inventing data.
- **Evidence scoring:** each signal is computed or marked unavailable, with a reason. Missing evidence is never treated as disagreement.
- **Decision policy:** thresholds and safeguards that decide automatic, manual or unresolved.
- **Evaluation toolkit:** capture of provider responses with hashes, offline replay, validation, and the metric code (`metrics.py`, and `metrics_c7.py` for Decision C7).
- **Benchmark preparation:** building cases from the LAGOS-AND dataset without passing benchmark labels to the system.

## 2. Kinds of test
| Kind | What it does | Why it is needed |
|---|---|---|
| **Unit tests** | Check one function on small inputs with hand-computed answers | Catch arithmetic and logic errors where the cause is easy to find |
| **Integration tests** | Run several components together (for example resolver plus database, API plus resolver) | Catch interface mistakes that unit tests cannot |
| **Replay tests** | Re-run the resolver on **saved** provider responses, offline | Test decisions without network variation or cost; the same input must give the same output |
| **Reproducibility tests** | Replay twice and compare every output byte for byte; verify stored response hashes | Show that results can be regenerated and that saved data has not changed |
| **Mutation sanity checks** | Deliberately break the code in a known way and confirm that a test fails | Show that the tests can actually detect the mistakes they claim to guard against |
| **Cross-checks** | Compare new code with independently produced artifacts or older code on real data | Guard against a misreading shared by code and tests |
| **Statistical-method validation** | Compare numerical routines with exact rational arithmetic, with an independent seeded simulation, and with published planning values; probe boundaries, extreme parameters and non-monotone behaviour | A statistical script can run without error and still be numerically wrong or silently choose the wrong answer; exact references expose both |
| **End-to-end rehearsal and Monte Carlo validation** | Run the whole pipeline on a synthetic world with a known hidden truth and compare every verified result with an independent computation; repeat the sampling design many times to check bias and coverage | Component tests cannot show that the pieces fit together or that estimators and intervals behave under repeated sampling |
| **Evaluation tests** | Run the protocol on benchmark or human-labelled data to measure performance | Not yet performed; the main evaluation has not started |

## 3. Synthetic data and benchmark data
- **Synthetic fixtures** are small cases built by hand so the correct answer is known with certainty (for example "four cases, one with rank 1, one with rank 3, one unmapped, one provider failure; end-to-end success@1 must be 1 of 4"). They test logic and denominators, not realism.
- **Smoke data** is a 50-case, 23-block capture from LAGOS-AND, used to check that the pipeline runs on real responses. It is not a probability sample, its cases within a block are not independent, and it carries no independently verified labels. It is never used to claim performance.
- **Benchmark experiments and human-reviewed labels** are the later stages. Benchmark ORCID agreement is provisional and potentially circular, so it is always reported separately from independently verified results.

## 4. How data leakage is checked
Leakage means the answer (the benchmark ORCID) reaching the system or a reviewer. Three layers are used:
1. **By construction:** the resolver source never references ORCID, and tests confirm that no ORCID or gold field reaches the query input.
2. **By search:** every prediction, evidence, seed, manifest, diagnostic and reviewer-facing artifact is searched for the exact gold ORCID values and for any ORCID-shaped string. Counts only are recorded, never the values. Raw provider responses legitimately contain ORCIDs and are excluded from reviewer packets by design.
3. **In the module under test:** the C7 module is checked to import no network library and read no ORCID field.
These checks find exact and pattern leaks. They do not detect indirect leakage (for example through names or affiliations).

## 5. How safeguards are validated
The decision policy refuses automatic assignment when evidence is weak: it needs a minimum score, a margin over the runner-up, at least two observed signals, a non-zero corroborating signal, no unscored competitor, no mismatched signal sets and no incomplete evidence. Validation uses (a) unit tests for each rule and its boundary; (b) a scripted check that every automatic assignment in saved replays satisfies each rule, using the stored evidence snapshots; (c) checks that each failure mode (provider failure, empty pool, no score, manual, unresolved) maps to its own outcome.

## 6. Testing results versus research performance
A passing test shows the **software does what its specification says**. It does not show that HAMMER resolves authors accurately. Accuracy claims need an independent sample, independent labels, and the C5 inference procedure, none of which exist yet. Each report therefore states what the result demonstrates and what it does not. Numbers produced by tool checks on smoke data are labelled "tool check" and are not quoted as results.

## 7. What counts as a passing test
- A unit or integration test passes if its assertions hold and it raises no unexpected error. A test is never edited to match a wrong output; when a test fails, the cause is investigated first, and any fix to a test fixture is recorded.
- A reproducibility test passes only if every output file is byte-identical. Differences in run metadata (for example git revision) are reported, not hidden.
- A capture-integrity test passes only if every stored response hash matches.
- A mutation check passes if every deliberate defect makes at least one test fail.
- A cross-check passes if the values agree exactly with the independent artifact.
- A leakage check passes if the count of gold values in prediction and reviewer-facing artifacts is zero.

## 8. Record keeping
Every activity gets a test ID, a report in `TEST_RESULTS/` (question, reason, expectation, environment, data, procedure, commands, expected versus actual, interpretation, limitations, artifacts, next steps), a row in the master register, and an entry in `VIVA_TESTING_SUMMARY.md`. Unedited outputs are kept in `RAW_OUTPUTS/<test>_<run>/` with SHA-256 hashes in `RAW_OUTPUTS/SHA256SUMS.txt`, separate from the generated reports. Reruns create new run folders. The software revision and dirty state are recorded with each run.


## 9. Addendum (20 November 2026): freezing, stop conditions and what counts as run
- **Freeze before capture.** `freeze_evaluation.py` writes a manifest of frozen-file hashes, the effective configuration, the adopted parameters and derived seeds; it refuses if any configuration override is present, and `verify` detects any later change. A change of the frozen set means a new freeze identifier and a new derived draw; the earlier freeze is kept and marked superseded (T015, F1 to F2).
- **Stop conditions are tested with mock transports** (T017): a stop must fire before the next request and the failing response must already be saved and hashed.
- **A step counts as "run" only if its real inputs were used.** Dry runs on the smoke capture in a scratch directory are labelled as such and define no study case.
- **Absent external inputs are recorded as dependencies, not simulated:** a missing provider credential or missing human reviewers leaves the affected result pending.
