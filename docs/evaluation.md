# Evaluation protocol and current evidence

## Dataset inventory

The current `backend/academic_search.db` has 29 persisted resolution episodes: 12 reviewer `manual_selected`, 14 `manual_selection_required`, and 3 `unresolved`; it contains 76 OpenAlex candidate snapshots over 10 normalized queries. `backend/candidates_test_results.json` has 11 operational smoke rows. It has no labels, source citations, or train/development/test split and is not a gold dataset.

The saved [pilot artifact](evaluation/pilot_predictions.json) contains 12 historical manual-selection episodes, row-level selected/top-ranked source IDs, configuration, and descriptive metrics. It reports top-1 agreement **8/12 (66.7%)**, automatic coverage **0/12**, manual-review rate **12/12**, and unresolved rate **0/12**. Automatic accuracy and false-merge rate are undefined because no episode was automatically resolved. This is a historical, potentially dependent pilot, not a validated label set or held-out benchmark; it must not be used for tuning. Its original database snapshot hash was not recorded, so the artifact is traceable as a saved output but not fully reproducible from an immutable source snapshot.

## Measures and definitions

For a future author-identity test set, define a correct positive as an exact match to an independently verified source-scoped author identifier. Report macro and micro results where their interpretations differ. A false merge is an automatic decision that selects a candidate other than the independently labelled target; report this over automatic decisions. Selective accuracy is correct automatic decisions divided by automatic decisions; coverage is automatic decisions divided by all labelled queries. Manual review and unresolved outcomes remain abstentions and must be reported separately. False-split/recall treatment must count a labelled target left unresolved or assigned to a wrong candidate as a miss.

For retrieval, label relevant publication document IDs for each query before execution. Report Recall@k, MRR, precision@k, empty-result rate, and latency. Do not use similarity scores as relevance labels. For generation, validate cited document IDs against supplied hits and review a sampled set of claim-to-source support; report unsupported claim rate and provider failures separately. This repository does not yet contain such query-to-publication relevance labels or human explanation reviews.

## Local functional verification (2026-10-15)

Backend regression, API workflow, and evaluation-tool tests most recently passed: **47 passed** (19 focused evaluation dataset/replay/metric/capture/annotation workflow tests included), with eight dependency/existing-test deprecation warnings. The Vite production build passed in the earlier application verification. A loopback browser run against a disposable copy of the backend database used the real persistent Chroma index and mocked only upstream candidate/publication responses; it covered candidate loading and evidence rendering, manual selection, publication results, explicit unresolved status, candidate-source failure, and repeat selection of one source profile. The API server was restarted and `/health` again reported 696 indexed records; a live local `/evidence/search` returned three hits with the deterministic no-provider explanation. The two project database files passed SQLite integrity checks and were not used for workflow writes.

No LLM provider credentials were configured, so only mocked provider tests and deterministic fallback were verified. The browser workflow itself used the in-app browser; the backend's separate Playwright Chromium executable was missing, so Scholar scraping was not exercised. These are functional checks, not retrieval relevance or identity-accuracy measurements.

## Current experiment status

| Comparison/artifact | Status |
|---|---|
| V1 deterministic resolver implementation | Existing and preserved |
| V1 baseline over independent labelled test split | **Not completed**; no independently verified, held-out dataset |
| V1 exploratory replay on persisted manual choices | 12 episodes; candidate top-1 agreement 8/12 (66.7%); all 12 replayed as manual review; not held out |
| Retrieval implementation | Added; index build and runtime verification pending successful model/index initialization |
| Retrieval Recall@k / MRR | **Not completed**; no relevance judgements |
| V2 identity-decision comparison | **Not completed**; retrieval does not change V1 scores or statuses until validated labels support safe scoring |
| LLM explanation generation | Mocked success, invalid citation, missing provider, and provider failure covered; no live credentials configured |
| Generation faithfulness / quality evaluation | **Not completed**; no live provider execution or human review set |
| Ablations and statistical intervals | **Not completed** |

The empirical comparison is blocked by the lack of independently verified labels and retrieval relevance judgments. Minimum next step: annotate at least 100 queries with source-level evidence, group splits by real author identity, freeze dev/test IDs, then run all resolver variants on the same cases. S2AND and WhoIsWho are relevant public benchmarks to investigate, but their tasks, licenses, metadata schemas, and operating requirements must be checked before adoption.

The repository now includes a dataset validator, a non-overwriting split freezer, a manifest sealer, read-only V1 replay, retrieval capture from a disposable index copy, and a metrics CLI. Input templates and requirements are documented in [the dataset notes](evaluation/dataset.md). The validator checks the 100-query minimum, independent reviewer/adjudication fields, exact query coverage, identity grouping and split leakage, frozen membership/labels, SQLite snapshot hash/revision/count, Chroma snapshot hash/collection/model/version/count, candidate snapshot IDs and query association, exact relevance-pool/judgment equality, and artifact hashes. Prediction evaluation rejects missing/extra query rows and any returned publication without a pool judgment. These tools do not create labels or run an experiment by themselves. At this update, only empty templates and the non-independent historical pilot exist, so no research evaluator was run.

### Local index-build observation

One full local build indexed 696 of 696 publications in 86.3 seconds (8.1 documents/second), including model initialization. An immediate idempotent rebuild changed zero documents and completed in 2.8 seconds. These are single-run engineering observations from this machine, not a comparative retrieval benchmark. The local persistent index directory, including the downloaded embedding model cache, occupied about 190 MB. No external LLM provider was configured, so no generation cost was incurred.

## Reproducibility record

The pipeline uses collection version `scholarly_records_v1`, document/index version `scholarly-record-v1`, default embedding model `all-MiniLM-L6-v2`, cosine distance, and top-k default 5 (bounded 1â20). The index is built explicitly with `scripts/build_vector_index.py`; its content hashes include version, embedding model, and normalized text. Runtime dependencies and candidate scoring weights are in `backend/requirements.txt` and `backend/config.py`. Keep the database snapshot, index model files, exact package lock/freeze, index counts, raw predictions, and dataset manifest together for a future paper run.