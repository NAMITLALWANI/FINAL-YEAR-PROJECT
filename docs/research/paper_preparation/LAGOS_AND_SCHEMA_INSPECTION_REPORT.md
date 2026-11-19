# LAGOS-AND v2.0 BLOCK-TRIMMED: bounded schema inspection

**Date:** 19 November 2026. **Nature:** read-only data inspection; this report is the only file created in the repository. No sampler, label mapper, toolkit change or capture was started. No OpenAlex or Gemini request was made.  
**Labels:** **[V]** verified in this task from the file or an official page · **[I]** inference · **[U]** unknown.

## 1. Source and bytes downloaded

| Item | Value |
|---|---|
| Record | LAGOS-AND: A Large Gold Standard Dataset for MAG/OpenAlex Author Name Disambiguation, **version 2.0 (ORCID+OpenAlex)**, published 2022-06-25, DOI `10.5281/zenodo.7313353`, concept DOI `10.5281/zenodo.4568623`, licence CC BY 4.0 [V: Zenodo API record] |
| File | `LAGOS-AND-BLOCK-TRIMMED.csv.tar.gz` |
| Size | 743,558,936 bytes [V] |
| Checksum (listed by Zenodo) | `md5:e9e6703f98d96294e93ba105d6c1c4ac` [V]; **not verified against the file** because only a prefix was downloaded |
| Method | `GET` with `Range: bytes=0-8388607` (HTTP 206, `accept-ranges: bytes`, `content-range: bytes 0-8388607/743558936`) |
| Bytes downloaded | **8,395,485** in total: 6,877 (record JSON) + 8,388,608 (archive prefix); limit was 16 MB. The complete archive was not downloaded or saved |
| Stored locally | prefix and its decompressed copy in `/private/tmp/claude-501/lagos/` (outside the repository); removed after this report |
| Inspection complete? | **No.** The first 8 MiB of the gzip stream decompressed to 27,189,258 bytes of CSV, i.e. about 11% of the member. 16,710 complete rows were parsed. The remaining 89% of the file is unseen |

The tar header (a verified read of the first 512 bytes) shows the single member `LAGOS-AND-BLOCK-TRIMMED.csv`, **2,428,531,041 bytes when extracted** [V]. At about 1.6 kB per row in the inspected part, the full file holds roughly 1.5 million rows [I].

## 2. Actual columns (14) [V]

`block_fullname`, `orcid`, `doi`, `pid`, `author_position`, `author_name`, `author_affiliation`, `coauthors`, `coauthor_affliations` (misspelled in the file), `venue`, `pub_year`, `paper_title`, `paper_abstract`, `train1_test0_val2`.

**Differences from the README's documented 15 fields** [V comparison]:
- Present in the README but **absent** here: `author_group_orcid`, `author_group_idx_in_block`, `citation_idx_in_author_group`. The ORCID is in a column called **`orcid`**.
- **Not documented anywhere I read but present:** `train1_test0_val2`, a per-row split flag.
- Neither the README nor the Zenodo page defines "TRIMMED". Which rows or fields it removes compared with the full BLOCK file **cannot be determined** without inspecting the full file (not downloaded) [U].

## 3. Sample observations (16,710 complete rows, contiguous from the start of the file)

| Property | Observation |
|---|---|
| Row shape | All rows have 14 fields; no malformed rows |
| Order | Sorted by block name, beginning `gillian, brown`, `gillian, forrester`, ...; **the prefix is a contiguous slice, not a random sample** |
| Blocks | 931 seen (930 complete); name format `"first, last"` lower-case |
| ORCID groups | 2,400; format valid in 100%; median 3 rows per group, 1 to 411 |
| Several ORCID groups per block | **926 of 930 complete blocks have at least 2 groups** (median 2, max 38), so blocks contain true same-name homonyms by construction [V in the sample] |
| `doi` | populated in 100%; all match `10.\d{4,9}/\S+`; all lower-case; no URL prefix; no whitespace |
| `pid` | populated in 100%; all digits; lengths 10 (98.5%), 9, 8, 7; range 2,167,373 to 3,216,628,035 |
| Duplicates | 195 duplicate-DOI rows; **189 DOIs map to more than one `pid`**; no `pid` maps to more than one DOI; no DOI is shared by two ORCID groups |
| `author_name` | printed name per citation; ORCID groups show variants (median 1, up to 9 strings in the first 300 groups) |
| `author_affiliation` | populated in 85.4%; free text; 391 rows contain a `#TAB#` artifact |
| `coauthors` | a bracketed list of **name strings** in 100% of rows; no identifier-like tokens (no OpenAlex/ORCID/URL patterns) in any row; the author's own name appears in the list in 16,689 of 16,710 rows (99.9%) |
| `venue`, `paper_abstract` | populated in 97.2% and 88.6% |
| `pub_year` | 1963 to 2022 |
| `train1_test0_val2` | values 1 (8,376 rows), 0 (3,836), 2 (4,498). **Constant within every ORCID group and within every block** (0 exceptions), i.e. a block-level split |

Example row (first group): block `gillian, brown`, ORCID `0000-0002-0675-0780`, DOI `10.1038/srep02486`, `pid` 2062065860, author name "Gillian Ruth Brown", year 2013, split 1.

## 4. `pid` interpretation

- **Documented:** the README says `pid` is the paper ID in Microsoft Academic / Microsoft Academic Graph [V]. The Zenodo v2.0 page says v2.0 is built on OpenAlex but never mentions `pid` [V].
- **Observed:** integer values up to 3.2 billion; 189 DOIs carry two different `pid`s (duplicate paper records for one DOI) while no `pid` carries two DOIs [V in the sample].
- **Assessment:** the values behave like **Microsoft Academic Graph paper IDs**, not a one-to-one OpenAlex work key [I]. Duplicate paper records for one DOI is a property of a graph with unmerged duplicates; it is the pattern I would expect from MAG-derived identifiers and not from a deduplicated work table. Years go up to 2022, so even in v2.0 the paper IDs are MAG-era in this file.
- **Not established:** whether `W` + `pid` equals the OpenAlex work ID for these papers. OpenAlex documents an `ids.mag` field on works ([works object](https://help.openalex.org/api-entities/works/work-object)), which suggests a mapping route, but whether it is exact is **[U]** and cannot be tested without an OpenAlex request. **`doi` is the safer join key** (100% populated, clean format in the sample); duplicates must be collapsed first.

## 5. ORCID label construction

**What the sources say [V]:**
- Labels are built **automatically** from "the two authoritative sources, ORCID and DOI": the pipeline queries DOIs by ORCID iD and ORCID iDs by DOI. No human intervention is used ([GitHub README](https://github.com/carmanzhang/LAGOS-AND/blob/main/README.md); [Zenodo v2.0](https://zenodo.org/records/7313353)).
- Block name = the ORCID "credible full name"; each ORCID author in a block is a citation group. `author_position` is "identified by heuristics" (not manually verified).
- Validation claimed: similarity to the whole MAG across six facets; synonym patterns and domains as the main checks; baselines evaluated, including MAG's author ID system ([arXiv abstract](https://export.arxiv.org/abs/2104.01821)).
- v2.0 is described as "ORCID+OpenAlex": built on OpenAlex because MAG was discontinued on 31 December 2021; v2.0 improves pairwise class-label accuracy. **The Zenodo page defines nothing further.**

**What I could not establish:**
- How the ORCID-to-DOI records were collected (public data file or API, snapshot date). The README says "two comprehensive resources" without naming them [U].
- Whether OpenAlex or MAG **author** IDs were used anywhere in label construction. None of the sources I could read states that they were, and no author-ID column exists in the file [V absence]; but the full paper was not readable in this task (the PDF and the publisher page were not accessible), so this is **[U]**, not a negative finding.
- Which source supplies the publication metadata in v2.0's rows: the observed `pid` values point to MAG-era IDs [I], while the record says OpenAlex.

## 6. Circularity assessment

Matching a benchmark ORCID to the `orcid` field of an OpenAlex author profile is **not an independent test of identity correctness**, for these reasons:
1. The benchmark's ORCID-DOI links are claims in ORCID records (author- or publisher-asserted), not verified identities. **[V: stated construction]**
2. OpenAlex attributes ORCIDs to author profiles from its own ORCID-linked works. If those are the same ORCID-DOI assertions, then "candidate carries the group ORCID" restates the system's existing attribution rather than testing it. How OpenAlex assigns ORCIDs to authors was **not examined here** **[U]**, but the dependence is plausible **[I]**.
3. An OpenAlex profile that is a fragment can carry the ORCID for a few works only; matching the ORCID string would then count a fragment as the correct person.
4. Publication overlap on DOIs from the same group would partly reproduce the label.

Therefore ORCID equality can serve as a **convenient automatic label with a measured error rate**, not as ground truth by itself. A manual audit of a sample (two reviewers using non-OpenAlex evidence) is required to estimate that error rate, and DOI-based context must stay exploratory as in the existing C1x design.

## 7. DOI and coauthor findings relevant to HAMMER
- **DOI quality: good** in the sample (clean, lower-case, no prefix); duplicates exist (195 rows, same ORCID group) and need collapsing by DOI before use.
- **Coauthors are name-only:** under the approved policy (OpenAlex author IDs only), the coauthor signal is **not supported** by this dataset, and the author's own name sits inside the list and must be removed from any context.
- **Institution** is a free-text string (85% populated, some artifacts): usable through token-sort name matching only.
- **Year** is a single publication year per row; an active-year range needs several rows of the group.
- **Splits:** a block-level split flag exists in the file (undocumented); whether it is balanced or sensible beyond the prefix is unknown. HAMMER does not train, so the flag is only useful for reporting and for keeping development and evaluation blocks apart.

## 8. Remaining unknowns
- Full-file row counts, how many ORCID groups have at least two or three citations, and the overall block and split distribution (the prefix is name-sorted and non-random).
- What TRIMMED removes relative to BLOCK.
- Whether `pid` joins to OpenAlex through `ids.mag`, and the fraction of DOIs found in OpenAlex.
- Whether OpenAlex author profiles carry these ORCIDs and how often profiles are fragmented.
- The paper's own account of label error and its limitations (unreadable here).
- MD5 of the full file (needs the full download).

## 9. Storage and access consequences
- Extracted size is 2.43 GB [V]; the compressed file is 0.74 GB. With 17 GiB free this is manageable.
- The gzip stream cannot be sampled randomly by byte offset. **A random sample of blocks needs the full 0.74 GB read sequentially** (it can be streamed and reduced without keeping the 2.4 GB CSV). A prefix slice is possible at no extra cost but is not random.

## 10. Recommendation: **proceed with restrictions**

The data are technically suitable for the part of RQ2 they can support: clean DOIs, printed author names with variants, affiliation text and year, ORCID-defined groups, true homonym blocks, and a block-level split flag, all verified in the sample. They are **not** suitable for the coauthor signal, for independent ground truth by ORCID matching alone, or for claims about unresolved identities.

**Restrictions before any sampler work:**
1. Treat ORCID-to-OpenAlex matching as an **automatic label with a measured error rate**, and budget a manual audit.
2. Join on **`doi`**, not on `pid`; collapse duplicate DOIs; do not call `pid` an OpenAlex ID.
3. Keep DOI overlap exploratory; primary C1 uses institution and years only.
4. Exclude the coauthor signal; strip the author's own name from any context.
5. Use a random block sample, which needs a one-time full sequential read (0.74 GB) **after the director approves that download**; do not generalise from the prefix.
6. Pin version 2.0, the DOI `10.5281/zenodo.7313353` and the file's MD5.
7. Resolve the three unknowns in section 8 on a bounded sample (about 50 queries) before committing to a sample size.

**Not rejected, because** no verified fact disqualifies it. **Not unrestricted, because** the label-independence question (section 6) is open and the file schema departs from its documentation.
