# HAMMER public benchmark feasibility report

**Date:** 19 November 2026. **Nature:** read-only audit. No code, toolkit, database or index was changed; no OpenAlex or Gemini call was made; **no dataset was downloaded**. All facts come from official repositories, dataset record pages, OpenAlex documentation, and the papers' HTML versions fetched in this task.  
**Labels:** **[V]** verified from the cited source in this task · **[I]** reasonable inference · **[U]** unknown, needs an experiment or a look at the actual files.  
**Important limit:** I did not open any released data file. Every "schema" statement is the schema *documented* by the official repository or record page; the instruction to verify the actual released schema is satisfied only to the extent that a cheap streaming peek at the first rows (task 1 in section 10) has not yet been done.

## 1. Executive recommendation

1. **Primary benchmark: LAGOS-AND (ORCID-labelled), version 2.0 (OpenAlex-based), starting from the TRIMMED block file only.** It is the only candidate whose labels are tied to a real-world identity anchor (ORCID) that can be matched to an OpenAlex author profile **without** using HAMMER output and **without** manual Stage B annotation, and it documents a DOI per citation, author names, affiliation strings, coauthor names, venue, year, title and abstract. [V: Zenodo record page; GitHub README]
2. **Secondary benchmark: none required.** S2AND is the best-known benchmark but cannot be linked to OpenAlex cheaply (no DOI or external IDs documented). A secondary public benchmark would add mapping cost without answering a question LAGOS-AND cannot.
3. **GSD1900: exclude from the evaluation; cite only as provenance.** It is a 1,900-row *pairwise* set of PubMed publications with names and PMIDs; it has no author-level identities, no candidate pools and no OpenAlex author labels.
4. **The 15-case manual pilot is no longer needed for ground truth.** Replace it with a small **label-validity audit** (about 30 cases, two reviewers) that checks the automatic ORCID-to-OpenAlex mapping, which is the main threat to this design (circularity, section 5).
5. **RQ2a and RQ2b can both be evaluated on the same dataset**, but only in part: coauthor evidence is not supported (names only), publication-overlap needs a leakage-controlled treatment, and unresolved cases must come from catalog gaps, not from annotation.

**Confidence:** moderate. The recommendation depends on three unverified items that a half-day of work resolves: the real columns of the TRIMMED file, what `pid` means in v2.0, and what fraction of ORCID groups have an OpenAlex author profile carrying that ORCID (section 9).

## 2. Dataset comparison

| | LAGOS-AND | S2AND | WhoIsWho / AMiner | GSD1900 |
|---|---|---|---|---|
| Official source | Zenodo v2.0 [record 7313353](https://zenodo.org/records/7313353); v1.0 [record 7313380](https://zenodo.org/records/7313380); [GitHub](https://github.com/carmanzhang/LAGOS-AND) | [github.com/allenai/S2AND](https://github.com/allenai/S2AND), S3 bucket named in README | [github.com/THUDM/WhoIsWho](https://github.com/THUDM/WhoIsWho); leaderboard [whoiswho.biendata.xyz](http://whoiswho.biendata.xyz/) | [github.com/amorgani/AND](https://github.com/amorgani/AND) |
| Paper | Zhang, Lu, Yang. JASIST 74(2) 2023; arXiv 2104.01821 (2021) | Subramanian et al. JCDL 2021 | Chen et al. KDD 2023; (AMiner HITL: Zhang et al. KDD 2018) | Vishnyakova et al. JAMIA 2019 |
| Downloadable files [V] | CSV in `.tar.gz`: BLOCK-TRIMMED 743.6 MB, BLOCK 5.7 GB, PAIRWISE 1.0 GB (v2.0, 7.5 GB total); v1.0 totals 4.7 GB | Arrow release about 10.1 GiB; legacy JSON/pickle about 55.5 GiB (S3, `--no-sign-request`) | Baidu Pan archives (demo subset NA_Demo, preprocessed toolkit data); the README gives no link to the full v3 data | Two CSVs in the repository: `1500_pairs_train.csv`, `400_pairs_test.csv` |
| License [V] | CC BY 4.0 (both records) | Dataset ODC-BY; repo CC-BY-4.0 / MIT package; affiliations partly from Microsoft Academic Graph | Not stated on the pages read | GPL-3.0 (repository) |
| Identity label | ORCID iD per author group within a full-name block | Source-dataset author clusters, aligned to Semantic Scholar | Human-curated author profiles per name | Same/different-author label for a *pair* of PubMed publications |
| Publication IDs [V] | `doi` (string), `pid` (int) | `paper_id` (Semantic Scholar); **no DOI or external IDs documented** | AMiner paper IDs; **no DOI documented** | PMIDs |
| Names [V] | `author_name` per citation, `block_fullname` | first/middle/last/suffix per signature | author names | last name, initials, first name |
| Affiliation [V] | `author_affiliation`, coauthor affiliations (strings) | per-signature `affiliations` (coverage 0.34-0.94 by dataset) | organisations of all authors | not documented in the repo README (paper reports 35.9% completeness) |
| Coauthors [V] | `coauthors` (name strings) | `authors` list per paper (names) | authors per paper | not provided |
| Year/date | `pub_year` | `year` | publication year | via PMID (external) |
| Candidate pools | None provided; block = same ORCID full name | Blocks (first initial + last name) | Name-keyed candidate authors; RND candidates built from name variants | None |
| Splits | Not documented [U] | By block, 80/10/10 per dataset [V] | By name, ratios not stated; test labels apparently withheld [U] | 1,500 train/validation, 400 test [V] |
| From-scratch task | Yes (BLOCK is built for clustering) | Yes | Yes (SND) | No (pairwise) |
| Incremental / assignment | Not a defined task | Yes, `predict_incremental` in the code | Yes (RND, with NIL) | No |
| Size [V] | v1.0: about 7.5 M citations, 798 K authors (BLOCK); about 1 M pairs | Table: 8 datasets, e.g. PubMed 2,871 records / 385 clusters; AMiner 157,448 records / 31,848 clusters | Over 1,000 names, 70,000+ authors, 1,000,000+ papers (paper) | 1,900 pairs |
| Known label limits | ORCID-derived; `author_position` by heuristics; coverage biased to ORCID holders [V/I] | Authors state no dataset is fully correct; disagreeing pairs dropped | Paper reports 99.6% accuracy on a 1,000-paper sample | Easy pairs excluded; kappa 0.96 |

**Why not WhoIsWho/AMiner:** the full data is distributed through a Chinese file host without a documented link, the schema is not documented in the README, no DOI is documented, and test labels appear to be withheld. [V for what the README states; U for the rest] It is the right benchmark for clustering and NIL-assignment research, not for linking to OpenAlex cheaply.

## 3. Verified data-schema findings

**LAGOS-AND** ([GitHub README](https://github.com/carmanzhang/LAGOS-AND/blob/main/README.md), [Zenodo v2.0](https://zenodo.org/records/7313353)):
- BLOCK documents 15 fields: `block_fullname`, `author_group_orcid`, `author_group_idx_in_block`, `citation_idx_in_author_group`, `doi`, `pid` (Int), `author_position`, `author_name`, `author_affiliation`, `coauthors` (string array), coauthor affiliations, `venue`, `pub_year`, `paper_title`, `paper_abstract`. [V as documented]
- Labels: `block_fullname` is the ORCID "credible full name"; `author_group_orcid` identifies one author's citation group; groups come from querying DOIs by ORCID iD and ORCID iDs by DOI. [V]
- `pid` is documented as the Microsoft Academic / MAG paper ID. The Zenodo v2.0 page says v2.0 is built on OpenAlex because MAG ended on 31 December 2021, and that v2.0 improved pairwise label accuracy. **Whether v2.0's `pid` is an OpenAlex work ID is not documented.** [V that both statements exist; U on their relation]
- No OpenAlex author ID is documented. PAIRWISE fields are not listed. TRIMMED is listed by size only; its content is not described. [V]
- Record counts for v2.0 are not on the page. [U]

**S2AND** ([README](https://github.com/allenai/S2AND), [data.md](https://github.com/allenai/S2AND/blob/main/docs/data.md), [paper HTML](https://ar5iv.labs.arxiv.org/html/2103.07534)): Arrow release about 10.1 GiB. Paper fields `paper_id`, `title`, `abstract`, `year`, `venue`, `journal_name`, `authors` (position, name), `references`; signature fields `signature_id`, `paper_id`, `author_info` (position, block, first, middle, last, suffix, email, affiliations). DOI and external IDs are not mentioned in any page read. Splits by block, 80/10/10. [V]

**WhoIsWho** ([README](https://github.com/THUDM/WhoIsWho), [paper HTML](https://ar5iv.labs.arxiv.org/html/2302.11848)): two-level name-author-paper dictionary; per paper title, authors with organisations, keywords, abstract, year, venue; DOI not mentioned; RND candidates are same-name authors; labels by an interactive process with 99.6% accuracy on a 1,000-paper sample. README gives no field names, sizes or licence. [V]

**GSD1900** ([repo](https://github.com/amorgani/AND), [article](https://pmc.ncbi.nlm.nih.gov/articles/PMC7647200/)): columns `PMID1, PMID2, Last_name1/2, Initials1/2, First_name1/2, Authorship (YES/NO)`; pairs from MEDLINE 2016 sharing last name and first initial; easy pairs removed; three curators per pair. [V]

## 4. HAMMER compatibility matrix

**Legend:** D = supported directly; P = supported after preprocessing; E = requires external enrichment (OpenAlex requests); N = not supported. Notes on every non-direct cell follow.

| Capability | LAGOS-AND | S2AND | WhoIsWho/AMiner | GSD1900 |
|---|---|---|---|---|
| R0 vs R2 retrieval | E (1-2 OpenAlex author requests per query) | E, plus paper-to-OpenAlex mapping first | E, same | N (no author-level query) |
| Recall@1/5/10, MRR | E (needs gold candidate = OpenAlex author with the ORCID) | E (no author identity anchor) | E (no anchor) | N |
| Catalog coverage | E (fraction of ORCIDs with an OpenAlex author profile) | N | N | N |
| C0 name-only | P (query from `author_name`) | P | P | P |
| C1 contextual evidence | P/E (see below) | P/E | P/E | N |
| Institution signal | P (free-text `author_affiliation`; token-sort, not IDs) | P (free text) | P (free text) | N |
| Publication overlap | E, leakage-prone (section 5) | E (no DOI) | E (no DOI) | N |
| Coauthor (IDs only) | **N** (names only; ID resolution needs OpenAlex works and is circular) | N | N | N |
| Temporal | P (`pub_year` of context citations to an active range) | P | P | N |
| `selective_policy_v2`, `legacy_gates_plus_p3`, `forced_top1` | D given pools and context | D | D | N |
| Automatic precision vs coverage | P (correctness from ORCID match) | P (needs mapping) | P (needs mapping) | N |
| Manual-review outcome | D (policy output) | D | D | N |
| Unresolved controls (gold) | **P (only catalog-gap cases are natural controls; no explicit unresolved labels)** | N | NIL papers exist in RND [V], but not mapped to OpenAlex | N |

Explanations: *R0/R2* require live OpenAlex author searches because none of the datasets ships OpenAlex candidate pools (they ship same-name blocks inside their own universe). *C1* is built from the dataset's own affiliation string, years and, with care, DOIs, never from OpenAlex. *Coauthor* is N because the pilot toolkit's approved policy accepts OpenAlex author IDs only, and LAGOS-AND lists coauthor *names*. Turning names into IDs would need the OpenAlex works of the same DOIs, which are gold evidence. *Unresolved controls:* every ORCID group is a resolved identity; abstention is evaluated as withholding on resolved cases and as false acceptance where the target is absent from the pool.

## 5. Leakage and evaluation validity

| Risk | LAGOS-AND | Control |
|---|---|---|
| **Same-publication leakage:** a DOI that defines the ORCID group also appears in the candidate's OpenAlex works | **High if DOIs are used as context** | Treat DOI overlap as exploratory (C1x). Primary C1 uses institution and years only. If DOIs are used, use a context subset disjoint from the DOIs used for gold mapping, and report it separately |
| **Author-ID / label-signal circularity:** the OpenAlex author profile gets its ORCID attribute from the same ORCID-linked works that formed the group | **Moderate to high [I]** | The gold mapping (candidate carries the ORCID) is derived from ORCID assertions, not from HAMMER; quantify circularity with the manual audit and a C1 run without any publication data |
| **Candidate-generation leakage:** querying OpenAlex with the exact ORCID full name favours the correct profile | Moderate [I]: the block name is ORCID's credible full name, which may differ from how papers print the name | Query with the per-citation `author_name` (the name actually printed), not `block_fullname`; report name-variant effect |
| **Train/test identity leakage:** HAMMER has no training, weights and thresholds are frozen | Low | No tuning on the benchmark; split by ORCID group only for reporting |
| **Selection bias:** ORCID holders skew recent, STEM, and career-visible | Real | State as a validity limitation; no universal claims |
| **Label noise:** ORCID records and DOI links can be wrong; `author_position` is heuristic | Present | The audit samples these |
| **Context-gold coupling:** using years/affiliation of citations *inside* the labelled group reveals group membership | Mild | Use the single query citation's affiliation and year, plus a context window from other citations only for the active-year range, and say so |

For the other datasets the same separation is possible in principle, but they lack the OpenAlex anchor, so the mapping itself becomes the dominant leakage and cost.

## 6. OpenAlex mapping feasibility

- **Verified from OpenAlex documentation:** works carry `ids.doi`, `ids.mag`, `ids.pmid`, `ids.openalex` ([works object](https://help.openalex.org/api-entities/works/work-object)); DOI filter exists and one filter accepts up to 100 OR-ed values ([works filter](https://help.openalex.org/api-entities/works/filter-works)); basic paging max 10,000 results, 100 per page ([paging](https://help.openalex.org/how-to-use-the-api/get-lists-of-entities/paging)). The author object documents `last_known_institutions`, `affiliations` and `display_name_alternatives` ([author object](https://help.openalex.org/api-entities/authors/author-object)).
- **Cost, observed in the captured Stage 1C responses:** without a key, requests share a small daily budget (the response states about $0.10) and one author-works request cost $0.0001; the notice states a free key gives its own $1/day. That is about 1,000 requests/day unauthenticated and about 10,000/day with a key. [V from the saved response metadata; the arithmetic is an inference]
- **LAGOS-AND to OpenAlex:** DOI to OpenAlex work: one request per up to 100 DOIs [V filter limit]. Gold author mapping by ORCID: candidates carry the author object's ORCID if present in search results [U: not verified in this task; the existing parser keeps the raw payload]. Assumption: most ORCID groups have a profile with that ORCID; **coverage is unknown [U]** and is exactly "catalog coverage" in the metrics.
- **S2AND / WhoIsWho to OpenAlex:** no DOI or external IDs documented, so mapping means title+year search per paper (one or more requests per paper, ambiguous). Impractical at scale; WhoIsWho's MAG relationship is **not documented** [U].
- **GSD1900:** PMIDs map through `ids.pmid` [V that the field exists; filter use U], but it yields publication matches, not author profiles.
- **Local/offline:** not feasible on a 17 GB disk if the full OpenAlex snapshot is needed (size not measured here [U]); the existing replay already runs offline from captured responses, which is the right form of "offline".

## 7. Storage and implementation estimates

Free disk space on this Mac now: **17 GiB** (measured). Estimates marked [I] are inferences from compression ratios typical of CSV.

| Item | Estimate |
|---|---|
| LAGOS-AND v2.0 BLOCK-TRIMMED download | 0.74 GB [V] |
| Extracted | about 2-4 GB [I] |
| LAGOS-AND BLOCK (full) download | 5.7 GB [V]; extracted likely well over 15 GB [I] → **do not download** |
| PAIRWISE | 1.0 GB [V]; not needed |
| First schema check | stream the first few MB of the TRIMMED archive without saving the file [I: feasible with a streamed `tar`] |
| Preprocessed benchmark slice (a few hundred ORCID groups) | tens of MB [I] |
| Captures (raw OpenAlex responses) | about 10-50 KB per response, a few hundred MB at most [I; observed 45 KB for a 19-work page] |
| S2AND | 10.1 GiB Arrow [V]; far more than needed |
| Requests for N = 300 queries | about 600-1,200 author requests plus about 150-300 DOI lookups, i.e. 1-2 days unauthenticated or a few hours with a free key [I] |
| Implementation work | seed generator from LAGOS rows; automatic gold mapper; adapt validator; larger-scale capture runner with resume; about 3-5 focused tasks [I] |
| A manageable legitimate subset | Yes: a seeded random sample of blocks with at least two ORCID groups (genuine homonyms), stratified only by block size, with the sampling rule frozen before looking at OpenAlex results |

## 8. Recommended experimental design

1. **Dataset:** LAGOS-AND v2.0 TRIMMED, subject to the schema peek. Freeze the sampling rule, seed, and version/DOI before capture. Record the record's DOI (`10.5281/zenodo.7313353` for v2.0; the page notes a newer version may exist, so pin the exact version) and file hash.
2. **Units:** one query per ORCID group. Query name = the printed `author_name` of one designated query citation; query context from that citation's affiliation and year.
3. **Conditions:** C0 name only; C1 institution string plus an active-year range; C1x adds DOI context from the group's other citations, exploratory only. Coauthor signal is excluded and reported as not supported.
4. **RQ2a:** R0 vs R2 pools (10 results, one page) from captured OpenAlex author responses. Gold-correct candidates = pool members whose OpenAlex author ORCID equals the group's ORCID. Metrics: Recall@1/5/10, MRR, catalog coverage, with the existing exact intervals and paired discordance.
5. **RQ2b:** the three policies on the frozen R2 pool. Correct automatic = selected candidate carries the group ORCID. Wrong automatic includes any automatic assignment where the target is not in the pool (these cases are the natural unresolved controls). Report coverage, precision, risk, manual-review rate, and separate categories exactly as in the protocol.
6. **Audit:** about 30 cases, two reviewers, checking (a) that the ORCID-matched profile really is the person, (b) that a pool without a match really lacks the person. Estimate the error rate of the automatic labels with an exact interval.
7. **Sample size:** set after the schema peek and a 50-query smoke capture; do not fix it now.
8. **Remove from scope:** coauthor-signal conclusions; any claim about unresolved identities beyond catalog-gap cases; any WhoIsWho/S2AND comparison; GSD1900 results; any claim of general accuracy; any use of DOI overlap in primary results.
9. **GSD1900:** exclude from evaluation, cite as provenance only.

## 9. Unresolved risks and unknowns

- **U1 Actual TRIMMED columns and row counts**, and what "trimmed" removes.
- **U2 `pid` in v2.0:** MAG integer or OpenAlex work ID; whether `doi` is populated for all rows.
- **U3 ORCID coverage in OpenAlex:** share of ORCID groups with an OpenAlex author profile carrying that ORCID; whether search results expose the `orcid` field. Verify with a small bounded capture (not done: no API call here).
- **U4 Circularity** of ORCID attribution in OpenAlex versus the dataset's ORCID-DOI links: needs the audit.
- **U5 Splits and blocks:** no official split documented; ambiguity level of blocks is unknown.
- **U6 Dataset version drift:** the record page says a newer version exists; pin the version used.
- **U7 License/attribution:** CC BY 4.0 for both LAGOS-AND records [V]; GSD1900 is GPL-3.0 [V]; S2AND and WhoIsWho terms are not fully established from the pages read.
- Paper-only evidence: the S2AND and WhoIsWho papers were read through HTML versions, not the released data.

## 10. Exact next implementation tasks (priority order)

1. **Schema peek (read-only, no storage):** stream the first rows of `LAGOS-AND-BLOCK-TRIMMED.csv.tar.gz` (v2.0) and record columns, an example group, whether `pid`/`doi` are populated. Requires a bounded download of a few MB: needs the director's go-ahead because it is a download.
2. **Sampler and seed builder:** from the extracted TRIMMED slice, a seeded, frozen sampler that outputs `seeds.csv` for C0/C1/C1x with a DOI register labelling the purpose of each DOI.
3. **Automatic label adapter:** replace Stage A/B with ORCID-based gold (`gold_person_id` opaque, candidate-to-gold mapping by candidate ORCID); the validator keeps freeze, hash and leakage checks and drops the 10/5 composition and reviewer-file rules for this track.
4. **50-query smoke capture** with a configured API key and a request budget; measures U3 and the real request rate.
5. **Scale capture and replay:** reuse the capture, replay, policy, metrics and manifest modules with resume and a larger budget.
6. **Label-validity audit sheet:** about 30 cases, two reviewers, reusing the review-file schema.

**Pilot toolkit reuse:** reusable as is: `RecordingTransport` capture of R0/R2 and enrichment, offline replay, the three policies, exact intervals and metrics, manifest and byte-identical reproducibility, DOI-purpose derivation. Needs modification: seed source (programmatic, not hand-written), label adapter and validator (no reviewers, no 15-case composition), batch/resume at hundreds of cases, and removal of the coauthor path for this track. Not reusable: Stage B manual mapping UI/CSV flow.

## 11. Sources
- [LAGOS-AND v2.0 Zenodo](https://zenodo.org/records/7313353) and [v1.0 Zenodo](https://zenodo.org/records/7313380) (files, sizes, CC BY 4.0, MAG to OpenAlex version change); [LAGOS-AND GitHub README](https://github.com/carmanzhang/LAGOS-AND/blob/main/README.md) (fields); [arXiv 2104.01821](https://arxiv.org/abs/2104.01821).
- [S2AND README](https://github.com/allenai/S2AND), [data.md](https://github.com/allenai/S2AND/blob/main/docs/data.md), [training.md](https://github.com/allenai/S2AND/blob/main/docs/training.md), [paper HTML](https://ar5iv.labs.arxiv.org/html/2103.07534).
- [WhoIsWho toolkit](https://github.com/THUDM/WhoIsWho), [paper HTML](https://ar5iv.labs.arxiv.org/html/2302.11848).
- [GSD1900 repository](https://github.com/amorgani/AND), [JAMIA article](https://pmc.ncbi.nlm.nih.gov/articles/PMC7647200/).
- OpenAlex documentation pages linked in section 6; the saved Stage 1C response metadata (`docs/research/paper_preparation/FIVE_SIGNAL_LIVE_VERIFICATION.md`).
- Existing project context: `PROTOCOL_FREEZE_RECOMMENDATION.md`, `PILOT_DATASET_AND_ANALYSIS_SPEC.md`, `LITERATURE_MASTER_INVENTORY.md`.
