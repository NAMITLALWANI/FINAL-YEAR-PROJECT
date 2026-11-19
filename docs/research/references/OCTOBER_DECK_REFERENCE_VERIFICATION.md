# October deck: reference verification report

**Scope:** Ten numbered slide 11 references, the eight identifiable slide 3 papers, the generic incomplete slide 3 citation, and the unnumbered GSD1900 source needed to interpret slide 10.  
**Method:** Verified bibliographic metadata and material claims against publisher, PubMed/PMC, ACL Anthology, arXiv or proceedings records. Links below lead to those primary records/full texts.  
**Status vocabulary:** **Verified** = title/authors/year/venue/identifier checked at a primary source; **Corrected** = deck metadata or claim is wrong; **Unverified** = the source or assertion is not identifiable/supported from checked material.  
**BibTeX:** There was no .bib library in the checkout before this audit. Verified entries below are now in HAMMER_REFERENCES.bib. The generic “Ferreira et al.; Han et al.” row has no entry because its papers cannot be identified from the deck.

## Numbered references from slide 11

### [1] PubMed Computed Authors

**Deck:** Y. Tian et al., “PubMed Computed Authors in 2024: An Open Resource of Disambiguated Author Names in Biomedical Literature,” Bioinformatics, 2024.

**Verified citation:** Shubo Tian, Qingyu Chen, Donald C. Comeau, W. John Wilbur and Zhiyong Lu. “PubMed Computed Authors in 2024: an open resource of disambiguated author names in biomedical literature.” Bioinformatics 40(11), btae672 (2024). DOI 10.1093/bioinformatics/btae672.

**Method/findings:** A PubMed-scale author resource with ORCID integration and regular updates. It reports over 21 million disambiguated authors from over 163 million author instances in nearly 36 million PubMed articles. It evaluates 40,000 ORCID-linked authors and also compares systems on GSD1900.

**Limit/relevance:** Biomedical/PubMed domain and the available labels/identifiers constrain generalization. It is a relevant deployed multi-signal resource and a useful benchmark context; it is not evidence for HAMMER’s results. The article’s GSD1900 accuracy values are pairwise accuracy, not top-1 candidate-ranking metrics.

**RQ/section fit:** RQ2 related work and benchmark provenance; source aggregation and author identity evaluation.

**Verification:** **Verified; deck title is substantially correct.**  
**Full text:** [PMC open full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC11588201/); [publisher record](https://academic.oup.com/bioinformatics/article/40/11/btae672/7888882). No local full-text copy was found in this checkout.

### [2] AggAND

**Deck:** V. I. Torvik and N. R. Smalheiser, “Aggregating Large-Scale Databases for PubMed Author Name Disambiguation,” JAMIA, 2021.

**Verified citation:** Li Zhang, Yong Huang, Jinqing Yang and Wei Lu. “Aggregating large-scale databases for PubMed author name disambiguation.” Journal of the American Medical Informatics Association 28(9), 1919–1927 (2021). DOI 10.1093/jamia/ocab095.

**Method/findings:** Aggregates external information from Microsoft Academic Graph, Semantic Scholar and PubMed Knowledge Graph to enrich names and identifiers, then evaluates AggAND. Reported F1 is 95.80% and 93.71% on two PubMed datasets.

**Limit/relevance:** The evaluation is PubMed-centered and depends on available external metadata. It directly shows that cross-database enrichment for author disambiguation is established prior work; it weakens a broad claim that HAMMER is the first multi-source author-resolution system.

**RQ/section fit:** RQ2 related work; metadata provenance and candidate evidence.

**Verification:** **Corrected authorship.** The deck has conflated this citation with Torvik and Smalheiser’s Author-ity work.  
**Full text:** [PMC open full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC8363810/); [PubMed record](https://pubmed.ncbi.nlm.nih.gov/34180522/). No local copy found.

### [3] Deep author name disambiguation using DBLP data

**Deck:** Zeyd Boukhers and Nagaraj Asundi, 2023, “Deep Author Name Disambiguation Using DBLP Data.”

**Verified citation:** Zeyd Boukhers and Nagaraj Bahubali Asundi. “Deep author name disambiguation using DBLP data.” International Journal on Digital Libraries 25, 431–441 (2024); published online 4 May 2023. DOI 10.1007/s00799-023-00361-6.

**Method/findings:** Groups same-surname/first-initial records and trains neural classifiers using Char2Vec author-name/coauthor representations and BERT embeddings for title/source context. The study uses over five million DBLP records and reports experiments on a large dataset.

**Limit/relevance:** The authors explicitly say their approach does not properly handle new authors; this supports the slide’s closed-set limitation. The paper also relies on DBLP data, whose accuracy is not guaranteed. The slide’s scalability limitation needs a specific discussion passage; do not assert it as a stated limitation without one.

**RQ/section fit:** RQ2 related work; evidence signals and open-set handling.

**Verification:** **Verified with publication-year clarification.** “2023” is the online-publication year; volume year is 2024.  
**Full text:** [Springer open full text and PDF](https://link.springer.com/article/10.1007/s00799-023-00361-6). No local copy found.

### [4] Name Disambiguation Scheme Based on Heterogeneous Academic Sites

**Deck:** X. Li et al., 2024; says hybrid rule+ML, with “no fusion strategy.”

**Verified citation:** Dojin Choi, Junhyeok Jang, Sangho Song, Hyeonbyeong Lee, Jongtae Lim, Kyoungsoo Bok and Jaesoo Yoo. “Name Disambiguation Scheme Based on Heterogeneous Academic Sites.” Applied Sciences 14(1), 192 (2024). DOI 10.3390/app14010192.

**Method/findings:** Combines metadata from several Korean academic sites, uses clustering/rule and learned disambiguation schemes, and trains a multi-classifier to select the appropriate scheme based on available metadata. The paper reports results for its own dataset and setup.

**Limit/relevance:** The paper states that evaluation data are available on request and are not public because they were provided by a company. A language expansion is future work. The slide’s “no fusion strategy” statement is **contradicted**: the multi-classifier selector is explicitly described.

**RQ/section fit:** RQ2 related work; heterogeneous metadata and missing-field adaptation.

**Verification:** **Corrected authorship; contradiction found in limitation summary.**  
**Full text:** [MDPI open full text/PDF](https://www.mdpi.com/2076-3417/14/1/192). No local copy found.

### [5] Author name disambiguation literature review with consolidated meta-analytic approach

**Deck:** S. Kumar et al., 2024; says the review has no implementation framework.

**Verified citation:** Natan S. Rodrigues, Ari M. Mariano and Celia G. Ralha. “Author name disambiguation literature review with consolidated meta-analytic approach.” International Journal on Digital Libraries 25, 765–785 (2024). DOI 10.1007/s00799-024-00398-1.

**Method/findings:** Review of 211 documents indexed in Web of Science and Scopus from 2003–2022. It organizes work around author grouping with similarity/clustering and author assignment with classification.

**Limit/relevance:** The authors characterize the paper as an exploratory overview rather than a protocol-driven systematic review with specified research questions. It is a source for taxonomy and history, not an implementation framework.

**RQ/section fit:** Related-work opening and taxonomy; not a performance baseline.

**Verification:** **Corrected authorship.** The slide’s broad observation that a review is not an implementation framework is fair, but should not be framed as an unmet research problem.  
**Full text:** [Springer open full text/PDF](https://link.springer.com/article/10.1007/s00799-024-00398-1). No local copy found.

### [6] AffilGood

**Deck:** N. Duran-Silva et al., 2024, “AffilGood: Building Reliable Institution Name Disambiguation Tools to Improve Scientific Literature Analysis.”

**Verified citation:** Nicolau Duran-Silva, Pablo Accuosto, Piotr Przybyła and Horacio Saggion. “AffilGood: Building reliable institution name disambiguation tools to improve scientific literature analysis.” Proceedings of the Fourth Workshop on Scholarly Document Processing (SDP 2024), 135–144. Association for Computational Linguistics, 2024. ACL Anthology ID 2024.sdp-1.13.

**Method/findings:** Provides tools and labeled datasets for affiliation-span extraction, organization/location named-entity recognition and seven ROR entity-linking datasets.

**Limit/relevance:** It resolves organizations from affiliation text, not full author identity. The deck’s department-level distinction is a task-scope boundary; it is not evidence of a defect in the paper.

**RQ/section fit:** RQ2 supporting evidence on institution features; system scope/limitations.

**Verification:** **Verified.**  
**Full text:** [ACL Anthology page and PDF](https://aclanthology.org/2024.sdp-1.13/). No local copy found.

### [7] From Raw Affiliations to Organization Identifiers

**Deck:** M. Kallipoliti et al., 2024.

**Verified citation:** Myrto Kallipoliti, Serafeim Chatzopoulos, Miriam Baglioni, Eleni Adamidi, Paris Koloveas and Thanasis Vergoulis. “From Raw Affiliations to Organization Identifiers.” In Linking Theory and Practice of Digital Libraries (TPDL 2025), Lecture Notes in Computer Science 16097, 111–126. Springer, first online 15 September 2025. DOI 10.1007/978-3-032-05409-8_8.

**Method/findings:** Introduces AffRo for mapping raw affiliation strings to organization IDs and AffRoDB, an expert-curated evaluation dataset. It addresses strings containing multiple organizations or extraneous material.

**Limit/relevance:** Directly relevant to affiliation normalization and canonical organization IDs. The deck’s 2024 date is wrong for the conference paper; the arXiv preprint is from May 2025.

**RQ/section fit:** RQ2 supporting signal; affiliation subtask and scope.

**Verification:** **Corrected year.**  
**Full text:** [arXiv open full text/PDF](https://arxiv.org/abs/2505.07577); [Springer version of record](https://link.springer.com/chapter/10.1007/978-3-032-05409-8_8). No local copy found.

### [8] Deduplicator

**Deck:** C. Forbes et al., 2024, “Deduplicator: Duplicate Record Detection.”

**Verified citation:** Connor Forbes, Hannah Greenwood, Matt Carter and Justin Clark. “Automation of duplicate record detection for systematic reviews: Deduplicator.” Systematic Reviews 13, article 206 (2024). DOI 10.1186/s13643-024-02619-9.

**Method/findings:** Compares a balanced Deduplicator algorithm with semi-manual EndNote deduplication on ten previous Cochrane systematic-review libraries, using two researchers in a crossover design. The paper reports high F1 for its tested configurations and reduced review time.

**Limit/relevance:** The task is publication-record deduplication across systematic-review search libraries. The authors note the possibility of shared reviewer mistakes; the study is bounded to ten libraries and two reviewers. “Not designed for institutional dashboards” is an application difference, not a scientific limitation.

**RQ/section fit:** Conditional RQ1 related work; publication equivalence must remain separate from author identity.

**Verification:** **Corrected title.**  
**Full text:** [Springer open full text/PDF](https://link.springer.com/article/10.1186/s13643-024-02619-9). No local copy found.

### [9] Reference coverage of OpenAlex

**Deck:** J. Culbert et al., 2024, “Reference Coverage Analysis of OpenAlex Compared to Web of Science and Scopus.”

**Verified citation:** Jack H. Culbert, Anne Hobert, Najko Jahn, Nick Haupka, Marion Schmidt, Paul Donner and Philipp Mayr. “Reference coverage analysis of OpenAlex compared to Web of Science and Scopus.” Scientometrics 130, 2475–2492 (2025). DOI 10.1007/s11192-025-05293-3. A 2024 preprint is arXiv:2401.16359.

**Method/findings:** Compares reference coverage and selected metadata on a cleaned corpus of 16.8 million recent publications present in all three sources. In that shared corpus, OpenAlex’s average reference counts and internal coverage are comparable to Web of Science and Scopus; other metadata comparisons vary by journal.

**Limit/relevance:** Conditioning on works shared by all three databases does not establish coverage over the full scholarly universe. This is evidence about metadata source coverage and provenance, not author identity resolution.

**RQ/section fit:** System context and RQ2 data-source limitations; not a resolver baseline.

**Verification:** **Corrected version-of-record year.** 2024 is the preprint year; journal version is 2025.  
**Full text:** [arXiv open full text/PDF](https://arxiv.org/abs/2401.16359); [Springer version of record](https://link.springer.com/article/10.1007/s11192-025-05293-3). No local copy found.

### [10] Dataset citation coverage across sources

**Deck:** “Comparison of Dataset Citation Coverage in Google Scholar, Web of Science, Scopus, Crossref, and DataCite,” Scientometrics, 2024.

**Verified citation:** Irina Gerasimov, Binita KC, Armin Mehrabian, James G. Acker and Michael P. McGuire. “Comparison of datasets citation coverage in Google Scholar, Web of Science, Scopus, Crossref, and DataCite.” Scientometrics 129, 3681–3704 (2024). DOI 10.1007/s11192-024-05073-5.

**Method/findings:** Examines citation coverage for NASA Earth Observing System Data and Information System dataset DOIs across five sources. It studies approximately 11,000 dataset DOIs and reports Google Scholar as the broadest source and Crossref as substantially less complete in this setting.

**Limit/relevance:** The unit is citations to NASA EOSDIS datasets, not general article-metadata agreement or author identity. It supports a carefully bounded point about source-dependent coverage.

**RQ/section fit:** Introduction/data provenance; do not use it as author-disambiguation evidence.

**Verification:** **Verified; correct title is plural “datasets.”**  
**Full text:** [Springer open full text/PDF](https://link.springer.com/article/10.1007/s11192-024-05073-5). No local copy found.

## Unnumbered source needed for slide 10: GSD1900

**Verified citation:** Dina Vishnyakova, Raul Rodriguez-Esteban and Fabio Rinaldi. “A new approach and gold standard toward author disambiguation in MEDLINE.” Journal of the American Medical Informatics Association 26(10), 1037–1045 (2019). DOI 10.1093/jamia/ocz028.

**Method/findings:** Introduces a 1,900-publication-pair MEDLINE gold standard built with crowdsourced and expert curation, designed to better reflect the database than earlier convenience datasets. It contains 1,500 pairs used for training/validation and a separate 400-pair never-seen final test set. The benchmark is pairwise. The 2024 Computed Authors paper notes that easy pairs were excluded.

**Limit/relevance:** GSD1900 is a benchmark, not a HAMMER result. The 92.2% accuracy shown in the 2024 Computed Authors article is that system’s accuracy on its 400-pair test subset; the same table reports 91.0% accuracy over all 1,900 pairs. It is not a top-1 author-candidate ranking score. No local copy of GSD1900 or HAMMER row-level predictions was found in the checkout.

**RQ/section fit:** RQ2 benchmark provenance and limitation discussion.

**Verification:** **Verified primary source; omitted from slide 11 despite slide 10 using the dataset.**  
**Full text:** [PMC open full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC7647200/); [publisher record](https://academic.oup.com/jamia/article/26/10/1037/5432091).

## Incomplete slide 3 row: classical methods

The row “Classical Rule-Based AND Methods” names “Ferreira et al.; Han et al.” but gives no exact titles, years, venues or stable identifiers. These are not enough to identify works reliably. **Unverified; no BibTeX entry created.** Supply the intended citations before retaining this row in a manuscript.

## Repository and access notes

Before this report, the checkout had a Markdown reference audit but no BibTeX library. This audit creates an additive BibTeX file at [HAMMER_REFERENCES.bib](HAMMER_REFERENCES.bib). Publisher/author-hosted full-text links are supplied above; none of these papers was downloaded into the checkout. “No local copy found” refers only to this project repository.

