# Deterministic Author Resolution V1

Implemented: OpenAlex candidate hypotheses, deterministic evidence extraction (name, affiliation, publication, coauthor, and temporal signals), configurable weighted scoring, conservative automatic/manual/unresolved decisions, auditable manual choices, and resolution-aware search gating.

An OpenAlex author ID is source-specific evidence only. It does not prove an identity in DBLP, Crossref, arXiv, Scholar, or any other source. Search responses therefore identify OpenAlex as `source_identified` and other name queries as `name_based` until a later source-linking stage provides supporting evidence.

The resolver is deterministic and explainable. Its weights and thresholds are configurable engineering heuristics with persisted resolver, scoring, and threshold versions; they are not scientifically validated accuracy claims.

V1 itself does not use embeddings, LLM resolution, graph ML, knowledge graphs, or a learned model. The application now has a separate Chroma publication-evidence retrieval path and optional citation-ID-validated explanation layer; these return contextual evidence but do not modify V1 scores, candidate ordering, or decisions. See `README.md` and `docs/evaluation.md` for the V1/V2 boundary and evaluation limitations. Publication deduplication remains a separate subsystem.

Before using this workflow against a real database, an operator must choose the canonical database, back it up, and run the verified additive migration from `backend/`:

```text
DATABASE_URL='sqlite+aiosqlite:////absolute/path/to/academic_search.db' alembic -c alembic.ini upgrade head
```