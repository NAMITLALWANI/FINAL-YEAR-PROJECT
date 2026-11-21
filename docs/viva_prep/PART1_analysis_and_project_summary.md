# Viva preparation, Part 1: deck analysis, inconsistencies and project summary

Sources read: `Group15_PPT.pdf` (18 slides, read text and the three picture slides), the current paper
(`paper/HAMMER_IEEE_PAPER`, 22 pages), and the application code (checked where the deck makes a technical claim).
Nothing here is invented; where the deck and the code disagree, both are quoted.

## 1. What HAMMER actually is (one paragraph each, in plain words)

**Publication side.** HAMMER collects paper records from OpenAlex, Crossref, DBLP and arXiv, cleans them into one
format, and decides when two records are the same paper (Deduplication Engine V2, string matching with RapidFuzz plus
DOI/title rules). It stores the merged paper and remembers which source supplied each field. Citation count is taken
as the **maximum across sources**; that is the whole "citation reconciliation".

**Author side.** Given a name (and optionally a workplace and years active), HAMMER asks OpenAlex for up to 10
candidate author profiles, scores each on up to five pieces of evidence (name 0.35, institution 0.25, publication
overlap 0.20, co-authors 0.10, timeline 0.10, re-weighted over whatever is available), and applies cautious rules:
score at least 0.75, a lead of at least 0.15 over the runner-up, the top score at least 1.35 times the runner-up, and
at least two evidence signals. The outcome is **automatic**, **manual review** or **unresolved**. The score is a
heuristic, not a probability, and the weights are engineering defaults that have not been calibrated.

**Search side.** Papers are embedded with the all-MiniLM-L6-v2 model, stored in Chroma, and retrieved by meaning.
Gemini can optionally write a short explanation (needs a key and is off without one).

**Research contribution (as the paper states it).** Not a new disambiguation algorithm. It is an implemented workflow
that keeps retrieval, ranking and the identity decision separate, treats missing evidence as unknown (not as "no"),
and a carefully designed, reproducible evaluation protocol with exploratory benchmark-derived observations.

## 2. Status table: what may be said about each feature

| Feature | Implemented | Tested (591 tests) | Evaluated on LAGOS-AND | Notes |
|---|---|---|---|---|
| Fetch from OpenAlex, Crossref, DBLP, arXiv | yes | yes (mocked) | OpenAlex only (candidate retrieval) | |
| Google Scholar connector | yes, **off by default** | partly | no | Scraper; not part of the evaluated system |
| Publication deduplication V2 | yes | yes | **no** (no dedup accuracy measured) | |
| Citation reconciliation | yes, simple (max across sources) | yes | no | Not a sophisticated method |
| Affiliation normalisation | yes (rule-based) | yes | used to build the C1 context | |
| Five evidence extractors | yes | yes | **four at most** available | Co-author unavailable; publication overlap only in exploratory C1x |
| Weighted scoring + renormalisation | yes | yes | yes | Heuristic, uncalibrated |
| Decision policy and safeguards B1-B5 | yes | yes | yes (benchmark-derived) | |
| Semantic search (Chroma, MiniLM) | yes | yes | no | |
| Gemini explanation | yes, optional | mocked | no | |
| Offline replay, freeze manifests | yes | yes | used for all reported numbers | |
| Independent human verification | **no** | n/a | **not done** | Future work |
| Verified accuracy of any kind | **no** | n/a | **not claimed** | |

## 3. Inconsistencies and risks, most serious first

Each item says what the deck says, what is true, and a suggested fix. Fixes are for you to decide; I have not edited
your PDF or PPTX.

1. **"Five signals" implies all five were used (slides 7, 12, 16).** In the experiment at most four are available:
   co-author evidence is unavailable, and publication overlap exists only in the exploratory condition C1x, which is
   leakage-prone (its DOI comes from the answer's own works) and is not the primary result. The primary condition C1
   uses name, institution and timeline. *Fix:* add a line on slide 12 or 13: "Five signals are built; in this test
   only name, workplace and years were available." The speakers must say this aloud either way.
2. **Tech stack slide 9 lists tools the application does not use.** `pandas`, `scikit-learn` and `LangChain` appear in
   no application code and not in `requirements.txt` (numpy appears only in the evaluation-sizing tools). The embedding
   model is all-MiniLM-L6-v2 but it runs through Chroma's ONNX runtime, not the Sentence-Transformers library. Missing
   from the slide but really used: SQLAlchemy (async) + aiosqlite, RapidFuzz, feedparser, BeautifulSoup, Playwright
   (scraping), onnxruntime, slowapi, pytest. *Fix:* remove the three unused logos and add RapidFuzz and SQLAlchemy, or
   be ready to say "listed in our original plan; not used in the final code". A panel member reading the slide may ask
   "where is scikit-learn used?" and the honest answer is "nowhere".
3. **"Machine learning-based name disambiguation" (slide 3, problem statement).** HAMMER's author matching is a
   rule-based, weighted evidence score with no trained model. ML appears only in the sentence-embedding model for search.
   *Fix:* reword the statement, or have Akshad say "evidence-based" and explain that no classifier was trained.
4. **Google Scholar (slides 2 and 9) vs the architecture (slide 8).** Slides 2 and 9 name Google Scholar; slide 8 does
   not, and the connector is disabled by default. *Fix:* say "Scholar is a scraping connector, disabled by default;
   the reported system uses OpenAlex, Crossref, DBLP and arXiv".
5. **"Tested on 68 real author searches" (slide 13).** The paper never pools the two samples: 50 (smoke) and 18
   (exploratory) are separate. The charts keep them apart, the headline joins them. Also, "Test 2" has only 18 cases
   because the free OpenAlex quota ran out (HTTP 429) after part of the capture; a panel may ask why 18 and not 50.
   *Fix:* "two small tests: 50 and 18 searches".
6. **"Right person" on slide 13 means "the profile carrying the benchmark's ORCID".** That is benchmark-derived, not
   verified identity, and the ORCID is also the label in OpenAlex (leakage risk). The limitations slide covers this
   in one line, but the results slide does not. *Fix:* add "(agreement with the dataset's ORCID label)".
7. **"Decides alone only when very sure: 4 of 50" (slide 13).** Of those four automatic assignments, three agree with
   the benchmark label and one does not (3 of 4, provisional, not verified). "Very sure" overstates it. Do not quote
   75% as precision. *Fix:* "only when the evidence is strong; 3 of those 4 matched the dataset's label".
8. **"92 of 92 real data requests succeeded" (slide 14).** True for the 50-case smoke capture. The record also contains
   a first attempt with a placeholder key (40 HTTP 401 responses), a capture where a header bug wasted 70 requests
   (found and fixed), and the exploratory capture that hit the free quota. *Fix:* keep the number but name its scope
   ("in the 50-case capture") and be ready to describe the two bugs: the seed-file format mismatch, and the
   compressed-response header bug in the cost guard.
9. **The name "HAMMER" never appears in the deck.** The title is the older project title. Fine if it is the official
   title, but panels have read the paper, which says HAMMER. Add one line: "Project name: HAMMER".
10. **Literature slides (4, 5) vs references (17).** Slides cite S2AND, WhoIsWho, LAGOS-AND, Ferreira and Han, and
    none of these is in the reference list; references [2], [6]-[10] (Torvik, AffilGood, Kallipoliti, Deduplicator,
    Culbert, dataset-citation coverage) are not discussed on any slide. The paper's own bibliography is the verified one.
11. **Research gaps slide (6) lists gaps HAMMER does not close**: real-time updates, class imbalance and scalability.
    The deck's scope slide and the paper do not claim to solve them. Namit should say which two or three HAMMER
    addresses (explainable decisions, missing metadata handled as unknown, multi-source with provenance, unresolved
    outcome instead of forced assignment) and say the rest are out of scope.
12. **Slide 10 (Implementation Schedule) is not in the allocation table.** Proposed owner: Akshad (project plan, next
    to his scope and demo slides). Slide 1 (title), 17 (references) and 18 (thank you) are also unassigned; suggested:
    the person speaking just before or after introduces them, and all three say thanks on slide 18.
13. **Slide 6 claim "weak temporal modelling" vs HAMMER's own temporal signal.** HAMMER's timeline evidence is a
    simple overlap of active years (weight 0.10), not career-progression modelling. Do not present it as solving the gap.
14. **Test count.** Deck and paper both say 591 passing tests, which I re-ran after the repository cleanup. The test
    count is not evidence of accuracy (see the question bank in Part 5).

## 4. Slide allocation (final deck order)

| Slide | Title | Presenter |
|---|---|---|
| 1 | Title | Namit opens (introduces the team) |
| 2 | Problem Description | Akshad |
| 3 | Problem Statement | Akshad |
| 4-5 | Literature Review | Nicholas |
| 6 | Research Gaps | Namit |
| 7 | Scope | Akshad |
| 8 | System Architecture | Namit |
| 9 | Tech Stack | Nicholas |
| 10 | Implementation Schedule | **not in your table; proposed Akshad** |
| 11 | Application Demonstration | Akshad |
| 12 | Dataset & Experimental Methodology | Namit |
| 13 | Experimental Results & Performance Evaluation | Nicholas |
| 14 | Software Testing & Validation | Namit |
| 15 | Limitations & Future Scope | Akshad |
| 16 | Conclusion | Nicholas |
| 17-18 | References, Thank you | Nicholas, then all |

Speaker switches are frequent (about twelve), so the scripts will end each section with a one-line hand-off.

## 5. Decisions needed from you before Part 2

1. Do you want the deck fixed (items 1-9) or kept as is and handled in the speeches? Fixing slides 3, 9, 12/13 is the
   safer choice.
2. Who owns slide 10 (default Akshad)?
3. Is "Design and Implementation of a Multi-Source Research Publication Reconciliation System" the official title and
   HAMMER the project name?
