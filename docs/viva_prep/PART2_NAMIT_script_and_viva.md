# Part 2: Namit Lalwani — script and viva preparation

Slides: **1** (opening), **6** Research Gaps, **8** System Architecture, **12** Dataset & Experimental Methodology,
**14** Software Testing & Validation. Read `PART1_analysis_and_project_summary.md` first: the scripts below already
work around the deck problems listed there (they say the truthful thing even where a slide is loose).

Rules for everyone: say "benchmark label", never "ground truth"; say "agreement with the dataset's label", never
"accuracy"; the score is a **heuristic score**, never a probability; four signals at most were available in the experiment.

---

## Opening (slide 1)

**SAY**
"Good morning. We are Group 15 from Information Technology. I am Namit Lalwani, and with me are Akshad Kedia and
Nicholas Coutinho; our guide is Mr. Sunil Shelke and our industry mentor is Mr. Sushant Nair. Our project is called
HAMMER, and it is about two things that sound similar but are different: knowing when two records describe the
same research paper, and knowing which real person an author's name belongs to. Akshad will start with the problem."

**Hand-off:** look at Akshad, nod.

---

## Slide 6 — Research Gaps (after Nicholas's literature review)

**SAY**
"Nicholas showed that many methods exist. From that reading we found gaps. The first is the closed-set assumption:
many methods must put an author into a group that already exists, so a genuinely new person gets forced into the
wrong group. Second, missing information: when abstracts, co-authors or affiliations are missing, results drop.
Third, many methods are tested only on one kind of data, such as PubMed or DBLP. Fourth, it is hard to see why a
method merged or split two authors; explanations are weak. And fifth, there is no single system that pulls
several sources together, removes duplicate papers, and also handles author identity carefully.

We want to be clear about what HAMMER addresses. It addresses four of these. It never forces an answer: it can say
'manual review' or 'unresolved'. It treats missing information as *unknown*, not as a 'no'. It keeps the evidence for
every decision so you can see why. And it combines several sources with the source of every field recorded.
It does not claim to solve the others, such as real-time updates or very large scale; those are outside our scope."

**WHAT THE SLIDE MEANS.** A gap is something the existing work does not do well. Each bullet is a weakness found in the
papers on slides 4 and 5. Our design choices answer some of them directly.

**TERMS**
- *Closed-set assumption:* the method only chooses among authors it already knows. The opposite is "open-set", where "none of these" is allowed.
- *Class imbalance:* a few authors have huge numbers of papers and most have a few, which confuses learning methods.
- *Explainability:* being able to say why a decision was made.
- *Affiliation normalisation:* writing "IIT Bombay", "Indian Institute of Technology, Bombay" and "IITB" in one standard form.
- *Domain bias:* a method works on the data type it was tested on and may fail on another.

**LIKELY QUESTIONS**
- *Basic:* What is the biggest gap you found? — The closed-set assumption, and missing metadata.
- *Technical:* Which gaps does HAMMER actually close? — Not all. Explainable, evidence-based decisions; an open outcome (manual/unresolved); missing data treated as unknown; multi-source with provenance. We did not address real-time updates or scale.
- *Challenge:* The slide says "weak temporal modelling"; is your temporal signal better? — No. Ours is simple: overlap of active years, weight 0.10. We do not model career change.
- *Weakness:* Slide says no unified multi-source system exists; is that true? — We found none in the papers we reviewed; we do not claim to have searched everything. OpenAlex and Google Scholar are aggregators, but they do not give the evidence-gated, reviewable identity decision we describe.

**Transition:** "These gaps shaped how we designed the system. Akshad will first define our scope, and then I will walk through the architecture."
(Slide 7 is Akshad's. When he finishes: "Thanks Akshad. Here is how the pieces fit together.")

---

## Slide 8 — System Architecture

**SAY**
"This is the whole system in seven boxes, left to right. Box one: data sources. We collect from OpenAlex, DBLP,
Crossref and arXiv. Box two: cleaning and combining. Every source describes a paper differently, so we put them in one
format, then find records that are the same paper and merge them into one, remembering which source gave which field.
Box three is the main database, SQLite, which stores papers, authors, source details and every matching decision.

Box four is author matching. When someone gives a name, we fetch possible people from OpenAlex and compare them using
evidence: publications, institution, co-authors and years. Box five is search: the paper texts are turned into numbers
called embeddings and kept in a vector store so we can find papers by meaning, not just by words. Box six is the
interface where a user searches and sees the evidence. Box seven, with a dashed line, is optional: a language model can
write a short plain explanation from the evidence, and the system works without it.

Two things I want you to remember. First, paper-merging and author-matching are separate: they do not share scores.
Second, the author step can end in three ways: automatic, manual review or unresolved."

**WHAT THE SLIDE MEANS.** Data flows left to right: collect → clean/merge → store → match authors / search → show.
The two lower boxes show what is stored: records and decisions in the database, and paper embeddings in Chroma.

**TERMS**
- *Connector / ingestion:* code that talks to one source's web API and converts its answer to our format.
- *Deduplication:* deciding two records are the same paper. Our engine blocks cheaply, vetoes or forces a merge on DOIs, then scores title/author/year with a threshold that depends on the source pair; groups are formed by union-find.
- *Provenance:* a record of which source supplied which field.
- *Embedding:* a list of numbers that represents the meaning of a text; similar meanings give close numbers.
- *Vector store (Chroma):* a database that finds the nearest embeddings. *RAG:* retrieve relevant papers first, then (optionally) let a language model write an explanation grounded in them.
- *Author entity resolution:* deciding which real person a name belongs to.

**LIKELY QUESTIONS**
- *Basic:* What does the system do end to end? — Collects, cleans, merges papers, stores them, matches author names to profiles with evidence, supports semantic search, shows everything in a web UI.
- *Basic:* Why do you need a database and Chroma? — Database holds the facts and decisions; Chroma holds embeddings for similarity search. Different jobs.
- *Technical:* How is deduplication different from author resolution? — Dedup asks "same paper?"; author resolution asks "which person?" Different data, different scores, no shared inputs.
- *Technical:* Where is Google Scholar? — A scraper exists but is disabled by default; the reported system uses the four API sources.
- *Challenge:* Why is the language model optional? — So the decision never depends on a generated text. It only explains evidence already retrieved. Without a key the system still works.
- *Weakness:* What happens if a source is down? — That source returns nothing; the rest still work. In the author flow, a provider failure is reported as failure, not as an "unresolved" identity, and an incomplete pool blocks automatic assignment (safeguard B5).
- *Weakness:* Did you measure deduplication accuracy? — No. We tested it with unit and integration tests, but no accuracy figure is reported for deduplication.

**Transition:** "Next, how we tested the author-matching part, which is the research question."
(Slide 9 Tech Stack and 10 Schedule belong to Nicholas and Akshad; slide 11 is the demo. After the demo:) "Thanks Akshad.
Let me explain how we tested the matching."

---

## Slide 12 — Dataset & Experimental Methodology

**SAY**
"To test author matching we needed names whose true person is known. We used LAGOS-AND, version 2.0, a public dataset
of author names grouped by person using ORCID identifiers and DOIs. It has about 1.48 million records in around 80
thousand name groups.

Important: the grouping is built *automatically* from ORCID, not checked by humans. So we call it a benchmark label, not
absolute truth. The system's own source of candidates, OpenAlex, also stores ORCIDs, so agreement can be partly shared
information. That is the leakage risk, and it is why we say our results are exploratory.

Here is what we did, left to right. We chose name groups and prepared test cases, and we froze the inputs before running,
with fixed random seeds, and no ORCID is given to the system. For each case HAMMER asks OpenAlex for up to ten possible
authors. We evaluate each with the signals, and then the decision rules give an outcome.

There are three test settings. C0: name only. C1: name plus a workplace and a year range taken from one paper of the real
person. That is our main setting. C1x: also gives paper identifiers, but those come from the answer person's own papers,
so it leaks; we report it separately and never as the main result.

Finally, the five signals: name, institution, publication overlap, co-author and timeline. Five are built. In this dataset
the co-authors come only as name strings, so the co-author signal could not be used, and publication overlap is used only
in the leaky C1x. So in the main test only name, institution and years were available. We ran two real samples: 50 cases,
then 18 cases, and we keep them separate."

**WHAT THE SLIDE MEANS.** The left box is the data; the top row is the pipeline; the bottom left lists the signals; the
bottom row lists the outcomes; the right box says what we looked at: whether the right person is found, how often the system
decides alone, how often it asks a human, and whether the run can be repeated.

**TERMS**
- *LAGOS-AND:* a large gold-standard dataset for author name disambiguation. 1,476,550 rows, 80,294 name blocks, 244,564 identity groups; built from ORCID and DOI evidence.
- *ORCID:* a persistent identifier that researchers register for themselves. *DOI:* a unique identifier of a paper.
- *Block:* all records that share one printed name form. *Smoke sample:* 50 cases from 23 blocks to check the pipeline runs; *exploratory sample:* 18 completed cases.
- *Freeze manifest:* a fingerprinted record of inputs, code and seeds fixed before the run so nothing can be tuned after seeing results.
- *Leakage:* the answer reaching the system (or its candidates) through another route. *Offline replay:* re-running the decision logic on saved provider responses, so results can be reproduced without calling the internet.
- *Seed:* the fixed starting number of a random draw, so the same sample is drawn every time.

**LIKELY QUESTIONS**
- *Basic:* Why LAGOS-AND? — Large, public, ORCID/DOI based, uses OpenAlex as its literature source, so it matches our candidate provider.
- *Basic:* What are C0, C1, C1x? — As above. Only C1 is primary.
- *Technical:* How did you stop the answer leaking in? — Seeds hold no ORCID, no pid, no co-author field. DOIs of the person's other papers are kept out of C1; only the one designated DOI feeds C1x. Tests scan all artifacts for the gold ORCIDs.
- *Technical:* Why did you reuse an affiliation and year from one of the person's papers? — That is what a user would know about a new paper. We record this as a design limitation: it gives a weak hint about group membership.
- *Challenge:* Why not just use the ORCID to check accuracy? — ORCID labels are automatically attached and OpenAlex also carries ORCIDs, so agreement may reflect shared source. Also only 57.5% of returned candidates had an ORCID in the smoke capture. That is why independent human verification is the next step.
- *Challenge:* Why only 50 and 18 cases? — 50 was a designed smoke test. The second was drawn as 50, but the free OpenAlex tier ran out of quota (HTTP 429) after 18 cases, and we had no budget for a paid key. We report it as an 18-case exploratory sample.
- *Weakness:* So did you validate the five signals? — Implemented and unit-tested, yes; evaluated, no: at most four were observable, and co-author was never available.
- *Weakness:* Are the weights validated? — No. They are engineering defaults, uncalibrated.

**Transition:** "Nicholas will now show what we found."

---

## Slide 14 — Software Testing & Validation (after Nicholas's results)

**SAY**
"Results mean nothing if the software is unreliable, so here is how we tested. Four areas. Functional: unit and integration
tests of the modules, the web interfaces and the decision rules, including error handling. Data integrity: checking the
database stays consistent and every result can be traced to its source, and making sure the answer key never leaks into a
decision. Reproducibility: replaying saved data offline, checking digital fingerprints, and comparing repeated runs.
And safeguards: automatic, manual and unresolved outcomes are all tested, including cautious limits and source failures.

The numbers: 591 automatic tests pass. In the 50-case capture, all 92 real data requests succeeded. And two bugs showed up
when we moved from tests to real runs. One was a file-format mismatch in our own evaluation seed file. The other was in our
cost-protection code: it mishandled compressed responses and wasted requests until we fixed it and added a test.

We want to be precise about what this proves. It proves the software behaves as designed, is repeatable, and keeps the
answer key out. It does not prove the author matching is accurate; that needs independent human verification, which is
future work."

**TERMS**
- *Unit test:* tests one small function. *Integration test:* tests modules together. *pytest:* the Python test tool.
- *Mock:* a fake stand-in for an outside service so tests do not call the internet.
- *SHA-256 fingerprint:* a hash of a file; if one byte changes the hash changes.
- *Mutation check:* deliberately break the code and confirm a test fails — proves the tests can catch mistakes.
- *Negative control:* a case that must fail, to prove a check is not blind.

**LIKELY QUESTIONS**
- *Basic:* What do 591 tests prove? — That the code does what we wrote it to do, including rules, edge cases and failures.
- *Technical:* Do passing tests mean the model is accurate? — No. Tests check behaviour against our intended rules; accuracy needs labelled evidence from independent reviewers.
- *Technical:* Are the tests against the live internet? — External services are mocked. The 92 real requests were a separate capture.
- *Challenge:* How do you know your tests are not weak? — Mutation checks: we introduced deliberate bugs (6, 11, 10, 15, 12 per module) and each made a test fail.
- *Challenge:* Why "92 of 92"? — That is for the 50-case capture. An earlier attempt with a placeholder key got 40 HTTP 401s, and the second capture hit the quota. We kept those records.
- *Weakness:* Any end-to-end test on the web app? — The API and logic are tested; we demonstrated the UI manually (demo) on replayed real responses.

---

## Delivery guide for Namit

**Do not say:** "accuracy", "ground truth", "proved", "the system is 76% accurate", "probability", "uses machine learning to match authors", "all five signals were tested".

**If interrupted:** stop, answer the question in one or two sentences, then say "I'll cover that in a moment" if it is on a later slide, or return with "As I was saying…".

**If you don't know:** "I don't have that number with me; what I can say is… , and I'd rather not guess." Then name the file or the teammate who owns it.

**Closing line (after slide 14):** "To summarise my part: we designed HAMMER as a cautious pipeline, tested the software thoroughly, and we are honest that
accuracy still needs independent human verification."

---

## Viva depth: concepts Namit must be able to explain

For each: what / why / how built / why this / alternatives / limits / likely question.

### 1. Author entity resolution and candidate retrieval
- **What:** deciding which real person (profile) an author name on a paper refers to.
- **Why:** many people share names (Rahul Sharma at IIT Bombay and IIT Delhi); wrong merges corrupt citation counts.
- **How:** `POST /author-resolutions/candidates` → `author_resolution/resolver.py` → asks OpenAlex for up to 10 candidates (R2 strategy: cleaned name, then a broader search/initials fallback) → enrichment → evidence → score → policy.
- **Why OpenAlex:** free, open, has author profiles with ORCID/institutions/works, and it is LAGOS-AND's literature source.
- **Alternatives:** Google Scholar (scraping, no API), ORCID API (only registered people), Scopus (paid).
- **Limits:** one provider; if the person's profile is not in the pool the system cannot find them (in the samples the expected profile was in the pool 76% and 72% of the time by benchmark label).
- **Panel asks:** what if the correct author is not retrieved? — Then every candidate is wrong; the policy still routes to manual review or unresolved, and the ground-truth check shows "expected ORCID not in pool" for 12 of 50 and 5 of 18 cases (some because the right profile has no ORCID).

### 2. Five evidence signals, weights, renormalisation
- Name 0.35, institution 0.25, publication overlap 0.20, co-author 0.10, timeline 0.10.
- **Renormalisation:** if a signal is unavailable (query lacks it or candidate lacks it), it is left out and the remaining weights are rescaled to sum to 1. Missing is **not** zero; a zero means "observed and does not support".
- **Danger:** a score of 1.0 can come from one signal alone, and two candidates may be scored on different signals, so scores are not directly comparable. Hence the rules: at least two observed signals, and safeguard B4.
- **Weights:** engineering defaults, not learned, not calibrated. The score is a heuristic, not a probability.
- **Alternative:** train a classifier on labelled pairs (needs verified labels we do not have); calibrate weights on verified data (future work).

### 3. Decision policy
- Automatic if: top score ≥ 0.75, at least two observed signals, lead over runner-up ≥ 0.15, and top ≥ 1.35 × runner-up (G1, G2); single-candidate pool waives the lead rule (G3).
- Safeguards that only withhold automation (B1–B5): unscored competitor; top has no observed non-zero institution/publication/co-author signal (so name + years alone is never enough); top has an observed zero; competitor scored on a different signal set; enrichment or parsing failure.
- **Manual review:** not automatic but top score ≥ 0.45. **Unresolved:** otherwise, or empty/unscored pool. Provider failure is a separate category: no decision recorded.
- **Why conservative:** a wrong automatic merge is worse than asking a person.
- **Result:** with name only, automatic assignment is structurally impossible (coverage 0 by design — not evidence of safety).

### 4. Benchmark leakage and verified vs benchmark-derived
- Benchmark-derived agreement = selected profile carries the dataset's ORCID. It is a provisional label.
- Verified accuracy = independent blinded reviewers (two reviewers + adjudicator) judge the cases. **Not done.**
- Reported figures that must not be called accuracy: 38/50 and 13/18 in pool; 22/50 and 7/18 provider's first candidate; 17/50 and 6/18 HAMMER top-one; 4/50 and 0/18 automatic (3 of 4 agree).

### 5. Offline replay and reproducibility
- Real OpenAlex responses are recorded with SHA-256 hashes; replay serves them to the same code, so any run gives the same outputs; the freeze manifest fixes seeds, thresholds and code before the run.

### 6. Testing (see slide 14 above). Mutation checks, 591 tests, mocked services.

**Namit's hardest questions (answers prepared in `PART5`):** why did HAMMER not beat OpenAlex's first candidate; why so low automatic coverage; what is the research contribution; what would you do with six more months.
