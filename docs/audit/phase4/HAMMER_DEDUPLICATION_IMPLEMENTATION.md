# HAMMER Publication Deduplication: Ingestion Idempotency Implementation

**System:** HAMMER (Hybrid Academic Metadata & Entity Resolution)  
**Topic:** Preventing Duplicate Publication Rows on Repeated Ingestion  

---

## 1. Identified Defect: Ingestion Idempotency Failure

During baseline forensics, 100 publication rows in `publications` were found to have `canonical_id = "raw_0"`, `"raw_1"`, etc. These rows had identical titles and DOIs to existing publications in the same database.

### Root Cause:
In `backend/services/search_service.py` (`_persist_publications`), duplicate detection relied exclusively on:
```python
res = await db.execute(select(Publication).where(Publication.canonical_id == pub.canonical_id))
existing = res.scalar_one_or_none()
```
If a new ingestion pass arrived with a different canonical ID format (e.g. from DBLP without DOI, or with prefix `raw_`), `existing` returned `None`, inserting a second duplicate publication row!

---

## 2. The Idempotency Implementation

To guarantee true ingestion idempotency without mutating existing data:
```python
res = await db.execute(select(Publication).where(Publication.canonical_id == pub.canonical_id))
existing = res.scalar_one_or_none()
if not existing and pub.doi:
    res_doi = await db.execute(select(Publication).where(Publication.doi == pub.doi))
    existing = res_doi.scalars().first()
if not existing and pub.title:
    res_title = await db.execute(select(Publication).where(func.lower(Publication.title) == pub.title.strip().lower()))
    existing = res_title.scalars().first()
```

### Verified Benefit:
Repeated ingestion passes update existing records (aggregating citations and source provenance) rather than creating duplicate publication records.
