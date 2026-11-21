# Part 5: shared team question bank (all three members must know these)

Answer style: short, plain, honest. Numbers in brackets are from the paper (benchmark-derived, exploratory, not verified accuracy).
**Always:** heuristic score (not probability); benchmark label (not truth); 50 and 18 are separate samples; at most four signals were available in the experiment.

## A. The project

**What exactly is HAMMER?**
A system that collects scholarly records from OpenAlex, Crossref, DBLP and arXiv, merges duplicate papers, and helps decide which real author profile a
name refers to, using evidence and cautious rules. Search by meaning and an optional explanation are included.

**What is the actual problem?**
The same paper appears differently on different platforms (duplicates, different citation counts), and names are ambiguous (many people share a name).

**Why can't we just use Google Scholar or OpenAlex?**
Each is a single source with its own errors. HAMMER combines sources and keeps where every field came from. For authors, it gives a reviewable decision with
evidence and an honest "manual" or "unresolved" outcome. OpenAlex is also what we use to fetch author candidates.

**Why OpenAlex for candidates?**
Open, free, structured author profiles with ORCID, institutions and works; it is the literature source of LAGOS-AND. Limit: one provider; free tier has a shared daily budget.

**What is the research contribution?**
Not a new algorithm (the paper says so). It is an implemented workflow that separates retrieval, ranking and identity decision; treats missing evidence as unknown;
uses conservative gates with a manual/unresolved outcome; and a leakage-aware, reproducible evaluation protocol with honest exploratory results.

**What are the biggest weaknesses?**
No independently verified accuracy; low automatic coverage; heuristic, uncalibrated weights; one provider; small samples; co-author evidence unavailable in the experiment; deduplication accuracy not measured.

**What would you do with six more months?**
Recruit independent reviewers; run the verified evaluation on a probability sample; calibrate weights and thresholds on verified data; add co-author and institution-ID evidence;
test a second provider; measure deduplication accuracy; try a learned model once verified labels exist.

## B. Paper deduplication vs author identity

**How is deduplication different from author disambiguation?**
Dedup: "are these two records the same paper?" It uses DOIs, titles, authors, year. Author resolution: "which real person is this name?" It uses name, institution, publication overlap, co-authors and years. Different questions, different scores, no shared inputs; a merged paper's confidence field is not used to identify authors.

**How does dedup work?**
Cheap blocking, then deterministic rules (same valid DOI forces merge; conflicting DOIs forbid; conflicting edition markers forbid; year gap of four or more without a DOI forbids), then weighted similarity of title, author keys, year against a threshold that depends on the pair of sources, with a title-similarity floor. Groups by union-find. Citation count = maximum across sources, with source recorded. Not measured for accuracy.

## C. Author evidence, scoring and decisions

**How do we distinguish two researchers with the same name?**
By institution, shared papers, co-authors and active years, scored for each candidate. If the evidence does not separate them (scores close) the system asks a person.

**How are scores calculated?**
Each available signal gets a value from 0 to 1. The weights are name 0.35, institution 0.25, publication overlap 0.20, co-author 0.10, timeline 0.10. Unavailable signals are left out and the rest rescaled to sum to 1. Score = weighted average.

**Why those weights? Are they scientifically validated?**
Engineering defaults reflecting that name and institution are the most informative cheap signals. They are not validated or calibrated; the paper says so. Calibrating them needs verified labels.

**What happens when information is missing?**
Unknown is not "no". It is excluded and weights are rescaled; but then at least two observed signals are needed for automatic assignment, name plus years alone is never enough, and candidates scored on different signals block automation (B4).

**Why does the system refuse to assign automatically?**
Because the rules require the top score ≥ 0.75, a lead ≥ 0.15, a ratio ≥ 1.35, at least two observed signals, and no safeguard blocker. In practice, near-ties and thin evidence block it most often.

**Manual review vs unresolved?**
Manual review: top score ≥ 0.45 but not strong enough to automate; a person chooses. Unresolved: no candidate with a defined score or an empty pool; nothing to choose from. Provider failure is separate: no decision is recorded.

**Is the score a probability?**
No. It is a heuristic, not calibrated. The High/Medium/Low band is a display convenience.

**Implemented vs available signals?**
All five extractors are implemented and unit-tested. In LAGOS-AND: name always; institution and timeline where metadata exists; publication overlap only in the leaky exploratory C1x; co-author never (names only, no IDs). The main condition C1 uses name, institution and years.

## D. Evaluation

**What is LAGOS-AND?**
A large public author-disambiguation dataset (1,476,550 rows, 80,294 name blocks, 244,564 ORCID-based identity groups), built automatically from ORCID and DOI evidence.

**What is benchmark leakage?**
When the answer reaches the system by another route. Here, ORCID is both the dataset's label and a field in OpenAlex profiles, so agreement can partly reflect shared data. We also keep ORCIDs and answer DOIs out of the inputs, and C1x (which uses an answer-paper DOI) is exploratory only.

**Why are ORCID-based labels not independent accuracy?**
They are automatically assigned, may be wrong, may be missing (only 57.5% of returned candidates had one in the smoke capture), and are partly shared with the provider.

**Why did HAMMER not beat OpenAlex's first candidate?**
HAMMER's top pick agreed with the label in 17/50 (34%) and 6/18 (33%); OpenAlex's first result in 22/50 (44%) and 7/18 (39%). Our untuned heuristic order is not better than the provider's. The samples are small and not independent, so this is an observation, not a proven difference.

**Why was automatic assignment so low?**
4/50 and 0/18 under C1. Median top score was 0.88, but the lead over the runner-up was below 0.15 in 37/50 and 14/18, the dominance ratio below 1.35 in 44 and 17, and fewer than two signals in 14 and 3. Near-identical competitors.

**Were the 4 automatic assignments correct?**
3 of 4 agree with the label (75%, exact interval 19–99%); one disagrees and is unclassified (wrong assignment or a label issue). Too few to be informative.

**What if the right author isn't retrieved?**
Then every candidate is wrong. The expected profile was missing in 12/50 and 5/18 cases (some because it has no ORCID). The system should send these to manual review; with a wrong-only pool a high-scoring wrong candidate could in principle be assigned automatically, which is why independent verification of automatic assignments (and the audit of the rest) is the core of the planned evaluation.

**Why only 18 in the second sample?**
Free OpenAlex quota ended (HTTP 429) after 38 successful requests; we had no budget. Reported as an 18-case exploratory sample; the earlier failed attempt (70 wasted requests due to a guard bug) was kept as a negative result.

**What is independent human verification?**
Two reviewers outside the team, blinded to HAMMER's answers and dataset labels, judge each case; a third adjudicates. Cohen's kappa for agreement. Planned and fully tooled; not performed.

**What is offline replay and why?**
Saved provider responses (hashed with SHA-256) are served to the same code, so results are reproducible without the internet or paid keys, and tuning after the fact is blocked by a freeze manifest with fixed seeds and code.

## E. Testing

**What do the 591 tests prove? Does passing mean accuracy?**
They prove the code does what we specified: rules, edge cases, failure handling, metric arithmetic, no leakage of labels into outputs, reproducibility. They say nothing about whether the author is the right person. External services are mocked in the tests.

**How do you know the tests aren't weak?**
Mutation checks: deliberate bugs inserted; each made a test fail.

**Does a successful API response mean the author was identified correctly?**
No. HTTP 200 means the provider answered; correctness needs labelled evidence.

## F. Design decisions

**Why a cautious policy?**
Wrongly merging two people's publications is worse than asking a person; the policy trades coverage for safety.

**Why three outcomes, not two?**
To distinguish "plausible, human please choose" from "no usable candidate".

**Why an optional Gemini explanation?**
It only rewrites evidence already retrieved; decisions never depend on generated text; works without a key.

**Why SQLite, FastAPI, React, Chroma?**
Simple set-up, async API, a common UI stack, local vector search. Alternatives: PostgreSQL, Django/Flask, FAISS, scikit-learn models. Limits: SQLite concurrency; small embedding model.

**Where did you use machine learning?**
The pre-trained embedding model for semantic search. The author matching is rule-based scoring; nothing was trained.

## G. Traps (be ready)

- "Your slide lists pandas / scikit-learn / LangChain." → Not used in the final code; early plan.
- "Your slide says Google Scholar." → A scraper exists but is off by default.
- "Five signals?" → Five built, at most four available, main test used three (name, institution, years).
- "68 searches, 76%?" → Two separate tests of 50 and 18; 76%/72% means the labelled profile was in the candidate list, not accuracy.
- "Very sure?" → Strong evidence under our rules, not certainty; 3 of 4 matched the label.
- "92 of 92?" → For the 50-case capture; other attempts hit a placeholder-key failure and the quota.
- "Why 591 vs 52?" → An earlier draft said 52; the final count is 591 passing tests, checked after the repository cleanup.

## H. When you don't know

Say: "I don't want to guess. What I do know is … The exact figure is in our paper, section …" Then pass to the teammate who owns the slide.
