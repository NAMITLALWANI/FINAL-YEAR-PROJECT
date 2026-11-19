# RQ2 Experiment Protocol — Retrieval and Selective Resolution

**Status:** Proposed; specifies a future experiment and does not run one
**Software baseline:** committed Git HEAD d41378cf4781a9bec8738ff60899ecec43227b6f

## Questions and units

Evaluate two stages separately:

- **Candidate retrieval:** Can the frozen search strategy return at least one independently mapped profile for the intended Confirmed person, and how high is the first mapped profile?
- **Identity decision:** Given the same frozen candidate pool and evidence inputs, does the full evidence resolver selectively assign the correct person, abstain, or assign incorrectly?

The primary unit is one preregistered query per identity group. Additional variants remain in that group and split and are secondary analyses.

## Retrieval arms

All arms share the endpoint, mailto/API-key behavior, common outer trim, per-page=10 limit, and one-page-only rule. They differ only in query normalization and fallback:

- **R0 — Raw-input search:** common outer trim only; send the remaining query to the authors endpoint with filter=display_name.search:{query}. No Unicode normalization, whitespace collapse, compound-name rewrite, or fallback.
- **R1 — Basic normalization:** apply NFC and trim/collapse whitespace, then the same filter. No compound-name rewrite or fallback.
- **R2 — Committed strategy:** apply committed clean_query_name (NFC, whitespace collapse, narrow Le/La compound join), then the same filter. If and only if the successful primary response yields no valid candidates and the query contains an initial, retry with search={query}; append only unseen IDs.

These are search strategies, not exact-name lookup. Retrieval Recall@k and MRR use API-returned order, not HAMMER scoring. The committed parser drops non-object results and candidates lacking an author ID or nonblank display name. It removes duplicate IDs preserving first-seen order. The initial request asks for one page with a maximum of 10; there is no pagination. Record endpoint, exact parameters, response limit, complete response and ordered unique IDs.

A timeout, HTTP error, rate limit, malformed body, or unsupported institutional input is a failed/unsupported source result. A successful response with zero valid candidates is empty. The current fallback catches request exceptions and can leave the final status empty; the study capture must preserve primary and fallback statuses separately. Do not relabel a failed request as an empty result.

## Frozen decision pool and baselines

### Verified committed behavior and frozen details

The committed cleaner applies NFC normalization, whitespace collapse, and a narrow Le/La compound join. The evidence name function uses RapidFuzz token_sort_ratio divided by 100 after casefolding, trimming, and whitespace collapse, comparing the query with candidate display name and aliases and taking the maximum. Candidate parsing drops records without a source ID or nonblank display name. The default maximum is 10 per request; one page is requested. Duplicate IDs are removed in first-seen order and fallback IDs append. These are source-verified facts at the named HEAD.

The resolver orders candidates by score availability, score, then source-author ID, with reverse sorting; equal scores therefore use descending ID. Missing signals are omitted and the configured weights are renormalized over available signals; no usable signal yields a null score. Current evidence signals are: name similarity; maximum institution token-set similarity; DOI/title publication overlap; normalized-name coauthor overlap; and active-year-range overlap. Weights are 0.35, 0.25, 0.20, 0.10, and 0.10 respectively. Freeze exact code/config hashes and effective values.

Threshold environment variables can override defaults: auto score 0.75, margin 0.15, dominance 1.35, manual score 0.45, and minimum two signals. Record overrides and effective values. Blank queries fail as invalid; institution-looking inputs fail as unsupported. Owner decision: if the top candidate score is null because no usable evidence exists, forced-top-1 makes no assignment and records a separate no-score outcome.

The current rank_candidates function has no custom-weight parameter. A name-only arm can be implemented in the offline evaluator by reusing extract_evidence and score_evidence with only name_similarity weight 1.0, then applying the same deterministic ID tie-break. This wrapper requires review and must not modify application code. If it cannot call the exact committed name function, omit the arm and document the limitation.

For each query, freeze the entire R2 candidate pool, structured candidate payloads, and context consumed by the resolver. Freeze local database/index state required to compute publication, coauthor, affiliation, and temporal evidence. All policies receive identical candidate IDs, evidence inputs, and context:

| Policy | Ranking | Assignment policy | What it isolates |
|---|---|---|---|
| Name-only forced top-1 | Name similarity only | Select only if top score is non-null; otherwise record no-score/no assignment | Conditional reference, only if exact offline reproduction is verified |
| Full-evidence forced top-1 | Committed five-signal score and rank | Select only if top score is non-null; otherwise record no-score/no assignment | Full-evidence ranking without abstention when score exists |
| Full-evidence selective | Same committed five-signal score and rank | Apply committed score, margin, dominance, and minimum-signal gates | Effect of selective gates |

The committed weights are name 0.35, institution 0.25, publication overlap 0.20, coauthor overlap 0.10, and temporal compatibility 0.10, dynamically renormalized over available evidence. Defaults are auto score 0.75, margin 0.15, dominance 1.35, minimum two available signals, and manual-review score 0.45. Record effective environment/configuration values; do not assume defaults if environment variables can override them. No threshold may be selected on the sealed test. Any new threshold chosen on development requires a new version and frozen configuration before test access.

The name-only baseline is an offline evaluation arm, not an application change. Its wrapper must reuse the committed name evidence implementation and deterministic tie-break; if it cannot, omit the arm rather than altering application behavior.

## Hypotheses and decision rule

- **H2a:** R2 improves test Recall@k or MRR over R0 on source-mappable Confirmed identities. Report each predeclared k (1, 5, 10), paired per-identity differences, and intervals. If the effect is non-positive or too uncertain, reject or call the result inconclusive.
- **H2b:** At the frozen operating point, full-evidence selective resolution is expected to lower selective risk versus full-evidence forced top-1. Report risk and coverage together with uncertainty. Ten percent coverage is provisional and not an empirically justified pass/fail floor. With few automatic decisions, results are descriptive and exploratory.
- The name-only forced-top-1 arm is a descriptive baseline for how other evidence features change decisions; it is not the primary gate comparison.

No 10% coverage floor is adopted. For any future main study, report selective risk and automatic coverage together at the operating point. Freeze effective environment-overridable thresholds before sealed-test unsealing; do not tune on test results.

## Pilot boundary

The approved 10-resolved/5-unresolved pilot validates annotation and mapping workflow only. Report evidence availability, agreement, candidate-pool sizes, mapping difficulty, workload, exact counts, denominators, and appropriate intervals. Do not calculate or report author-resolution accuracy, baseline superiority, or a performance pass/fail result from the pilot.

## Run sequence

1. Freeze RQ2, query rubric, identity labels, split, mapping crosswalk, source cutoff/capture window, metric implementation, thresholds, coverage floor, and claims.
2. Verify label, split, and query hashes before examining candidate responses or predictions.
3. Capture R0, R1, and R2 requests/responses, ordered candidate IDs, result payloads, UTC timestamps, status/error, and response hashes.
4. After capture, complete blinded candidate-to-gold mapping and source-coverage audit. Seal mapping results before calculating metrics.
5. Freeze the R2 decision pool, query context, database/index snapshot hashes, evidence payloads, code/config hashes, and runtime package hashes.
6. Run the three policies offline against that exact pool. Emit one row per query per policy, including source failure, empty pool, manual review, unresolved, selected profile, ranks, scores, and reason.
7. Hash run inputs and predictions; evaluate with METRIC_DEFINITIONS.md.
8. Unseal test metrics once. Preserve query-level outputs and report exact denominators, exclusions, intervals, and failure categories.

No experiment was run for this task. Existing V3 and Day 5 files lack complete aligned same-run evidence and cannot be retroactively promoted to this protocol.

## Required artifacts for an approved future run

Sealed query/identity-label/mapping/split artifacts and hashes; candidate response snapshots for every arm; capture time, endpoint, parameters, API metadata, status, and raw response; R2 payloads and stable order; frozen evidence/database/index snapshot identifiers; Git SHA and dirty state; scorer/candidate/threshold/evaluator hashes; runtime and package versions; per-query predictions for every policy; metrics with denominators and intervals; and a run manifest linking output hashes to input hashes.


## Implementation update — five-signal evidence architecture (19 November 2026, uncommitted working tree on top of `bee7eab`)

**Implementation amendment, not an approved protocol change.** This section records where the implemented behaviour differs from the protocol text above. Approved policy 3 and the approved definitions remain as written; no weight, threshold, hypothesis or decision is changed. Items marked **awaiting approval** are implemented but not yet authorised by the research director, and must be approved, modified or removed before a baseline is frozen. Software test counts are engineering evidence, not research performance evidence.

1. **Software baseline.** The `d41378c` baseline named above is historical. Any frozen run must name the commit that contains the five-signal changes, not `d41378c` or `bee7eab`.
2. **Evidence inputs (corrects the sentence about "local database/index state").** Evidence extraction reads only the candidate payload (including its stored enrichment) and the typed request context. It reads no local database or index state. Enrichment (OpenAlex works lookups) runs before extraction and is stored on the candidate snapshot; freeze the **enrichment responses and the query context**, not a local index.
3. **Signal availability.** Publication overlap needs supplied DOIs or OpenAlex work IDs plus a successful OpenAlex works lookup; coauthor overlap needs supplied **OpenAlex author IDs** plus a successful bounded works sample (names alone are never scored); institution needs a supplied institution; temporal needs a supplied year range. Name is always available. Unavailable signals are omitted and weights renormalised, unchanged. Each evidence row now carries a status (`observed`, `unavailable_query_input_absent`, `unavailable_candidate_data_absent`, `unavailable_not_retrieved`, `unavailable_retrieval_failed`, `unavailable_inconclusive`, `unavailable_input_unresolvable`).
4. **Institution function (awaiting approval).** The protocol text above says "maximum institution token-set similarity". The implemented comparison is OpenAlex institution ID / ROR equality when both sides have it, otherwise RapidFuzz `token_sort_ratio`. These are **not equivalent**: token-set scored a token subset as 1.0. Token-sort is provisional, does not resolve institution identity, and still mis-scores abbreviations, aliases and similarly named institutions. Institution score values differ from any earlier run; weights are unchanged.
5. **Decision policy (awaiting approval).** The approved gates are unchanged, but the implemented selective behaviour **differs from approved policy 3** as written ("committed gates"). Automatic assignment is additionally withheld when: a competitor has no score; no observed non-zero institution, publication or coauthor signal supports the top candidate; the top candidate has an observed signal scoring exactly 0.0; competitors were scored on different signal sets; or evidence retrieval failed or a candidate could not be read. These safeguards rest on a conservative design assumption that name and temporal agreement alone are insufficient for automatic identity assignment; this is not an empirical finding. Policy 3 is not redefined here: until approval, results from the implemented behaviour must be labelled as such. Ranking order is unchanged, so forced top-1 policies are unaffected, but **candidates scored on different signal sets are not necessarily directly comparable**; this limitation also applies to forced top-1 analysis. Per-candidate `signal_set` and effective weights are recorded so pools can be reported by signal-set composition. Scores are heuristic, not probabilities.
6. **Single-candidate pools.** Margin and dominance do not apply to a single candidate; the other gates and safeguards still do.
7. **Empty vs failed retrieval.** `create_resolution` no longer treats a successful empty response as a provider failure: it records `unresolved` with no candidate rows and reports `candidate_retrieval_status: empty`. Provider failures raise with an `error_code` and record nothing. An offline evaluator should still use the candidate service's structured status directly. A failed initials-only fallback request is still swallowed and can end as `empty` (unchanged; record both request outcomes in the capture).
8. **Retrieval bounds.** Query-works lookup: at most 50 identifiers, one request per identifier kind. Coauthor sample: at most 2 pages of 100 works per candidate, basic paging, explicit sort `publication_date:desc,cited_by_count:desc` (recent works favoured; OpenAlex does not document tie order). Provenance records sort, page size, pages requested and succeeded, works examined, provider total, truncation and partial-failure state. Zero overlap in an incomplete sample is inconclusive. These are retrieval bounds, not decision thresholds.
9. **Live verification is partial.** A six-request live check (see `docs/research/paper_preparation/FIVE_SIGNAL_LIVE_VERIFICATION.md`) confirmed that the `doi:` and `openalex:` filters, `select`, the explicit sort and basic paging are accepted and return the expected structure. It did **not** confirm a positive publication or coauthor match for a real author. Live operation of the five-signal pipeline is therefore not established.
