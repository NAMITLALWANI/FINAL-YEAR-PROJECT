# HAMMER Offline Demonstration Readiness

**System:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Topic:** Zero-Internet Viva Defense Guarantee  

---

## 1. Offline Capability Matrix

| Subsystem | Internet Required? | Offline Fallback Mechanism | Status |
|---|---|---|---|
| **Frontend UI** | **NO** | Pre-bundled Vite static assets served locally | **100% Offline** |
| **API Endpoints** | **NO** | Local FastAPI server on `localhost:8000` | **100% Offline** |
| **Relational Database** | **NO** | Local SQLite `backend/academic_search.db` | **100% Offline** |
| **Vector Search** | **NO** | Local ChromaDB collection `backend/vector_index` | **100% Offline** |
| **Embedding Generation** | **NO** | Local `all-MiniLM-L6-v2` ONNX model | **100% Offline** |
| **Candidate Generation** | Optional | Cached candidate snapshots in database | **100% Offline** |
| **Scholarly Explanations**| Optional | Local deterministic evidence summarizer | **100% Offline** |

---

## 2. Examiners' "Unplug the Cable" Test

If the examiner asks: *"Will your system crash if the internet disconnects right now?"*
- **Answer:** *"No, sir. Core search, author candidate scoring, deduplication, vector retrieval, and evidence explanations run entirely against our local SQLite and ChromaDB indices with local deterministic fallbacks."*
