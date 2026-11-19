# HAMMER literature search log

**Search date:** 19 November 2026 (single session).  
**Repository commit at time of search:** `bee7eabfba2d88c4a03c12d227ac6b04624fb8c8`.  
**This is not a systematic review.** It is a reuse of prior audit work plus a small, targeted extension. No protocol was pre-registered, no database export was screened, and no dual screening was done. Do not describe it as systematic in the manuscript.

## 1. Sources searched

| Source | How used | Notes |
|---|---|---|
| Repository documents (`docs/research/...`) | Read in full: literature matrix, gap reassessment, related-work structure, reference verification, October deck analysis, `HAMMER_REFERENCES.bib`, historical timeline, Stage 0/1 proposal, Stage 2 documents | Starting point. Existing work reused, not redone. |
| Crossref REST records (`api.crossref.org/works/{doi}`) via the fetch tool | Bibliographic verification of DOIs | Several calls returned HTTP 429 when sent in parallel; they were retried in smaller batches. One Crossref title was truncated (`CrowdER`). |
| arXiv abstract pages | Metadata and abstract-level summaries | `1705.08500`, `2103.07534`, `2302.11848`, `1706.04599`, `1910.12202`, `1710.00204`, `1803.05714`. |
| PMLR and JMLR pages | Metadata and abstract paraphrase | `geifman19a`, `el-yaniv10a`. |
| General web search (standard mode) | Exploratory queries and DOI look-ups | US-only general web search, **not** Scopus, Web of Science, Google Scholar, dblp, Semantic Scholar or ACM/IEEE search. |
| The original PowerPoint | **Not opened.** The existing analysis file `OCTOBER_EVALUATION_PRESENTATION_ANALYSIS.md` was used. | The `.pptx` was not found in the checkout (a file search of the repository found none). |

A single attempted direct network request from the shell was blocked by the tool-permission layer (my error: it put an email address in a request header). It was not retried; all later verification used the fetch and search tools.

## 2. Search clusters and queries

Queries are listed exactly as issued. Title-lookups are included because they affect what was verified.

### Exploratory topic queries (targeted at the RQ2 gap)

| # | Cluster | Query | Outcome |
|---|---|---|---|
| Q1 | 5 | `author name disambiguation abstention reject option selective prediction risk-coverage` | About ten results. None addressed author disambiguation; all were general selective-classification/abstention papers. Several had arXiv IDs of the form 26xx.xxxxx which could not be treated as verified, so they were not used. The general risk-coverage framing was confirmed as standard terminology. |
| Q2 | 3 | `author disambiguation candidate generation retrieval recall@k assignment new paper to existing author profile` | Returned WhoIsWho (real-time assignment task), CONNA (match then assign-or-new-person), and patents. The search summary stated that none of these reported Recall@k for the candidate stage; that statement is itself unverified. |
| Q3 | 5 | `author name disambiguation human-in-the-loop uncertain cases manual review confidence threshold precision coverage` | Returned AMiner HITL, Kim (2018) on DBLP, a citation-network AND paper, a practitioner guide and patents. The search summary found no source measuring precision-versus-coverage for human-reviewed AND; again unverified. |
| Q4 | 5 | `entity resolution selective classification abstain precision at coverage human review queue` | Returned HUMO and r-HUMO (human/machine workload splitting with precision/recall targets) and several general abstention papers. No source measuring precision at fixed coverage for an entity-resolution review queue was identified. |

### Title look-ups

| # | Purpose | Query | Outcome |
|---|---|---|---|
| T1 | Verify Müller, Reitz & Roy (2017) | `Müller Reitz Roy "Data sets for author name disambiguation: an empirical analysis and a new resource" Scientometrics 2017 doi` | DOI `10.1007/s11192-017-2363-5`, then confirmed through Crossref. A first DOI recalled from memory (`10.1007/s11192-017-2297-y`) resolved to an unrelated paper and was discarded. |
| T2 | Verify Kim (2018) | `Kim "Evaluating author name disambiguation for digital libraries: a case of DBLP" Scientometrics 2018 doi` | DOI `10.1007/s11192-018-2824-5` from several listings; **not** fetched from Crossref. |
| T3 | Verify CrowdER full title | `"CrowdER: Crowdsourcing Entity Resolution" Wang Kraska Franklin Feng PVLDB 5(11) 1483-1494` | Full title and PVLDB 5(11), 1483-1494 confirmed from listings. |

### Direct DOI/record verification (no search involved)

Crossref DOIs checked: `10.1145/2350036.2350040`, `10.1145/996350.996419`, `10.1145/1552303.1552304`, `10.7717/peerj-cs.1536`, `10.1177/0165551519888605`, `10.1145/3377455`, `10.1007/s10994-024-06534-x`, `10.1109/TIT.1970.1054406`, `10.18653/v1/2021.naacl-main.200`, `10.1109/TKDE.2007.250581`, `10.1016/j.datak.2009.10.003`, `10.1109/TKDE.2011.13`, `10.1145/3219819.3219859`, `10.1109/JCDL52503.2021.00029`, `10.1145/3580305.3599930`, `10.14778/2350229.2350263`, `10.1007/3-540-44503-X_20`, `10.1002/asi.24720`, `10.1093/jamia/ocz028`, `10.1007/s11192-017-2363-5`.

## 3. Screening counts

**Not recorded and not invented.** Each search returned a list of roughly ten links; those lists were skimmed, not systematically screened, and no record count was kept. Reporting a "records screened" figure would be fabrication.

What *can* be stated exactly:

| Item | Number |
|---|---:|
| Entries already in `HAMMER_REFERENCES.bib` (reused) | 18 |
| New references added to the inventory | 22 |
| New references with DOI/publisher metadata verified in this task | 16 |
| New references verified only at arXiv or search-listing level | 6 |
| Sources read in full | 0 |
| Sources with an abstract-level summary seen | 9 |
| Leads noted but excluded | 9 |

## 4. Inclusion criteria

A source was included if it (a) exists and has verifiable bibliographic metadata, **and** (b) bears directly on one of the six clusters in a way that supports an argument the paper may actually make for RQ2 (or the conditional RQ1), **and** (c) is a scholarly publication (journal, proceedings or a recognised preprint repository).

## 5. Exclusion criteria

- Patents, practitioner guides and vendor documentation (found in search results; not scholarly evidence).
- Search results whose identifiers could not be checked (for example arXiv IDs that looked future-dated).
- Papers about unrelated AI topics reached by drifting search terms (LLM abstention, time-series selection and similar).
- Recalled references not found or not verified in this task (see inventory section 8).
- Duplicates of already-inventoried work.

## 6. Full texts

| Status | Papers |
|---|---|
| Read in full in this task | None |
| Abstract-level summary seen (tool-produced) | S2AND; WhoIsWho; SelectiveNet; Geifman & El-Yaniv 2017; El-Yaniv & Wiener 2010; Guo et al. 2017; CONNA; HUMO; r-HUMO |
| Metadata only | Everything else new to the inventory |
| Content known only from the prior repository audit | The other existing bib entries |

## 7. Unavailable or not accessed

- `OCTOBER EVALUATION final(1).pptx`: not located in the repository checkout; the existing analysis document was used instead.
- Publisher full texts: not downloaded or read. The fetch tool returns a summarised view of a page, not the paper.
- Subscription databases: not searched.

## 8. Limitations of this search

1. **Search engine bias.** General web search in standard mode is not a scholarly index; it surfaced patents and irrelevant general-ML papers and may have missed relevant AND work.
2. **No full reading.** No novelty conclusion in `RESEARCH_GAP_AND_POSITIONING.md` should be treated as final until Cluster 3 and the AND-specific part of Cluster 5 have been read properly.
3. **Absence statements are weak.** "Search summaries found no source measuring X" is a statement about four queries, not about the literature.
4. **Tool summaries can be wrong.** Several claims about paper content came from a small summarising model. They are flagged wherever used.
5. **Rate limiting** delayed some verifications; all were eventually retried or are listed as unresolved.
6. **Single searcher, single day.** No second reviewer; no re-run.

## 9. Recommended follow-up searches (not done)

1. Google Scholar and Semantic Scholar with: `"author name disambiguation" "precision" "coverage" abstain`, `"author disambiguation" "recall@k" candidate`, `"author name disambiguation" "reject option"`, `"author assignment" "human review" threshold`.
2. dblp and ACM DL for JCDL/KDD/CIKM/Scientometrics/JASIST papers on *assignment* (as opposed to clustering) with explicit unresolved or new-author outcomes.
3. Citation chasing forward from CONNA, WhoIsWho and AMiner HITL.
4. Read the full text of S2AND, WhoIsWho, CONNA and AMiner HITL for how each evaluates assignment, abstention and new-author handling.
