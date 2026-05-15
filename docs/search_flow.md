# Search & Identity Flow

The system employs a "Candidate First" approach to solve the author ambiguity problem (e.g., multiple "Andrew Ng").

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant OA as OpenAlex
    participant C as Connectors
    participant P as Pipeline

    U->>F: Search "Andrew Ng"
    F->>B: GET /search/candidates
    B->>OA: fetch_authors()
    OA-->>B: Candidate list
    B->>B: Compute Dominance Ratio
    alt Dominance Ratio > 3 & Score > 0.6
        B-->>F: Auto-selected Candidate
    else Manual Selection Required
        B-->>F: List of Candidates
        F->>U: Show Selector UI
        U->>F: Select Profile
    end
    
    F->>B: GET /search?author_id=...
    B->>B: Check Cache
    alt Cache Hit
        B-->>F: Results
    else Cache Miss
        B->>C: Parallel Fan-out (OpenAlex, DBLP, ArXiv, etc)
        C-->>B: Raw Source Records
        B->>P: Normalize & Deduplicate
        P-->>B: Canonical Papers
        B->>B: Save to DB & Cache
        B-->>F: Final Merged Results
    end
    F->>U: Display Papers
```

## Dominance Ratio Formula
To determine if an author is "unambiguous", we use:
`dominance_ratio = (top_candidate_works) / (second_candidate_works + 1)`

If `dominance_ratio > 3` and the top score is high, we bypass manual selection.
