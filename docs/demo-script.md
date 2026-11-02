# Final demonstration script

## Preparation

1. Use a copy or a verified snapshot of the intended database. Confirm the backend `DATABASE_URL` path from `backend/` before starting.
2. Install backend and frontend dependencies; run the test/build commands in `README.md`.
3. Build the local evidence index with `cd backend && ../.venv/bin/python scripts/build_vector_index.py`. Confirm `integrity_ok: true` and a non-zero `total`.
4. Start FastAPI and the Vite frontend in separate terminals. Visit `/health`; explain that Scholar browser scraping is optional and may log a browser-unavailable warning.
5. For a network-independent retrieval demo, use the local `/evidence/search` API. For a live candidate search, explain that OpenAlex must be reachable. Do not claim a live source result if the provider timed out.

## Walkthrough

1. Submit a researcher query with a known institution hint or relevant publication clue.
2. Show candidate profiles and their deterministic name, affiliation, publication, coauthor, and temporal evidence.
3. Show retrieved publications with stable index IDs, years, provider names/IDs, DOI/source links, and retrieval ranks. State that semantic similarity ranks topical records and is not author identity confidence.
4. If the resolver requests manual selection, select a candidate and show that the explicit user action is persisted. If evidence is insufficient, mark unresolved and show that publication search is gated.
5. Show the explanation behavior: provider-configured text can cite only supplied document IDs; unverified IDs are rejected. Without provider settings, deterministic fallback text is displayed.
6. Demonstrate failure handling by using an empty/missing index or unavailable provider in a disposable local setup. The deterministic resolver should remain usable.
7. End with `docs/evaluation.md`: tests establish software behavior; the 12 manual-history replay is exploratory and no accuracy improvement has been demonstrated.

## Viva framing

Separate publication deduplication from author identity resolution. Emphasize that a canonical publication is not an author identity; a provider ID is source-scoped; missing evidence is not negative evidence; and the relational store remains authoritative. Present the unresolved evaluation dataset as a limitation and describe the required independent annotation protocol before discussing performance.