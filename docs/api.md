# API workflows

FastAPI provides interactive docs at `/docs` while running locally.

## Search and author review

### `POST /author-resolutions/candidates`

Body: `{"author_name":"Ada Lovelace","institution_hint":"Example University","context":{"publications":["10.1000/xyz123"],"coauthors":[{"name":"Grace Hopper"}],"active_year_start":2015,"active_year_end":2022}}` (institution and context are optional; every context key is optional). Accepted context keys: `aliases`, `institutions` / `institution_hints` (text or `{name, openalex_id, ror}`), `publications` (DOIs or OpenAlex work IDs only; titles are ignored), `coauthors` (`{openalex_id}` entries score; names alone are accepted but never scored and yield `unavailable_input_unresolvable`), `active_year_start` and `active_year_end` (1800-2200, both or neither). Invalid identifiers or years return `422`. The response adds `candidate_retrieval_status` (`ok` or `empty`), `algorithmic_assessment` (advisory status, reason, withheld-automation blockers, per-candidate signal sets), `context_received`, `enrichment` (per-signal retrieval status), and per-evidence `status`, `explanation` and effective `weight`. A successful response with zero candidates returns `200` with `candidate_retrieval_status: "empty"`; a provider failure returns `503` with `error_code` and `candidate_retrieval_status: "failed"`. Returns OpenAlex profile hypotheses, deterministic V1 evidence and scores, ranked local publication hits, an explanation status, and a note that retrieved similarity does not change identity decisions. Candidate profiles remain source-specific. If the candidate source fails, the route returns `503`; it does not save an unresolved decision because source failure is not evidence of unresolved identity. If the candidate source fails, the route returns `503`; it does not save an unresolved decision because source failure is not evidence of unresolved identity.

### `POST /author-resolutions`

Create a persisted outcome from the same name/context fields, optionally adding `candidate_ids`, `selected_candidate_id`, `mark_unresolved`, and a short `reason`. Outcomes include automatic selection, manual selection, manual review, and unresolved. The response reports `decision_source` (`reviewer` when a candidate was selected or the query marked unresolved, otherwise `algorithm`), `candidate_retrieval_status`, and the advisory `algorithmic_assessment`; a reviewer decision stores the algorithmic assessment in `decision_reason` after the reviewer's reason. Without `candidate_ids`, a successful empty candidate response is recorded as `unresolved` with no candidate rows, while a provider failure returns `503` with `error_code` and records nothing. Manual selection must refer to a candidate from the same normalized query. The endpoint writes audit/author data and currently has rate limiting but no authentication; protect it before public deployment.

When `candidate_ids` is supplied, including an empty list, the request uses that captured candidate set and does not fetch candidates again. Re-selecting an already linked source profile reuses its internal author and source-scoped external ID.

When `candidate_ids` is supplied, including an empty list, the request uses that captured candidate set and does not fetch candidates again. Re-selecting an already linked source profile reuses its internal author and source-scoped external ID.

### `GET /author-resolutions/{resolution_id}`

Returns stored status, versioned resolver/scoring/threshold metadata, score margin, selected candidate, and signal evidence with provenance.

### `GET /search?name=...&resolution_id=...`

Runs the existing scholarly-source aggregator only after a selected resolution. A manual-review state asks the user to select a candidate; an unresolved state does not start the multi-source search. Without `resolution_id`, optional source-specific candidate parameters preserve the legacy API path.

## Evidence retrieval

### `POST /evidence/search`

Example body:

    {"query":"graph neural networks for scholarly entity resolution","top_k":5,"year":2023,"source":"openalex"}

`query` is required (2â1,000 characters), `top_k` is 1â20, and optional filters are exact DOI, publication year, or primary source provider. Response includes status, index version, retrieval latency, and ranked hits with stable document IDs, canonical IDs, source providers and identifiers, authors, publication-level affiliation mentions, DOI/URL, and retrieval score. Scores rank retrieval and are not probabilities.

An optional explanation has `status`, `summary`, `claims`, and provider timing/token usage when available; a provider HTTP status is included when a response was received. Each displayed generated claim must cite document IDs in the returned hit set. No-hit, absent provider configuration, invalid citations, timeouts, and provider failures have explicit fallback or abstention behavior. See [local LLM provider configuration and the deliberate smoke command](llm-provider.md).

## Health and errors

`GET /health` reports liveness, source circuit-breaker status, and retrieval index state/count/version/model without loading the model. `422` indicates invalid request fields, `429` rate limiting, and `503` an unavailable/missing author schema or retrieval index where applicable. Index builds are an operator CLI action and are not exposed as a public API.