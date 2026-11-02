# HAMMER Confirmed Defects, Code Modifications & Regression Verification

**Audit Phase:** Phase 3B — Defect Resolution  
**Date:** November 2026  
**Auditor:** Senior Software Engineer & Systems Architect  
**Status:** All Confirmed Defects Remediated & Regression-Verified  

---

## 1. Summary of Confirmed Defects

During the Phase 3 and Phase 3B evaluations, two confirmed application defects and one evaluation contract discrepancy were identified. Per strict Phase 3B rules, only confirmed defects were modified, and each fix is strictly isolated, documented, and covered by new automated regression tests.

| Defect ID | Severity | Subsystem | Description | Fix Applied | Verification |
|---|---|---|---|---|---|
| **DEF-01** | **P1 (High)** | Backend API | `GET /similarity-log/{pub_id}` crashes with `MultipleResultsFound` (HTTP 500) | Changed `.scalar_one_or_none()` to `.scalars().all()` in `backend/main.py:366` | Verified live HTTP 200 + automated regression test |
| **DEF-02** | **P2 (Medium)** | Backend API | `POST /author-resolutions/candidates` with whitespace name returns HTTP 503 instead of 422 | Added `@field_validator` in `AuthorCandidateSearchRequest` (`main.py:84`) | Verified live HTTP 422 + automated regression test |
| **DEF-03** | **P3 (Evaluation)** | Evaluation Tooling | Test script passed `?author_name=` and `?author=` instead of `?name=` | Updated test script parameter dictionary to match route contract | Verified live HTTP 200 on all endpoints |

---

## 2. Code Modifications & Diff Documentation

### Defect 1: `MultipleResultsFound` on `/similarity-log/{pub_id}`

**File Modified:** `backend/main.py` (Lines 364–376)

```diff
 @app.get("/similarity-log/{pub_id}")
 async def get_similarity_log(pub_id: int, db: AsyncSession = Depends(get_db)):
     grp_res = await db.execute(
-        select(DuplicateGroup).where(DuplicateGroup.publication_id == pub_id)
+        select(DuplicateGroup).where(DuplicateGroup.publication_id == pub_id).order_by(DuplicateGroup.id.desc())
     )
-    group = grp_res.scalar_one_or_none()
-    if not group:
-        return {"pub_id": pub_id, "logs": []}
-
-    record_ids = json.loads(group.source_record_ids or "[]")
-    if not record_ids:
-        return {"pub_id": pub_id, "logs": []}
+    groups = grp_res.scalars().all()
+    if not groups:
+        return {"pub_id": pub_id, "logs": []}
+
+    record_ids = []
+    for g in groups:
+        for rid in json.loads(g.source_record_ids or "[]"):
+            if str(rid) not in record_ids:
+                record_ids.append(str(rid))
+    if not record_ids:
+        return {"pub_id": pub_id, "logs": []}
```

**Rationale:** Table `duplicate_groups` lacks a unique constraint on `publication_id`. Repeated ingestion passes insert multiple group entries for the same publication ID. Using `.scalars().all()` and aggregating unique record IDs eliminates crashes and correctly retrieves all logged comparisons.

---

### Defect 2: Whitespace Query Returning HTTP 503

**File Modified:** `backend/main.py` (Lines 9 and 84–98)

```diff
-from pydantic import BaseModel
+from pydantic import BaseModel, field_validator
 
 class AuthorCandidateSearchRequest(BaseModel):
     author_name: str
     institution_hint: Optional[str] = None
     context: Optional[Dict[str, Any]] = None
+
+    @field_validator("author_name")
+    @classmethod
+    def validate_author_name(cls, v: str) -> str:
+        if not v or not v.strip():
+            raise ValueError("author_name cannot be empty or whitespace")
+        if len(v.strip()) < 2:
+            raise ValueError("author_name must have at least 2 non-whitespace characters")
+        return v.strip()
```

**Rationale:** Enforces FastAPI/Pydantic input validation at the edge. Empty strings or whitespace-only inputs are rejected immediately with HTTP 422 Unprocessable Entity, preventing false upstream outage errors (HTTP 503).

---

## 3. Automated Regression Test Suite

A dedicated regression test file was added: [`backend/tests/test_api_defects_regression.py`](file:///Users/nileshlalwani/Desktop/FINAL%20YEAR%20PROJECT/academic-search/backend/tests/test_api_defects_regression.py).

### Tests Included:
1. `test_author_candidates_whitespace_and_empty_validation`:
   - Tests empty string `""` $ightarrow$ Asserts HTTP 422.
   - Tests whitespace string `"   "` $ightarrow$ Asserts HTTP 422.
   - Tests single character `"a"` $ightarrow$ Asserts HTTP 422.
2. `test_get_similarity_log_handles_multiple_duplicate_groups`:
   - Creates a disposable SQLite database with 1 publication and 2 colliding `DuplicateGroup` entries.
   - Calls `GET /similarity-log/{pub_id}` $ightarrow$ Asserts HTTP 200, verifies zero crashes, and checks that similarity log entries are returned.
3. `test_get_search_candidates_query_parameter_contract`:
   - Verifies that omitting required parameter `name` returns HTTP 422 with a descriptive error.

### Regression Test Execution Output:
```bash
$ pytest backend/tests/test_api_defects_regression.py
========================= 3 passed, 1 warning in 1.96s =========================
```

### Full Backend Test Suite Output:
```bash
$ pytest backend/tests/ -v
======================== 54 passed, 4 warnings in 3.24s ========================
```
- **Total Backend Tests:** **54** (increased from 51)
- **Pass Rate:** **100.0%**
- **Failed / Broken Tests:** **0**