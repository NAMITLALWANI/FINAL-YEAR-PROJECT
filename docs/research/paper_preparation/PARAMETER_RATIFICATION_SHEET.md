# Parameter ratification sheet (for the research director)

**Status:** recommendations only. **Nothing on this sheet is selected or frozen.** Each recommendation cites the evidence that supports it. The director marks Approve or Change and initials; only then may the freeze (runbook step 1) proceed. Evidence: T006 (sizing), T010 (simulation), T011 (real frame counts).

| # | Parameter | Recommended | Evidence and rationale | Approve / change |
|---|---|---|---|---|
| 1 | HAMMER weights and thresholds | keep the code defaults: weights 0.35, 0.25, 0.20, 0.10, 0.10; thresholds 0.75, 0.15, 1.35, 0.45, at least 2 signals | not tuned on LAGOS; no environment override set; hash the effective configuration at the freeze | |
| 2 | Split and frame | test split only, minus the 23 smoke blocks and the pilot blocks | T011 counts: S 8,038, M 8,360, L 1,173, XL 9 after the smoke exclusion | |
| 3 | XL stratum | floor 9 (census in the main sample); **no test-split XL pilot** (nothing would remain); XL uses the prior only in the sizing | XL has 9 test blocks (T011); train has 17 and validation 13, but a fallback adds a transfer assumption for at most 9 cases | |
| 4 | Floors | S 0, M 0, L 0, XL 9 | follows item 3 | |
| 5 | Pilot sizes (test split) | S 100, M 100, L 50, XL 0 (250 cases) | T010: pilots of 30 to 40 left the predictive rule about 2 points under target when the prior was mismatched; larger pilots narrow the posterior; 250 requests cost well under one dollar at the smoke unit cost | |
| 6 | Predictive and sensitivity priors | Jeffreys primary, uniform sensitivity | C9; both implemented (T006) | |
| 7 | beta | 0.05 (target probability 0.95) | T010: with beta 0.10 the realised success was 0.88 to 0.90 under a mismatched prior; beta 0.05 costs about 6 to 7% more cases (N 413 against 390 at m = 32, c = 0.10, T006) | |
| 8 | gamma | 0.10, Bonferroni over the 4 strata | C9; the lower-bound check was conservative (0.998) in T010 | |
| 9 | N_max | 2,500 | covers the largest planning case at 0.95 (m = 100, c = 0.05: 2,331, T006); far below the frame (17,580); reviewer capacity, not cost, will bind | |
| 10 | m and m' (target automatic assignments) | **open: set from reviewer capacity** (`reviewer_time_summary` after the B7 pilot) | reviewer burden grows with m (every automatic case is verified); zero-error 95% upper bounds on risk: 0.171 at 16, 0.089 at 32, 0.030 at 100 | |
| 11 | Audit size | **open: remainder of reviewer capacity** after the automatic verification | Decision A | |
| 12 | Bootstrap minimum stratum size | 20 non-census cases; otherwise no pooled bootstrap from that stratum | rule of thumb; pooled bootstrap covered 0.935 against 0.95 in T010 with 20 to 40 cases per stratum | |
| 13 | Negligible-weight rule | drop strata with frame weight below 0.005 from the pooled estimand, report them separately | affects only XL (0.05%); S, M, L are 45.7%, 47.6%, 6.7% | |
| 14 | Diagnostics | sampling fraction 0.10; sparse warnings 30 automatic and 5 errors; clustered warning 20 blocks | provisional warnings, not validity boundaries | |
| 15 | Seeds | derive each seed as the first 8 hex digits (as an integer) of SHA-256 of `HAMMER|<role>|<freeze id>` for pilot, main and audit | removes the choice of a favourable seed; auditable | |
| 16 | Group-paper cap K, works cap | K = 10; one page of 25 works per candidate, at most 10 candidates per case, allow-listed fields | Decision B; to be checked in the B7 pilot | |
| 17 | Provider request ceiling | 1.5 times the planned count: planned about 1.05 requests per case plus 7 works requests per reviewed case | smoke: 92 requests for 50 cases (shared queries) | |
| 18 | Cost ceiling | USD 10 for pilot, main and works captures; stop at 80% | smoke: USD 0.047 for 92 requests, about USD 0.5 per 1,000 requests, so about a 2x margin | |
| 19 | Stop conditions | existing: stop on HTTP 401, 403, 429, on budget exhaustion, no resume into a partial case; add: stop at 80% of the cost ceiling, after 3 consecutive 5xx or timeouts, or on a hash mismatch | `capture.py` already implements the first three | |
| 20 | Secondary cases | capture them for the exploratory clustered analysis only if budget remains after the primary captures | benchmark-derived, no verification cost | |
| 21 | Personnel | **deferred** (outside peers as reviewers, faculty adjudicator; attestations; hours) | director's ruling; the B7 pilot is the first step that needs them | |

**Director's initials and date:** ______________

**Update 20 November 2026.** Under the autonomous-execution instruction every recommendation above except items 10 and 11 (m, m', audit size) and 21 (personnel) was adopted in `PARAMETERS_ADOPTED_F2.json` and frozen in `HAMMER-EVAL-F2`. The director's initials are still needed to confirm; nothing has been captured, so any value can still change under a new freeze.
