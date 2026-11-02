# HAMMER — Viva Readiness Guide

## 1. One-Sentence Summary

HAMMER is a hybrid academic metadata system that ingests publications from four scholarly APIs, normalises and deduplicates them using blocking + fuzzy scoring, resolves ambiguous author identities through five evidence signals and a conservative decision tree, and explains retrieved evidence using a live Gemini LLM with zero-trust citation validation.

---

## 2. Anticipated Questions & Defensible Answers

### On Deduplication

**Q: Why use fuzzy matching rather than exact DOI matching?**  
A: DOIs are only present in ~60% of records. DBLP and older ArXiv entries often lack DOIs. Fuzzy matching handles the remaining 40% using title, author, and year signals. Exact DOI matching is still the first priority; fuzzy is the fallback.

**Q: What prevents false positives in deduplication?**  
A: Three mechanisms: (1) source-pair-aware thresholds (Scholar requires 0.92-0.95 due to lower data quality), (2) a blocking pass that requires at least one cheap anchor before fuzzy scoring runs, and (3) manual exclusion overrides for known false merge cases.

**Q: How do you handle the same paper appearing with slightly different titles?**  
A: `rapidfuzz.fuzz.token_sort_ratio` is word-order invariant. "Deep Learning in Computer Vision" and "Computer Vision Deep Learning" score identically. Additionally, punctuation is stripped and whitespace collapsed before comparison.

---

### On Author Resolution

**Q: Why is your auto-resolution threshold so conservative (0.75)?**  
A: A false disambiguation is worse than no disambiguation. If we auto-select the wrong person, every subsequent publication result is silently contaminated. The three-gate design (score ≥ 0.75 AND margin ≥ 0.15 AND dominance ≥ 1.35) ensures the top candidate is not just good in absolute terms but clearly better than the alternative.

**Q: What happens when institution hint is missing?**  
A: The institution_similarity signal returns `UNAVAILABLE`. The scoring formula re-normalises the remaining weights over available signals only. The total score is still meaningful — it just relies on name, publications, coauthors, and temporal signals.

**Q: How is the coauthor overlap computed?**  
A: Coauthor names from the request context and from OpenAlex are normalised to `FIRST_INITIAL_LASTNAME` format (e.g. "Y_LECUN"), and the Jaccard intersection is computed. This prevents "John Lee" matching "J Lee" as a different person while avoiding full-name string sensitivity.

**Q: Can the system be gamed by providing false coauthors?**  
A: The context is provided by the user and is not cross-validated against external sources. The system is designed for internal research use, not adversarial settings. The evidence trail records exact raw values, so any input can be audited.

---

### On Semantic Retrieval

**Q: Why use all-MiniLM-L6-v2?**  
A: It is a well-benchmarked, lightweight (80MB), Apache-licensed sentence embedding model that runs locally without API calls. It scores well on BEIR benchmarks for document retrieval tasks. The key constraint is offline demonstration reliability — a local model ensures the demo works without internet access.

**Q: What is the minimum similarity score and why 0.35?**  
A: 0.35 was determined empirically from Phase 4 evaluation runs. Below this threshold, retrieved documents were consistently topically irrelevant to the query. The floor prevents low-quality hits from being sent to Gemini and from appearing in the response.

**Q: How does the deduplication within retrieval results work?**  
A: After ChromaDB returns up to `top_k × 4` candidates, we build a `seen_keys` set containing canonical_id, DOI, and normalised title. If any of these three keys for a new hit already appear in seen_keys, the hit is dropped. This prevents the same paper appearing twice under different embeddings.

---

### On Gemini Integration

**Q: How do you prevent the LLM from hallucinating citations?**  
A: Zero-trust citation validation. Every claim the LLM returns must include `document_ids` — a list of IDs from the retrieved documents. We cross-reference each cited ID against `hit_by_id` (a dict built from actual retrieved hits). Any claim that cites a document not in the retrieval set is silently dropped. The LLM cannot invent document references.

**Q: What if Gemini is unavailable during the demo?**  
A: A five-level fallback hierarchy ensures the system always responds. If Gemini is unreachable, the system returns a deterministic summary of retrieved publication titles with status `provider_error_fallback`. This is also the path when `GEMINI_API_KEY` is not set.

**Q: Why temperature=0?**  
A: Reproducibility. With temperature=0, the same query + retrieved documents produce the same explanation. This makes the system evaluatable — you can run the same query twice and get the same result.

---

### On Architecture Decisions

**Q: Why SQLite instead of PostgreSQL?**  
A: The system is a single-node research prototype. SQLite with aiosqlite provides async-safe access, eliminates a server dependency, and keeps the demo setup to a single file copy. The schema is fully PostgreSQL-compatible via SQLAlchemy if scaling is needed.

**Q: Why not use FAISS instead of ChromaDB?**  
A: ChromaDB provides persistence out of the box (directory-based), has a Python-native interface, and stores metadata alongside embeddings. FAISS requires manual metadata management and a separate serialisation step. For research prototype scale (449 embeddings), ChromaDB is more than adequate.

**Q: How does the circuit breaker work?**  
A: Each source connector tracks consecutive failures in `circuit_breaker_state`. After 5 failures (configurable), the source enters `open` state and is skipped for 15 minutes. After the timeout, it transitions to `half_open` and one test request is allowed through. This prevents a single unstable source from blocking the entire search.

---

## 3. Live Demo Script

### Setup (before demo)

```bash
# Terminal 1 — Backend
cd backend && source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
```

### Demo Flow (5 minutes)

1. **Open browser** at `http://localhost:5173`

2. **Search for publications**: Type `Geoffrey Hinton` → Show multi-source results with source badges, merge indicators

3. **Show metrics**: `GET http://localhost:8000/metrics` → 454 publications, 2053 raw records, 4.5× compression

4. **Show dedup log**: Click any paper → Show similarity log with merge scores

5. **Author resolution**: Trigger `/search/candidates?name=Y+LeCun` → Show candidate selection flow

6. **Evidence search**: Submit a semantic query → Show ChromaDB hits with cosine scores and Gemini explanation

7. **Show test suite**: `backend/venv/bin/python -m pytest backend/tests/ -v --tb=short` → 55/55 passing

---

## 4. Key Numbers to Memorise

| Metric | Value |
|--------|-------|
| Sources integrated | 4 active (6 implemented) |
| Publications in DB | 454 |
| Raw source records | 2,053 |
| Dedup compression | ~4.5× (2053 → 454) |
| Evidence signals | 5 |
| Auto-resolve threshold | score ≥ 0.75, margin ≥ 0.15, dominance ≥ 1.35 |
| ChromaDB embeddings | 449 |
| Embedding model | all-MiniLM-L6-v2 (384-dim) |
| Retrieval floor | 0.35 cosine similarity |
| Gemini model | gemini-3.5-flash |
| Automated tests | 55 / 55 passing |
| Alembic migrations | 1 (author resolution foundation) |
| Database tables | 16 |

