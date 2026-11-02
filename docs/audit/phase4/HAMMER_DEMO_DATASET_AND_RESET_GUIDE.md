# HAMMER Demonstration Dataset & Reset Guide

**System:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Topic:** Reproducible Demo Execution & Safe State Reset  

---

## 1. Verified Local Demonstration Corpus

The demonstration relies strictly on the frozen baseline database:
- **Location:** `backend/academic_search.db`
- **Total Publications:** 454 canonical papers
- **Core Topics:** Deep learning, neural networks, transformers, capsule architectures, diffusion models, computer vision.
- **Key Authors:** Geoffrey Hinton, Yoshua Bengio, Yann LeCun, Kaiming He, Alex Krizhevsky.

---

## 2. Safe Demonstration Reset Procedure

If manual candidate selections or test queries are executed during a viva demonstration, the database can be reset instantly to its pristine Phase 4 baseline:

```bash
# 1. Stop backend service
kill -9 $(lsof -ti:8000)

# 2. Restore baseline database snapshot
cp backups/phase4_baseline_20261101_173430/backend_academic_search.db backend/academic_search.db

# 3. Restart backend service
cd backend && venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```
