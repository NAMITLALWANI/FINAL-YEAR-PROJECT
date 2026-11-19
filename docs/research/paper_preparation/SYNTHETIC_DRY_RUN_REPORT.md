# Synthetic end-to-end dry run of the pilot toolkit

**Scope:** engineering verification of `backend/hammer_pilot/` on **fabricated** data. No real people, no real annotations, no provider call. Nothing here is a research result; the numbers below describe the synthetic fixtures only and must not be quoted as HAMMER performance.  
**Baseline:** `main` at `bee7eab` plus uncommitted work; nothing committed or staged.

## 1. Synthetic dataset composition
15 fabricated cases (`build_synthetic_pilot` in `backend/tests/pilot_fixtures.py`), generated into a temporary directory outside the repository. 10 planned and final resolved, 5 unresolved; fabricated names, institutions, DOIs (`10.9999/...`) and OpenAlex-like identifiers.

| Situation required | Case(s) |
|---|---|
| Multiple candidate profiles for one resolved identity (fragments) | P02 (two profiles, both mapped to the same person), P03 (true profile plus a different person) |
| Empty result | P04 (resolved), P13 (unresolved) |
| Provider failure | P05 (HTTP 500) |
| Partial enrichment | P06 (coauthor works lookup fails for the only candidate) |
| DOI-disjoint case | P07 (gold DOI and query-context DOI differ; query-context DOI resolves to the candidate) |
| `both` DOI case | P08 (justified `both` DOI; excluded from primary C1, present in C1x) |
| No eligible coauthor IDs | P09 (coauthor supplied by name only) |
| Policy abstains | P02, P09, P11, P15 (manual review) and P14 (unresolved) |
| Policy assigns automatically | P01, P03, P07, P08; also P10 (wrong person, incorrect) and P12 (false acceptance on an unresolved control) |
| R0 and R2 differ | P02 (double-space query: R0 raw query returns nothing, R2 normalised query finds the profiles) |
| Reviewer disagreement and adjudication | P14 (A: unresolved, B: uncertain, adjudicated unresolved) |

Candidate capture was produced **in-process through a mocked transport** (the capture CLI deliberately refuses to run without `--allow-network`, so it was not used).

## 2. Commands executed (from `backend/`)
```
./.venv/bin/python scripts/validate_hammer_pilot.py --pilot-dir <tmp>/pilot
./.venv/bin/python scripts/replay_hammer_pilot.py --pilot-dir <tmp>/pilot --out-dir <tmp>/out
./.venv/bin/python scripts/verify_hammer_pilot_reproducibility.py --pilot-dir <tmp>/pilot --work-dir <tmp>/repro
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest tests -q -p no:cacheprovider
node --test frontend/src/features/author_resolution/contextModel.test.js
```

## 3. Validation result
`valid: true`, no errors. Info: final composition 10 resolved / 5 unresolved / 0 uncertain. One expected warning: P08's seed DOI overlaps gold evidence (`both`); the derived primary C1 excludes it, the seed and register were left unchanged. The validator was confirmed not to modify any input file (hash comparison test).

## 4. Policy-by-policy outcome counts (synthetic, 15 eligible cases each)

| Condition / policy | auto | manual | unresolved | no_score | provider_failed | empty_pool |
|---|---:|---:|---:|---:|---:|---:|
| C0 `forced_top1` (name-only) | 12 | 0 | 0 | 0 | 1 | 2 |
| C0 `selective_policy_v2` | **0** | 11 | 1 | 0 | 1 | 2 |
| C1 `forced_top1` | 12 | 0 | 0 | 0 | 1 | 2 |
| C1 `legacy_gates_plus_p3` | 7 | 4 | 1 | 0 | 1 | 2 |
| C1 `selective_policy_v2` | 6 | 5 | 1 | 0 | 1 | 2 |
| C1x `selective_policy_v2` | 6 | 5 | 1 | 0 | 1 | 2 |

- C0 automatic coverage is **0 by design** (labelled `automatic_coverage_zero_by_design` and "BY DESIGN" in `metrics.json`); it is not a safety result.
- C1 `selective_policy_v2`: automatic precision 4/6, incorrect automatic 2 (one wrong person, one false acceptance on an unresolved control). Legacy auto precision 5/7. The synthetic data were built to exercise these paths; the values mean nothing about real performance.
- Retrieval (synthetic): catalog coverage 7/10; R2 Recall@1 7/7, R0 6/7; paired comparison: 1 R2-only hit (P02) among 7.
- Provider failure, empty pool, no-score, manual and unresolved stay separate columns throughout.

## 5. Per-gate policy checks (Task 2)
Each P4-P8 safeguard has a fixture in which that gate alone withholds `selective_policy_v2` (manual) while `legacy_gates_plus_p3` assigns automatically:
P4 unscored competitor (unit), P5 name + temporal only, P6 observed 0.0 signal, P7 incomparable signal sets, P8 failed enrichment. P0 (null score), P1 (two signals), P2 (margin and dominance, including a case where margin passes and dominance fails), P9 and P10 boundaries hold identically in both selective policies. P3 is shown to relax only margin and dominance for a single candidate (a single candidate with one signal, with a score below 0.75, or with a close competitor is not assigned).

**Not reconstructable from a replay snapshot:** P4. A captured response cannot produce an unscored competitor, because the parser drops profiles without a display name and every parsed candidate has a name score. P4 is verified only at the policy-function level. `legacy_gates_plus_p3` is derived from the policy-v2 outcome's threshold-gate result (P0-P3, P9, P10); this is exact for those rules, but it is not an independent implementation.

## 6. DOI leakage results (Tasks 1 and 4)
- A gold-evidence DOI placed in a primary C1 seed is removed from the derived C1, listed as an overlap warning, and preserved in the seed and register (seed bytes unchanged).
- A `both` DOI is absent from C1 and present in C1x: P08 publication overlap is `unavailable_query_input_absent` in C1 and `observed` in C1x.
- A disjoint query-context DOI (P07) is eligible: publication overlap is `observed` in C1.
- A `both` DOI without justification is an error; a C1 seed DOI missing from the register is an error; a DOI shared across cases is an error.

## 7. Shared R0/R2 response provenance (Task 3)
- When the R0 and R2 primary requests are identical (14 of 15 cases here; 9 of the 10 resolved cases), the request is issued once, stored as one body file, and both logical records in `run_manifest.json` carry the same `body_file`, `seq` and `sha256` plus `shares_response_with`.
- Logical requests: 30; physical responses: 16; one body file per physical response.
- `retrieval.csv` flags `shares_response_with_other_arm`; `metrics.json` reports the shared-case count and counts the paired comparison on independent cases only (1 independent, 9 shared among the 10 resolved cases). The shared response is documented as one observation, not two.
- P02, where R0 and R2 issued different requests, has two distinct responses.

## 8. Reproducibility (Task 5)
`identical: true`; all five artifacts (`predictions.csv`, `retrieval.csv`, `evidence_snapshot.jsonl`, `metrics.json`, `run_manifest.json`; about 155 kB) byte-identical across two replays with the **fixed run ID `reproducibility-check`** present in every row and in both manifests. Outside the comparison, the default run ID is derived deterministically from the frozen inputs. The manifest hashes eight `author_resolution/*.py` implementation files (scoring, evidence, context, enrichment, enrichment types, policy, resolver, candidates) plus the other module files, `config.py`, and the evaluator sources. Every rate carries a numerator and denominator (asserted recursively); `metrics.json` also lists the hashes of the frozen inputs and derived tables it was computed from.

## 9. Validator hardening (Task 4)
Added and tested: cross-case duplicate DOIs; mandatory `development_exclusions.csv`; two separate review files with distinct reviewer IDs; adjudicator distinct from both reviewers on a disagreement; reviewer submissions barred from containing rank/score/decision columns, HAMMER-output wording, or captured candidate IDs; Stage A submissions must precede candidate capture and Stage B must follow it; one gold person cannot be assigned to two cases; `both` DOI justification and C1x-only treatment; missing review files are reported, not crashed on.

## 10. Remaining limitations
- **Workflow ordering (for director review):** the DOI register carries reviewers' gold DOIs, and the freeze hashes the register, so the freeze is validated as occurring after Stage A and before capture. The protocol text lists seed freeze before Stage A. Context in the seeds is still frozen before any candidate is seen; the clarification should be recorded in the protocol.
- Only mocked transports were exercised; the real HTTP capture path (`httpx.AsyncHTTPTransport`) is unrun in this repository, and the live Stage 1C check covered a single author.
- A budget stop in mid-case blocks resume by design.
- Reviewer independence is checked structurally (distinct IDs, separate files, blind content), not behaviourally.
- The old 100-query scripts are untouched and still unsuitable for this pilot.

## 11. Files
**Created (untracked):** `backend/tests/test_hammer_pilot_dry_run.py` (28 tests), this report.  
**Modified (the previously untracked toolkit and tests):** `backend/hammer_pilot/{capture,replay,manifest,pipeline,metrics,validation,reproducibility}.py`; `backend/tests/pilot_fixtures.py` (synthetic builder, review/Stage B writers); `backend/tests/test_hammer_pilot_metrics_validation.py` (updated to the review-file schema).  
No tracked application file was modified.

## 12. Test results
Pilot toolkit tests (4 files): 66 passed. Full backend suite: **219 passed**, 0 failed. JS tests: 8 passed. Not run: `backend/test_scraper_local.py` (unrelated stray file) and the frontend build (frontend untouched).

## 13. Safety confirmation
No provider call (all transports mocked; a test patches the real HTTP transport to fail during replay). Database hash prefix `3659ab2867e43b47` and the combined `vector_index`/`chroma_db` digest are unchanged; the tracked `git diff` hash is identical to its pre-task value; nothing staged or committed. The dry run's temporary data live outside the repository.

## 14. Verdict
**Ready for director approval of the toolkit** as engineering infrastructure for a **synthetic dry run**, subject to the workflow-ordering clarification in section 10. It is **not** a verdict that a live pilot capture works: the real transport path remains unrun, and no real seeds, annotations or API key exist yet.
