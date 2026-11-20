# Stage 2 verification notes (Sections 3-5)

Facts in Sections 3-5 were read from the code and artifacts on 20 Nov 2026, not from earlier summaries.

## Verified against code
- Weights 0.35/0.25/0.20/0.10/0.10 and thresholds 0.75 / 0.15 / 1.35 / 0.45 / min 2 signals: `backend/config.py`, `author_resolution/policy.py`, `scoring.py`.
- Renormalised score, signal statuses, five extractors: `author_resolution/evidence.py`, `scoring.py`. Ordering: score, then descending source ID: `resolver.rank_candidates`.
- Safeguards B1-B5 = `S1..S5` in `policy.py` (protocol IDs P4-P8). Single-candidate rule relaxes margin and dominance only.
- R0/R2 definitions: `hammer_pilot/capture.py`; R2 live behaviour and fallback: `author_resolution/candidates.py`.
- DOI-purpose rule: `hammer_pilot/context_rules.py`. Metrics and exact intervals: `hammer_pilot/metrics.py`.
- Dedup rules and thresholds: `deduplication/engine.py`; normalization: `deduplication/normalize.py`.

## Verified against artifacts (research_data/lagos_and_v2)
Dataset counts, sampler seed, 50 cases / 23 blocks, strata, 32/15/3 split, 2 cases without institution, DOI register (1,713 = 1,663 gold_evidence + 50 both), 92 requests (42 authors + 50 works, all 200), cost $0.047, hit counts (R0 36/21/32/36; R2 38/22/34/38), replay outcomes (C0 0/50, C1 4/46, C1x 7/43; legacy C1x 26/24), 40 distinct printed names among 50 cases.

## Discrepancies found (not silently resolved)
1. Catalog coverage: `docs/research/stage2/METRIC_DEFINITIONS.md` defines the mapped set by a separate source-coverage audit; the toolkit defines it from the captured pools (lower bound). The manuscript uses the toolkit definition and carries a TODO.
2. Empty/failure rate denominators: toolkit uses resolved cases; the older metric file uses all eligible cases.
3. `legacy_gates_plus_p3` is documented as "P4-P8 off", but an unscored competitor still fails the margin gate in the code. The manuscript says so.
4. The older protocol describes institution matching as token-set similarity; the code uses token-sort (documented as provisional). The manuscript follows the code.
5. The application's own R2 fallback swallows a failed fallback request (known defect, unchanged); the toolkit records primary and fallback separately.
6. `rag/retrieval.py` has a stale docstring (cosine-floor formula); not used in the paper.
7. A legacy author picker in `services/search_service.py` (`get_author_candidates`) has its own score and auto-select rule; it is not the evaluated resolver.
8. `PublicationAuthorship` exists in the schema but no application code writes to it; no claim is made about it.

## Still unverified (TODO markers in the .tex)
- How the dataset's ORCID attribution was established (dataset paper not read in full).
- Exact audit sheet and the comparison between reviewer mapping and ORCID mapping.
- Main sample size, frame and the block-dependence analysis choice.
- Whether and how to extend affiliation cleaning beyond `#TAB#`.
- Compilation: no LaTeX engine is installed; nothing has been compiled.

## Stage 2.1 revision (director review)
Decision register applied: catalog coverage renamed candidate-pool mapping rate; conditional Recall@k and end-to-end success@k both reported; coauthor evidence stated unavailable on LAGOS (at most four signals); C1 supplies no publications and publication overlap is C1x-only; R0/R2 described as descriptive smoke observations; policy ablation renamed "threshold-gate ablation with P3 relaxation"; label audit rewritten around blinded candidate dossiers and described as a label-validity study; main sample new, one case per block preferred, block-clustered inference otherwise; sample size left open. Section 1 (RQ2a metric list) was changed to the new term for consistency.

**Correction to an earlier statement (code-verified).** Earlier text, and discrepancy 3 above, said an unscored competitor still fails the margin gate in `legacy_gates_plus_p3`. Running `evaluate_decision` on test pools shows the margin gate fails only when *no* competitor has a score. With a scored and an unscored competitor, the gates pass and only blocker B1 stops automation, so the ablation would assign. The manuscript now says this.

New TODOs: dossier contents and review form; block-clustered inference method; end-to-end outputs in the reporting script; how main-evaluation labels are obtained beyond the audit.
