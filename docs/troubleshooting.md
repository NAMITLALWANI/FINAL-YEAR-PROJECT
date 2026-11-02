# Troubleshooting

## Backend dependency or import errors

Run commands with the project virtual environment and from `backend/`. The system Python may not have the project packages. Install with `python -m pip install -r requirements.txt` in the environment.

## Wrong SQLite schema or missing author tables

Check the working directory and resolved `DATABASE_URL`. The root and backend SQLite files are separate. Inspect the selected file and Alembic current revision before taking a backup and applying the additive migration. Do not fix a schema mismatch with `create_all`, file copying, or database recreation.

## Evidence endpoint returns `empty`

Check `/health` for index status and count. Build/reconcile the index explicitly from `backend/` with `../.venv/bin/python scripts/build_vector_index.py`. Confirm it points at the same canonical database as the running API and that publications have titles. Empty retrieval is valid; it must not trigger an identity match.

## First index build fails to download the model

The local `all-MiniLM-L6-v2` ONNX model is downloaded on first use into `VECTOR_INDEX_PATH/model_cache/`. Allow network access to the configured model source or pre-stage the verified Chroma model files. The relational database remains unchanged; rerun the index command after resolving access. The index is a projection and can be rebuilt.

## Index schema/model mismatch

The collection is versioned. Check the index and embedding model reported by `/health` and the index command. Do not change the model string without an implementation that actually uses it and a new index version. Rebuild into an isolated index path before replacing a production index.

## LLM explanation fallback

Set `GEMINI_API_KEY`, `GEMINI_MODEL`, and optionally `GEMINI_BASE_URL` in the ignored local `backend/.env` or runtime environment. Never put a key in Git, a browser bundle, or a command-line argument. The client calls Gemini's native `generateContent` API. Run the explicit local check in [llm-provider.md](llm-provider.md) to inspect status, HTTP status, latency, and citation validation without printing response content. Provider timeout, malformed JSON, or citations outside the supplied hit IDs cause deterministic fallback text; a response with no validated claims is marked as citation-validation fallback. Citation IDs do not guarantee claim support. V1 resolution remains available.

## Candidate source returns `503`

This means candidate retrieval failed, not that the identity is unresolved. The application does not save a decision for that request. Retry after checking provider availability; use the unresolved action only when a reviewer has considered the available evidence.

## Browser/Scholar unavailable

Playwright requires an installed Chromium browser for Scholar scraping. Core OpenAlex, DBLP, Crossref, arXiv, and resolution flows can be used without Scholar. Do not treat a missing browser or a CAPTCHA as an empty publication profile.

## Vite requests fail after deployment

Set frontend `VITE_API_BASE_URL` to the backend origin and backend `CORS_ORIGINS` to the exact frontend origin. Vite's proxy only applies in local development.