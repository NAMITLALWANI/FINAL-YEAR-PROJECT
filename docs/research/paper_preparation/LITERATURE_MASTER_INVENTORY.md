# HAMMER literature master inventory

**Status:** Research-preparation document. Not manuscript text.  
**Prepared:** 19 November 2026 for the repository at commit `bee7eabfba2d88c4a03c12d227ac6b04624fb8c8`.  
**Companion files:** `LITERATURE_MATRIX.csv` (same rows, machine-readable), `LITERATURE_SEARCH_LOG.md`, `RESEARCH_GAP_AND_POSITIONING.md`.  
**Existing bibliography:** `docs/research/references/HAMMER_REFERENCES.bib` was read and **not modified**. Proposed additions below are not yet in any `.bib` file.

## 1. How to read this inventory

This task reused the existing audit (`HAMMER_REFERENCE_VERIFICATION.md`, `LITERATURE_REVIEW_MATRIX.md`, `GAP_REASSESSMENT_AND_CITATION_MAP.md`) and added a limited, targeted extension. **No source was read in full in this task.** Three evidence levels are kept apart:

| Code | Meaning |
|---|---|
| `VT` | Metadata verified in this task (DOI/publisher/proceedings record) |
| `VTA` | arXiv or search-listing record checked in this task; formal venue metadata not fully confirmed |
| `VP` | Metadata verified in prior repo audit; not re-fetched in this task |

| Code | Inspection level |
|---|---|
| `M` | Metadata only |
| `MA` | Metadata + abstract-level summary (fetch-tool summary, not read by hand) |
| `P` | Content described by prior repo audit; not re-inspected here |

Rules applied: where a field says *Not inspected in this task*, nothing was written from memory about the paper's method or results. Where content is described, it is attributed either to the earlier repository audit or to an abstract-level summary returned by a fetch tool. **Abstract summaries produced by a tool are not a substitute for reading the paper**; every row marked `MA` or `P` must be checked against the actual text before a specific claim is attributed to it in the manuscript.

## 2. Counts

| Item | Count |
|---|---:|
| Rows in this inventory | 40 |
| Already in `HAMMER_REFERENCES.bib` | 18 |
| New to the bibliography (proposed) | 22 |
| Metadata verified in this task (`VT`) | 22 |
| arXiv/search-listing level in this task (`VTA`) | 6 |
| Metadata verified only in the prior audit (`VP`) | 12 |
| Abstract-level summary seen in this task (`MA`) | 9 |
| Read in full in this task | 0 |
| Unverified leads listed but not included | 9 |

The eight deck papers (Boukhers & Asundi; Tian et al.; Choi et al.; Rodrigues et al.; AggAND; AffilGood; AffRo; Deduplicator), plus the deck's two source-coverage papers (Culbert et al.; Gerasimov et al.) and GSD1900, are all among the 18 existing entries.

## 3. Coverage by research cluster

A paper may appear in more than one cluster. Depth is a count of rows, not a judgement of coverage quality.

| Cluster | Rows | Verified-in-task rows | Assessment |
|---|---:|---:|---|
| 1 Author name disambiguation | 16 | 11 | Reasonable breadth (two surveys, early supervised work, several systems). Most rows beyond the existing audit are metadata-only. |
| 2 Benchmarks and ground truth | 7 | 6 | Good for S2AND, WhoIsWho, LAGOS-AND, GSD1900; the 2017-era benchmark-quality studies are metadata-only. |
| 3 Candidate generation and retrieval | 6 | 4 | **Thin.** Only a blocking survey, CONNA, WhoIsWho's assignment task and OpenAlex context. No source found that reports Recall@k for an author-candidate stage. |
| 4 Evidence-based identity resolution | 13 | 6 | Adequate for signals; weak on how evidence weights are chosen or validated beyond Tang et al. and Fellegi-Sunter. |
| 5 Selective prediction, abstention, human review | 11 | 11 | General selective-prediction foundations are good; **author-disambiguation-specific abstention evidence is thin** (AMiner HITL, CONNA, HUMO line). |
| 6 Metadata integration and provenance | 14 | 5 | Adequate for source coverage and dedup; provenance is covered by one classic reference. |

## 4. Reference records by cluster

Each record is deliberately short. Full structured fields are in `LITERATURE_MATRIX.csv`.

### Cluster 1 Author name disambiguation

| Key | Citation | Check | Inspection | In bib | Role for HAMMER |
|---|---|---|---|---|---|
| `tian2024pubmedcomputedauthors` | Tian, S.; Chen, Q.; Comeau, D. C.; Wilbur, W. J.; Lu, Z. (2024). PubMed Computed Authors in 2024: An Open Resource of Disambiguated Author Names in Biomedical Literature. Bioinformatics 40(11), btae672. | `VP` | `P` | Yes | Prior system and benchmark context; source of the 92.2% / 91.0% figures that must not be read as HAMMER top-1 results. |
| `zhang2021aggand` | Zhang, L.; Huang, Y.; Yang, J.; Lu, W. (2021). Aggregating Large-Scale Databases for PubMed Author Name Disambiguation. J. American Medical Informatics Association 28(9), 1919-1927. | `VP` | `P` | Yes | Direct prior art for multi-source author evidence; weakens any 'first multi-source' claim. |
| `boukhers2024deepdblp` | Boukhers, Z.; Asundi, N. B. (2024 (online 2023-05-04)). Deep Author Name Disambiguation Using DBLP Data. Int. J. on Digital Libraries 25, 431-441. | `VP` | `P` | Yes | Signals used (name, coauthor, title/source context) and the new-author boundary. |
| `choi2024heterogeneoussites` | Choi, D.; Jang, J.; Song, S.; Lee, H.; Lim, J.; Bok, K.; Yoo, J. (2024). Name Disambiguation Scheme Based on Heterogeneous Academic Sites. Applied Sciences 14(1), 192. | `VP` | `P` | Yes | Missing-metadata handling and multi-source prior art. |
| `rodrigues2024andreview` | Rodrigues, N. S.; Mariano, A. M.; Ralha, C. G. (2024). Author Name Disambiguation Literature Review with Consolidated Meta-Analytic Approach. Int. J. on Digital Libraries 25, 765-785. | `VP` | `P` | Yes | Opening taxonomy; not a baseline. |
| `subramanian2021s2and` | Subramanian, S.; King, D.; Downey, D.; Feldman, S. (2021). S2AND: A Benchmark and Evaluation System for Author Name Disambiguation. Proc. ACM/IEEE Joint Conf. on Digital Libraries (JCDL), 170-179. | `VT` | `MA` | Yes | Core benchmark reference; supports identity-disjoint splits and cross-dataset caution. |
| `chen2023whoiswho` | Chen, B.; Zhang, J.; Zhang, F.; Han, T.; Cheng, Y.; Li, X.; Dong, Y.; Tang, J. (2023). Web-Scale Academic Name Disambiguation: The WhoIsWho Benchmark, Leaderboard, and Toolkit. Proc. 29th ACM SIGKDD Conf. (KDD '23), 3817-3828. | `VT` | `MA` | Yes | Shows large-scale benchmarks and online assignment already exist; do not claim their absence. |
| `zhang2018aminerhitl` | Zhang, Y.; Zhang, F.; Yao, P.; Tang, J. (2018). Name Disambiguation in AMiner: Clustering, Maintenance, and Human in the Loop. Proc. 24th ACM SIGKDD Int. Conf. (KDD '18), 1002-1011. | `VT` | `P` | Yes (pages missing in bib; use 1002-1011) | Direct prior art for human-in-the-loop AND; HAMMER's novelty cannot be 'has a reviewer'. |
| `ferreira2012brief` | Ferreira, A. A.; Gonçalves, M. A.; Laender, A. H. F. (2012). A Brief Survey of Automatic Methods for Author Name Disambiguation. ACM SIGMOD Record 41(2), 15-26. | `VT` | `M` | No | Candidate identification of the deck's unidentified 'Ferreira et al.' row; owner must confirm this is the intended work. |
| `han2004twosupervised` | Han, H.; Giles, L.; Zha, H.; Li, C.; Tsioutsiouliklis, K. (2004). Two Supervised Learning Approaches for Name Disambiguation in Author Citations. Proc. 4th ACM/IEEE-CS Joint Conf. on Digital Libraries (JCDL), 296-305. | `VT` | `M` | No | Candidate for the deck's unidentified 'Han et al.' row (several Han et al. AND papers exist); owner must confirm. |
| `torvik2009authority` | Torvik, V. I.; Smalheiser, N. R. (2009). Author Name Disambiguation in MEDLINE. ACM Trans. Knowledge Discovery from Data 3(3), 1-29. | `VT` | `M` | No | Likely the true source of the deck's Torvik & Smalheiser attribution (Author-ity lineage); do not cite for AggAND. |
| `debonis2023graph` | De Bonis, M.; Falchi, F.; Manghi, P. (2023). Graph-Based Methods for Author Name Disambiguation: A Survey. PeerJ Computer Science 9, e1536. | `VT` | `M` | No | Named in the mission's starting list; contextual survey. |
| `sanyal2021review` | Sanyal, D. K.; Bhowmick, P. K.; Das, P. P. (2021 (online 2019)). A Review of Author Name Disambiguation Techniques for the PubMed Bibliographic Database. J. Information Science 47(2), 227-254. | `VT` | `M` | No | Named in the mission's starting list. |
| `kim2018dblp` | Kim, J. (2018). Evaluating Author Name Disambiguation for Digital Libraries: A Case of DBLP. Scientometrics 116(3), 1867-1886. | `VTA` | `M` | No | Evaluation-methodology background for AND benchmarks. |
| `tang2012unified` | Tang, J.; Fong, A. C. M.; Wang, B.; Zhang, J. (2012). A Unified Probabilistic Framework for Name Disambiguation in Digital Library. IEEE Trans. Knowledge and Data Engineering 24(6), 975-987. | `VT` | `M` | No | Example of probabilistic evidence combination in AND; contrast with HAMMER's heuristic weights. |
| `chen2020conna` | Chen, B.; Zhang, J.; Tang, J.; Cai, L.; Wang, Z.; Zhao, S.; Chen, H.; Li, C. (2020 (arXiv v1 2019)). CONNA: Addressing Name Disambiguation on The Fly. Accepted to IEEE TKDE 2020 per arXiv comments; journal volume/pages not verified; arXiv:1910.12202. | `VTA` | `MA` | No | Closest prior art found for 'match then decide whether to assign': narrows novelty of a decision stage after candidate ranking. |

### Cluster 2 Benchmarks and ground truth

| Key | Citation | Check | Inspection | In bib | Role for HAMMER |
|---|---|---|---|---|---|
| `tian2024pubmedcomputedauthors` | Tian, S.; Chen, Q.; Comeau, D. C.; Wilbur, W. J.; Lu, Z. (2024). PubMed Computed Authors in 2024: An Open Resource of Disambiguated Author Names in Biomedical Literature. Bioinformatics 40(11), btae672. | `VP` | `P` | Yes | Prior system and benchmark context; source of the 92.2% / 91.0% figures that must not be read as HAMMER top-1 results. |
| `vishnyakova2019gsd1900` | Vishnyakova, D.; Rodriguez-Esteban, R.; Rinaldi, F. (2019). A New Approach and Gold Standard Toward Author Disambiguation in MEDLINE. J. American Medical Informatics Association 26(10), 1037-1045. | `VT` | `M` | Yes | Provenance of the October deck's dataset; must be cited with exact subset and denominator. |
| `subramanian2021s2and` | Subramanian, S.; King, D.; Downey, D.; Feldman, S. (2021). S2AND: A Benchmark and Evaluation System for Author Name Disambiguation. Proc. ACM/IEEE Joint Conf. on Digital Libraries (JCDL), 170-179. | `VT` | `MA` | Yes | Core benchmark reference; supports identity-disjoint splits and cross-dataset caution. |
| `chen2023whoiswho` | Chen, B.; Zhang, J.; Zhang, F.; Han, T.; Cheng, Y.; Li, X.; Dong, Y.; Tang, J. (2023). Web-Scale Academic Name Disambiguation: The WhoIsWho Benchmark, Leaderboard, and Toolkit. Proc. 29th ACM SIGKDD Conf. (KDD '23), 3817-3828. | `VT` | `MA` | Yes | Shows large-scale benchmarks and online assignment already exist; do not claim their absence. |
| `zhang2023lagosand` | Zhang, L.; Lu, W.; Yang, J. (2023 (online 2022)). LAGOS-AND: A Large Gold Standard Dataset for Scholarly Author Name Disambiguation. J. Assoc. Information Science and Technology 74(2), 168-185. | `VT` | `P` | Yes | Candidate external benchmark; owner decision pending. |
| `muller2017datasets` | Müller, M.-C.; Reitz, F.; Roy, N. (2017). Data Sets for Author Name Disambiguation: An Empirical Analysis and a New Resource. Scientometrics 111(3), 1467-1500. | `VT` | `M` | No | Benchmark-quality background (2017-era benchmark study). |
| `kim2018dblp` | Kim, J. (2018). Evaluating Author Name Disambiguation for Digital Libraries: A Case of DBLP. Scientometrics 116(3), 1867-1886. | `VTA` | `M` | No | Evaluation-methodology background for AND benchmarks. |

### Cluster 3 Candidate generation and retrieval

| Key | Citation | Check | Inspection | In bib | Role for HAMMER |
|---|---|---|---|---|---|
| `culbert2025openalexcoverage` | Culbert, J. H.; Hobert, A.; Jahn, N.; Haupka, N.; Schmidt, M.; Donner, P.; Mayr, P. (2025 (preprint 2024)). Reference Coverage Analysis of OpenAlex Compared to Web of Science and Scopus. Scientometrics 130, 2475-2492. | `VP` | `P` | Yes | Source coverage and provenance context for OpenAlex-only pools. |
| `chen2023whoiswho` | Chen, B.; Zhang, J.; Zhang, F.; Han, T.; Cheng, Y.; Li, X.; Dong, Y.; Tang, J. (2023). Web-Scale Academic Name Disambiguation: The WhoIsWho Benchmark, Leaderboard, and Toolkit. Proc. 29th ACM SIGKDD Conf. (KDD '23), 3817-3828. | `VT` | `MA` | Yes | Shows large-scale benchmarks and online assignment already exist; do not claim their absence. |
| `priem2022openalex` | Priem, J.; Piwowar, H.; Orr, R. (2022). OpenAlex: A Fully-Open Index of Scholarly Works, Authors, Venues, Institutions, and Concepts. arXiv:2205.01833 (preprint). | `VP` | `P` | Yes | Primary source for HAMMER's candidate provider. |
| `papadakis2020blocking` | Papadakis, G.; Skoutas, D.; Thanos, E.; Palpanas, T. (2020). Blocking and Filtering Techniques for Entity Resolution: A Survey. ACM Computing Surveys 53(2), 1-42. | `VT` | `M` | No | Candidate-generation vocabulary and evaluation measures for the retrieval stage; HAMMER's provider-search candidate pool is not a blocking scheme in this sense. |
| `petroni2021kilt` | Petroni, F.; Piktus, A.; Fan, A.; Lewis, P.; Yazdani, M.; De Cao, N.; Thorne, J.; Jernite, Y.; Karpukhin, V.; Maillard, J.; Plachouras, V.; Rocktäschel, T.; Riedel, S. (2021). KILT: a Benchmark for Knowledge Intensive Language Tasks. Proc. NAACL-HLT 2021, 2523-2544 (ACL). | `VT` | `M` | No | Contextual only for retrieval/provenance evaluation of supporting features; proves nothing about HAMMER's citation faithfulness. |
| `chen2020conna` | Chen, B.; Zhang, J.; Tang, J.; Cai, L.; Wang, Z.; Zhao, S.; Chen, H.; Li, C. (2020 (arXiv v1 2019)). CONNA: Addressing Name Disambiguation on The Fly. Accepted to IEEE TKDE 2020 per arXiv comments; journal volume/pages not verified; arXiv:1910.12202. | `VTA` | `MA` | No | Closest prior art found for 'match then decide whether to assign': narrows novelty of a decision stage after candidate ranking. |

### Cluster 4 Evidence-based identity resolution

| Key | Citation | Check | Inspection | In bib | Role for HAMMER |
|---|---|---|---|---|---|
| `tian2024pubmedcomputedauthors` | Tian, S.; Chen, Q.; Comeau, D. C.; Wilbur, W. J.; Lu, Z. (2024). PubMed Computed Authors in 2024: An Open Resource of Disambiguated Author Names in Biomedical Literature. Bioinformatics 40(11), btae672. | `VP` | `P` | Yes | Prior system and benchmark context; source of the 92.2% / 91.0% figures that must not be read as HAMMER top-1 results. |
| `zhang2021aggand` | Zhang, L.; Huang, Y.; Yang, J.; Lu, W. (2021). Aggregating Large-Scale Databases for PubMed Author Name Disambiguation. J. American Medical Informatics Association 28(9), 1919-1927. | `VP` | `P` | Yes | Direct prior art for multi-source author evidence; weakens any 'first multi-source' claim. |
| `boukhers2024deepdblp` | Boukhers, Z.; Asundi, N. B. (2024 (online 2023-05-04)). Deep Author Name Disambiguation Using DBLP Data. Int. J. on Digital Libraries 25, 431-441. | `VP` | `P` | Yes | Signals used (name, coauthor, title/source context) and the new-author boundary. |
| `choi2024heterogeneoussites` | Choi, D.; Jang, J.; Song, S.; Lee, H.; Lim, J.; Bok, K.; Yoo, J. (2024). Name Disambiguation Scheme Based on Heterogeneous Academic Sites. Applied Sciences 14(1), 192. | `VP` | `P` | Yes | Missing-metadata handling and multi-source prior art. |
| `duran-silva-etal-2024-affilgood` | Duran-Silva, N.; Accuosto, P.; Przybyla, P.; Saggion, H. (2024). AffilGood: Building Reliable Institution Name Disambiguation Tools to Improve Scientific Literature Analysis. Proc. 4th Workshop on Scholarly Document Processing (SDP 2024), 135-144. | `VP` | `P` | Yes | Scope boundary for HAMMER's token-based institution signal. |
| `kallipoliti2025affro` | Kallipoliti, M.; Chatzopoulos, S.; Baglioni, M.; Adamidi, E.; Koloveas, P.; Vergoulis, T. (2025). From Raw Affiliations to Organization Identifiers. TPDL 2025, LNCS 16097, 111-126 (Springer). | `VP` | `P` | Yes | Narrows any affiliation-normalisation novelty claim. |
| `fellegi1969recordlinkage` | Fellegi, I. P.; Sunter, A. B. (1969). A Theory for Record Linkage. J. American Statistical Association 64(328), 1183-1210. | `VP` | `P` | Yes | Linkage foundations; three-way decision lineage (to be confirmed in text). |
| `ferreira2012brief` | Ferreira, A. A.; Gonçalves, M. A.; Laender, A. H. F. (2012). A Brief Survey of Automatic Methods for Author Name Disambiguation. ACM SIGMOD Record 41(2), 15-26. | `VT` | `M` | No | Candidate identification of the deck's unidentified 'Ferreira et al.' row; owner must confirm this is the intended work. |
| `han2004twosupervised` | Han, H.; Giles, L.; Zha, H.; Li, C.; Tsioutsiouliklis, K. (2004). Two Supervised Learning Approaches for Name Disambiguation in Author Citations. Proc. 4th ACM/IEEE-CS Joint Conf. on Digital Libraries (JCDL), 296-305. | `VT` | `M` | No | Candidate for the deck's unidentified 'Han et al.' row (several Han et al. AND papers exist); owner must confirm. |
| `torvik2009authority` | Torvik, V. I.; Smalheiser, N. R. (2009). Author Name Disambiguation in MEDLINE. ACM Trans. Knowledge Discovery from Data 3(3), 1-29. | `VT` | `M` | No | Likely the true source of the deck's Torvik & Smalheiser attribution (Author-ity lineage); do not cite for AggAND. |
| `tang2012unified` | Tang, J.; Fong, A. C. M.; Wang, B.; Zhang, J. (2012). A Unified Probabilistic Framework for Name Disambiguation in Digital Library. IEEE Trans. Knowledge and Data Engineering 24(6), 975-987. | `VT` | `M` | No | Example of probabilistic evidence combination in AND; contrast with HAMMER's heuristic weights. |
| `elmagarmid2007duplicate` | Elmagarmid, A. K.; Ipeirotis, P. G.; Verykios, V. S. (2007). Duplicate Record Detection: A Survey. IEEE Trans. Knowledge and Data Engineering 19(1), 1-16. | `VT` | `M` | No | Classical background for work-level dedup (conditional RQ1). |
| `kopcke2010frameworks` | Köpcke, H.; Rahm, E. (2010). Frameworks for Entity Matching: A Comparison. Data & Knowledge Engineering 69(2), 197-210. | `VT` | `M` | No | Background for combining match evidence in entity matching. |

### Cluster 5 Selective prediction, abstention, human review

| Key | Citation | Check | Inspection | In bib | Role for HAMMER |
|---|---|---|---|---|---|
| `zhang2018aminerhitl` | Zhang, Y.; Zhang, F.; Yao, P.; Tang, J. (2018). Name Disambiguation in AMiner: Clustering, Maintenance, and Human in the Loop. Proc. 24th ACM SIGKDD Int. Conf. (KDD '18), 1002-1011. | `VT` | `P` | Yes (pages missing in bib; use 1002-1011) | Direct prior art for human-in-the-loop AND; HAMMER's novelty cannot be 'has a reviewer'. |
| `geifman2019selectivenet` | Geifman, Y.; El-Yaniv, R. (2019). SelectiveNet: A Deep Neural Network with an Integrated Reject Option. Proc. 36th ICML, PMLR 97, 2151-2159. | `VT` | `MA` | Yes | Motivates reporting risk at coverage; does not transfer performance claims. |
| `hendrickx2024reject` | Hendrickx, K.; Perini, L.; Van der Plas, D.; Meert, W.; Davis, J. (2024). Machine Learning with a Reject Option: A Survey. Machine Learning 113(5), 3073-3110. | `VT` | `M` | No | Primary general reference for abstention/selective decisions; supports terminology. |
| `chow1970reject` | Chow, C. K. (1970). On Optimum Recognition Error and Reject Tradeoff. IEEE Trans. Information Theory 16(1), 41-46. | `VT` | `M` | No | Classical origin of the reject-option error-reject trade-off. |
| `elyaniv2010foundations` | El-Yaniv, R.; Wiener, Y. (2010). On the Foundations of Noise-free Selective Classification. J. Machine Learning Research 11, 1605-1641. | `VT` | `MA` | No | Formal foundation for coverage-risk language. |
| `geifman2017selective` | Geifman, Y.; El-Yaniv, R. (2017). Selective Classification for Deep Neural Networks. arXiv:1705.08500 (venue not stated on the arXiv page). | `VTA` | `MA` | No | Risk-coverage framing; the example shows how coverage must accompany risk. |
| `wang2012crowder` | Wang, J.; Kraska, T.; Franklin, M. J.; Feng, J. (2012). CrowdER: Crowdsourcing Entity Resolution. Proc. VLDB Endowment 5(11), 1483-1494. | `VT` | `M` | No | Human review of machine-filtered entity-resolution cases is established prior art. |
| `guo2017calibration` | Guo, C.; Pleiss, G.; Sun, Y.; Weinberger, K. Q. (2017). On Calibration of Modern Neural Networks. ICML 2017 (per arXiv comments); arXiv:1706.04599. | `VTA` | `MA` | No | Supports the wording that HAMMER's heuristic score is not a calibrated probability, as a cautionary reference only. |
| `chen2020conna` | Chen, B.; Zhang, J.; Tang, J.; Cai, L.; Wang, Z.; Zhao, S.; Chen, H.; Li, C. (2020 (arXiv v1 2019)). CONNA: Addressing Name Disambiguation on The Fly. Accepted to IEEE TKDE 2020 per arXiv comments; journal volume/pages not verified; arXiv:1910.12202. | `VTA` | `MA` | No | Closest prior art found for 'match then decide whether to assign': narrows novelty of a decision stage after candidate ranking. |
| `chen2018humo` | Chen, Z.; Chen, Q.; Fan, F.; Wang, Y.; Wang, Z.; Nafa, Y.; Li, Z.; Liu, H.; Pan, W. (2018 (arXiv 2017)). Enabling Quality Control for Entity Resolution: A Human and Machine Cooperation Framework. ICDE 2018 (camera-ready per arXiv comments); arXiv:1710.00204. | `VTA` | `MA` | No | Prior art for quality-controlled human/machine splitting; HAMMER does not provide guarantees of this kind. |
| `hou2018rhumo` | Hou, B.; Chen, Q.; Chen, Z.; Nafa, Y.; Li, Z. (2018). r-HUMO: A Risk-Aware Human-Machine Cooperation Framework for Entity Resolution with Quality Guarantees. arXiv:1803.05714 (no venue listed on the arXiv page). | `VTA` | `MA` | No | Related to risk-based routing to human review. |

### Cluster 6 Metadata integration and provenance

| Key | Citation | Check | Inspection | In bib | Role for HAMMER |
|---|---|---|---|---|---|
| `zhang2021aggand` | Zhang, L.; Huang, Y.; Yang, J.; Lu, W. (2021). Aggregating Large-Scale Databases for PubMed Author Name Disambiguation. J. American Medical Informatics Association 28(9), 1919-1927. | `VP` | `P` | Yes | Direct prior art for multi-source author evidence; weakens any 'first multi-source' claim. |
| `choi2024heterogeneoussites` | Choi, D.; Jang, J.; Song, S.; Lee, H.; Lim, J.; Bok, K.; Yoo, J. (2024). Name Disambiguation Scheme Based on Heterogeneous Academic Sites. Applied Sciences 14(1), 192. | `VP` | `P` | Yes | Missing-metadata handling and multi-source prior art. |
| `duran-silva-etal-2024-affilgood` | Duran-Silva, N.; Accuosto, P.; Przybyla, P.; Saggion, H. (2024). AffilGood: Building Reliable Institution Name Disambiguation Tools to Improve Scientific Literature Analysis. Proc. 4th Workshop on Scholarly Document Processing (SDP 2024), 135-144. | `VP` | `P` | Yes | Scope boundary for HAMMER's token-based institution signal. |
| `kallipoliti2025affro` | Kallipoliti, M.; Chatzopoulos, S.; Baglioni, M.; Adamidi, E.; Koloveas, P.; Vergoulis, T. (2025). From Raw Affiliations to Organization Identifiers. TPDL 2025, LNCS 16097, 111-126 (Springer). | `VP` | `P` | Yes | Narrows any affiliation-normalisation novelty claim. |
| `forbes2024deduplicator` | Forbes, C.; Greenwood, H.; Carter, M.; Clark, J. (2024). Automation of Duplicate Record Detection for Systematic Reviews: Deduplicator. Systematic Reviews 13, 206. | `VP` | `P` | Yes | Conditional RQ1 background; document identity vs person identity. |
| `culbert2025openalexcoverage` | Culbert, J. H.; Hobert, A.; Jahn, N.; Haupka, N.; Schmidt, M.; Donner, P.; Mayr, P. (2025 (preprint 2024)). Reference Coverage Analysis of OpenAlex Compared to Web of Science and Scopus. Scientometrics 130, 2475-2492. | `VP` | `P` | Yes | Source coverage and provenance context for OpenAlex-only pools. |
| `gerasimov2024datasetcoverage` | Gerasimov, I.; KC, B.; Mehrabian, A.; Acker, J. G.; McGuire, M. P. (2024). Comparison of Datasets Citation Coverage in Google Scholar, Web of Science, Scopus, Crossref, and DataCite. Scientometrics 129, 3681-3704. | `VP` | `P` | Yes | Optional bounded support for 'coverage varies by source'. |
| `fellegi1969recordlinkage` | Fellegi, I. P.; Sunter, A. B. (1969). A Theory for Record Linkage. J. American Statistical Association 64(328), 1183-1210. | `VP` | `P` | Yes | Linkage foundations; three-way decision lineage (to be confirmed in text). |
| `priem2022openalex` | Priem, J.; Piwowar, H.; Orr, R. (2022). OpenAlex: A Fully-Open Index of Scholarly Works, Authors, Venues, Institutions, and Concepts. arXiv:2205.01833 (preprint). | `VP` | `P` | Yes | Primary source for HAMMER's candidate provider. |
| `petroni2021kilt` | Petroni, F.; Piktus, A.; Fan, A.; Lewis, P.; Yazdani, M.; De Cao, N.; Thorne, J.; Jernite, Y.; Karpukhin, V.; Maillard, J.; Plachouras, V.; Rocktäschel, T.; Riedel, S. (2021). KILT: a Benchmark for Knowledge Intensive Language Tasks. Proc. NAACL-HLT 2021, 2523-2544 (ACL). | `VT` | `M` | No | Contextual only for retrieval/provenance evaluation of supporting features; proves nothing about HAMMER's citation faithfulness. |
| `elmagarmid2007duplicate` | Elmagarmid, A. K.; Ipeirotis, P. G.; Verykios, V. S. (2007). Duplicate Record Detection: A Survey. IEEE Trans. Knowledge and Data Engineering 19(1), 1-16. | `VT` | `M` | No | Classical background for work-level dedup (conditional RQ1). |
| `kopcke2010frameworks` | Köpcke, H.; Rahm, E. (2010). Frameworks for Entity Matching: A Comparison. Data & Knowledge Engineering 69(2), 197-210. | `VT` | `M` | No | Background for combining match evidence in entity matching. |
| `buneman2001whyandwhere` | Buneman, P.; Khanna, S.; Tan, W.-C. (2001). Why and Where: A Characterization of Data Provenance. Database Theory - ICDT 2001, LNCS, 316-330. | `VT` | `M` | No | Gives a defined vocabulary for 'provenance' so HAMMER's usage is not loose. |
| `chen2018humo` | Chen, Z.; Chen, Q.; Fan, F.; Wang, Y.; Wang, Z.; Nafa, Y.; Li, Z.; Liu, H.; Pan, W. (2018 (arXiv 2017)). Enabling Quality Control for Entity Resolution: A Human and Machine Cooperation Framework. ICDE 2018 (camera-ready per arXiv comments); arXiv:1710.00204. | `VTA` | `MA` | No | Prior art for quality-controlled human/machine splitting; HAMMER does not provide guarantees of this kind. |

## 5. Claims the paper can safely make from each source

These are *permitted wordings*, subject to confirming the exact passage in the paper.

| Key | Safe wording | Do not claim |
|---|---|---|
| `tian2024pubmedcomputedauthors` | 'Tian et al. report 92.2% pairwise accuracy on the 400-pair GSD1900 test subset and 91.0% over all 1,900 pairs' (their system, their metric). | That 92.2% is a HAMMER or top-1 result. |
| `zhang2021aggand` | 'Prior work has aggregated several scholarly databases to improve PubMed author disambiguation.' | That HAMMER is the first multi-source author system; that AggAND is by Torvik & Smalheiser. |
| `boukhers2024deepdblp` | 'Boukhers and Asundi note that new authors are not handled properly by their approach.' (confirm exact passage first) | A scalability limit the authors did not state. |
| `choi2024heterogeneoussites` | 'Choi et al. select a disambiguation scheme according to the metadata available from heterogeneous sites.' | That the method has no fusion strategy. |
| `rodrigues2024andreview` | 'Disambiguation methods fall into grouping (similarity/clustering) and assignment (classification) families (Rodrigues et al.).' | That it is a protocol-driven systematic review or an implementation framework. |
| `duran-silva-etal-2024-affilgood` | 'Organisation linking from affiliation strings is a distinct, tool-supported task (AffilGood).' | Anything beyond the sentence in the previous column. |
| `kallipoliti2025affro` | 'Recent work maps raw affiliation strings to organisation identifiers (AffRo).' | A 2024 date. |
| `forbes2024deduplicator` | 'Duplicate-record detection for systematic reviews is an established work-level task (Forbes et al.).' | Anything beyond the sentence in the previous column. |
| `culbert2025openalexcoverage` | 'Source coverage differs and is task-dependent; shared-corpus comparisons do not establish global coverage.' | Anything beyond the sentence in the previous column. |
| `gerasimov2024datasetcoverage` | Only as an example that coverage varies by source for a specific task. | Anything beyond the sentence in the previous column. |
| `vishnyakova2019gsd1900` | 'GSD1900 contains 1,900 MEDLINE publication pairs (Vishnyakova et al.).' | That GSD1900 is a candidate-ranking dataset. |
| `subramanian2021s2and` | 'Models trained on a single AND dataset often transfer poorly to others (Subramanian et al.).' | Anything beyond the sentence in the previous column. |
| `chen2023whoiswho` | 'WhoIsWho provides a >1 M-paper benchmark with a real-time assignment task.' | That online assignment or web-scale AND is unaddressed in the field. |
| `zhang2018aminerhitl` | 'Human-in-the-loop name disambiguation is deployed in AMiner (Zhang et al.).' | That having a human reviewer is novel. |
| `zhang2023lagosand` | 'LAGOS-AND is a large AND gold standard derived from ORCID and DOI evidence.' | Anything beyond the sentence in the previous column. |
| `geifman2019selectivenet` | 'Selective prediction trades coverage for lower risk on the answered inputs (Geifman and El-Yaniv).' | Any transfer of its results to author disambiguation. |
| `fellegi1969recordlinkage` | Cite for record-linkage foundations only. | That HAMMER's heuristic score is a probabilistic linkage model. |
| `priem2022openalex` | 'OpenAlex is the candidate source; its author IDs are profiles, not verified persons.' | Anything beyond the sentence in the previous column. |
| `ferreira2012brief` | Only as a general survey citation after reading. | Anything beyond the sentence in the previous column. |
| `han2004twosupervised` | Only as an early supervised AND example after reading. | Anything beyond the sentence in the previous column. |
| `torvik2009authority` | Cite only as MEDLINE AND prior work after reading. | Anything beyond the sentence in the previous column. |
| `debonis2023graph` | Only as a survey citation after reading. | Anything beyond the sentence in the previous column. |
| `sanyal2021review` | Only as a survey citation after reading. | Anything beyond the sentence in the previous column. |
| `muller2017datasets` | Only as evidence that AND data-set quality has been analysed, after reading. | Anything beyond the sentence in the previous column. |
| `kim2018dblp` | Only after reading. | Anything beyond the sentence in the previous column. |
| `tang2012unified` | Only after reading. | Anything beyond the sentence in the previous column. |
| `papadakis2020blocking` | Only for general candidate-generation background after reading. | Anything beyond the sentence in the previous column. |
| `hendrickx2024reject` | Only for terminology after reading. | Anything beyond the sentence in the previous column. |
| `chow1970reject` | Cite for the classical reject-option framing after reading. | Anything beyond the sentence in the previous column. |
| `elyaniv2010foundations` | Cite for selective-classification foundations. | Anything beyond the sentence in the previous column. |
| `geifman2017selective` | 'Selective classifiers trade coverage for risk (Geifman and El-Yaniv).' | Anything beyond the sentence in the previous column. |
| `petroni2021kilt` | Contextual mention only. | Anything beyond the sentence in the previous column. |
| `elmagarmid2007duplicate` | Only after reading. | Anything beyond the sentence in the previous column. |
| `kopcke2010frameworks` | Only after reading. | Anything beyond the sentence in the previous column. |
| `wang2012crowder` | Only after reading. | Anything beyond the sentence in the previous column. |
| `buneman2001whyandwhere` | Cite for the term only; do not claim HAMMER implements why/where-provenance. | Anything beyond the sentence in the previous column. |
| `guo2017calibration` | Cautionary reference for 'score is not a calibrated probability'. | Anything beyond the sentence in the previous column. |
| `chen2020conna` | 'CONNA decides whether to assign a paper to its top-matched person or create a new one (Chen et al.).' | That assign-versus-new-person decisions are absent from prior work. |
| `chen2018humo` | 'Human-machine splits with quality targets exist for entity resolution (Chen et al.).' | Anything beyond the sentence in the previous column. |
| `hou2018rhumo` | Cite cautiously as a preprint. | Anything beyond the sentence in the previous column. |

## 6. Bibliographic corrections already established (preserve)

| Deck or earlier statement | Verified correction | Source of correction |
|---|---|---|
| AggAND authors Torvik & Smalheiser | Li Zhang, Yong Huang, Jinqing Yang, Wei Lu | Prior audit |
| Heterogeneous-sites paper by Li et al. | Choi, Jang, Song, Lee, Lim, Bok, Yoo | Prior audit |
| 2024 literature review by Kumar et al. | Rodrigues, Mariano, Ralha | Prior audit |
| AffRo 2024 | First online 2025 (TPDL 2025, LNCS 16097) | Prior audit |
| 'Ferreira et al.; Han et al.' classical methods | Still unidentified as the deck's intended works. Plausible candidates exist (`ferreira2012brief`, `han2004twosupervised`) and their metadata is verified, but **whether they are what the deck meant is an owner question.** Do not cite them *as* the deck's references. | This task |
| AMiner entry lacks pages | Pages 1002-1011 verified via Crossref this task | This task |
| LAGOS-AND year | Crossref issued year is 2022 (online); volume 74(2) is 2023. The bib's 2023 is the volume year. | This task |
| First guess at a DOI for Müller et al. 2017 | The first recalled DOI resolved to a *different* paper (Boyack, topic detection). The correct DOI came from search plus Crossref. This is an example of why recalled DOIs must not be used unchecked. | This task |

## 7. Unresolved bibliographic questions

- `boukhers2024deepdblp`: Locate the exact new-author passage before quoting.
- `duran-silva-etal-2024-affilgood`: DOI not recorded in bib; confirm whether one exists.
- `gerasimov2024datasetcoverage`: Consider dropping if space is short; weakly related to RQ2.
- `subramanian2021s2and`: Read full text for the facet definitions before describing them.
- `chen2023whoiswho`: Read full text to confirm task definitions and metrics.
- `zhang2018aminerhitl`: Add pages = {1002--1011} to the bib entry (not done: bib untouched).
- `zhang2023lagosand`: Crossref lists 2022 as issued (online); volume 74(2) is 2023: bib uses 2023 (acceptable, but state which).
- `fellegi1969recordlinkage`: Confirm the 'possible link' (three-outcome) formulation in the full text before citing it for that point.
- `priem2022openalex`: Check whether a peer-reviewed/versioned citation is preferable to the arXiv preprint.
- `ferreira2012brief`: Owner to confirm whether the deck's 'Ferreira et al.' meant this paper.
- `han2004twosupervised`: Owner to confirm intended 'Han et al.' work.
- `torvik2009authority`: Read before use; confirm it is the Author-ity paper the project means.
- `debonis2023graph`: Read before use.
- `sanyal2021review`: Decide whether to cite as 2019 (online) or 2021 (issue year); use one convention project-wide.
- `muller2017datasets`: Read before use. Author spelling Muller/Müller: use the form the paper prints.
- `kim2018dblp`: Verify DOI against Crossref/Springer; read before use.
- `tang2012unified`: Read before use.
- `papadakis2020blocking`: Read to see which recall-style measures the survey defines (pair completeness etc.).
- `hendrickx2024reject`: Read before using any specific statement.
- `chow1970reject`: Crossref lists author as 'C. Chow'; the paper is commonly cited as C. K. Chow: use the printed form.
- `geifman2017selective`: Venue (NeurIPS 2017) was not confirmed on the fetched page: verify before citing as a conference paper.
- `petroni2021kilt`: Include only if the supporting retrieval/explanation features are discussed at length.
- `elmagarmid2007duplicate`: Read before use.
- `kopcke2010frameworks`: Optional; drop if not read. Author spelling Köpcke/Koepcke: use the form the paper prints.
- `wang2012crowder`: Read before use.
- `buneman2001whyandwhere`: LNCS volume number not recorded; add from the publisher page.
- `guo2017calibration`: Optional; PMLR record for ICML 2017 not fetched.
- `chen2020conna`: Read full text; verify TKDE metadata.
- `chen2018humo`: Verify ICDE proceedings metadata.
- `hou2018rhumo`: Find the published venue, if any.

## 8. Leads noted but not included

| Lead | Why excluded |
|---|---|
| Smalheiser & Torvik (2009), 'Author name disambiguation', ARIST 43(1) | Recalled from memory; not searched or verified in this task. Verify before any use. |
| Torvik et al. (2005), JASIST, probabilistic AND for MEDLINE | Recalled from memory; not verified. |
| Treeratpituk & Giles (2009), JCDL, random forests for author disambiguation | Recalled from memory; not verified. |
| Hussain & Asghar (2017), survey of AND techniques 2010-2016 | Recalled from memory; not verified. |
| Han et al. (2005), K-way spectral clustering for author-citation disambiguation | Alternative candidate for the deck's 'Han et al.'; not verified. |
| Reimers & Gurevych (2019), Sentence-BERT; Wang et al. (2020), MiniLM | Basis of the all-MiniLM-L6-v2 embedding model; relevant only to the supporting retrieval feature; not searched. |
| CASRAI practitioner guide on ORCID + algorithmic matching + manual review | Found only as a search result; a grey-literature guide, not verified or read. |
| Several arXiv records with IDs of the form 26xx.xxxxx returned by the search tool | IDs look future-dated relative to what could be checked; not fetched, not used. |
| Patents (ResearchGate/Elsevier 'author disambiguation and publication assignment') | Returned by search; patents are not scholarly evidence for this paper; not used. |

## 9. Known inventory limitations

- Not systematic: see `LITERATURE_SEARCH_LOG.md`. The inventory is a verified starting set, not a complete survey of the field.
- Only 9 of 40 rows have even abstract-level content seen in this task; 17 are metadata-only. The `Method`, `Findings` and `Limitations` columns for those rows are mostly *Not inspected*.
- Cluster 3 (candidate generation) and the author-disambiguation-specific part of Cluster 5 are the thinnest and the most important for RQ2. Further reading there should precede any novelty wording.
- Inclusion in this inventory does not mean a reference should be cited. Cite only what materially supports an argument actually made in the paper.
