# HAMMER historical evidence timeline and metric reconciliation

**Purpose:** Keep presentation claims, repository artifacts and later interpretations separate. This timeline uses committed Git HEAD d41378c as the code baseline, per the user’s instruction. No tests or experiments were run for this research review.

## Timeline

| Date/time | Evidence | Dataset/unit | Reported outcome | Reproducibility and citable status |
|---|---|---|---|---|
| 16 May 2026 | Initial Git commit in repository history. | Application baseline. | ProjectX application begins in Git history. | Git history is traceable; not a research result. |
| October evaluation deck (filename labels it October; exact creation date not used as evidence) | Slides 10, 14 and 15 in OCTOBER EVALUATION final.pptx. | Slide 10 names GSD1900, a 1,900 publication-pair MEDLINE benchmark. It does not state the exact HAMMER subset, split IDs or denominator. | Slide 10 cards report 92% “Accuracy (Top-1 baseline),” 0% false merge and 88% abstention; it says a subset was used and full set was planned. Slides 14–15 say there was no sealed/labeled benchmark or completed controlled result at that review stage. | **Unverified and internally inconsistent.** No GSD1900 data, HAMMER row-level predictions, manifest, denominator or metric script found in the checkout. The slides do not date/version the different claims. |
| 8 Apr 2019 source benchmark, relevant to deck | Vishnyakova, Rodriguez-Esteban & Rinaldi publish the GSD1900 source paper in JAMIA. | 1,900 MEDLINE publication pairs; pairwise gold-standard task. | Defines the benchmark; it is not a HAMMER run. Later paper notes easy pairs were excluded. | Primary source available at [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7647200/). It is citable as benchmark provenance, not as HAMMER performance. |
| 2024 source result, relevant to deck’s 92% | Tian et al. publish PubMed Computed Authors and compare it on GSD1900. | Their 400-pair test subset and full 1,900-pair set. | Reported accuracy: 0.922 on 400 test pairs and 0.910 over 1,900 pairs. These are pairwise classification results for Computed Authors/Author-ity, not candidate-ranking results for HAMMER. No 88% abstention card appears in that table. | Primary source available at [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11588201/). The numerical similarity to the deck’s 92% does not establish the deck’s provenance. |
| 2 Nov 2026, 07:22 UTC (artifact timestamp) | docs/finalisation/week1/day5/e2e_evaluation_metrics.json and per-query output, generated against author benchmark V2. | 56 gold queries drawn from the 100-query author set; the stored candidate-ID lists are the Day 5 production retrieval output. | Day 5.1 reports 0 candidate-harvesting dropouts. Rejoining the stored candidate IDs by query ID to the later V3 gold labels reproduces 52/56 top-1 hits overall (50/50 Confirmed, 2/6 Probable), MRR 52/56 = 0.9286; all 56 have at least one candidate. The V2 gold-rank fields themselves are stale for V3 because several IDs were corrected. | The recalculation is reproducible offline from the committed candidate lists plus V3 labels. The candidate lists were produced against live OpenAlex with local cache, so this is not a fresh independent API replay or cross-provider validation. |
| 2 Nov 2026, 07:52:21 UTC | docs/audit/phase4/results/author_resolution_benchmark_100_v3_sealed.json records sealed_at timestamp. | 100 queries: 56 gold identities (50 Confirmed, 6 Probable), 44 controls. Stored outcomes: 13 auto-selected, 52 manual-selection-required, 35 unresolved. | On the 13 auto-selected: 12 labels are Confirmed, one is Probable; all selected IDs match stored gold IDs. This supports 12/12 among Confirmed labels and 13/13 only if Probable is accepted. Auto coverage is 13/100; 87/100 are manual or unresolved. However, the V3 rows’ stored top_cand differs from the Day 5 production candidate list’s rank-1 ID for 30/56 gold queries (including unresolved rows with no stored V3 top candidate). The 13 auto-selected rows align with the Day 5 rank-1 candidate, but that does not establish a full same-run resolver replay. | Hash-identified internal benchmark. Gold entities are OpenAlex IDs; the repo audit says replacements were checked against publication/DOI/affiliation evidence, but no independent provider-level test is shown. Keep the Confirmed/Probable split and state that retrieval and decision artifacts are not a single fully aligned run. |
| 2 Nov 2026, 07:53:02 UTC | docs/finalisation/week1/reproducibility_manifest_v3.json. | Hashes benchmark, scripts, configuration and reported result artifacts; manifest records commit 2c4c5a93… and live-with-local-cache OpenAlex mode. | Provides file hashes and environment metadata for the then-current experiment. | Improves traceability. It does not make a live API state immutable or replace a replay from the candidate payload snapshot. Current HEAD is later, d41378c; do not imply this manifest was generated at current HEAD. |
| 2 Nov 2026 | docs/audit/phase4/results/deduplication_evaluation_50.json and later audit docs. | 50 publication pairs; aggregate has 33 TP, 0 FP, 15 TN, 0 FN over 48 decided pairs, plus two uncertain/boundary cases described in reports. | Aggregate reports precision/recall/F1 of 1.0 for the decided pairs. | The aggregate lacks paired per-record predictions for V1 and V2, so it cannot establish an improvement over baseline. Committed V2 contains the edition-regex defect flagged in the Stage 0 audit. Treat RQ1 as unverified until correction and replay. |
| 2 Nov 2026, Git HEAD | Current main commit d41378c, after the benchmark-generation commits. | Code and committed research artifacts. | Current committed code includes author candidate/evidence scoring, explicit decision states, and V1/V2 dedup components. | Source-code presence is verifiable from Git. It is not an independent experiment or peer-reviewed result. |
| 19 Nov 2026 | This research review and additive files in docs/research. | Literature and existing artifacts. | Corrects reference metadata, reappraises gaps, and proposes a bounded RQ2-first paper argument. | Research development material. It is not a completed experiment or manuscript section. |

## What the October numbers can and cannot mean

### GSD1900 and “92% top-1”

GSD1900 is an external set of 1,900 publication pairs created by Vishnyakova et al. for MEDLINE author-disambiguation evaluation. It is pairwise, not a list of author queries with ranked candidate IDs. The slide does not identify how it transformed pairs into a top-1 ranking task, which pairs were sampled, or how ties/abstentions were scored.

A separate 2024 paper reports 92.2% pairwise accuracy on a 400-pair test subset and 91.0% on the total 1,900 pairs. This may explain why a 92% value appears in the same literature context, but no evidence proves that the presentation borrowed that number. Until the HAMMER input rows, prediction rows and metric code are found, label the slide figure **reported by presentation, unverified as HAMMER evidence**.

### False merges and abstention

The slide gives 0% false merges and 88% abstention without denominators or decision definitions. The later V3 repository result has 13/100 auto-selected and 87/100 manual/unresolved. That 87% is a different benchmark and result, and cannot be used to validate an 88% October card. V3 records no automatic misselection among its 13 auto-selected cases, but only 12 are Confirmed; one is Probable. Report this category split, not universal “zero false merges.”

### Same-deck contradiction

Slides 10 and 14–15 are part of the same supplied deck. Slide 10 reports some measured values; slide 14 says there was no sealed benchmark or controlled experiment, and slide 15 says there was no labeled benchmark. The deck supplies no dates, version identifiers, sample mapping, or note that slide 10 uses a published comparator. Treat this as an unresolved intra-deck conflict, not a clean chronology.

## Publication-use disposition

| Claim | Disposition |
|---|---|
| “GSD1900 contains 1,900 MEDLINE publication pairs” | **Verified publication**, cite Vishnyakova et al. |
| “HAMMER achieved 92% top-1 accuracy on GSD1900” | **Unverified presentation claim**; do not use until raw rows, split, candidate rankings and metric code are recovered. |
| “HAMMER had 0% false merges and 88% abstention” | **Unverified presentation claim**; denominator/definitions and matching run artifacts are absent. |
| “V3 auto-selected 13, with no mismatches among selected OpenAlex IDs” | **Reported repo artifact**. State 100-query total, 13 auto cases, 12 Confirmed + 1 Probable; qualify as internal curated benchmark evidence, not external validation. |
| “V3 achieved confirmed automatic precision 12/12” | **Computable from sealed V3 rows**, assuming those stored curated labels are the reference standard; report the small n and label provenance. |
| “Dedup V2 outperforms V1” | **Not established** by aggregate JSON; paired replay needed. |
| “The October and November numbers describe the same test” | **Unsupported.** Their datasets, units and definitions differ or are unspecified. |

## Audit trail

The V3 JSON records 100 result rows, 56 gold-labeled identities (50 Confirmed, 6 Probable) and 44 negative/sparse controls. Its recorded outcomes are 13 auto-selected, 52 manual-selection-required and 35 unresolved. The reproducibility manifest records file hashes and its own timestamp/commit; it records live-with-local-cache OpenAlex data mode. The Day 5 per-query file’s stored gold_rank fields reference V2 and must not be relabeled; its candidate_ids can be re-scored against V3 gold IDs by query ID, as reported above.

Relevant repository artifacts:
- docs/audit/phase4/results/author_resolution_benchmark_100.json
- docs/audit/phase4/results/author_resolution_benchmark_100_v2_corrected.json
- docs/audit/phase4/results/author_resolution_benchmark_100_v3_sealed.json
- docs/audit/phase4/results/deduplication_evaluation_50.json
- docs/finalisation/week1/day5/e2e_per_query_results.json
- docs/finalisation/week1/reproducibility_manifest_v3.json
- docs/finalisation/week1/DAY6_BENCHMARK_V3_AND_REPRODUCIBILITY.md
- docs/finalisation/week1/DAY7_FINAL_EXPERIMENTAL_AUDIT.md

