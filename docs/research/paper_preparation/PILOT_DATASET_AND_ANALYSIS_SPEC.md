# Pilot dataset and analysis specification

**Status:** Revised (Stage 2.1) after the research-director decisions recorded in `PROTOCOL_FREEZE_RECOMMENDATION.md`, which governs where they conflict. It creates no data, no directories and no notebook environment. **Tooling caveat:** the existing capture, replay and validation scripts do **not** currently support this pilot (see `PILOT_TOOLING_COMPATIBILITY_AUDIT.md`); the schemas below are the target, not a description of what the scripts accept.  
**Reuse first:** existing templates in `docs/evaluation/templates/` (`identity_query_seed.csv`, `identity_evidence_packet.csv`, `identity_review.csv`, `identity_adjudication.csv`, `identity_labels.csv`, `frozen_candidate_manifest.csv`, `resolver_predictions.csv`, `split_manifest.csv`, `split_freeze.json`, `dataset_manifest.template.json`) and scripts in `backend/scripts/` (`prepare_identity_review.py`, `merge_identity_reviews.py`, `validate_evaluation_dataset.py`, `freeze_split_manifest.py`, `seal_evaluation_manifest.py`, `replay_frozen_resolver.py`). Whether they accept the new context/enrichment fields was **not verified**; Codex checks before reuse. New columns below are additive.

## 1. Pilot scope
15 cases: 10 resolved, 5 unresolved controls. Purpose: workflow feasibility, evidence availability, rubric clarity, reviewer agreement, pool sizes, mapping effort and workload. Results are descriptive; no accuracy claim, pass criterion, coverage floor or minimum automatic count.

## 2. Schemas (CSV unless stated; every file carries `dataset_version`)

### 2.1 Pilot case seed (`identity_query_seed.csv`; hidden from system output and from reviewers' view of HAMMER)
`case_id` (opaque, e.g. P001) · `query_text` · `identity_group_id` · `context_c0_json` (always `{}`: name-only) · `context_c1_json` (primary C1 context: institution text, optional institution OpenAlex ID/ROR, optional active years, optional OpenAlex coauthor IDs, and `query_context` DOIs **only** where section 6.1 of the protocol allows) · `context_c1x_json` (exploratory variant including DOIs whose disjointness from gold evidence is not established, else empty) · `selection_reason` · `frame_ref` · `selected_on` · `selected_by` · `seed_frozen_at` · `seed_sha256`. No predictions, candidate IDs, scores or HAMMER output. **Frozen before any candidate generation; never edited afterwards** (a change is a new dataset version, recorded in `context_modified_after_candidates_seen`, which must be `false`).

### 2.1a DOI register (`doi_register.csv`)
`case_id` · `doi` (normalised) · `purpose` (`gold_evidence` | `query_context` | `both`) · `registered_by` (frame_preparer | reviewer_A | reviewer_B) · `source_independent_of_openalex` (true|false) · `justification_if_both` (required when `both`) · `registered_at`. Derived per case after Stage A: `gold_query_doi_overlap` (list), `publication_overlap_primary` (true only if the overlap is empty or justified), otherwise the case's publication-overlap results are exploratory (`C1x`) and excluded from the primary pilot interpretation. The derivation uses labels and the register only, never HAMMER output.

### 2.2 Stage A annotation (`identity_review.csv`, one row per reviewer per case)
`case_id` · `reviewer_id` · `status` (resolved|unresolved|uncertain) · `confidence` (1-5) · `rationale` · `person_level_source` (URL/ID) · `publication_dois` (list, ≥2 if resolved; each also entered in the DOI register as `gold_evidence`) · `searches_performed` (for unresolved: sources and queries checked) · `evidence_refs` · `capture_dates` · `minutes_spent` (optional workload measure).

### 2.3 Adjudication and labels
`identity_adjudication.csv`: `case_id` · `adjudicator_id` · `final_status` · `adjudication_status` (agreed|adjudicated|uncertain) · `rationale`. `identity_labels.csv` (final): `case_id` · `final_status` · `gold_person_id` (opaque local ID; ORCID only as evidence) · `identity_group_id` · `evidence_summary`.

### 2.4 Candidate capture (one row per query × arm; raw bodies stored as files)
`run_id` · `case_id` · `arm` (R0|R2) · `request_endpoint` · `request_params` (no secrets) · `primary_status` · `fallback_status` (R2 only) · `http_status` · `captured_at_utc` · `raw_response_path` · `raw_response_sha256` · `ordered_candidate_ids` (provider order) · `pool_size`.

### 2.5 Stage B mapping (blind to rank, score and decision)
`case_id` · `candidate_source_author_id` · `reviewer_id` · `judgment` (same|not_same|cannot_tell) · `evidence_refs` · then adjudicated `final_judgment`. Derived: `mapped_profiles` per case, `catalog_covered` (≥1 mapped profile).

### 2.6 Enrichment capture (only for cases whose context contains DOIs or coauthor IDs)
`run_id` · `case_id` · `kind` (query_works|author_works_p1|author_works_p2) · `candidate_source_author_id` (for author works) · `request_endpoint` · `request_params` (sort, per-page, page, select) · `http_status` · `captured_at_utc` · `raw_response_path` · `raw_response_sha256`.

### 2.7 Prediction and evidence snapshot (one row per case × context condition × policy)
`run_id` · `case_id` · `condition` (C0|C1|C1x_exploratory) · `policy` (`forced_top1` | `selective_policy_v2` | `legacy_gates_plus_p3`; `forced_top1` in C0 is name-only) · `outcome` (auto|manual|unresolved|no_score|provider_failed|empty_pool; five distinct categories plus auto, never merged) · `selected_candidate_id` · `top_score` · `second_score` · `margin` · `dominance` · `threshold_gates_passed` · `auto_blockers` (list) · `top_signal_set` · `candidate_signal_sets` (JSON) · `per_candidate_evidence` (JSON: signal, status, score, effective weight, provenance reference) · `reason`. One snapshot row set per frozen run; never overwritten.

### 2.8 Run manifest (`run_manifest.json`)
`run_id` · `created_at_utc` · `git_sha` · `working_tree_clean` · `python_version` · `package_versions` · `effective_thresholds` and `weights` (read from configuration; no values echoed from the environment beyond these) · `policy_version` · `enrichment_bounds` (page size, max pages, sort) · input file hashes (seed, labels, mapping, split) · capture file hashes · `known_deviations`.

## 3. Inclusion and exclusion rules
- **Include:** one case per underlying person; a person-level and two DOI-level evidence sources accessible without restricted material (resolved); a documented ambiguous query with two documented search passes (unresolved).
- **Exclude:** anyone in V3, Day 5, the October deck or `pilot_predictions.json`; aliases/variants of an included person; cases whose truth would depend on an OpenAlex profile or a HAMMER output; private individuals and minors; cases with a shared decisive DOI with another case (keep one).
- **Uncertain cases:** stay in the dataset, are counted, and are excluded from primary rates. Whether an uncertain control may be replaced is an owner decision (open).

## 4. Pilot workflow
1. **Freeze protocol:** approve `PROTOCOL_FREEZE_RECOMMENDATION.md`; commit the implementation baseline (owner action); record SHA.
2. **Frame and seeds:** prepare the sampling frame and case seeds (C0/C1/C1x contexts, DOI purposes) with no HAMMER output visible; hash and freeze seeds **before any candidate generation**.
3. **Stage A:** reviewers A and B (roles; people assigned before Stage A) work independently and register gold DOIs; adjudicate; compute the DOI overlap flag from labels and the register; freeze labels and hashes.
4. **Capture:** run the R0 and R2 request captures once (and enrichment captures for C1 cases that need them) with a configured API key; save and validate each raw response before the next request; seal hashes.
5. **Stage B:** blind candidate-to-gold mapping; adjudicate; freeze.
6. **Offline replay:** an evaluator script computes policy outcomes from captured files only (no network, no database writes) for each condition and policy; writes the snapshot tables.
7. **Metrics and report:** regenerate all tables and figures by script; produce a descriptive pilot report: counts, denominators, exact intervals, agreement, adjudication rate, workload, pool sizes, signal-set composition, availability rates.
8. **Decision:** the director reviews workflow results and sets the main-study design.

## 5. Main-study separation
New sampling frame and dataset version; identity-disjoint from the pilot and from development material; thresholds, policy and code SHA frozen before capture; test labels sealed until one final unsealing; any test-informed change forces a new version and a new test. Pilot cases are never reused in the confirmatory test set.

## 6. Repository and analysis layout (proposed; not created)

```
research_data/pilot_v1/                      # frozen inputs and captures (large or restricted files stay out of Git)
  manifest/            dataset_manifest.json, run_manifest.json, hashes.txt
  seeds/               identity_query_seed.csv
  annotation/          identity_review_A.csv, identity_review_B.csv, identity_adjudication.csv, identity_labels.csv,
                       stage_b_mapping.csv, stage_b_adjudication.csv
  captures/            candidates/{R0,R2}/<case_id>.json (+ .meta.json), enrichment/<case_id>_*.json
  snapshots/           predictions.csv, evidence_snapshot.jsonl
analysis/
  src/                 hammer_eval/ (metrics.py, replay.py, io.py, intervals.py): pure functions, unit-tested
  scripts/             run_replay.py, make_tables.py, make_figures.py   # the only path to final outputs
  notebooks/           exploration only (JupyterLab); never the source of a reported number
  tables/              generated CSV/LaTeX tables
  figures/             generated vector figures (PDF/SVG) + source CSV
  reports/             pilot_report.md (generated), reproducibility notes
```
Rules: final numbers, tables and figures are produced by `analysis/scripts` from frozen `research_data` and verified by re-running; notebooks may read the same frozen files but are not cited as sources; no dashboard. JupyterLab is installed in a **separate** analysis environment, not in the application's `backend/.venv`; this task did not create it. Intervals use exact binomial methods implemented in `intervals.py` with unit tests. Sensitive evidence captures follow the existing rule: restricted material stays out of Git.

## 7. Expected outputs
| ID | Output | Source | Notes |
|---|---|---|---|
| T-P1 | Case composition and exclusions | seeds, labels | Counts per status, uncertain count |
| T-P2 | Annotation workflow | review files | Agreement, adjudication rate, minutes per case, evidence availability |
| T-P3 | Candidate pools | captures | Pool size distribution, empty, failures, catalog coverage |
| T-P4 | Retrieval, R0 vs R2 | captures + mapping | Recall@1/5/10, MRR with n, exact intervals, discordant pairs |
| T-P5 | Selective resolution by policy (`forced_top1`, `selective_policy_v2`, `legacy_gates_plus_p3`) and condition | snapshots | Outcome counts, coverage, precision (or "no automatic assignments"), manual, unresolved, no-score, failed, empty. **C0 automatic coverage is 0 by design and is shown as such, not as a safety result** |
| T-P6 | Signal availability, and DOI-overlap register summary | snapshots | Rate each signal is available, by condition and candidate; signal-set composition |
| T-P7 | Error analysis | snapshots + mapping | Cause categories per case |
| F-P1 | Outcome flow per condition | T-P5 | Counts, not probabilities |
| F-P2 | Signal-set composition and availability | T-P6 | Bar chart of counts |
| F-P3 | Retrieval rank per case, R0 vs R2 | T-P4 | Paired dot plot, n = |M| |
No coverage-risk *curve* is produced from the pilot (too few automatic decisions); a curve is a main-study figure. No illustrative or synthetic figure is made.

## 8. Reproducibility requirements
Seeds, labels, mappings, captures and thresholds hashed and frozen; replay performs no network or database access; the run manifest records SHA, dirty state, package versions and effective configuration; any deviation is listed in `known_deviations`; two runs of the replay on the same frozen inputs must produce byte-identical tables.
