# Part 3: Akshad Kedia — script and viva preparation

Slides: **2** Problem Description, **3** Problem Statement, **7** Scope, **10** Implementation Schedule (proposed; not in
your original table), **11** Application Demonstration, **15** Limitations & Future Scope.
Read `PART1_analysis_and_project_summary.md` and the "rules for everyone" at the top of `PART2`.

---

## Opening (after Namit's introduction)

**SAY**
"Thank you Namit. I will start with the problem we set out to solve."

---

## Slide 2 — Problem Description

**SAY**
"Think about how a university reports its research. A professor's papers are listed on several websites, such as Google
Scholar, DBLP and arXiv, and each site writes the same paper in its own way. So four things go wrong. One, the same paper
appears more than once. Two, the citation count is different on each site. Three, author names are ambiguous: there may be
many people called 'Rahul Sharma'. And four, affiliations are written in different styles, so 'IIT Bombay' and 'Indian
Institute of Technology Bombay' look like different places. Since no single system brings these together and cleans them,
the publication list and the citation numbers a department reports cannot be fully trusted."

**WHAT THE SLIDE MEANS.** It is a plain description of messy data. The key point for the panel: two separate problems hide
in it: *same paper listed twice* (a paper-level problem) and *same name, different people* (a person-level problem).

**TERMS**
- *Metadata:* data about a paper: title, authors, year, DOI, citations, affiliations.
- *Duplicate record:* two entries that describe the same paper.
- *Citation reconciliation:* choosing one citation count when sources disagree. In HAMMER we keep the highest value across sources and record which source it came from; it is a simple rule.
- *Affiliation:* the institution an author is attached to.

**LIKELY QUESTIONS**
- *Basic:* What is the actual problem? — The same research is recorded inconsistently across platforms, so lists and counts are unreliable.
- *Basic:* Why does it matter? — Institutions use publication counts and citations for reports and rankings.
- *Technical:* Why can't we just use Google Scholar or OpenAlex? — Each is one source with its own gaps and errors; neither gives you the combined, de-duplicated record with the source of every field, nor a reviewable identity decision with evidence. OpenAlex is, in fact, our main source of author candidates.
- *Challenge:* Slide says Google Scholar. Do you use it? — We built a connector, but it is switched off by default because it scrapes a website; the reported system uses OpenAlex, Crossref, DBLP and arXiv.
- *Weakness:* Did you fix the citation counts? — We take the maximum across sources and keep the source. We did not evaluate this against a reference.

**Transition:** "That is the problem. In one sentence, here is what we set out to build."

---

## Slide 3 — Problem Statement

**SAY**
"Our statement is: build one system that collects publications from several sources and cleans them: finding duplicates,
standardising affiliations, reconciling citations, and working out which author is which. I will be honest about one
word on this slide, 'machine learning'. In the final system, the author decision is made by an evidence-based scoring
method with fixed rules; we did not train a model for it. Machine-learning embeddings are used in the semantic search part.
So when you hear 'name disambiguation' from us, it means careful evidence scoring, not a trained classifier."

**TERMS**
- *Name disambiguation:* telling apart people with the same or similar names.
- *Embedding model (all-MiniLM-L6-v2):* a small pre-trained language model; the only learned model in HAMMER, used for finding similar papers.
- *Rule-based vs machine learning:* rules are written by us; ML learns from labelled examples. We had no verified labels to learn from.

**LIKELY QUESTIONS**
- *Technical:* Where is the machine learning? — In the semantic search (a pre-trained embedding model). Author matching is a transparent weighted score with decision rules. Duplicate detection uses string similarity (RapidFuzz) with rules.
- *Challenge:* Then why does the statement say ML? — It was our original plan. In the final implementation we chose an explainable method because labelled verified data to train on did not exist, and explainability was one of the gaps we found.
- *Challenge:* Why not train a classifier now? — Needs verified labels; the benchmark's labels are provisional and leakage-prone. Training on them would hide the same problem. This is future work.

**Transition:** "Nicholas will now take you through what other researchers have done."

---

## Slide 7 — Scope (after Namit's gaps slide)

**SAY**
"So what is in scope? On the functional side: we collect publications from multiple sources; clean the title, authors, year,
DOI and citations; find and merge duplicates; fetch author candidates and decide the identity using five kinds of evidence: name,
institution, publication overlap, co-authors and timeline; support three outcomes (automatic, manual review, unresolved);
provide search by meaning; and keep the records, the author information, the decision history and where each fact came from.

Non-functional means qualities we promised: reliability, transparency (we keep the evidence), maintainability (modular code),
reproducibility (replaying saved data), data integrity, performance, usability and room to grow.
One clear statement: we built five evidence signals, but in our experiment only some of them had data."

**WHAT THE SLIDE MEANS.** Left = what the system *does*; right = how well it should behave. Both are claims about design;
the evaluated parts are only the author-resolution experiment and the software tests.

**TERMS**
- *Functional requirement:* a feature. *Non-functional requirement:* a quality (speed, reliability, etc.).
- *Provenance:* who supplied what. *Resolution history:* stored record of each decision.

**LIKELY QUESTIONS**
- *Basic:* What is not in scope? — Real-time updates, very large collections, training models, and human verification of results.
- *Technical:* Which requirements did you actually test? — Reproducibility, data integrity and the decision behaviour are covered by the tests; "performance" and "scalability" are intentions: we did not run load tests.
- *Challenge:* "Scalability" is listed; how do you scale SQLite? — We don't claim to. SQLite suits this project; moving to PostgreSQL is future work.
- *Weakness:* Did you evaluate duplicate detection? — Tested for behaviour, not measured for accuracy.

**Transition:** "Namit will now explain the architecture." (Slide 8.)

---

## Slide 10 — Implementation Schedule

**SAY** (adapt to your own memory of the months)
"This chart shows how we spread the work from February to November: literature and problem study first, dataset and platform
study, architecture design, then data collection and cleaning, then duplicate detection and author matching, and finally
integration, testing, documentation and this demonstration. Several steps overlapped, and the evaluation work grew in the last months,
because we decided to evaluate the author matching carefully rather than only demonstrate it."

**LIKELY QUESTIONS**
- Which part took the longest? — Answer from your own memory; a safe truthful answer is the evaluation design, because we had no verified labels and chose to build a reproducible protocol.
- Did you meet the plan? — Be honest: the application and the evaluation tooling are done; independent verification is not.

---

## Slide 11 — Application Demonstration

**Before the demo.** The demo runs with saved real OpenAlex responses (replay), so it works without internet and without a
key. Start both servers beforehand and test once. If the app fails, switch to the screenshots (keep them in the deck backup) and say so calmly.

**SAY (while clicking)**
"Step 1. I open the Author Identity Resolution tab and type a researcher's name. The name is enough. I can also add the
workplace and the years the person was active, but nothing extra is required.
Step 2. The system lists people with similar names and shows why each scored as it did: you can see the evidence behind each score
under 'heuristic score band'. In this example three people scored 0.88, 0.84 and 0.83.
Step 3. Notice the three scores are close. Our rule says the best must be clearly ahead of the second best, by at least 0.15, and also
at least 1.35 times as high. Here it is not, so the system does not guess: it sends the case to a human reviewer. It decides by itself only
when one match is clearly the best and enough evidence exists. If I give the name alone, it never decides automatically, by design."

Optional (only if time): show a normal paper search, where merged papers show their sources.

**WHAT THE DEMO PROVES.** The workflow works end to end and the system is cautious. It does **not** prove accuracy; the
example is one saved case.

**TERMS**
- *Heuristic score band:* High/Medium/Low label from the same two thresholds; a display convenience, not calibrated, not a probability.
- *Replay:* saved real responses are served instead of calling the live provider.
- *Manual review:* a person must choose. *Automatic:* the system assigns.

**LIKELY QUESTIONS**
- *Basic:* Why did it not choose the 0.88 one? — Because 0.88 vs 0.84 is a gap of only 0.04, far below the 0.15 required; a wrong automatic assignment is worse than asking.
- *Technical:* What does 0.88 mean? — A heuristic score from 0 to 1 built from weighted evidence; it is not a probability that the profile is right.
- *Technical:* Is this live data? — Saved real responses from OpenAlex, replayed. The same logic runs live when a provider is reachable.
- *Challenge:* In your experiments the "right" one was also not the top-scored one often. — Yes: HAMMER's top pick agreed with the dataset label 34% (17/50) and 33% (6/18) of the time, below the provider's first candidate (44% and 39%). Our heuristic ordering did not improve on OpenAlex's ordering in these samples; that is why the system asks a human.
- *Weakness:* Can the user override? — Manual review is exactly that: a person selects the candidate; the decision and evidence are stored.

### Worked example (hypothetical, not a result)
Two profiles for "Rahul Sharma": A at IIT Bombay, B at IIT Delhi. The user supplies IIT Bombay and 2015–2022.
- Signals available: name, institution, timeline (weights 0.35, 0.25, 0.10 → total 0.70, rescaled to 1).
- A: name 1, institution 1, timeline 1 → score 1.00. B: name 1, institution 0 (observed, different), timeline 1 → 0.45/0.70 ≈ 0.64.
- Lead 0.36 ≥ 0.15 and 1.00/0.64 ≈ 1.56 ≥ 1.35; at least two observed non-zero signals → **automatic: A**.
- Variant: both candidates list IIT Bombay → both 1.00 → lead 0 → **manual review**.
- Variant: A's profile has no institution on record → rescaled over name and timeline only → no institution/publication/co-author evidence → safeguard B2 → **manual review**.
- Variant: no candidate at all → **unresolved (empty retrieval)**.
These numbers are made up to teach the logic; never present them as results.

**Transition:** "That is the system in action. I will hand over to Namit, who will explain the dataset and how we tested it." (Order after your demo: Namit slide 12 → Nicholas slide 13 → Namit slide 14 → you slide 15.)

---

## Slide 15 — Limitations & Future Scope

**SAY**
"We want to be open about the limits. First, source data can be incomplete, and author details such as affiliations and
co-authors can be missing, which weakens the evidence. Second, people with similar names remain hard. Third, the matching settings,
the weights and thresholds, are fixed engineering choices and have not been checked against human-verified answers. Fourth, we tested on
only 68 real searches, in two small samples of 50 and 18, and the 'right answer' in them is a dataset label, not human-verified.

For the future: add more sources; make better use of affiliation and co-author information; test on many more searches checked by independent
human reviewers; and then use that verified data to tune the settings. We have already written the evaluation protocol, the sampling tools and the
reviewer-packet tools for that step. The one thing it needs is people: independent reviewers."

**TERMS:** *Independent human verification:* two reviewers who have not seen HAMMER's answer or the dataset label judge each case; a third resolves disagreements. *Tuning/calibration:* adjusting weights and thresholds using verified data.

**LIKELY QUESTIONS**
- *Basic:* Biggest weakness? — No verified accuracy; low automatic coverage.
- *Technical:* Why is automatic coverage low? — Top scores are high (median 0.88) but competitors with similar names score nearly the same: the lead was below 0.15 in 37 of 50 and 14 of 18 cases, and the 1.35 ratio failed in 44 and 17; fewer than two observed signals in 14 and 3.
- *Challenge:* Is low coverage a failure? — For a cautious system it is the intended behaviour, but it also means the benefit is small until the evidence improves; coverage must be balanced against precision, which we cannot yet measure.
- *Challenge:* What would you do with six more months? — Recruit independent reviewers, run the verified evaluation on a probability sample, calibrate weights, add co-author and affiliation-ID evidence, test a second provider, and measure deduplication accuracy.
- *Weakness:* Why not do the human verification already? — It needs independent reviewers and time; we deliberately did not simulate reviewers or invent labels.

**Closing line (your last):** "We built the system and a way to test it honestly; the next step is people to verify it."

---

## Delivery guide for Akshad

**Do not say:** "machine learning disambiguation", "Google Scholar integration works", "we solved the duplicate problem", "accuracy", "very sure means correct", "scalable".
**If the demo breaks:** "Let me show the saved screenshots; the logic is the same." Do not debug live.
**If interrupted:** answer briefly, then continue. **If you don't know:** "That is Namit's/Nicholas's area; I would rather not guess."

## Viva depth: concepts Akshad must be able to explain
1. **Deduplication vs author disambiguation.** Dedup: records of works; checks DOI veto/force-merge, edition markers, year gap ≥ 4 without DOI forbids, then weighted title/author/year similarity against a source-pair threshold and a title floor; groups by union-find; merged record keeps per-field source. Author resolution: people; evidence scoring against candidate profiles; separate scores, no shared inputs. Alternatives: ML pair classifiers, clustering. Limit: no accuracy measured for dedup.
2. **Why three outcomes.** Automatic (strong, safeguarded), manual review (plausible but not clear), unresolved (nothing plausible or no score), plus provider failure kept separate; the aim is to never silently guess.
3. **Missing information.** Unknown ≠ no. Left out and weights rescaled; but then scores over different signal sets are not comparable (B4) and a single-signal score can be 1.0 (needs at least two signals).
4. **Heuristic score vs probability.** A probability would have to be calibrated against verified outcomes; we have none, so we call it a score and say so.
5. **Benchmark-derived vs verified.** See PART2 §4.
6. **Limitations and future work** (above).
