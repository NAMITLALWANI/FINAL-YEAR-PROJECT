# What remains, who must do it, and the exact commands

**As of 20 November 2026.** Everything below is the work that cannot be done by software alone. Nothing here has been done, simulated or assumed.

## A. Needs you (credentials and decisions)
| # | Action | Why it blocks | Exact step |
|---|---|---|---|
| 1 | Provide an OpenAlex API key in **your own shell** (never in chat or in a file in the repository) | every provider capture returns HTTP 401 without it (the failed first attempt proved this) | `export OPENALEX_API_KEY=...` and, if you want a different address, `export OPENALEX_MAILTO=<non-personal address>` before running the commands in section B |
| 2 | Confirm or change `PARAMETERS_ADOPTED_F4.json` | values were adopted from the ratification sheet under the 20 Nov instruction; capture has not started, so any change is still free (write a new freeze id) | edit nothing in place; ask for a new freeze |
| 3 | Decide a **cost ceiling** for provider spending | the pilot is estimated at about 470 requests and USD 0.5 from the smoke unit cost; the adopted ceiling is USD 10 (stop at 80%) | confirm or change |

## B. Commands that are ready (run from `backend/`; they refuse to overwrite)
```bash
# 0. build the pilot capture inputs from the F4 pilot manifest (needs the protected identity map in LAGOS_SOURCE/protected/pilot_F4)
.venv/bin/python scripts/run_helpers.py seeds --manifest ../../LAGOS_SOURCE/protected/pilot_F4/manifest.json --identity-map ../../LAGOS_SOURCE/protected/pilot_F4/identity_map.json --catalog ../../LAGOS_SOURCE/block_catalog_PROTECTED.json --archive ../../LAGOS_SOURCE/LAGOS-AND-BLOCK-TRIMMED.csv.tar.gz --capture-dir ../research_data/lagos_and_v2/eval_F4/pilot/capture --protected-dir ../../LAGOS_SOURCE/protected/pilot_F4/gold --include-secondary no
# 1. verify nothing frozen has changed
.venv/bin/python scripts/freeze_evaluation.py verify --freeze ../research_data/lagos_and_v2/eval_F4/freeze_F2.json
# 2. pilot capture (about 470 requests; stops on 401, 403, 429, budget, 3 consecutive 5xx or 80% of the cost ceiling)
.venv/bin/python scripts/capture_hammer_pilot.py --pilot-dir ../research_data/lagos_and_v2/eval_F4/pilot/capture --budget 720 --cost-ceiling-usd 10 --allow-network
# 3. offline replay of the pilot and the per-stratum automatic counts
.venv/bin/python scripts/replay_hammer_pilot.py --pilot-dir ../research_data/lagos_and_v2/eval_F4/pilot/capture --out-dir ../research_data/lagos_and_v2/eval_F4/pilot/replay
.venv/bin/python scripts/run_helpers.py pilot-counts --predictions ../research_data/lagos_and_v2/eval_F4/pilot/replay/predictions.csv --seeds ../research_data/lagos_and_v2/eval_F4/pilot/capture/seeds.csv --condition C1 --policy selective_policy_v2 --out ../research_data/lagos_and_v2/eval_F4/pilot/pilot_counts.json
```
Then (after the reviewer-time pilot sets m'): `size_hammer_main_sample.py`, `build_selection_manifest.py` (main), `run_helpers.py seeds`, main capture and replay, freeze the predictions, `run_helpers.py audit-frame`, the audit draw, `capture_works` and `prepare_review_release.py` (built in T017), and finally `assemble_c7_report.py` and `make_result_tables.py` (see `EXECUTION_RUNBOOK.md`).

## C. Needs people (deferred by the director; not simulated)
| Role | Count | What they do | Needed before |
|---|---|---|---|
| Independent reviewers | at least 2 (outside the project team) | Stage A and Stage B judgments from released packets (`REVIEWER_INSTRUCTIONS.md`) | any verified result |
| Adjudicator | 1 (neither reviewer nor packet builder) | resolves disagreements | any verified result |
| Packet builder | 1 (may be a project member who is not a reviewer or the adjudicator) | runs `prepare_review_release.py`, holds the protected directory | releasing packets |
| Reviewer-time pilot | about 6 smoke cases | measures minutes per case; sets the audit size and m' | the main sample size |

Until these exist, the verified-results sections of the paper stay pending. This is intended, not a gap in the software.

## D. Tooling for a LaTeX compile
No TeX distribution is installed and none was installed without your consent. Either upload `paper/HAMMER_IEEE_PAPER.zip` to Overleaf (the original plan), or tell me to install a TeX engine locally (for example the `tectonic` binary) and I will compile and check the PDF page by page.


## E. Update after the no-spend instruction (20 November 2026)
The user ruled out any payment or API key. A keyless request works on OpenAlex's free tier (USD 0.10 per day shared per network address, about 100 cases per day at the smoke unit cost, and the quota is shared with other users of the same address). The pilot of 250 cases would take about three daily quotas and cannot be resumed after an HTTP 429 (the capture refuses to mix a partial case), so it needs either a free key (USD 1 per day, no payment) or a fresh capture directory per day. The 18-case exploratory capture used today's quota (T019). Nothing else here changed: reviewers, adjudicator and the director's confirmation are still outstanding, and a confirmatory sample needs a new freeze id and must exclude the 50 exploratory blocks.
