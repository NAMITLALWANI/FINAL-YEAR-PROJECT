# Evaluation dataset and annotation protocol

## Current status

The repository contains only the empty CSV/JSON templates in `docs/evaluation/templates/` and the historical `pilot_predictions.json`. There is no independently verified identity dataset, no frozen development/test membership, no query-to-publication relevance set, and no sealed evaluation manifest. The 12 historical manual choices are stored in the pilot artifact as provisional labels but are explicitly not independent, held-out, or suitable for resolver tuning. No benchmark run was performed from them in this task.

The mutable application database is not an evaluation snapshot. At the last application audit, `backend/academic_search.db` held 696 canonical publications, 2,186 source records, 76 candidate snapshots, and 29 resolution episodes. The database used for research must be an immutable, checkpointed copy; the application database must never be the test fixture or a place to add synthetic evaluation rows.

## Identity query sampling and independent review

Prepare **at least 100 author queries**. Sample cases to cover common and rare names, name variants, differing scripts/transliterations where applicable, affiliation changes, discipline changes, sparse profiles, conflicting source evidence, and cases for which the correct result is unresolved. Include multiple query variants for some people; keep all variants of a person in the same identity group. Track the sampling frame and excluded queries outside resolver output.

### Reviewer packet workflow and 10-query pilot

Start with 10 queries to check whether reviewers interpret the rubric consistently. Select them from the sampling frame without looking at resolver predictions; include varied evidence conditions and at least one case that may remain uncertain. The pilot is protocol development only: do not count it as held-out evaluation, and record any rubric change before starting the main annotation. If the final protocol changes, re-review affected pilot cases under the final instructions.

Prepare `identity_query_seed.csv` with only `query_id`, `query_text`, and `context_json`. It must not contain predictions, rankings, candidate IDs, or scores. `identity_evidence_packet.csv` can contain verified source references, capture timestamps, evidence types, and locator notes. Keep downloaded/source captures in the approved research workspace. The local HTML generator displays query context and evidence links, and creates separate reviewer packets without resolver outputs:

```sh
cd backend
../.venv/bin/python scripts/prepare_identity_review.py \
  --queries ../path/to/pilot/identity_query_seed.csv \
  --evidence ../path/to/pilot/identity_evidence_packet.csv \
  --output-dir ../path/to/pilot/reviewer-packets
```

Give `reviewer_1.html` and `reviewer_2.html` to different reviewers. Each saves one CSV row per query; aggregate each reviewer's rows into `reviewer_1.csv` and `reviewer_2.csv`. The packet asks each reviewer to record status, 1â5 confidence, rationale, a source-scoped ID when resolved, and evidence references. The adjudicator reviews disagreements and records only those pairs in `identity_adjudication.csv`; unresolved evidence conflicts can be adjudicated as `uncertain`. Merge the independent files into the exact `identity_labels.csv` schema used by the manifest:

```sh
../.venv/bin/python scripts/merge_identity_reviews.py \
  --queries ../path/to/pilot/identity_query_seed.csv \
  --review-1 ../path/to/pilot/reviewer_1.csv \
  --review-2 ../path/to/pilot/reviewer_2.csv \
  --adjudication ../path/to/pilot/identity_adjudication.csv \
  --output ../path/to/pilot/identity_labels.csv
```

The merge refuses missing/extra query rows, same reviewer IDs, invalid grades, missing source evidence, unadjudicated disagreements, or overwrites. It unions the two independent evidence-reference lists and any adjudication evidence. Then run the normal dataset validator; it remains the final check for source evidence structure, labels, identity grouping, and split freeze. Pilot output should remain separate from the eventual sealed dataset until the rubric is accepted.

Two reviewers independently adjudicate every query before seeing candidate rankings, resolver scores, or each other's annotation. Use source-level evidence such as official institutional profiles, authoritative researcher profiles, source records with stable author IDs, and publication records with stable publication IDs. A name-only match or semantic similarity is not sufficient evidence for identity. Record the source, persistent URL or source-scoped ID, capture timestamp, evidence type, and a short reviewer rationale. For unresolved labels, record which sources/searches were checked and why the evidence did not uniquely identify a person. Do not add private or restricted source material to Git.

Allowed final labels:

- `resolved`: evidence supports one specific **source-scoped** author identifier. `gold_source` and `gold_author_id` are required.
- `unresolved`: independent review finds no uniquely supported target. Gold source and ID must be blank.
- `uncertain`: evidence is insufficient or contradictory, or the reviewers cannot safely settle the label. Gold source and ID must be blank. These rows remain in the dataset and their count is reported, but they are excluded from primary resolved/unresolved metrics.

Record each reviewerâs status, confidence from 1 (low) to 5 (high), rationale, and reviewer ID. If labels agree, set `adjudication_status=agreed` and make the final label match both reviewers. If they disagree, a third reviewer records the adjudicated label and confidence with `adjudication_status=adjudicated`; if evidence remains inadequate, set the final status and adjudication status to `uncertain`. Keep rationale and evidence references for every row. The validator requires two distinct reviewer IDs, valid confidence values, evidence references, and internally consistent final/adjudication fields.

The CSV stores source references, not proof that a URL remains live. Preserve source captures or archival references in the project-approved secure research workspace. Before publication, review source terms, privacy, and redistribution rights.

## Identity groups and frozen splits

Assign a stable `identity_group_id` representing the underlying person, not the query string. All variants and repeated queries for that person go into one split. The same resolved `(gold_source, gold_author_id)` cannot occur in different identity groups. Use separate `train`, `development`, and `test` groups; tune thresholds and make design choices only with training/development data. Freeze development and test membership before the first prediction run. Inspect the test set only for one final, versioned report; do not tune against it.

After labels and split assignments are final, create a non-overwritable freeze record. For example:

```sh
cd backend
../.venv/bin/python scripts/freeze_split_manifest.py \
  --labels ../path/to/evaluation/identity_labels.csv \
  --splits ../path/to/evaluation/split_manifest.csv \
  --split-version identity-v1 \
  --frozen-at 2026-10-15T12:00:00Z \
  --output ../path/to/evaluation/split_freeze.json
```

Use the actual freeze timestamp. The record contains the split-file hash, labels hash, test-membership hash, test query count, and split version. Changing labels or split membership afterward invalidates the freeze and requires a new dataset version and documented reason; do not silently replace the freeze record.

## Separate publication relevance judgments

Build a separate retrieval query set. For each query, freeze a pool of candidate canonical publications using a documented protocol before judgments are revealed to the systems/evaluators. The pool should include independently known relevant publications and the union of the result lists from all compared variants. `retrieval_pool.csv` stores every expected query/publication pair and the non-sensitive pool source IDs; `retrieval_queries.csv` binds each query to the pool file hash, protocol version, and index snapshot. Reviewers must not see which system returned a pooled record. Independently grade every query/publication pair as:

- `0`: not relevant to the information need.
- `1`: relevant.
- `2`: strongly relevant.

Two reviewers independently grade every pair and record evidence notes. Record `review_status=complete` on a retrieval query only after the entire documented pool has been assessed. Agreement may be recorded as `agreed` only when both grades and the final grade match. Disagreements require a named adjudicator, an adjudicated grade, and `adjudication_status=adjudicated`. Preserve the query, pool-building protocol, canonical publication IDs, corpus/index snapshot, reviewers, and adjudication. The dataset validator checks that the judgment pairs exactly equal the frozen pool and that each query's declared pool count and hash match. Missing judgments are never treated as irrelevant. The metrics CLI also rejects any returned item without a complete pool judgment, so the pool must cover every item returned by each evaluated run.

This is a relevance task, not an author identity label. Do not use embedding similarity scores as relevance judgments. A publication author list or affiliation mention is not proof of a cross-source identity link.

Prepare `retrieval_review_packet.csv` with one row for every frozen query/publication pair, including query text, canonical ID, title, abstract, DOI/URL, and pool protocol version. Exclude system names, rank, similarity score, and pool source attribution from reviewer copies. Generate two separate reviewer workbooks as local HTML packets, aggregate downloaded rows into `reviewer_1.csv` and `reviewer_2.csv`, and record only disagreements in `retrieval_adjudication.csv`:

```sh
../.venv/bin/python scripts/prepare_retrieval_review.py \
  --packet-csv ../path/to/retrieval/retrieval_review_packet.csv \
  --output-dir ../path/to/retrieval/reviewer-packets
../.venv/bin/python scripts/merge_retrieval_reviews.py \
  --pool ../path/to/retrieval/retrieval_pool.csv \
  --review-1 ../path/to/retrieval/reviewer_1.csv \
  --review-2 ../path/to/retrieval/reviewer_2.csv \
  --adjudication ../path/to/retrieval/retrieval_adjudication.csv \
  --output ../path/to/retrieval/retrieval_relevance.csv
```

The merge requires one valid grade and evidence note per reviewer for every frozen pair, a distinct adjudicator for disagreements, and refuses to overwrite. Its output matches the manifest's `retrieval_relevance.csv` schema; afterward, validator checks reviewer assignments and pool hash/count coverage.

## Frozen snapshot and manifest

Create a research copy of the selected SQLite database and the persistent Chroma index. Use SQLiteâs backup mechanism to produce a checkpointed copy, and copy the index only after the index build is complete and no process is updating it. Do not run migrations, tests, candidate generation, or annotation writes against the application database. Candidate snapshots listed in `candidate_manifest.csv` must already exist in the frozen SQLite copy and match the normalized query. Record candidate source outcome as `ok`, `empty`, or `failed`; `ok` requires candidate IDs, `empty` requires `[]`, and `failed` requires an error code and `[]`. A failed source is replayed as `candidate_source_failed`, not misreported as an unresolved identity. An empty successful result is replayed through V1 as unresolved.

Copy `dataset_manifest.template.json` into the evaluation dataset directory and fill in the dataset ID/version, freeze time, snapshot paths, and Chroma collection name. Artifact paths are relative to that manifest. The sealing tool calculates hashes and checks the recorded SQLite Alembic revision/publication count plus the Chroma collection, embedded index/model versions, and document count. It validates annotations and refuses to overwrite an existing sealed manifest:

```sh
cd backend
../.venv/bin/python scripts/seal_evaluation_manifest.py \
  --draft ../path/to/evaluation/dataset_manifest.draft.json \
  --output ../path/to/evaluation/dataset_manifest.json
```

Then validate it independently:

```sh
../.venv/bin/python scripts/validate_evaluation_dataset.py \
  --dataset-manifest ../path/to/evaluation/dataset_manifest.json
```

For a manifest that includes relevance judgments, add `--require-retrieval`. Sealing requires at least 100 independently reviewed identity queries by default. The unit tests use smaller synthetic fixtures only to test the validator; those fixtures are not labels, predictions, or experimental results.

## Read-only V1 replay

Run the deterministic V1 resolver against the candidate IDs from the frozen candidate manifest and the database snapshot selected by the sealed manifest:

```sh
../.venv/bin/python scripts/replay_frozen_resolver.py \
  --dataset-manifest ../path/to/evaluation/dataset_manifest.json \
  --run-id v1-baseline-2026-01 \
  --output ../path/to/evaluation/v1_predictions.csv
```

The replay opens the snapshot with SQLite `mode=ro, immutable=1`; it never writes to the database or calls an external candidate provider. It validates all candidate IDs against the frozen database, checks the source query, records per-query candidate hashes, scoring-configuration hash, resolver-code hash, runtime-package hash, Python version, and binds predictions to dataset, database, index, resolver, scoring, and threshold versions. It refuses to overwrite predictions. The application database is not selected implicitly.

## Metrics and denominators

Identity metrics require exactly one prediction for every labelled query, including uncertain rows, with no extras. Only adjudicated `resolved` and `unresolved` labels enter primary metrics; uncertain labels are counted and excluded. Reports include exact match counts, explicit denominators, source failures, and abstentions:

- Automatic selective accuracy = correct automatic source-scoped IDs / automatic decisions.
- Automatic coverage = automatic decisions / resolved plus unresolved gold queries.
- Resolved-target automatic recall = correct automatic decisions / all resolved gold queries. Wrong selections and abstentions count as misses.
- Top-1 candidate accuracy = exact top-candidate matches / all resolved gold queries.
- Manual-review, unresolved, candidate-source-failure, and combined abstention counts/rates are reported separately.
- Unresolved recall = correctly unresolved queries / gold unresolved queries.

The V1 baseline metrics command verifies the frozen manifest, prediction hashes, snapshot IDs, and split membership:

```sh
../.venv/bin/python scripts/evaluate_benchmark.py identity \
  --dataset-manifest ../path/to/evaluation/dataset_manifest.json \
  --predictions ../path/to/evaluation/v1_predictions.csv \
  --output ../path/to/evaluation/v1_metrics.json
```

Before ranking, freeze and annotate the full query/pool set. Then capture retrieval output from a disposable copy of the sealed Chroma snapshot. The capture command refuses to overwrite a previous run and checks that the original snapshot hash remains unchanged:

```sh
../.venv/bin/python scripts/capture_retrieval_predictions.py \
  --dataset-manifest ../path/to/evaluation/dataset_manifest.json \
  --run-id retrieval-v1-2026-01 \
  --top-k 5 \
  --output ../path/to/evaluation/retrieval_predictions.json
```

The saved JSON includes code/runtime identifiers, query/pool/judgment hashes, latency, and ordered canonical publication IDs. Every returned canonical publication ID must have a complete, adjudicated pool judgment:

```sh
../.venv/bin/python scripts/evaluate_benchmark.py retrieval \
  --dataset-manifest ../path/to/evaluation/dataset_manifest.json \
  --predictions ../path/to/evaluation/retrieval_predictions.json \
  --k 5 \
  --output ../path/to/evaluation/retrieval_metrics.json
```

Recall@k and MRR use queries with at least one judged relevant publication. Recallâs denominator is all relevant publications in that queryâs judged pool. Precision@k uses fixed denominator `k`, including unfilled result positions; empty queries therefore have zero precision. Empty-result rate uses all fully judged queries. Latency percentiles use queries with a recorded non-negative latency. Each report stores SHA-256 hashes for labels, predictions, splits, relevance queries/judgments, and canonical database/index snapshots.

Do not combine identity, retrieval, and explanation support into a single âRAG accuracyâ number. The current retrieval UI provides evidence context but does not change V1 decisions. No V1-versus-retrieval identity comparison is supported until both systems have frozen predictions against the same independently adjudicated identity cases.