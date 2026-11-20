# Viva testing summary

An examiner-friendly summary, updated as tests are completed. Last updated 20 November 2026 (T007 to T010 added). Details: `TESTING_MASTER_REGISTER.md` and `TEST_RESULTS/`.

**The one-sentence position.** The system is reproducible and its safeguards and metric arithmetic are tested, but **no accuracy or precision has been measured yet**: the independent labels and the probability sample that such a claim needs do not exist.

## T001: offline baseline
- **What did we test?** The existing test suites, the offline replay of a saved 50-case capture, reproducibility, the integrity of the saved provider responses, the safeguards of the decision policy, and whether benchmark ORCIDs leak.
- **Why?** Everything later rests on the system being reproducible and on the benchmark answer never reaching the system.
- **How?** Ran all 236 automated tests; replayed the capture twice and compared outputs byte for byte; checked 92 stored SHA-256 hashes; scripted checks of every automatic assignment against each policy rule; searched all artifacts for the 50 gold ORCIDs and for any ORCID pattern.
- **What did we observe?** 236 tests passed. Replay produced 450 predictions, 100 retrieval rows and 150 evidence snapshots, identical to the committed outputs. 92 of 92 hashes matched. The 40 requests of the preserved failed attempt all returned HTTP 401. There were no gold ORCIDs in predictions, evidence or seeds. All 11 automatic assignments satisfied the safeguards. The older metrics module disagreed with Decision C7.
- **What does it demonstrate?** The software runs, reproduces, and keeps benchmark labels out of its predictions; the safeguards held on the observed cases.
- **What does it NOT demonstrate?** Accuracy; behaviour on live providers; behaviour in the four outcome categories that never occurred in the smoke data (empty pool, provider failure, no score, unresolved; covered by unit tests only); absence of indirect leakage.
- **Likely follow-up.** *"Why did the byte count differ between two runs?"* The manifest lists every code file, and the second run happened after the new module existed, so it gained one line (+102 bytes). The data outputs were unchanged.

## T002: the C7 metrics module on synthetic cases
- **What?** The new module that computes the evaluation metrics and denominators defined in Decision C7.
- **Why?** The old module computed some quantities differently (for example it dropped uncertain cases from the coverage denominator and lacked end-to-end success@k). Wrong denominators would silently distort every reported rate.
- **How?** 49 unit tests on small hand-built cases with hand-computed answers, and a **mutation check**: six deliberate bugs were introduced one at a time to confirm that tests catch them.
- **Observed?** 49 of 49 passed; each of the six bugs made at least one test fail; the full suite then had 290 passed. Test failures during development were all fixture errors in the tests, and the module's behaviour was not changed to pass a test.
- **Demonstrates?** The code implements the written rules, including the key ones: an automatic assignment to an unresolved case, or to a case where no candidate is the right person, counts as **incorrect and stays in the denominator**; only uncertain and unverifiable cases leave it, and they appear in all-wrong and all-right brackets. Census strata get no interval; a zero-error result never gets a bootstrap interval.
- **Does NOT demonstrate?** That the rules themselves are the best possible; that intervals have nominal coverage in large samples; that an alternative reading of C7 is wrong. Five open ambiguities are listed for the director.
- **Likely follow-up.** *"Why count a wrong-candidate and a no-candidate case as errors?"* Because dropping them would inflate precision: the system still assigned a person when it should not have.

## T003: the C7 module against independent artifacts
- **What?** The same module on the real 50-case smoke capture.
- **Why?** Hand-built tests can share a misreading with the code. An independent script and the old metrics module cannot.
- **How?** Compared outcome counts, mapping rate, success@1/5/10, **the first-mapped rank of every case**, and precision and coverage numerators and denominators with the independent diagnostics script and the old module; applied the one-case-per-block rule to the real blocks; checked output is deterministic and ORCID-free.
- **Observed?** Exact agreement (for example mapping 38 of 50 and the rank of the expected profile equal in all 50 cases); 23 primary and 27 secondary cases under the one-per-block rule.
- **Demonstrates?** The arithmetic is consistent on real data and the module never writes an ORCID.
- **Does NOT demonstrate?** Performance. Smoke is 50 cases in 23 blocks, not independent, not a probability sample, without verified labels. ORCID agreement is a provisional label. The printed numbers are tool checks and **must not be quoted as results**.
- **Likely follow-up.** *"So what is HAMMER's precision?"* Not measured yet. The protocol requires a probability sample, independent blinded reviewers and the stratified inference of Decision C; those steps have not started.

## T004: the five director rulings in the C7 module
- **What did we test?** That the metrics module implements five rulings: how a label error in the audit is derived; that an automatic case the reviewers cannot verify stays "Uncertain"; that a case with no intended person (ground truth) is not confused with HAMMER declining to decide; that the name-only R2 pool is the primary pool; and that "no matching candidate" is claimed only after every candidate was judged.
- **Why?** Each rule decides what enters a numerator or a denominator. A reviewer can fairly ask why a case was counted or dropped.
- **How?** 36 new tests (one group per ruling) on hand-built cases; the 54 earlier tests re-run on the revised code; the full suite; and a mutation check with 11 deliberate bugs.
- **What did we observe?** All new tests passed; the earlier tests passed after fixture updates for one deliberate change (the manual error flag was replaced by derived reasons); the full suite had 326 passing; every one of the 11 bugs was detected.
- **What does it demonstrate?** An audit error is now computed from the adjudicated record (impure group, false mapping, missed mapping), each case counted once with reasons reported separately; an impure group is automatically an error, an unresolved group is not; "cannot tell" is never an error; HAMMER abstentions stay in retrieval evaluation, while only ground-truth unresolved cases leave it; "no matching candidate" needs every candidate judged.
- **What does it NOT demonstrate?** That these rules are the only reasonable ones, or that real reviewers' records will fit them; no human-reviewed data exists. The rules are the director's, and four new points are flagged for confirmation (T004 section 11).
- **Likely follow-up.** *"Why is a cannot-tell judgment not an error?"* Because it expresses lack of evidence, not disagreement; counting it either way would bias the rate, so it is bracketed (all-right, all-wrong) instead.

## T005: group validity versus case-level verification
- **What did we test?** That the metrics keep two questions apart: "is the benchmark's group really one person?" (Stage A) and "was the case's candidate verified?" (Stage B), and that nothing from the audit changes the overall retrieval numbers.
- **Why?** The benchmark asserts that each group's papers belong to one author. If a reviewer finds the group impure, that is a finding about the benchmark. But a case whose verification is uncertain must not enter the error rate as if it were definite, or the rate would mix facts with guesses.
- **How?** 16 new tests plus the 90 earlier C7 tests, the full suite, and a mutation check with 10 deliberate bugs. One test proves that the overall retrieval output is identical, byte for byte, with and without verified labels attached.
- **What did we observe?** All passed (full suite 342); every bug was detected. A pure group with an unresolved label is now "indeterminate", not "consistent"; an uncertain case with an impure group stays out of the definite error rate and is reported under group validity; conditional verified retrieval keeps its denominator (cases with a verified-same candidate) and reports every other category separately. This refines two definitions in T004.
- **What does it demonstrate?** The definitions are implemented as written, and the audit cannot adjust overall retrieval by construction.
- **What does it NOT demonstrate?** That real reviewers' records will fit these three purity states; no human-reviewed data exists. Three points await the director (T005 section 11).
- **Likely follow-up.** *"Why is an impure group in an uncertain case not counted as an error?"* Because the error rate is defined on definite labels. The impurity is not hidden: it is reported separately, and it enters the all-wrong end of the bracket.

## T006: the sample-size (sizing) script
- **What did we test?** A script that works out how many cases the main evaluation must draw so that, with a stated probability, it obtains at least *m′* automatic assignments, given a pilot's observed automatic rate in each of the four block-size strata.
- **Why?** The number of automatic assignments determines how precisely precision can be estimated, and it is random. A rule such as N = m/c only reaches *m* about half the time (0.52 to 0.54 in our checks). The script instead uses the full predictive distribution, including uncertainty about each stratum's rate.
- **How?** Four independent checks: exact rational (fraction) arithmetic for the distributions; a seeded Monte Carlo simulation of the same model; regression to the planning values published in the design (for example N = 390 and N = 413 for m = 32, c = 0.10), each confirmed exactly; and a mutation check with 15 deliberate bugs. Special fixtures cover whole strata taken as censuses, strata with no pilot data, floors and rounding.
- **What did we observe?** 86 tests passed (full suite 428); the design's planning values were reproduced exactly; the exact and simulated probabilities agree; a finite pilot gives a larger N than the pooled shortcut, and a huge pilot converges to it. A real numerical error in my first version (large pilots) was caught by the built-in normalisation check and fixed.
- **What does it demonstrate?** The script implements the written procedure correctly, including the rule that the probability condition must hold for every larger N up to N_max. That rule matters: in a test case, rounding of the allocation made the probability fall when N grew from 32 to 33, and a naive "first N that works" would have returned 31 instead of 34.
- **What does it NOT demonstrate?** That the design's assumptions hold for HAMMER's real coverage; any value of *m′*, β, γ, N_max, floors or pilot size (none is chosen); anything about the real sample. It was run on synthetic inputs only.
- **Likely follow-up.** *"What sample size do you need?"* Not decided: it depends on reviewer capacity, which sets the target number of automatic assignments, and on a pilot that has not been run. The script is ready to compute it once those inputs are approved.

## T007 to T010: the evaluation tooling and the rehearsal
- **What did we test?** The programs that will run the main evaluation: the selector that draws the pilot, main and audit samples; the builder of blinded reviewer packets and its leak scanner; the review-record layer (two reviewers, adjudicator, agreement) that converts labels into the evaluation metrics; and a full rehearsal on a synthetic world where the truth is known.
- **Why?** A sampling or blinding mistake cannot be fixed after the study. Testing on synthetic data with a known answer lets us find such mistakes before any real data, money or reviewer time is spent.
- **How?** Unit tests with hand-computed answers; mutation checks (deliberate bugs, 12, 12 and 11 respectively, all detected); a uniformity check over 1,500 seeds; an in-memory test showing that the real captured payloads contain the benchmark ORCID but the packets built from them never do; and a rehearsal whose verified precision and audit error rate were compared with independent calculations from the hidden truth (exact match). A Monte Carlo study repeated the sampling design hundreds of times to check estimators, intervals and the sample-size rule.
- **What did we observe?** Everything matched. The person-level estimator needs the group-count weights (ignoring them biased the estimate by about 20 standard errors). Per-stratum exact intervals were conservative (0.96 to 0.97 coverage); the pooled bootstrap covered 0.935 against 0.95 nominal. The predictive sample-size rule reached its 0.90 target when its model matched (0.899) but only 0.88 when the real coverage distribution differed and the pilot was small; the shortcut N = m/c reached 0.55 to 0.68.
- **What does it demonstrate?** The pipeline is wired correctly, the blinding controls work against the real payload shape, and the statistical procedures behave as designed, with known limits.
- **What does it NOT demonstrate?** Anything about HAMMER's real performance: all data are synthetic, the real frame is unknown, no real pilot, capture or human label exists.
- **Likely follow-up.** *"Why trust a simulation you wrote?"* Because the checks use independent references (exact fraction arithmetic, a known hidden truth, a different sampling code path) and negative controls (wrong weights, deny-list leakage, corrupted crosswalk) that must fail, and mutation checks show the tests can detect real mistakes. What it cannot show is whether the simulated world resembles the real one; the real data will answer that.

## T014 to T018: getting ready to run the evaluation
- **What did we test?** Five preparation steps: a full scan of the dataset's year range; a freeze manifest that records the code, settings and seeds before any capture, plus the draw of the coverage-pilot sample; the program that turns a replay into the final metrics report; extra emergency-stop rules for provider capture and the program that prepares blinded reviewer packets; and a claim-by-claim check of five key references.
- **Why?** A reviewer will ask whether any setting could have been adjusted after seeing results. The freeze makes that detectable, and the seeds are derived by a fixed rule, so nobody chooses a favourable one.
- **How?** Unit tests with fake data and fake network transports; deliberate-bug (mutation) checks (19 of 19 caught, after three tests were strengthened); a dry run on the smoke data that built 16 packets and found no leak; reading the source papers.
- **What did we observe?** The year range 1870 to 2022 is right (an earlier note covered only a slice of the file). The pilot of 250 whole blocks was drawn and its inputs contain no benchmark ORCID. The full test suite has 585 passing tests.
- **What does it demonstrate?** The remaining steps are mechanical and safe to run once a provider credential and reviewers exist.
- **What does it NOT demonstrate?** Any performance of HAMMER. **The pilot capture was not run: there is no OpenAlex API key in the environment.** No reviewer exists, so there is no verified label.
- **Likely follow-up.** *"Why is there no accuracy result?"* Because the evaluation needs two things only the team can provide, a credential for the provider and independent human reviewers; the paper says so and reports no number it cannot support.

## T019: what we could run for free, and what it showed
- **What did we test?** With no money and no API key, we ran the pipeline on 18 new real queries using the provider's free tier (it stopped when the free daily quota ran out), and analysed those together with the 50 smoke queries.
- **Why?** To get as much real evidence as possible without payment or human reviewers, and to see whether the pipeline survives real use.
- **How?** A guarded capture, an offline replay (reproduced byte for byte), hash checks, a leak check, and a benchmark-derived analysis with exact intervals.
- **What did we observe?** (1) The first real runs exposed two bugs our synthetic tests had missed; both are fixed with regression tests and the failed runs are kept. (2) The expected profile was in the candidate pool for about three quarters of queries. (3) Automatic assignment was rare (4 of 50 and 0 of 18) because the best candidate's score was rarely far above its same-name competitors. (4) HAMMER's own ordering agreed with the benchmark label no more often than the provider's order.
- **What does it demonstrate?** Where the present design is limited, and that the pipeline works on real data.
- **What does it NOT demonstrate?** Accuracy. The label is a provisional ORCID match, nothing is independently verified, and 18 to 68 cases is far too few for any claim about the system.
- **Likely follow-up.** *"Why does your paper report numbers if nothing is verified?"* Because they are labelled as benchmark-derived observations that point to hypotheses; the verified evaluation is specified, tooled and costed (about 435 to 950 primary cases for 32 automatic assignments) but needs reviewers.

## What has not been tested (say so plainly)
Live provider behaviour beyond the 92 saved responses; the coverage pilot; the reviewer-time pilot; the sample selector (the sizing script is tested on synthetic inputs only); the dossier builder and leak scan; any human-verified label; any benchmark experiment; the main evaluation.
