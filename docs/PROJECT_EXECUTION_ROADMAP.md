# HAMMER — Project Execution Roadmap

**Status:** Authoritative planning and recovery record; ENG-01, ENG-02A, ENG-02B, ENG-02C, and ENG-02D recovery work verified; research execution remains gated  
**Planning baseline:** Git HEAD d41378cf4781a9bec8738ff60899ecec43227b6f  
**Repository:** existing FINAL-YEAR-PROJECT checkout only  
**Last planning update:** 19 November 2026

This document is the single current roadmap for engineering recovery, the approved research pilot, any later main study, the research paper, White Book, ESE demonstration, and final submission. The older Phase 3 completion plan is retained as historical material and is superseded by this roadmap. Do not use its hour estimates, 100-query evaluation proposal, or live-provider demo assumptions as current decisions.

This plan records a route to completion; it does not authorize implementation, database migration, dependency installation, API use, annotation, or experiments. The owner’s explicit approval and the gates below control execution.

## Recovery implementation update — 19 November 2026

This update records the subsequently authorized application-recovery work. It
supersedes earlier statements in this roadmap that describe ENG-02A through
ENG-02D as untested, uninstalled, or awaiting migration. The research gates
below remain unchanged.

| Scope | Verified recovery outcome |
|---|---|
| Checkout and data preservation | Work stayed in the existing checkout. Pre-existing dirty/untracked work was preserved. The root-level SQLite snapshot was not opened for migration, copied, merged, or overwritten. |
| Database safeguard and migration | A verified SQLite online-backup snapshot and manifest were created under `backups/application-recovery/` before migration. Integrity and foreign-key checks passed for source and backup. Alembic migration `20260907_01` was applied only to `backend/academic_search.db`; legacy table counts remained unchanged, all eight author-resolution tables and fourteen migration indexes are present, and the revision is at head. |
| Environment | A project-local Python 3.12 virtual environment was created at `backend/.venv`; pinned runtime/test dependencies install cleanly and `pip check` passes. Playwright Chromium was installed because the configured Scholar source is enabled. |
| Backend reliability | Candidate-pool and resolution writes now roll back on database errors; invalid candidate-pool selections are rejected; resolution requests validate names; candidate review remains available if optional topical retrieval fails; and disabled Scholar no longer launches a browser at startup. No scoring weights, thresholds, gates, retrieval model, or retrieval strategy changed. |
| Frontend reliability | The UI no longer silently falls back to the legacy candidate endpoint, auto-selects a sole candidate, or proceeds with an unpersisted selection. It preserves review controls after a save failure, disables duplicate decision clicks while saving, and displays an explicit empty-candidate/unresolved path. |
| Verification | `80 passed` backend tests; `npm run build` completed successfully; local FastAPI startup, enabled Playwright start/stop, and `/health` were verified. Health reported the preserved `scholarly-record-v1` index as ready with 449 documents. No index rebuild occurred. |

No live scholarly-provider, Gemini, ingestion, benchmark, annotation, or
research experiment was run. The deterministic Gemini fallback remains the
expected behaviour until credentials are deliberately configured and separately
verified. Deployment remains a separate, gated operation.

## 1. Current project status

Evidence labels used here:

- **Verified now:** read-only inspection during this roadmap task.
- **Audit finding:** reported in the supplied comprehensive audit dated 19 November 2026; the audit file is an attachment, not stored in the repository.
- **Repository evidence:** an existing file or approved decision exists, but its claim has not necessarily been independently rerun.
- **Awaiting external information:** depends on college instructions, dates, or a source not supplied in the repository.

### Application

| Area | Status | Evidence and limits |
|---|---|---|
| Git baseline and working tree | **VERIFICATION REQUIRED** | HEAD is d41378cf4781a9bec8738ff60899ecec43227b6f. The checkout is dirty: backend/database.py is modified, cache/metadata files are modified, and research files are untracked. Preserve them. The commit is the documented baseline, not a clean working copy. |
| Backend ORM models | **RESTORED / RUNTIME VERIFICATION REQUIRED** | ENG-02A restored the eight HEAD model definitions and legacy-only `init_db()` scope in backend/database.py. Static source comparison confirms the restored block and initializer match HEAD; the module and application have not been imported or runtime-tested. |
| SQLite databases and migration | **PLAN PREPARED / TARGET NOT APPROVED** | ENG-02B read-only comparison: backend DB has 396 publications / 1,801 source records; root DB has 546 / 857. Both pass `quick_check`, have no FK violations, and lack author/Alembic tables. Backend DB is the provisional operational candidate because `.env.dev` and default config target it; data snapshots differ materially, so neither is declared canonical. Migration remains gated. |
| Dependencies and repeatable setup | **PARTIALLY IMPLEMENTED** | backend/requirements.txt exists but does not declare chromadb, sentence-transformers, alembic, or pytest. The audit reports these packages are missing from its Python 3.12 environment. Runtime availability was not retested here; do not install packages during planning. |
| Candidate generation and persistence | **PARTIALLY IMPLEMENTED / BLOCKED** | Candidate code and APIs exist in the repository. The audit reports persistence is blocked by missing ORM/database tables. Two candidate-search API paths and differing response schemas are reported; consolidation is not approved. |
| Author-resolution decisions/manual review | **BROKEN / BLOCKED** | The audit reports writes fail because model tables are absent. Existing UI catches a persistence error. A repair depends on model/database recovery and explicit verification. |
| Frontend feedback and integration | **PARTIALLY IMPLEMENTED** | React source and author-resolution controls exist. The audit reports swallowed persistence failures; source contains a catch logging “Could not persist manual resolution.” A successful visual click is not evidence that a decision persisted. |
| Publication deduplication | **IMPLEMENTED, DEFECT/RESULT VERIFICATION REQUIRED** | Code and regression-test files exist. Stage 2 records an edition-regex control-character defect and conflicting historical pair results. No test was run for this roadmap. RQ1 is conditional and must follow its approved paired-replay protocol. |
| Semantic retrieval / vector index | **PARTIALLY IMPLEMENTED, VERIFICATION REQUIRED** | Retrieval code and two Chroma SQLite files exist. The audit reports 449 vectors in the active index and mismatch with the active relational database. Counts were not re-read here. Do not rebuild or replace an index or database without approval. |
| LLM explanations and citation checks | **PARTIALLY IMPLEMENTED** | The audit reports live Gemini calls fail and local fallback is used. Citation validation checks document-ID membership, not semantic support. No provider call was made here. Keep claims bounded to the implemented structural check. |
| Tests and reproducible verification | **VERIFICATION REQUIRED** | Fourteen test files are present under backend/tests. No test suite was run. The supplied audit reports pytest is unavailable in its environment; no environment or dependencies were changed here. |
| Demo readiness | **BLOCKED** | The backend/persistence state and vector-store/dependency state are not verified for a reliable end-to-end demonstration. The old demo suggestions assume live calls; prefer an approved, repeatable local demonstration after recovery and verification. |

### Research

| Area | Status | Evidence and limits |
|---|---|---|
| Research direction and Stage 2.1 decisions | **COMPLETED** | Approved direction and owner decisions are recorded in docs/research/stage2/UPDATED_DECISION_REGISTER.md and STAGE2_1_REVIEW_AND_OPEN_DECISIONS.md: RQ2 primary; RQ1 conditional; RQ3/RQ4 supporting; 10 resolved + 5 unresolved workflow pilot; no pilot performance claim; no 10% coverage floor; main-study size deferred. |
| Literature review / references | **IMPLEMENTED, VERIFICATION REQUIRED** | Literature matrices, citation maps, reference verification, and a BibTeX file exist. Their existence is verified; full metadata/citation correctness is not certified by this roadmap. |
| V3 benchmark | **EXPLORATORY / NOT CONFIRMATORY** | Stage 2 audit finds OpenAlex-derived gold IDs, no auditable row-level external evidence trail, and disagreement/alignment issues with Day 5 outputs. Do not combine V3 and Day 5 into an end-to-end result or use V3 as sealed test evidence. |
| Pilot annotation materials | **IN PROGRESS — DRAFTS PREPARED** | Five empty/draft Stage A files are in docs/research/stage2/pilot/. No identities, evidence packets, reviewer assignments, or candidate mapping packets were created. Owner review and open protocol decisions remain. |
| Pilot execution | **AWAITING APPROVAL / PREREQUISITES** | No annotation, candidate generation, or pilot run has occurred under the approved protocol. Execute only after rubric, cases, evidence policy, blinding, and workload capture are ready. Pilot purpose is workflow feasibility only. |
| Main-study benchmark / independent labels | **AWAITING PILOT** | The former 40/20/60 split is deferred. Sample size and statistical objective are not approved. Preserve Stage A external identity labeling, Stage B blinded candidate mapping, identity-disjoint splits, and leakage safeguards. |
| Retrieval and selective-resolution experiments | **NOT STARTED** | R0/R1/R2 and same-pool decision baselines are protocol proposals. No new candidate responses or experiments were collected. Main-study freeze must precede confirmatory runs. |
| Dedup RQ1 replay | **AWAITING PREREQUISITES / APPROVAL** | The defect and historical-result reconciliation are documented, but code correction, label review, and paired replay have not occurred. RQ1 may be omitted if prerequisites cannot be met. |
| Analysis and performance claims | **NOT STARTED** | There are no new pilot or main-study result artifacts from this plan. Every later numeric claim must map to a frozen result artifact and pass Gate D. |

### Deliverables

| Deliverable | Status | Evidence and limits |
|---|---|---|
| Research paper | **IN PROGRESS / NOT READY FOR CLAIMS** | Markdown drafts, revision notes, diagrams, and claim matrices exist. They are not a final, approved manuscript; reported corpus/results require correction or evidence reconciliation. No DOCX is to be created until separately approved. |
| White Book / project report | **AWAITING EXTERNAL REQUIREMENT** | No verified college template, rubric, mandatory front matter, page limits, or chapter format was found in the inspected repository paths. |
| ESE presentation | **PARTIALLY PREPARED / VERIFICATION REQUIRED** | Repository contains an analysis of an October evaluation deck. The final required slide structure, date, and marking rubric are not verified. |
| ESE demonstration | **NOT READY** | Depends on backend recovery, persistence verification, a stable index/dependency setup, and a repeatable no-surprises demo path. |
| Source-code handover | **IN PROGRESS** | Git repository exists, but working tree has pre-existing modifications/untracked research files and setup/dependency reproducibility is unresolved. |
| Hard copy, signatures, soft-copy upload, deadlines | **AWAITING EXTERNAL REQUIREMENT** | No confirmed college submission instructions or dates were found. Do not invent them. |

## 2. Approved direction and working rules

- RQ2, author candidate retrieval and selective resolution, is the primary empirical question.
- RQ1 deduplication is conditional on a corrected implementation and valid paired replay.
- RQ3 semantic retrieval ranking and RQ4 explanation faithfulness remain supporting capabilities.
- The V3 benchmark is exploratory/development evidence only. Day 5 candidate outputs and V3 resolver results are not aligned.
- The approved pilot has 10 resolved identities and 5 unresolved controls. It assesses evidence availability, rubric clarity, reviewer agreement, candidate-pool sizes, mapping difficulty, and workload. It is not a performance evaluation.
- Pilot reports use descriptive exact counts, denominators, and suitable intervals. There is no pilot accuracy claim, minimum automatic-decision count, statistical pass criterion, or 10% coverage floor.
- Primary statuses are resolved, unresolved, and uncertain. Historical V3 Probable rows are not encoded as resolved; no separate Probable grade is approved initially.
- Forced-top-1 makes no assignment when the top score is null; report no-score separately.
- Retain name-only only if an offline evaluator exactly reproduces the committed name function and tie-break; otherwise omit it and document why.
- Keep one checkout. Preserve local changes. No destructive Git commands, duplicate checkouts, database/index overwrite, unapproved migration, dependency install, live ingestion, API experiment, or claim promotion.

## 3. Phases, milestones, and gates

No dates or durations are assigned. Dates remain **AWAITING EXTERNAL REQUIREMENT** until the college provides its schedule.

### Phase 0 — Project control and baseline

**Objective:** Establish one source of truth and protect the current checkout.  
**Prerequisites:** None.  
**Tasks:** Record current Git HEAD and dirty state; retain this roadmap as the canonical tracker; record approved research decisions; obtain ESE/White Book instructions and deadlines.  
**Outputs:** docs/PROJECT_EXECUTION_ROADMAP.md; owner decision register; college requirements checklist when supplied.  
**Definition of done:** Baseline and owner decisions are documented, known dirty changes are preserved, and external requirements are either recorded or explicitly marked unknown.  
**Verification:** Git status/HEAD readout; linked decision records; college-issued template/rubric or written confirmation.  
**Risks/dependencies:** The attached audit is not in the repository; working-tree findings may change. College requirements are missing.  
**Approval:** The planning document is prepared; owner confirmation is required before execution tasks.

### ENG-01 and ENG-02A — Source recovery findings

ENG-01 found that the working-tree `backend/database.py` had removed Author, AuthorExternalId, AuthorAlias, AuthorAffiliation, AuthorCandidate, AuthorResolution, AuthorResolutionEvidence, and PublicationAuthorship, plus their relationships, foreign keys, constraints, indexes, and imports. The API imports three missing models, blocking author-resolution route imports. The same edit broadened `init_db()` to all metadata, which could create migration-owned tables outside Alembic.

**ENG-02A is complete as a source-only restoration.** The eight model definitions/imports and HEAD's explicit seven-table legacy `init_db()` scope were restored in `backend/database.py`. Static text comparison confirms the model block and initializer match HEAD. Unrelated pre-existing edits remain. No module import, app startup, DB write, migration, dependency change, or runtime test was performed. Runtime health is unverified.

### ENG-02B — Read-only database preservation and migration plan (prepared; owner review required)

**Effective target configuration:** In the inspected process, `APP_ENV` and process `DATABASE_URL` were unset. Config selects `backend/.env.dev`; its relative SQLite URL resolves to `backend/academic_search.db`. `backend/.env` points to the same file; `backend/.env.demo` is present but has no `DATABASE_URL`. `backend/config.py` allows a process environment override, and `backend/alembic/env.py` imports that resolved value instead of the relative URL in `alembic.ini`. Any later Alembic command must set an explicit absolute `DATABASE_URL` inline and verify the resolved target first.

**Exact current snapshots (read-only):** Both files have the same seven legacy tables and same three named indexes. All legacy columns/types match except `similarity_logs.record1_id` and `record2_id`: INTEGER in backend DB, TEXT in root DB. No legacy table declares foreign keys. Neither DB has an author-resolution table, `alembic_version`, a conflicting migration-created index, or a trigger. Both `PRAGMA quick_check` results were `ok`; `PRAGMA foreign_key_check` returned no violations.

| Table | `backend/academic_search.db` | root `academic_search.db` |
|---|---:|---:|
| publications | 396 | 546 |
| source_records | 1,801 | 857 |
| duplicate_groups | 902 | 546 |
| similarity_logs | 116 | 138 |
| cache_entries | 5 | 8 |
| scholar_cache | 2 | 3 |
| circuit_breaker_state | 3 | 2 |

The `publications.canonical_id` sets have 186 common, 210 backend-only, and 360 root-only IDs. File sizes were 41,799,680 bytes (backend) and 25,493,504 bytes (root). These are divergent snapshots, not interchangeable copies; do not merge or overwrite either. The current ORM maps similarity-log IDs as TEXT, matching root DB and differing from backend DB. Migration 20260907_01 does not touch that table, but it is a separate compatibility risk.

**Operational candidate, not canonical selection:** `backend/academic_search.db` is the strongest continuity candidate because both active dev profile and default config resolve there and it has more source-record provenance (1,801 vs 857). Root DB has more publications (546 vs 396) and substantially different IDs, so counts alone cannot establish which corpus should be authoritative. Owner confirmation/provenance review remain required before migration or production use.

**Migration compatibility:** `20260907_01` is the sole Alembic revision (`down_revision=None`). It creates eight author tables, fourteen named indexes, and `alembic_version`; it does not update/delete rows in legacy tables. Its only references to existing legacy tables are `publication_authorships.publication_id -> publications.id` and `source_record_id -> source_records.id`; other foreign keys connect the new author tables internally (authors, candidates, resolutions, and evidence). Both DBs have these tables and INTEGER primary keys, with no table/index name conflicts; the migration is structurally compatible with both on static inspection. No runtime migration/schema test was run. It is unsafe on a partially-created target. Downgrade drops all new author tables and any author data therein; restoring a pre-migration backup is preferable to downgrade.

**Backup and restore plan for a later authorized run:** Select the target and protected backup location; stop app/background writers; capture pre-migration table counts and hashes. Create a unique, restrictive-permission SQLite online backup with `Connection.backup()` in the ignored repository `backups/` directory or another owner-approved location. Check `PRAGMA integrity_check`, `PRAGMA foreign_key_check`, and table counts against the backup before migration. To restore, stop writers; preserve the migrated database and any `-wal`/`-shm` sidecars in a unique quarantine (do not delete); validate the backup read-only; replace the target from backup while retaining the migrated file for diagnosis. Current journal mode is DELETE; verify again at execution time.

**Guarded commands for later authorization only (candidate path shown; not executed):** Run from `backend/`, once ENG-02C provides an approved environment and owner selects this target. The inline URL overrides dotenv values. First verify config resolves to the exact file:

```sh
cd '/Users/nileshlalwani/Documents/COLLEGE WORK/YEAR LONG PROJECT/SYSTEM/FINAL-YEAR-PROJECT/backend'
DATABASE_URL='sqlite+aiosqlite:////Users/nileshlalwani/Documents/COLLEGE WORK/YEAR LONG PROJECT/SYSTEM/FINAL-YEAR-PROJECT/backend/academic_search.db' python - <<'PY'
import sys
sys.path.insert(0, '.')
from config import DATABASE_URL
expected = 'sqlite+aiosqlite:////Users/nileshlalwani/Documents/COLLEGE WORK/YEAR LONG PROJECT/SYSTEM/FINAL-YEAR-PROJECT/backend/academic_search.db'
assert DATABASE_URL == expected, f'Unexpected migration target: {DATABASE_URL!r}'
print('Verified target:', expected)
PY
```

After backup validation and explicit migration approval, run:

```sh
DATABASE_URL='sqlite+aiosqlite:////Users/nileshlalwani/Documents/COLLEGE WORK/YEAR LONG PROJECT/SYSTEM/FINAL-YEAR-PROJECT/backend/academic_search.db' python -m alembic -c alembic.ini upgrade 20260907_01
```

Then run this read-only verification from `backend/`:

```sh
python - <<'PY'
import sqlite3
from pathlib import Path
p = Path('academic_search.db').resolve()
c = sqlite3.connect(f'file:{p.as_posix()}?mode=ro', uri=True)
assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
assert c.execute('PRAGMA foreign_key_check').fetchall() == []
assert c.execute('SELECT version_num FROM alembic_version').fetchone()[0] == '20260907_01'
expected = {'authors','author_candidates','author_external_ids','author_aliases','author_affiliations','author_resolutions','author_resolution_evidence','publication_authorships'}
actual = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
assert expected <= actual, expected - actual
print('integrity, foreign keys, revision and author tables verified')
c.close()
PY
```

These are future commands only. Alembic is absent from the inspected environment and is not declared in `requirements.txt`; ENG-02C/approval are prerequisites. Never substitute the root DB path without a fresh owner decision and target review.

**Open ENG-02B decisions:** owner-selected authoritative DB/corpus; protected backup path and retention; approval to migrate; approved Python/Alembic environment under ENG-02C; and disposition of the existing `similarity_logs` type mismatch. No backup, migration, DB write, app startup, or dependency install occurred.

### Phase 1 — Engineering recovery

**Objective:** Restore a reliable, reproducible application without losing data or local work.  
**Prerequisites:** ENG-01 and source-only ENG-02A are complete. Each later recovery task has its own review and approval; no database, dependency, or application changes are authorized by this roadmap alone.
**Tasks, in reviewable steps:**

1. **ENG-02A — Model restoration:** completed as a source-only restoration from HEAD, preserving unrelated working-tree edits. Runtime import/application verification remains unperformed; author-resolution tables are still absent.
2. **ENG-02B — Database/migration preparation:** read-only comparison and guarded migration plan are prepared in this roadmap. Owner must select the target and protected backup location; no backup or migration until separately authorized.
3. **ENG-02C — Dependency/environment preparation:** prepare a pinned dependency and reproducible environment proposal. Do not install or uninstall packages without approval.
4. **ENG-02D — API/frontend persistence verification:** only after approved model/schema recovery and environment readiness, verify API persistence and make frontend persistence failures observable; end-to-end checks require separate authorization.
5. **P1-6 — Vector/retrieval verification:** reconcile DB and Chroma provenance/counts read-only. Do not rebuild or replace an index. Check local fallback behavior and describe citation-ID validation accurately.
6. **P1-7 — Dedup replay preparation:** preserve prior result evidence; separately review the regex defect and paired-replay protocol. No correction or replay without authorization.

**Outputs:** separately reviewed code proposal/change, database preservation plan, environment proposal, persistence and DB/index evidence, and (if separately approved) dedup replay artifacts.  
**Definition of done:** App starts, candidate generation and persistence behave coherently, manual/unresolved decisions persist, no data loss occurs, retrieval has a known snapshot, and reproducible verification passes. Do not call this complete from code inspection alone.  
**Verification:** task-specific owner-reviewed diffs; migration/table checks only on an approved DB; authorized automated and workflow checks in the approved environment; manual UI checks with logs.  
**Risks/dependencies:** Existing DB snapshots differ; current working file diverges from HEAD; missing packages; possible UI fallback masking. Model restoration alone does not create the required author tables.  
**Approval:** **Gate A — Engineering recovery approval.** Review each exact scope before implementation. No destructive Git action, database migration, dependency installation, database/index replacement, or data-changing recovery without explicit approval.

### Phase 2 — Research pilot preparation

**Objective:** Prepare Stage A independent identity-labeling materials for the approved 10-resolved / 5-unresolved workflow pilot.  
**Prerequisites:** Approved Stage 2.1 decisions. Stage A preparation is independent of ENG recovery. Candidate capture and Stage B remain separate and blocked pending an approved capture environment.

**P2-1 / Stage A preparation:** Drafts are in `docs/research/stage2/pilot/`: annotation protocol, prediction-independent selection protocol, reviewer guide, empty evidence/workload CSV, and readiness checklist. They define approved statuses, independent external evidence, two blinded reviewers/adjudication, and open decisions where the existing protocol does not specify a detail. No identities, evidence packets, reviewer assignments, labels, or annotations were created. Do not inspect predictions or select cases in this preparation.

**Independent preparation stream:** Owner review must settle evidence sufficiency, source/search boundaries, uncertain-control quota rule, sampling frame, prior-exposure eligibility, and secure storage before case selection/annotation. Stage A preparation has no application dependency.

**Capture-dependent stream (P2-2 / Phase 2B):** Candidate request/response capture and blinded Stage B mapping packets depend on ENG-02 recovery, approved environment, frozen Stage A labels, and Gate B. Stage B reviewers must not see rank/scores.

**Outputs:** Draft Stage A protocol, selection instructions, reviewer guide, empty evidence/workload template, and readiness checklist; no case data.  
**Definition of done for preparation:** Owner-reviewed materials; open operational decisions resolved; privacy/storage, reviewer assignment, evidence sufficiency, identity grouping, and Stage A freeze process ready. Document creation alone is not readiness. Pilot reports remain descriptive, with exact counts, denominators, and suitable intervals; no accuracy claim or pass criterion.  
**Verification:** Review against the decision register and author-benchmark protocol; confirm no predictions/cases/labels were accessed or added; inspect sample packets only after separately approved case preparation.  
**Risks/dependencies:** Older `docs/evaluation/dataset.md` still describes a 10-query pilot and a ≥100-query benchmark process; it is not modified here. The approved Stage 2.1 10+5 owner decision governs this pilot. Existing identity-label templates use source-scoped gold fields; do not overload them before the identity/candidate crosswalk question is reviewed.  
**Approval:** Stage A drafts await owner review. Annotation, candidate generation, Stage B mapping, and pilot execution remain gated; approved pilot scope does not mean pilot readiness.

### Phase 3 — Pilot execution and review

**Objective:** Test workflow feasibility, not resolver performance.  
**Prerequisites:** Gate B readiness; no unresolved privacy or source-access issue.  
**Tasks:** Complete blinded Stage A labels and adjudication; capture candidate pools only after identity labels are fixed; conduct blinded Stage B mapping; log evidence availability, reviewer agreement/disagreements, adjudication, candidate-pool sizes, mapping difficulty, source errors, and effort; report exact counts/denominators and suitable uncertainty intervals. Do not calculate author-resolution accuracy or baseline superiority.  
**Outputs:** pilot workflow report, issue/rubric change log, workload summary, updated feasibility estimate.  
**Definition of done:** All 15 cases have recorded workflow outcomes or documented failures; data are preserved; findings are limited to workflow feasibility.  
**Verification:** double-review coverage and adjudication audit; compare query counts to all 15; owner review of pilot report.  
**Risks/dependencies:** Incomplete external evidence, reviewer disagreement, empty/failed API retrieval, environment instability.  
**Approval:** Owner reviews pilot findings before changing the main-study protocol. Pilot cases remain exposed and cannot silently become sealed test data.

### Phase 4 — Main-study design freeze

**Objective:** Decide whether a main study is feasible and freeze its complete protocol.  
**Prerequisites:** Reviewed pilot report and actual workload/evidence/mapping observations.  
**Tasks:** Reassess main-study sample size and statistical objective; decide whether to proceed, reduce scope, or make the paper a systems/pilot study; create identity-disjoint splits; independently establish labels and separate Stage B candidate mappings; freeze R0/R1/R2 requests, same-pool decision baselines, conditional name-only inclusion, null-score behavior, effective thresholds, metrics, uncertainty method, source capture, and claim limits; seal test access and artifact hashes.  
**Outputs:** approved protocol version, label/mapping/split artifacts, manifests/hashes, preregistered analysis plan.  
**Definition of done:** Every test input, label, split, baseline, threshold, denominator, exclusion, and analysis method is fixed and independently reviewable before test predictions are opened.  
**Verification:** validator/sealer, independent leakage review, manifest hash check, owner sign-off.  
**Risks/dependencies:** Pilot may show too little evidence or impractical mapping workload; small samples may not support a confirmatory precision claim.  
**Approval:** **Gate C — Main-study freeze.** No confirmatory experiment before approval.

### Phase 5 — Main experiments

**Objective:** Execute only the approved retrieval and selective-resolution evaluation; consider RQ1 separately.  
**Prerequisites:** Gate C; stable approved application/evaluation environment; sealed artifacts.  
**Tasks:** Capture raw R0/R1/R2 API requests/responses and ordered IDs; distinguish failures from empty results; freeze common decision pools; run baselines on identical pools; preserve all per-query candidates/scores/decisions and source failures; report retrieval Recall@k/MRR separately from auto precision/risk, coverage, manual-review, unresolved, no-score, and failure rates with denominators/intervals. Consider dedup paired replay only if labels, defect correction, and paired artifacts are approved.  
**Outputs:** immutable run manifests, per-query predictions, captured raw responses, metric files, error analysis.  
**Definition of done:** All outputs tie to a Git/config/data hash; every query has an accounted outcome; no threshold or protocol changed after test access.  
**Verification:** independent manifest/hash review; reproducible metric calculation; owner review of outputs.  
**Risks/dependencies:** Live provider drift, rate limits, missing candidates, small automatic-decision count, leakage, data/model mismatch.  
**Approval:** Main-study execution is gated by C. RQ1 additionally requires a separately reviewed replay authorization.

### Phase 6 — Research analysis and claim verification

**Objective:** Ensure every result and claim has traceable evidence.  
**Prerequisites:** Frozen experiment outputs.  
**Tasks:** Analyze hypotheses against predeclared baselines; inspect failures and missingness; report uncertainty and limitations; map each numerical statement to a result artifact; revise the claim/evidence matrix; remove unsupported claims.  
**Outputs:** results memo, reproducible tables/figures, updated claim/evidence matrix, approved limitations.  
**Definition of done:** Independent reviewer can trace every number to a frozen artifact and reproduce denominator arithmetic.  
**Verification:** artifact-to-table crosswalk, rerun of metric computation from frozen inputs only, reviewer sign-off.  
**Risks/dependencies:** Results may be inconclusive or contradict hypotheses; do not change methods to force a preferred outcome.  
**Approval:** **Gate D — Results approval.** No performance claim enters the paper before output and analysis review.

### Phase 7 — Research paper completion

**Objective:** Produce a scientifically bounded, internally reviewed paper after evidence exists.  
**Prerequisites:** Approved claims/results; verified related work and citations.  
**Tasks:** Finalize title/abstract/introduction; related work; system and methods; benchmark/protocol; results; tables/figures; limitations/threats; conclusion; citation/reference review; formatting and internal review. Keep current Markdown draft as the source until a manuscript format is explicitly approved. Do not create a DOCX in this planning task. Assess publication venues only after the paper is scientifically ready; publication is not assumed to be a college requirement.  
**Outputs:** single approved manuscript source, claim/evidence crosswalk, verified reference list, release PDF if required.  
**Definition of done:** all claims are supported and all required sections/citations/layout pass review.  
**Verification:** claim matrix, source checks for citations, table/figure provenance, final owner/guide review.  
**Risks/dependencies:** Main study may not be feasible; no performance claims if there are no validated results.  
**Approval:** **Gate E — Manuscript approval.** No final paper or submission before claims, citations, tables, and limitations are approved.

### Phase 8 — White Book and ESE preparation

**Objective:** Match the actual college rubric and prepare a reliable defense.  
**Prerequisites:** College-issued White Book template/rubric, ESE schedule, demo constraints, guide instructions.  
**Tasks:** Obtain and record requirements; map implementation evidence to report chapters; prepare required certificates/front matter; prepare architecture and methodology diagrams; create presentation and viva Q&A; stabilize demo on approved local data; rehearse offline/failure handling; verify code handover/setup.  
**Outputs:** White Book/report, presentation, demo script and fallback, Q&A sheet, source handover instructions.  
**Definition of done:** All artifacts match confirmed rubric, timing, naming, formatting, demonstration, and handover requirements.  
**Verification:** checklist against official college docs; guide review; rehearsal and file-open check.  
**Risks/dependencies:** Requirements and dates are absent; live APIs/network can fail; backend currently blocked.  
**Approval:** **Gate F — College submission readiness.** No completion claim until every applicable ESE/White Book requirement is checked.

### Phase 9 — Final submission and closure

**Objective:** Complete and prove every required submission.  
**Prerequisites:** Gate F; final guide approval.  
**Tasks:** Track rubric items; incorporate examiner comments; obtain signatures; submit bound copies if required; submit source and paper only as required; upload correctly named soft copy; archive receipts and final hashes.  
**Outputs:** signed final report, source handover, final uploads, submission receipts, examiner-comment disposition.  
**Definition of done:** Each applicable requirement has evidence of completion; unknown requirements are resolved, not assumed.  
**Verification:** submission receipt/file checklist and guide confirmation.  
**Risks/dependencies:** External deadlines, signatures, hard-copy rules, and upload naming remain unknown.  
**Approval:** Owner/guide confirms closure.

## 4. Approval gates summary

- **Gate A — Engineering recovery:** review exact code diff and data-preservation plan before recovery; explicit approval before database-changing/destructive work or installs.
- **Gate B — Pilot readiness:** cases, rubric, evidence, blinding, reviewer process, and storage ready before execution.
- **Gate C — Main-study freeze:** labels, splits, metrics, baselines, thresholds, analysis, and leakage controls frozen before confirmatory runs.
- **Gate D — Results approval:** review run artifacts and analysis before performance claims.
- **Gate E — Manuscript approval:** review claims, references, figures, tables, and limitations before final manuscript/submission.
- **Gate F — College readiness:** check official ESE and White Book rules before declaring project complete.

## 5. Single progress tracker

Use this table as the sole project tracker. Status vocabulary is exactly: NOT STARTED, IN PROGRESS, BLOCKED, AWAITING APPROVAL, VERIFICATION REQUIRED, COMPLETED. Mark COMPLETED only with the listed evidence.

| Task ID | Phase | Task | Status | Priority | Dependencies | Expected output | Verification criteria | Owner approval required | Blocking issue |
|---|---|---|---|---|---|---|---|---|---|
| P0-1 | 0 | Record HEAD, dirty state, approved decisions | COMPLETED | P0 | None | This roadmap + Stage 2 register | Git SHA/status and decision record present | No | Local changes preserved |
| P0-2 | 0 | Obtain college template, ESE dates, submission rules | BLOCKED | P0 | College/guide | Requirement checklist | Official instructions and dates recorded | No | Awaiting external college documents |
| P1-1 / ENG-01 | 1 | Read-only inspect model deletion, migration, both databases | COMPLETED | P0 | P0-1 | ENG-01 record | Imports, migration structure, DB schemas and risks documented | Review before operations | ENG-02A subsequently restored source only |
| P1-2 / ENG-02A | 1 | Restore eight ORM models and HEAD legacy-only init_db behavior | COMPLETED | P0 | ENG-01 | Source restoration | Source comparison and runtime import/startup verification | No | Legacy-only initializer remains preserved |
| P1-3 / ENG-02B | 1 | Back up and migrate the configured backend database | COMPLETED | P0 | ENG-01, ENG-02A | Verified backup/manifest and Alembic revision `20260907_01` | Integrity/FK checks, legacy-count comparison, author schema/index inspection, and Alembic head check | Completed under explicit recovery authorization | Root database remains a distinct protected snapshot |
| P1-4 / ENG-02C | 1 | Establish reproducible dependency and browser setup | COMPLETED | P1 | ENG-01 | Pinned requirements, Python 3.12 virtual environment, Playwright Chromium | `pip check`, backend tests, production frontend build, and local startup | Completed under explicit recovery authorization | Live providers remain intentionally untested |
| P1-5 / ENG-02D | 1 | Verify API persistence and frontend error paths | COMPLETED | P0 | ENG-02A, ENG-02B, ENG-02C | Transaction/validation regression coverage and reviewed UI flow | 80 backend tests, production build, and local `/health` verification | Completed under explicit recovery authorization | Interactive live-provider search is outside this recovery scope |
| P1-6 | 1 | Verify preserved vector index and deterministic fallback readiness | IN PROGRESS | P1 | ENG-02B, ENG-02C | DB/index compatibility record | Health reports 449 ready documents; deliberate local semantic retrieval and configured-provider checks remain separate | Yes before rebuild or live provider call | No rebuild; source/provider behaviour remains untested |
| P1-7 | 1 | Prepare dedup defect review and paired-replay protocol; replay only if separately approved | NOT STARTED | P2 | Existing evidence; explicit authorization before correction/replay | Defect note and paired-replay plan | Preserve historical outputs; freeze paired inputs and labels before any authorized replay | Yes | Conditional RQ1; no correction or replay authorized |
| P2-1 | 2A | Prepare Stage A materials, independent case-selection and reviewer procedures | IN PROGRESS | P0 | Approved Stage 2.1 decisions | Five draft files under docs/research/stage2/pilot/ | Owner review and open decisions; no cases or labels | Yes before case selection/annotation | Drafts are not readiness; no identities selected |
| P2-2 | 2B | Prepare candidate-capture protocol, ordered response capture and Stage B mapping packets | BLOCKED | P0 | P2-1 review, ENG-02B owner target decision, ENG-02C, approved capture environment | Capture schema and blinded mapping procedure | Review raw-response/order/error/blinding plan after authorization | Yes at Gate B | No candidate generation; freeze Stage A labels first |
| P3-1 | 3 | Execute descriptive workflow pilot | AWAITING APPROVAL | P0 | P2-1, P2-2, Gate B | Pilot feasibility report | Exact counts/workload; no accuracy claim | Yes at Gate B readiness | No cases/packets yet; pilot not run |
| P4-1 | 4 | Reassess main study size/statistical objective | AWAITING APPROVAL | P0 | P3-1 | Revised protocol decision | Based on observed evidence/agreement/workload | Yes | Pilot findings unavailable |
| P4-2 | 4 | Freeze labels, mapping, splits, metrics, thresholds, analysis | NOT STARTED | P0 | P4-1, Gate C | Sealed dataset/run manifest | Leakage audit and hashes pass | Yes | Main design deferred |
| P5-1 | 5 | Run approved retrieval/resolution evaluation | NOT STARTED | P0 | P4-2, Gate C | Frozen predictions and metrics | Full artifact traceability and denominators | Yes | Dataset and experiment not frozen |
| P5-2 | 5 | Run conditional RQ1 paired replay | NOT STARTED | P2 | P1-6 and explicit authorization | Per-pair V1/V2 outputs | Frozen inputs, corrected implementation, label review | Yes | Conditional secondary question |
| P6-1 | 6 | Verify results and claim matrix | NOT STARTED | P0 | P5-1/P5-2 | Results/claim crosswalk | Every number traces to a result file | Yes at Gate D | No new results |
| P7-1 | 7 | Verify and consolidate existing literature review and preliminary Markdown drafts | VERIFICATION REQUIRED | P1 | Existing literature/reference files | Reviewed related work and draft outline | Source/claim audit; distinguish preliminary text from supported results | Yes at Gate E | Files exist but are not final or fully claim-verified |
| P7-2 | 7 | Complete final manuscript after approved research analysis | NOT STARTED | P1 | P6-1, P7-1 | Single approved manuscript source | Claim matrix, citations, tables, figures and limitations verified | Yes at Gate E | No validated main-study results |
| P8-1 | 8 | Prepare White Book/ESE artifacts to official rubric | AWAITING APPROVAL | P0 | P0-2, P1-4, P6-1 | Report, slides, demo, Q&A | Official checklist and rehearsal | Yes at Gate F | College instructions absent |
| P9-1 | 9 | Submit and archive completion evidence | NOT STARTED | P0 | P8-1, deadlines | Receipts, final files, signed copies | Every requirement has proof | Yes | Deadline/submission rules unknown |

## 6. Working model and safe task format

For each future task, the owner should receive: objective, reason, prerequisites, exact scope, expected files/evidence, prohibited actions, verification criteria, risks, and the approval gate. Keep engineering, research, and manuscript work in small reviewable tasks. Codex may inspect, implement, or run controlled experiments only when explicitly authorized for that task. ChatGPT acts as project planner; the owner approves significant choices.

Mandatory protections: no destructive Git operations; no duplicate checkout; no database/vector overwrite, migration, or rebuild without an approved preservation plan; no dependency installation without approval; no live ingestion/API experiment without explicit authorization; preserve the current uncommitted changes; do not alter approved research methodology silently.

## 7. Immediate next work

1. **ENG-02B:** Owner reviews the evidence-based provisional backend DB candidate, selects the intended operational database and protected backup location, and separately authorizes any later backup/migration.
2. **P2-1:** Owner reviews the five Stage A drafts and resolves the evidence, unresolved-control, exposure, reviewer, and secure-storage decisions before case selection or annotation.
3. **P2-2:** Remains dependent on approved ENG-02 recovery/environment and frozen Stage A labels; this work did not authorize candidate generation.
4. **ENG-02C:** Prepare a reproducible environment proposal separately; Alembic is unavailable in the inspected environment.

**Recommended next task for ENG-02B:** Owner review and target/backup-location decision using the findings above. No backup or migration is implied.  
**Recommended next task for P2-1:** Owner review of the five drafts and decisions listed in them. No case selection or annotation is implied.
