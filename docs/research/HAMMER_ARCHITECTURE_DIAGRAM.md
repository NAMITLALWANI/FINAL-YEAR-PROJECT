# HAMMER — System Architecture and Dataflow Specification

This document provides the formal architectural topology and dataflow diagrams for **HAMMER (Hybrid Academic Metadata Aggregator and Evidence-Guided Author Entity Resolution System)**, illustrating the strict operational separation between authoritative relational persistence, derived semantic indexing, and supplementary explanation generation.

---

## 1. End-to-End Pipeline Architecture

```mermaid
graph TD
    subgraph MultiSourceIngestion ["1. Multi-Source Ingestion & Connectors"]
        OA["OpenAlex API"]
        CR["Crossref API"]
        DB["DBLP API"]
        AX["arXiv API"]
        SC["Google Scholar (Scraper - Disabled by default)"]
        CB["Circuit Breaker & Rate Limiter Pool"]
        OA --> CB
        CR --> CB
        DB --> CB
        AX --> CB
        SC -.-> CB
    end

    subgraph MetadataNormalization ["2. Normalization & Deduplication Pipeline"]
        CB --> RAW["Raw Ingestion Staging (source_records)"]
        RAW --> NORM["Unicode NFC, Case & DOI Sanitizer"]
        NORM --> DEDUP["Deduplication Engine V2<br/>(Hard DOI Veto | Edition Guard | Year Gap | Title Floor)"]
        DEDUP --> MERGE{"Merge Decision?"}
        MERGE -- "Match (Duplicate)" --> GRP["duplicate_groups Table"]
        MERGE -- "Distinct / Canonical" --> PUB["publications Table<br/>(Authoritative SQLite Database)"]
        GRP --> PUB
    end

    subgraph AuthorResolutionPipeline ["3. Evidence-Guided Author Entity Resolution (V1)"]
        PUB --> AGG["Target Author Extractor"]
        AGG --> CAND_GEN["Candidate Generation<br/>(OpenAlex Querying | NFC Normalization | Surnames)"]
        CAND_GEN --> EV_EXT["Evidence Extractor<br/>(Name Sim | Affiliation | Coauthors | Overlap | Temporal)"]
        EV_EXT --> SCORER["Deterministic Scorer<br/>(Weights: Name 0.35, Inst 0.25, Pub 0.20, Co 0.10, Temp 0.10)"]
        SCORER --> DECIDE{"Decision Gates<br/>Score >= 0.75<br/>Margin >= 0.15<br/>Dominance >= 1.35"}
        DECIDE -- "Pass All Gates" --> AUTO["auto_selected<br/>(13/100 Benchmark V3)"]
        DECIDE -- "Plausible but Narrow" --> MAN["manual_selection_required<br/>(52/100 Benchmark V3)"]
        DECIDE -- "Insufficient Signals" --> UNRES["unresolved<br/>(35/100 Benchmark V3)"]
        AUTO --> RES_TABLE["author_resolutions Table<br/>(Authoritative SQLite)"]
        MAN --> HITL["Human-in-the-Loop Review UI"]
        HITL --> RES_TABLE
        UNRES --> RES_TABLE
        EV_EXT --> EV_TABLE["author_resolution_evidence Table"]
    end

    subgraph DerivedSemanticRetrieval ["4. Derived Semantic Retrieval Index"]
        PUB -.->|Background Ingestion| VEC_SYNC["Embedding Generator<br/>(sentence-transformers: all-MiniLM-L6-v2)"]
        VEC_SYNC --> CHROMA["ChromaDB Vector Store<br/>(449 Dense Vectors | 384-dim | Cosine Metric)"]
        USER_Q["User Semantic Query"] --> DENSE_SEARCH["Cosine Similarity Search<br/>(Distance Floor >= 0.35)"]
        CHROMA --> DENSE_SEARCH
        DENSE_SEARCH --> RET_HITS["Ranked Supporting Publications<br/>(Context for Review UI)"]
        RET_HITS -.-> HITL
    end

    subgraph SupplementaryExplanation ["5. Evidence-Grounded Explanation (Optional LLM)"]
        RET_HITS --> CTX_BUILD["Strict JSON Context Builder<br/>(Top-8 Documents | Untrusted Metadata)"]
        USER_Q --> CTX_BUILD
        CTX_BUILD --> GEMINI["Google Gemini 2.5 Flash API<br/>(Zero-Trust Prompt Schema)"]
        GEMINI --> PARSE["JSON Response Parser"]
        PARSE --> CITE_VAL{"Citation Containment Validator<br/>(All cited doc_ids in context?)"}
        CITE_VAL -- "Valid Attributions" --> DISPLAY["Verified Synthesis Summary"]
        CITE_VAL -- "Invalid / Hallucinated IDs" --> FALLBACK["Deterministic Fallback Summary"]
        PARSE -- "Malformed Output / API Failure" --> FALLBACK
    end

    classDef authoritative fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef derived fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef llm fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef human fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;

    class PUB,RAW,GRP,RES_TABLE,EV_TABLE authoritative;
    class CHROMA,VEC_SYNC,DENSE_SEARCH derived;
    class GEMINI,CTX_BUILD,PARSE,CITE_VAL,DISPLAY,FALLBACK llm;
    class HITL human;
```

---

## 2. Core Architectural Invariants

1. **System of Record Invariance:** SQLite strictly owns identity truth (`publications`, `authors`, `author_resolutions`, `duplicate_groups`). ChromaDB is purely downstream and rebuildable.
2. **Decision Isolation Invariance:** Semantic dense retrieval results in ChromaDB are strictly visual/contextual aids for the human-in-the-loop review interface; they do not alter the deterministic scores or decision gates of Author Resolution V1.
3. **Safety Through Abstention:** Cases failing the conservative dominance (1.35) or score margin (0.15) thresholds are never forced into an automatic merge, routing instead to human adjudication (`manual_selection_required`) or preserved as `unresolved`.
4. **Citation Defense Invariance:** The explanation pipeline never accepts unverified document IDs; any hallucinated reference triggers claim sanitization or fallback to deterministic evidence summaries.
