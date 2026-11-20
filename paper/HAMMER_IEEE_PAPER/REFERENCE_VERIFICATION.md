# Reference verification (Stage 1)

**Scope.** Bibliographic metadata of every entry in `references.bib` was re-checked on 20 Nov 2026 against Crossref (DOI records), arXiv, the Zenodo API, and the JMLR/PMLR pages. **Metadata verification is not the same as reading the paper.** "Inspection" is the depth reached by the project literature inventory (`docs/research/paper_preparation/LITERATURE_MATRIX.csv`); no paper was read in full. Before the manuscript attributes a specific finding to a source, read the source.

Inspection codes: **M** metadata only; **A** abstract-level summary; **P** described by the earlier repository audit, not re-read.

| Key | Verified against | Inspection | Notes |
|---|---|---|---|
| fellegi1969recordlinkage | Crossref | P | Foundation only |
| elmagarmid2007duplicate | Crossref | M | General survey citation only |
| forbes2024deduplicator | Crossref | P | Work-level dedup |
| papadakis2020blocking | Crossref | M | Background only |
| ferreira2012brief | Crossref | M | Ferreira, Gonçalves, Laender (SIGMOD Rec.). Not the unresolved "Ferreira/Han" item |
| rodrigues2024andreview | Crossref | P | IJDL 25(4); authors Rodrigues, Mariano, Ralha |
| debonis2023graph | Crossref | M | |
| han2004twosupervised | Crossref | M | Pages 296--305 added from Crossref |
| torvik2009authority | Crossref | M | Page range 1--29 as given by Crossref |
| tang2012unified | Crossref | M | TKDE 24(6) 975--987 |
| tian2024pubmedcomputedauthors | Crossref | P | |
| zhang2021aggand | Crossref | P | Authors Zhang, Huang, Yang, Lu (corrected earlier) |
| boukhers2024deepdblp | Crossref | P | Online 2023; volume 25(3) is a 2024 issue |
| choi2024heterogeneoussites | Crossref | P | Choi et al.; Appl. Sci. 14(1):192. Crossref's issue date is Dec 2023 (online); volume year 2024 used |
| zhang2018aminerhitl | Crossref | P | Pages 1002--1011 (missing in the older .bib) |
| chen2020conna | Crossref, arXiv, DBLP | A | TKDE 34(7):3139--3152, **2022** (arXiv v1 2019). The matrix earlier called it "not verified" |
| subramanian2021s2and | Crossref | A | |
| chen2023whoiswho | Crossref | A | |
| zhang2023lagosand | Crossref | P | Online 2022, vol. 74 (2023) |
| zhang2022lagosandv2 | Zenodo API | M | See open items |
| vishnyakova2019gsd1900 | Crossref | M | |
| muller2017datasets | Crossref | M | Claim limited to "datasets have been examined" |
| kim2018dblp | Crossref | M | Claim limited to "evaluation has been examined" |
| priem2022openalex | arXiv | P | Preprint, no peer-reviewed venue found |
| culbert2025openalexcoverage | Crossref | P | |
| duran-silva-etal-2024-affilgood | Crossref | P | DOI 10.18653/v1/2024.sdp-1.13 now recorded |
| kallipoliti2025affro | Crossref | P | First online 2025 |
| buneman2001whyandwhere | Crossref | M | LNCS volume number not retrieved, so omitted |
| chow1970reject | Crossref | M | Crossref gives "C. Chow"; "C. K. Chow" follows the inventory |
| elyaniv2010foundations | JMLR page (HTTP 200) | A | No DOI |
| geifman2019selectivenet | PMLR page (HTTP 200) | A | No DOI |
| hendrickx2024reject | Crossref | M | Used for terminology only |
| chen2018humo | Crossref | A | ICDE 2018, DOI 10.1109/ICDE.2018.00107 (was arXiv-only) |
| hou2020rhumo | Crossref | A | TKDE 32(2):347--359 (was arXiv-only) |
| wang2012crowder | Crossref | M | Crossref's short title is "CrowdER"; full title as on the arXiv/VLDB record |

## Open items
1. **LAGOS-AND dataset DOI.** The inventory listed `10.5281/zenodo.7313380`. The record we downloaded and checked is `10.5281/zenodo.7313353` (version 2.0 "ORCID+OpenALex", titled "...for MAG/OpenAlex Author Name Disambiguation", published 2022-06-25, CC BY 4.0; concept DOI `10.5281/zenodo.4568623`). The Zenodo record lists one creator (Li Zhang), whereas the JASIST paper lists three authors; the manuscript cites the dataset record and the paper separately. Confirm which the dataset's own citation request prefers.
2. **"Ferreira/Han"** (from the earlier inventory) remains unresolved and is **not** cited.
3. **Choi et al. year.** Crossref dates the online publication Dec 2023; volume 14 is 2024. Decide the house convention (the current entry uses 2024).
4. **Table I** (`tables/literature_comparison.tex`) and the Related Work text rely on abstract-level readings for S2AND, WhoIsWho, CONNA, HUMO and others. Read each before submission. In particular confirm the evaluation family stated for S2AND, WhoIsWho and CONNA, and the "eight datasets" and "more than one million papers" figures.
5. **Absence statements** ("we did not find ...") are limited to the project inventory. Run the follow-up searches listed in `LITERATURE_SEARCH_LOG.md` before the paper keeps them.
6. No BibTeX style problems could be checked without a compiler; see README.


## Added 20 November 2026 (statistical references for Section 5)
Each entry below was fetched from the Crossref API on 20 November 2026 and the title, authors, year, venue, volume, issue and pages were compared with the BibTeX entry. No DOI was typed from memory.
| Key | DOI | Verified fields |
|---|---|---|
| clopper1934 | 10.1093/biomet/26.4.404 | Clopper and Pearson, Biometrika 26(4), 404-413, 1934 |
| cohen1960kappa | 10.1177/001316446002000104 | Cohen, Educational and Psychological Measurement 20(1), 37-46, 1960 |
| efron1979bootstrap | 10.1214/aos/1176344552 | Efron, Annals of Statistics 7(1), 1-26, 1979 |
| horvitz1952 | 10.1080/01621459.1952.10483446 | Horvitz and Thompson, JASA 47(260), 663-685, 1952 |
| jeffreys1946 | 10.1098/rspa.1946.0056 | Jeffreys, Proc. Royal Society A 186(1007), 453-461, 1946 |
The papers were verified at metadata level only; none was read in full for this manuscript.


## Claim-level check of five key sources (20 November 2026, T018)
Method: the abstract pages and the readable HTML or text of each paper on arXiv were read through a fetch agent; where the agent could not read the full text it said so, and its answers marked "summary" were not treated as verified. The JASIST version of the LAGOS-AND paper (Wiley) returned HTTP 403 and was **not** read; the description of LAGOS-AND rests on the arXiv preprint (2104.01821) and the Zenodo record.
| Key | Project statement | Verdict | Correction made in the manuscript |
|---|---|---|---|
| subramanian2021s2and | consolidates eight datasets into a uniform format; single-dataset models may generalize poorly; B-cubed F1; no retrieval, abstention or assign-or-new stage in the text read | supported | "often transfer poorly" changed to "may generalize poorly" |
| chen2023whoiswho | more than one million papers; a real-time assignment task (new paper to existing authors, NIL allowed); weighted precision, recall and F1, pairwise F1, AUC and MAP; no retrieval-stage measure found | supported | Table I: evidence "Curated benchmark labels" and measures "F1, AUC and MAP, by task" (the earlier "interactive annotation" was not verified) |
| chen2020conna | matches to the top candidate, then assign or create a new person; deployed on AMiner; arXiv comment says accepted by TKDE 2020 (journal volume 34 is 2022 per Crossref) | supported with a caveat | "trained jointly" changed to jointly fine-tuned by reinforcement learning after separate training |
| chen2018humo, hou2020rhumo | machine and human workload division with precision and recall targets; r-HUMO adds risk analysis; evaluated on entity-resolution data (for example DBLP-Scholar), not author disambiguation | supported | none; the text already says entity resolution in general |
| zhang2023lagosand, zhang2022lagosandv2 | ORCID and DOI as label sources; version 2.0 moves the literature source from MAG to OpenAlex | partly supported | "blocks" now qualified ("including a block subset"); LAGOS-AND-PAIRWISE is a separate labelled-pair subset; how each record's ORCID was established could not be read and is stated as such |
Open: the TKDE year of CONNA (arXiv 2020, Crossref issue 2022) is left as the Crossref value; r-HUMO's journal venue is not shown on arXiv and rests on Crossref. The absence statements ("we did not find ...") remain limited to the project inventory, as the manuscript now says.
