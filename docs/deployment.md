# Deployment guide

## Prepared architecture

`render.yaml` describes a FastAPI backend with a persistent 5 GB disk. The SQLite database and Chroma index share `/var/data`; Chroma can be rebuilt from canonical publication records, while relational decisions and provenance require persistent storage and backups. The service exposes `/health` as a health check. Database migrations are an explicit operator step rather than an automatic deployment hook.

The frontend is a Vite static app. Configure its host with project root `frontend`, build command `npm ci && npm run build`, output directory `dist`, and `VITE_API_BASE_URL` set to the deployed backend origin. Set backend `CORS_ORIGINS` to the exact deployed frontend origin(s), comma separated.

## Deploy steps

1. Review the Render blueprint, select a plan that supports persistent disks, and connect the repository.
2. For a new deployment, set the secret values (`CORS_ORIGINS`, and optionally `GEMINI_API_KEY` and `GEMINI_MODEL`) in the host secret store. Never place secrets in YAML or `.env.example`. Public deployment remains deferred; see [local Gemini provider setup](llm-provider.md).
3. Create the new database on the persistent disk. Before applying migration `20260907_01` to any database, create and verify a backup and inspect its path/revision. Do not point a production service at either local SQLite file.
4. Deploy the backend and verify `/health`. From a controlled shell against the deployed persistent volume, build the vector index with `python scripts/build_vector_index.py`; this may download the embedding model on first use.
5. Deploy the frontend with `VITE_API_BASE_URL` and verify candidate, manual-selection, unresolved, evidence, and provider-failure flows against the public endpoints.

## Current deployment state

No hosting credentials, existing app target, or public deployment URL are present in the repository/session. The Render blueprint is prepared but has not been submitted or verified. Deployment remains **not completed** until a hosting account/repository connection and secrets are configured and the deployed endpoints are exercised. The hosting tier must support a persistent disk; an ephemeral filesystem would lose SQLite data and the Chroma index.

**Public write protection is also required before launch.** Candidate generation and resolution endpoints persist candidate snapshots, decisions, and author rows; they currently have rate limits but no user authentication. CORS is not an authorization boundary. Add host-level authentication or an authenticated application session before exposing these routes publicly. Do not put a shared backend key in the static frontend bundle.

## Operations

- Back up `/var/data/academic_search.db` before every migration and on a scheduled cadence. Verify backup integrity and restore procedure.
- The vector index can be rebuilt with `scripts/build_vector_index.py` from the same relational DB and model/index settings.
- Use deployment logs for health and provider failure signals, but do not log API keys or complete prompts.
- Restrict `CORS_ORIGINS` to the frontend. Rate limits are process-local; use an upstream limit if horizontally scaling.
- Avoid SQLite for concurrent multi-instance writes. Move to managed PostgreSQL only after planning and testing a data migration.