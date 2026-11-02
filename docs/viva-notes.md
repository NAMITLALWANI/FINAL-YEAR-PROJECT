# Viva preparation notes

## Core design decisions

- **Why aggregate multiple sources?** They have different coverage and field quality. The app keeps provider provenance so a merged display does not hide disagreements.
- **Why keep normalization/dedup separate from author resolution?** Publication record linkage asks whether records describe the same work. Author name disambiguation asks whether author mentions/profiles refer to the same person. Their evidence and error costs differ.
- **Why is the database authoritative?** Persisted canonical records, decisions, and provenance need relational integrity. The vector index is a derived view that can be rebuilt.
- **Why Chroma and all-MiniLM-L6-v2?** A local persistent index is simple for the project's modest local corpus; the small sentence embedding model avoids an external embedding service. It is an initial engineering choice, not a measured best model.
- **Why not let semantic similarity auto-resolve authors?** Similar topics do not prove a shared identity. The current implementation surfaces retrieved work context but leaves V1 status unchanged until independent labels can validate a distinct V2 signal.
- **Why abstention/manual review?** Sparse or contradictory evidence should not be converted into certainty. Automatic coverage must be reported with selective accuracy and false-merge cost.
- **How are citations grounded?** The generator receives retrieved document IDs; claims citing unknown IDs are removed, and its unreferenced free-form summary is discarded. This validates citation membership, not semantic entailment, so human review remains necessary.

## Failure cases to explain

- Shared names, transliteration/name variants, affiliation changes, missing abstracts, and topic-near false retrievals.
- A relevant paper absent from the local corpus cannot be retrieved.
- Provider timeouts and rate limits are expected; V1 and deterministic fallback should still run.
- A correct source-specific OpenAlex ID does not establish an identity in DBLP, Crossref, arXiv, or Scholar.
- Current author decisions were not evaluated on an independent held-out benchmark. The local replay had 12 manual-selection episodes and all replayed as manual review; top-ranked agreement was 8/12. These are exploratory values only.
- Deployment is not complete: persistent storage is configured, but credentials, public write-route authentication, and endpoint verification remain.

## Do not claim

- Do not call the system novel, state that accuracy improved, or report the historical 170x latency figure without reproducible experimental evidence.
- Do not call retrieval similarity an identity confidence or a probability.
- Do not describe citation-ID checking as a complete faithfulness guarantee.
- Do not claim successful public deployment or a publication-ready paper.