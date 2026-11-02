# Local Gemini explanation provider

## Provider behavior

The optional explanation layer calls Gemini's native `generateContent` REST API using HTTPX. It sends a bounded query and at most eight retrieved publication records, requests JSON output at temperature zero, and gives instructions that records are untrusted input and cannot determine author identity. Returned claims are retained only when they cite IDs from the retrieved records. The display summary is assembled from those validated claims; deterministic evidence text is used when the provider is unavailable or returns unusable citations.

The API root defaults to `https://generativelanguage.googleapis.com/v1beta`; the model path is `/models/{GEMINI_MODEL}:generateContent`. Requests use the `x-goog-api-key` header. See Google's [GenerateContent REST API](https://ai.google.dev/api/generate-content) and [structured output documentation](https://ai.google.dev/gemini-api/docs/generate-content/structured-output) for the provider contract. Model availability, quotas, and pricing depend on the current account and can change; check the current [Gemini models and pricing](https://ai.google.dev/gemini-api/docs/pricing) before use.

## Configure locally

`backend/config.py` loads `backend/.env.<APP_ENV>` when present, or `backend/.env` otherwise. Process environment variables also work. Set:

- `GEMINI_API_KEY`: key created through Google AI Studio.
- `GEMINI_MODEL`: a model identifier available to your account, such as `gemini-2.5-flash`.
- `GEMINI_BASE_URL`: optional API root; defaults to `https://generativelanguage.googleapis.com/v1beta`.

Edit the ignored local `backend/.env` (or the active environment-specific file) without replacing other application settings. `backend/.env.example` contains placeholders only. Never paste a key into chat, source files, frontend `VITE_*` variables, a command-line argument, or logs. The repository ignores `.env` and `.env.*`.

To disable generated explanations, unset `GEMINI_API_KEY` or leave `GEMINI_MODEL` empty. Retrieval and deterministic evidence text remain available. A missing provider configuration does not fail application startup and does not affect V1 author decisions.

## Deliberate live smoke request

Once the key and model are set locally, explicitly run this command from the repository root:

```sh
cd backend
../.venv/bin/python scripts/smoke_llm_provider.py
```

It makes one request through the same `generate_explanation` client used by the API, using one synthetic, non-sensitive evidence record. It does not read or write either SQLite database, access the Chroma index, or run at application startup. Use `--timeout 20` to override the 12-second default; allowed values are 1â60 seconds.

Success exits with status 0 and prints provider format/host, model, application status, HTTP status, latency, whether the explanation is usable, and citation-ID validation. It never prints the key, authorization header, response body, or raw exception. Missing configuration exits 2 with `live_request_made: false`. Provider errors, invalid citations, or unusable responses exit nonzero. A successful check validates request/response integration and citation-ID filtering only; it does not establish semantic claim support or demonstrate research performance.

The smoke call is an explicit live request and may consume quota or incur a charge. Tests use mocks, never call Gemini, and do not spend provider credits.

## Boundaries

Tests cover Gemini request construction, API-key header, model/base URL selection, JSON response parsing, empty/malformed responses, timeout/network and HTTP failures, safe deterministic fallback, citation filtering, and the smoke command's one-attempt behavior. The LLM remains an optional explanation layer; its output cannot affect V1 scores, ranking, automatic resolution, manual review, or unresolved safeguards. Citation-ID validation does not prove a claim is supported. A successful provider call is not an evaluation result and does not show that retrieval improves author resolution.