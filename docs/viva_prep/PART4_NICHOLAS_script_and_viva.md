# Part 4: Nicholas Coutinho — script and viva preparation

Slides: **4–5** Literature Review, **9** Tech Stack, **13** Experimental Results & Performance Evaluation, **16** Conclusion,
**17** References. Read `PART1_analysis_and_project_summary.md` and the "rules for everyone" at the top of `PART2`.

---

## Slides 4 and 5 — Literature Review (after Akshad's problem statement)

**SAY (slide 4)**
"Author name disambiguation has been studied for a long time. We looked at five groups of work. Boukhers and Asundi in 2023 used a
neural network with character and BERT features on DBLP data. It captures meaning well, but it assumes the set of authors is fixed, and it
struggles to scale. Tian and colleagues built PubMed Computed Authors in 2024, a large production resource that combines machine learning
clustering with ORCID. It works at scale, but only for biomedical literature and with limited explanations. Li and colleagues in 2024 combine
rules and machine learning across different academic sites, which suits mixed sources, but their dataset is not public and they have no
way of fusing the sources. Kumar and colleagues reviewed many methods and pointed out the common gaps, but give no implementation. And the
classic rule-and-clustering methods, such as Ferreira and Han, are simple and easy to understand, but suffer when metadata is missing.
Taken together, they show the need for methods that allow 'unknown' answers, cope with missing data and work across domains."

**SAY (slide 5)**
"The second table is about benchmarks, the data used to test methods. S2AND from 2021 gives a benchmark with several datasets and methods.
WhoIsWho in 2023 is a large, human-annotated benchmark that includes authors who are not in the database. LAGOS-AND in 2023 is a very large dataset
built from ORCID and DOI links. Its labels are created automatically using external identifiers, which is its strength for size and its weakness
for exactness. That is why we chose it as the data foundation for HAMMER's evaluation, and also why we say its labels are provisional."

**WHAT THE SLIDE MEANS.** Each row: *what the paper did → what is good → what is limited → why it matters to us*. Slide 4 is about methods,
slide 5 about benchmarks.

**TERMS**
- *Closed-set / open-set:* choosing only among known authors, versus allowing "new / none of these".
- *Char2Vec, BERT:* ways of turning text (characters, words) into number vectors that capture similarity.
- *Clustering:* grouping records into piles that seem to belong to one person.
- *ORCID integration:* using the identifier as a strong hint.
- *Benchmark / gold standard:* a labelled dataset used to compare methods. *NIL author:* an author who is not in the reference database.
- *Meta-analysis:* a study that combines results from many studies.

**LIKELY QUESTIONS**
- *Basic:* Which paper is closest to your work? — Li et al., since they combine rules and learning across heterogeneous sites; and LAGOS-AND as our data.
- *Technical:* Why didn't you use a neural method like Boukhers & Asundi? — They need labelled training data and a closed set; we did not have verified labels, and we wanted explainable decisions and an "unresolved" option.
- *Challenge:* So your method is simpler than the state of the art. — Yes. We do not propose a new disambiguation algorithm. The contribution is an implemented, cautious, evidence-based workflow and a rigorous evaluation protocol. We do not claim it outperforms those methods.
- *Challenge:* Did you compare against any of these? — No. Their data and code were not part of our evaluation. We compared only with OpenAlex's own candidate order.
- *Weakness:* Some papers on the slide are not in your reference list. — Correct; the slide cites S2AND, WhoIsWho, LAGOS-AND, Ferreira and Han; the full verified bibliography is in the paper. (If asked for details, give only what the slide says.)

**Transition:** "Namit will now describe the gaps that these papers leave."

---

## Slide 9 — Tech Stack (after Namit's architecture)

**SAY**
"This slide shows the tools behind each box of the architecture. Data comes from OpenAlex, DBLP, Crossref and arXiv; we call them from Python using HTTPX. We
clean and standardise the records with our own Python code and Pydantic for data checking. Everything is stored in SQLite, with Alembic for database changes.
The author matching is our own Python logic: the weighted evidence score and the decision rules. For semantic search we use the all-MiniLM-L6-v2 embedding model, which runs through
Chroma's runtime. Chroma stores the embeddings. The interface is React with Vite, and the API layer is FastAPI. The optional explanation uses the Gemini API.
I want to be clear on three logos you see on the slide: pandas, scikit-learn and LangChain. Our final code does not use them; they were in our early design, and
what actually does the matching is our own code. What the slide leaves out are things we really used: RapidFuzz for string similarity in duplicate detection, SQLAlchemy for the database layer, and pytest for testing."

(If you prefer not to say this, ask for the slide to be corrected before the presentation.)

**WHAT THE SLIDE MEANS.** The numbered boxes mirror the architecture on slide 8 so each stage has its tool.

**TERMS**
- *FastAPI:* a Python framework for web APIs; async, with automatic input validation. *Uvicorn:* the server that runs it.
- *HTTPX:* HTTP client for calling the data sources. *Pydantic:* checks that data has the right shape.
- *SQLite:* a file-based database, no server needed. *SQLAlchemy:* Python layer to talk to the database. *Alembic:* database migration tool (versioned schema changes; used for the author-resolution tables).
- *RapidFuzz:* fast fuzzy string matching (title/author similarity).
- *all-MiniLM-L6-v2:* a small sentence-embedding model (384 numbers per text). *Chroma:* vector database. *ONNX runtime:* runs the model without a heavy deep-learning framework.
- *React, Vite:* front-end library and build tool. *Gemini:* Google's language model, used only for optional explanations.
- *Playwright, BeautifulSoup:* browser automation and HTML parsing for the scraper connectors (disabled by default).
- *slowapi:* rate limiting for the API.

**LIKELY QUESTIONS**
- *Basic:* Why FastAPI? — Fast, async (many provider calls at once), automatic validation and API docs, easy to test.
- *Basic:* Why SQLite? — Zero set-up, one file, ideal for a demo and replay; enough for this scale.
- *Technical:* Why Chroma and not a plain database for embeddings? — A vector store gives nearest-neighbour search on embeddings directly.
- *Technical:* Where is scikit-learn/pandas/LangChain used? — Not in the final application. They were planned; we did not need them. (Say it directly.)
- *Challenge:* Why a small embedding model? — Runs locally on CPU, free, no key. The trade-off is lower quality than big models; we have not evaluated search quality.
- *Challenge:* What if Gemini is unavailable? — Nothing breaks; the explanation is an optional layer and the system returns the evidence without it.
- *Weakness:* Is SQLite a bottleneck? — For large concurrent use, yes; PostgreSQL is a future step.
- *Weakness:* Does the demo depend on an API key? — The OpenAlex free tier works without a key but has a daily shared budget; we had it run out during the exploratory capture, which is why the replay uses saved responses.

**Transition:** "Akshad will walk you through the schedule and then show the application."

---

## Slide 13 — Experimental Results & Performance Evaluation (after Namit's methodology)

**SAY**
"Here is what we found, in two small tests. Test 1 had 50 searches, Test 2 had 18; we keep them apart because they are different samples. Please remember that 'the right person' here
means the profile that carries the dataset's ORCID. That is a provisional label, not human-verified. So these are exploratory observations, not accuracy.

Left chart, 'Did we find the right person?'. First bars: the right profile was somewhere in the list of up to ten candidates in 38 of 50, that is 76%, and 13 of 18, 72%. That is about three out of four. Second bars:
the source's own first pick, OpenAlex's first result, was the right one in 22 of 50 (44%) and 7 of 18 (39%): so for common names, even the provider's top result is right less than half the time. Third bars: our system's own top pick was right in 17 of 50
(34%) and 6 of 18 (33%). So honestly, our scoring did not do better than the provider's order in these samples.

Right chart, 'Can the system decide on its own?'. With name only, it never decides: 50 of 50 go to a person, by design. With name plus workplace and years, it decided alone in 4 of 50 searches; in the second test, none of 18. The reason is
that several similar names score almost the same, so it asks a person instead of guessing. Of those four automatic decisions, three matched the dataset's label and one did not, which we cannot yet say is a wrong decision or a label problem.
Small numbers, so we do not draw conclusions from them."

**WHAT THE SLIDE MEANS.** Left: retrieval and ranking. Right: coverage of automatic decisions. Maroon = Test 1 (smoke, 50), grey = Test 2 (exploratory, 18).

**TERMS**
- *Retrieval (pool):* did the right profile appear among the candidates? *Ranking:* was it first?
- *Success@1 / top-1:* the first-ranked candidate is the right one. *Coverage:* share of cases decided automatically. *Precision (automatic):* of automatic decisions, share that are right (not measurable without verified labels; we only have agreement with the dataset label).
- *95% confidence interval:* range that likely contains the true rate; with 50 cases it is wide (for 38/50: about 62–87%; for 22/50: about 30–59%).
- *Benchmark-derived:* computed against the dataset's own labels.

**LIKELY QUESTIONS**
- *Basic:* What is the main result? — The right profile was found in the candidate list about three times in four, but ranking correctly and deciding automatically were much harder; the system mostly defers to a person.
- *Technical:* Why did HAMMER's ranking not beat OpenAlex's first candidate? — The score sorts candidates by name, institution and years; many candidates share a name and some lack the institution, so scores are close (median top score 0.88). Our weights are untuned and we have no learned model. The heuristic order should not be expected to beat a provider's ranking.
- *Technical:* Why was automatic coverage so low (4/50, 0/18)? — Gates: lead over runner-up below 0.15 in 37/50 and 14/18; ratio below 1.35 in 44 and 17; fewer than two observed signals in 14 and 3. High scores are common; clear winners are rare.
- *Technical:* What about the 4 automatic ones? — 3 of 4 agreed with the dataset label (75%, 95% CI 19–99%); with n = 4 this means nothing statistically. Never quote it as precision.
- *Challenge:* So is the system useful? — As a cautious triage tool: it avoids forced guesses and shows evidence, but we cannot claim accuracy.
- *Challenge:* Why only 18 in test 2? — Free tier quota ended (HTTP 429); no paid key. Reported as an 18-case exploratory sample, not a random sample of anything.
- *Challenge:* Why do you not pool 50 + 18? — Different samples and purposes; the paper reports them separately. The slide's "68 searches" just counts how many searches we ran.
- *Weakness:* What is C1x? Why not shown? — A leaky setting: the paper identifier given to the system comes from the answer's own papers. It reaches 7/50 and 3/18 automatic with the safeguards, and 26/50 and 8/18 without them; we report it only as exploratory and never as the main result.
- *Weakness:* Is 76% the system's accuracy? — No. It is how often the dataset-labelled profile appears in OpenAlex's list; it is partly a measure of OpenAlex and of label availability.

**Transition:** "Namit will now explain how we tested the software behind these numbers."

---

## Slide 16 — Conclusion

**SAY**
"To conclude: HAMMER brings publications from several sources into one place, standardises them, removes duplicates and keeps track of where each fact came
from. For authors, it proposes candidates and weighs five kinds of evidence: name, affiliation, publication overlap, co-authors and timeline. It decides automatically only for strong matches, and
sends unclear cases to a person or leaves them unresolved. In our small experiments, only some of these signals were available, the system was mostly cautious, and what we have is exploratory.
What we built is also a base for repeatable evaluation. The independent verification, and so any claim about accuracy, is our future work. Thank you."

**LIKELY QUESTIONS**
- *Basic:* What did you achieve? — A working multi-source system with an evidence-based author-resolution workflow, a reproducible evaluation set-up and 591 tests.
- *Technical:* What is the actual research contribution? — Not a new algorithm. A careful separation of retrieval, ranking and identity decisions; explicit handling of missing evidence; conservative gates with an unresolved outcome; and a leakage-aware, reproducible evaluation design with honest, benchmark-derived exploratory results.
- *Challenge:* Is that enough for a final-year project? — The system, the tests and the evaluation protocol are complete and working; the missing piece is independent human verification, which needs people we did not have.
- *Weakness:* Biggest risk in your claims? — Benchmark leakage and small samples: all reported rates are provisional.

**Closing:** "That brings us to the end of our presentation. We'll be happy to take your questions."

## Slide 17 — References
Only say: "These are the key references; the full verified list is in our paper." Do not read them. Slide 18: all three say thank you.

---

## Delivery guide for Nicholas

**Do not say:** "accurate", "76% accuracy", "outperforms", "state of the art", "we use scikit-learn / pandas / LangChain", "the system is very sure".
**Explaining charts:** point to the title, then to each bar, give the count first (38 of 50), then the percentage, then what it means in one sentence.
**If interrupted:** answer in a sentence, then resume. **If you don't know:** "I'm not certain; the paper's results section gives the exact figure; I'd rather not guess."

## Viva depth: concepts Nicholas must be able to explain
1. **Evaluation metrics.** Pool inclusion (is the expected profile among ≤10 candidates), Success@k (end to end), conditional recall@1 (22/38; 7/13), MRR (0.54; 0.50), coverage, benchmark-derived precision, forced top-1. What each denominator is. Confidence intervals are exact Clopper–Pearson and ignore clustering of cases within blocks (smoke cases are from 23 blocks, so the intervals are optimistic).
2. **Why the system cannot beat the provider's ranking yet.** Heuristic weights, missing evidence, near-ties; no training.
3. **R0 vs R2.** Two retrieval strategies; R2 is the application's own (query cleaner, a broader search and an initials fallback) and R0 is a plainer search. They share one stored response when their requests are identical, so the paper makes no comparison between them.
4. **Why C1x is not primary.** Leakage.
5. **Technology choices.** See slide 9 above; alternatives: Flask/Django, PostgreSQL, Elasticsearch/FAISS, scikit-learn classifier, LangChain.
6. **Literature positioning.** HAMMER is a workflow plus protocol, not a new algorithm.
