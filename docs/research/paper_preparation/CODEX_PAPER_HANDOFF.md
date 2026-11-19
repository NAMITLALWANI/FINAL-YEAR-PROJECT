# HAMMER paper-production handoff

**Audience:** Codex (implementation engineer), ChatGPT (research director), or any assistant picking this up cold.  
**Prepared:** 19 November 2026 by the research-preparation assistant (read-only role).  
**Rule for this file:** it records state, gaps and recommendations. It authorises nothing. Every "recommended" task below needs the owner's approval before it is done.

## 1. Version inspected

| Item | Value |
|---|---|
| Remote | `git@github.com:NAMITLALWANI/FINAL-YEAR-PROJECT.git` |
| Branch | `main` |
| Commit inspected | `bee7eabfba2d88c4a03c12d227ac6b04624fb8c8` ("Add HAMMER research design and literature documentation") |
| Remote `main` at check time | identical (`git ls-remote`) |
| Engineering recovery commit | `5250c1f56d803e2777d6a76c63b0420895d36ee9`: ancestor of `main`, on GitHub |
| Research documentation commit | `bee7eab...`: ancestor of `main`, on GitHub |
| Local uncommitted state | `.DS_Store`, tracked `.pyc` files and `backend/academic_search.db` modified; not on GitHub, not research-relevant except the database (see section 14) |
| Stage 2 documents' stated baseline | `d41378c`: **stale**. Use `bee7eab` or later for any frozen run. |

Everything in this handoff was produced without running code, tests, providers or Gemini, and without committing, pushing or modifying application files.

## 2. Research questions (unchanged)

- **RQ2 (primary):** How effectively does HAMMER retrieve author candidates, and how do its evidence-guided decision gates balance automatic assignment precision against coverage? Sub-parts: RQ2a retrieval (H2a: R2 improves Recall@k/MRR over R0), RQ2b selective resolution on one frozen pool (H2b: selective resolver reduces risk versus forced top-1 while reporting coverage).
- **RQ1 (conditional):** duplicate-publication detection. Included only if the edition-regex defect is fixed under a separate approval, a valid paired V1/V2 replay is run on identical frozen, labelled pairs, and the denominator is clear. Otherwise it is not a contribution.
- Supporting capabilities only: semantic retrieval, evidence extraction, Gemini explanation, citation handling, metadata aggregation.

## 3. Approved methodology (summary; source documents govern)

Source: `docs/research/stage2/`. Key approved items (Decision Register D01-D19):

- Retrieval arms R0 (raw trim-only), R1 (NFC + whitespace), R2 (committed `clean_query_name` + initials-only fallback). Retrieval rank = provider order.
- Decision policies on one frozen R2 pool: name-only forced top-1 (conditional on exact offline reproduction), full-evidence forced top-1, full-evidence selective. Null top score ⇒ no assignment, recorded as a separate no-score outcome.
- Stage A (independent identity labels, two blind reviewers plus adjudication) and Stage B (blind candidate-to-gold mapping) are **proposed protocols**; none has been performed.
- Pilot: **10 resolved + 5 unresolved**, workflow feasibility and workload only; descriptive counts; no accuracy claim, no pass criterion, no minimum automatic-decision count, no coverage floor.
- Statuses: resolved / unresolved / uncertain; V3 "Probable" is never encoded as resolved.
- Main-study size deferred until after the pilot. Historical data is not confirmatory.
- Metrics and denominators: `METRIC_DEFINITIONS.md`.

## 4. Literature inventory status

| Item | State |
|---|---|
| Rows | 40 (18 already in the bib, 22 proposed) |
| Verified this task against DOI/publisher records | 22 (6 existing + 16 new) |
| arXiv/search-listing level only | 6 |
| Read in full | **0** |
| Bib file | `HAMMER_REFERENCES.bib` untouched; the 22 new entries are **not** in any `.bib` |

Files: `LITERATURE_MASTER_INVENTORY.md`, `LITERATURE_MATRIX.csv`, `LITERATURE_SEARCH_LOG.md`. The search was **not systematic**. Cluster 3 (candidate generation) and the AND-specific part of Cluster 5 are the weakest and most important.

Bibliographic corrections to preserve: AggAND authors are Zhang, Huang, Yang, Lu; the heterogeneous-sites paper is Choi et al.; the 2024 review is Rodrigues, Mariano and Ralha; AffRo is 2025; the deck's "Ferreira et al.; Han et al." is **still unidentified** (candidates `ferreira2012brief` and `han2004twosupervised` exist but need owner confirmation). AMiner pages are 1002-1011 (bib lacks them). A recalled DOI was wrong during this task; **never add a DOI that was not fetched.**

## 5. Research-gap recommendation

Source: `RESEARCH_GAP_AND_POSITIONING.md`.

- The defensible gap is **narrow and unproven**: not established, from the sources inspected, that prior work reports retrieval-stage recall and selective automatic-assignment precision-versus-coverage jointly on one frozen pool with manual-review, unresolved and failure outcomes counted. Use "within the sources reviewed" wording only, until the follow-up searches are done.
- Novelty risks: CONNA (assign vs new person), HUMO/r-HUMO/CrowdER (quality-controlled human review), WhoIsWho (online assignment), selective prediction (general ML).
- Contribution tiers: engineering (describable now); evaluation-protocol (approved, unexecuted); empirical (impossible until annotation and a main study exist).
- It is acceptable if the literature shows the gap is weak; then the paper is an applied case study with an honest protocol.

## 6. Implementation facts

Source: `PAPER_IMPLEMENTATION_FACTS.md` (with file and line references). Facts the next phase must not lose:

1. Candidates come only from the OpenAlex authors endpoint: one request, `per-page=10`, no pagination, one conditional initial-only fallback.
2. `publication_overlap` and `coauthor_overlap` are **unavailable for every live candidate** (`candidates.py:265,267` set both fields to `None`); `temporal_compatibility` needs caller-supplied years that the UI and the Day 5 script do not send. **Effective signals in those paths: name and institution only.** *Code reading; confirm by a dry run.*
3. Weights 0.35/0.25/0.20/0.10/0.10 with renormalisation over available signals; thresholds 0.75 / 0.15 / 1.35 / 0.45 / min 2 signals (environment-overridable). Resolver, scoring and threshold versions `v1`.
4. Ties are ordered by descending source ID.
5. Auto-selection with no second scored candidate skips the margin and dominance gates.
6. `create_resolution` maps an `empty` pool to "source unavailable" (no row written). Do not copy this into an evaluator.
7. Embedding `all-MiniLM-L6-v2`, Chroma cosine space, similarity `1 - d`, floor 0.35. Older docstrings that say Euclidean and `1 - d/2` are wrong.
8. Gemini model comes from `GEMINI_MODEL`; not pinned. Citation check is document-ID membership, not entailment.
9. Edition-regex defect still present (`engine.py:90-93`).

## 7. Historical evidence restrictions

Do not use as HAMMER results (see `HISTORICAL_EVIDENCE_TIMELINE.md`):

| Claim | Status |
|---|---|
| October deck: 92% top-1, 0% false merge, 88% abstention | Unsupported; no denominators or raw predictions; contradicted internally by deck slides 14-15 |
| GSD1900 92.2% / 91.0% | Another system's **pairwise** accuracy (Tian et al.) |
| Day 5: 52/56 top-1, 50/50 Confirmed, 2/6 Probable, MRR 0.9286 | Offline re-scoring of old candidate lists against later V3 labels; not a fresh run; not aligned with V3 resolver output |
| V3: 13 auto / 52 manual / 35 unresolved (12 Confirmed + 1 Probable auto) | Exploratory; stored `top_cand` differs from Day 5 rank-1 on 30/56 gold queries; 24/33 identities have evidence sidecars; no blind annotation trail; do not combine with Day 5 retrieval metrics |
| Dedup 33 TP / 15 TN / 0 FP / 0 FN | No paired per-pair predictions; defect present |
| 696 publications, 2,186 source records, "100% coverage", "92.86 Recall@1", ".35 eliminates all out-of-distribution", inconsistent model identifiers | Unsupported; still present in `docs/research-paper.md` and `HAMMER_RESEARCH_PAPER_REVISED_DRAFT.md` (not removed; they are historical drafts) |

## 8. Missing experiment artifacts

None of the following exists in the repository:

- Frozen sampling frame, selection record, pilot case ledger.
- Sealed query seeds, identity labels, split manifest, split freeze (only empty templates in `docs/evaluation/templates/`).
- Captured R0/R1/R2 provider requests and raw responses with timestamps and hashes.
- Frozen R2 decision pool; evidence/database/index snapshot hashes.
- Per-query predictions for the three policies.
- A run manifest (run ID, commit, dirty state, package versions, effective thresholds, model identifiers).
- A paired V1/V2 dedup prediction table (RQ1).
- `docs/evaluation/pilot_predictions.json` exists but is a historical resubstitution-style replay of one manual-selection episode and is explicitly not usable.

## 9. Missing annotation artifacts

- No Stage A reviews (two reviewers), no adjudications, no evidence packets, no Stage B mapping, no agreement statistics.
- `PILOT_STAGE_A_READINESS_CHECKLIST.md` is entirely unchecked: owner review of protocols, sampling frame, search boundary for unresolved controls, uncertain-control replacement rule, eligibility of V3/Day 5 identities, selection-ledger location, reviewer identities, source-terms/privacy review.

## 10. Required dataset and experiment manifests

Reuse the schemas in `docs/evaluation/templates/` and scripts in `backend/scripts/` (`validate_evaluation_dataset.py`, `freeze_split_manifest.py`, `seal_evaluation_manifest.py`, `capture_retrieval_predictions.py`, `replay_frozen_resolver.py`, `evaluate_benchmark.py`) where they fit. Needed fields are listed in `EXPERIMENT_PROTOCOL_RQ2.md` ("Required artifacts for an approved future run"). A candidate-to-gold crosswalk is not yet in the templates (Decision D06, proposed). A file hash proves file identity only, not truth.

## 11. Required results (none exist)

RQ2a: Recall@1/5/10, MRR, pool size, empty-pool and source-failure rates per arm, with identity-grouped denominators. RQ2b: automatic precision, selective risk, automatic coverage, manual-review rate, unresolved rate, no-score outcomes, source-failure and empty rates, for the three policies on one pool, with exact intervals. RQ1 only if conditions in section 2 are met.

## 12. Figures and tables

| ID | Item | Can be produced now? | Why |
|---|---|---|---|
| F01 | HAMMER architecture | **Yes** | From `PAPER_IMPLEMENTATION_FACTS.md` sections 1-2; show one retrieval path and the facades honestly |
| F02 | Metadata integration | **Yes, partly** | Source flow is inspectable; avoid implying evaluated completeness |
| F03 | Author candidate-resolution workflow | **Yes** | Sections 6-10 |
| F04 | Evidence signals | **Yes, with caveat** | Show five defined signals **and** the effective-availability finding |
| F05 | Decision boundaries | **Yes** | Gates from `resolver.py:77-89`; do not draw as a calibrated probability |
| F06 | Annotation and adjudication protocol | **Yes**, labelled "proposed" | Source: Stage 2/pilot protocol |
| F07 | Dataset construction and split workflow | **Blocked** (a protocol diagram marked "proposed" is possible) | No frozen dataset manifest exists |
| F08 | Candidate retrieval results | **Blocked** | No valid evaluation output |
| F09 | Coverage-risk curve | **Blocked** | No valid evaluation output; do not create illustrative curves |
| F10 | Error analysis | **Blocked** | Needs aligned query-level predictions and labels |
| T1 | Related-work comparison | **Yes**, after reading the key papers | Matrix exists; many cells still "not inspected" |
| T2 | System components | **Yes** | |
| T3 | Signals and weights | **Yes** | Heuristic weights; state effective availability |
| T4-T8 | Dataset, config, retrieval, selective metrics, error categories | **Blocked** | Need frozen data and runs |

Equations that match the implementation and can be written now: weighted evidence score with renormalisation; the four-condition auto gate. Recall@k, MRR, selective precision, coverage, selective risk follow `METRIC_DEFINITIONS.md` and need no new definitions. Do not call the heuristic score a probability.

## 13. Manuscript sections ready, and sections that must wait

Ready to draft (as evidence-bounded text, IEEE two-column, one living LaTeX manuscript when authorised): Introduction (bounded problem), Related Work (after reading key papers), System/Architecture, Methods (evidence signals, decision gates, protocol described as *proposed*), Threats to validity and Limitations, Reproducibility plan.  
Must wait: Abstract, Results, Error analysis, Discussion of findings, Conclusion's empirical claims, any claim of performance. This task did not create a manuscript, an Overleaf project, authors, affiliations or an abstract.

## 14. Outstanding owner decisions

1. Sampling frame, window, context fields, diversity quotas (if any), unresolved-control search boundary, replacement rule for `uncertain`, ledger location (all in `PILOT_CASE_SELECTION_PROTOCOL.md`).
2. Eligibility of V3/Day 5 identities for the pilot (decide without viewing predictions).
3. Whether to include the name-only arm (only if exact offline reproduction is possible).
4. Whether RQ1 is pursued: approve a minimal fix of the edition regex and a paired replay, or drop RQ1.
5. **New:** how to describe the evidence signals given that only name and institution are available in the committed paths. Options for the owner and ChatGPT (not for me to choose): describe it as a five-signal framework with two realised signals; pass richer context; or decide whether publication/coauthor evidence is intended to exist at all.
6. **New:** reconcile `EXPERIMENT_PROTOCOL_RQ2.md` (evidence from DB/index state) with the code (evidence from payload and request context only).
7. **New:** whether the evaluator should reuse `create_resolution` (maps `empty` to unavailable) or must bypass it.
8. Confirm the identity of the deck's "Ferreira et al.; Han et al." references.
9. Whether to use the existing BibTeX keys as canonical, and how to treat arXiv-only references (venue unconfirmed).
10. Whether the working-tree `backend/academic_search.db` change should be committed or left out (affects any dataset-snapshot claim).

## 15. Recommended next tasks for Codex (each needs approval; none done)

Priority order:
1. **Dry-run availability check (read-only).** On a few made-up queries with a mocked transport (as the tests do), print which signals are available per candidate in each path. Confirms or refutes section 6 item 2. Do not call live providers.
2. **Write an offline evaluator wrapper** for the three policies that reuses `extract_evidence`, `score_evidence`, `decide` and does **not** call `create_resolution`; verify the name-only arm can reuse the exact name function and tie-break.
3. **Edition-regex fix + paired replay** (only if RQ1 is kept): one minimal change, plus a test, under explicit approval.
4. **Align stale docstrings** (scoring, resolver gates, retrieval distance, README claims) *only if the owner approves a documentation-only change*; they currently contradict the code.
5. **Produce F01-F06 and T2-T3** as vector figures and LaTeX tables from the facts file (no result figures).
6. **Experiment-manifest and run-ID generator** that records commit, dirty state, package versions, effective environment overrides, input hashes.
7. **Capture tooling check** for R0/R1/R2 request/response snapshots, with failed vs empty kept separate.
8. After approval and annotation: run the pilot tooling.

## 16. Tasks that stay with ChatGPT / the owner

Research positioning, claim wording, final gap statement, whether and how to qualify "evidence-guided", RQ1 go/no-go, the main-study design after the pilot, abstract and manuscript prose, interpretation of any result, and the follow-up literature reading (S2AND, WhoIsWho, CONNA, AMiner HITL, selective-prediction surveys) that should precede any novelty wording.

## 17. Risks and dependencies

| Risk | Dependency / mitigation |
|---|---|
| Effective signals fewer than documented | Task 15.1 before any "five-signal" text |
| Novelty weaker than hoped | Read CONNA/HUMO/AMiner; run follow-up searches (search log section 9) |
| Annotation workload | Pilot first; no time estimates exist (Stage 2.1 review) |
| Source circularity (OpenAlex as candidates and gold namespace) | Execute Stage A/B blinding as approved |
| Live-provider behaviour unverified | Capture responses; never rely on a later live call for replay |
| Stale baseline commit in Stage 2 docs | Update baseline to a frozen commit before any run |
| Historical numbers leaking into the draft | Keep the restrictions table (section 7) at the top of every drafting prompt |
| Tool-produced literature summaries may be wrong | Read the original papers before attributing specifics |
| Working tree has uncommitted DB changes | Decide snapshot policy before manifesting any run |

## 18. Document map

`docs/research/paper_preparation/`: `LITERATURE_MASTER_INVENTORY.md`, `LITERATURE_MATRIX.csv`, `LITERATURE_SEARCH_LOG.md`, `RESEARCH_GAP_AND_POSITIONING.md`, `PAPER_IMPLEMENTATION_FACTS.md`, this file. Existing material to keep using, not duplicate: `docs/research/stage2/*`, `docs/research/HISTORICAL_EVIDENCE_TIMELINE.md`, `docs/research/literature_review/*`, `docs/research/references/*`, `docs/PROJECT_EXECUTION_ROADMAP.md`.
