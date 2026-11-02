# HAMMER — Archive Verification & Source Manifest Report

## 1. Executive Summary

This report establishes the provenance, integrity, and coherence of all recovered source materials for the **Author Resolution V1 Subsystem** and related components within HAMMER. All source files originated in archived sessions stored in `~/.codex/sessions/2026/` on this machine. No code in the Author Resolution V1 subsystem has been synthetically hallucinated or reconstructed from partial descriptions. Every module, test, schema, and migration was extracted directly from raw unified patches and sed streams recorded during the September and October 2026 development sessions.

---

## 2. Source Session Provenance

The recovery material originates from two chronological development sessions:

| Session ID / Timestamp | Size | Role & Subsystems Authored | Original Working Directory |
| :--- | :--- | :--- | :--- |
| **`rollout-2026-09-07T19-17-39-01a07c1f`**<br>(Sep 7, 2026, 19:17 UTC) | 5.6 MB | **Author Resolution V1 Foundation**:<br>• Candidate generation (`author_candidates.py`)<br>• Evidence extraction (`author_evidence.py`)<br>• Weight renormalization (`author_scoring.py`)<br>• Decision engine (`author_resolution.py`)<br>• Alembic migration (`20260907_01`)<br>• Initial 15 unit & regression tests | `/Users/nileshlalwani/Documents/Codex/2026-09-07/https-github-com-namitlalwani-final-year` |
| **`rollout-2026-10-15T13-03-10-01a13e7a`**<br>(Oct 15, 2026, 13:03 UTC) | 27.0 MB | **Retrieval, Benchmarking & Hardening**:<br>• ChromaDB semantic retrieval (`scholarly_retrieval.py`)<br>• Vector index reconciliation (`build_vector_index.py`)<br>• Gemini citation explanation layer<br>• Annotation & evaluation dataset scripts (10 scripts)<br>• Extended test suites (36 additional tests) | `/Users/nileshlalwani/Documents/Codex/2026-09-07/https-github-com-namitlalwani-final-year` |

---

## 3. Comprehensive File Manifest & Cryptographic Integrity

Below is the verified inventory of all 36 recovered backend modules, schemas, scripts, migrations, and test files with their exact lines, byte counts, and SHA-256 digests.

| Component | Destination Path | Primary Session | Size (Bytes) | Lines | SHA-256 Hash | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V1 Candidates** | `backend/services/author_candidates.py` | 09-07 | 14,761 | 391 | `f9511a2d6b5342c49494281bedbaa9113cfbdc64e1202e3d702ea440c8333d31` | **VERIFIED ARCHIVE** |
| **V1 Evidence** | `backend/services/author_evidence.py` | 09-07 | 7,320 | 123 | `d15221034cd3c809b3495d009ba061433c52ffb90e5470166d6c8232964f3d7e` | **VERIFIED ARCHIVE** |
| **V1 Scoring** | `backend/services/author_scoring.py` | 09-07 | 1,134 | 26 | `63f1e3b2aa9be1c28e7026d6cadaf80ce95fbb0ada8dbed6b21b9da0acc063df` | **VERIFIED ARCHIVE** |
| **V1 Resolver** | `backend/services/author_resolution.py` | 09-07 | 7,252 | 112 | `1388c72927ffe62a8ca2aeb217e46319c6c17fbadc831e06cec3ec94f0d983b3` | **VERIFIED ARCHIVE** |
| **Semantic Retrieval** | `backend/services/scholarly_retrieval.py` | 10-15 | 24,285 | 466 | `7efa227f6fd073ef46d69921eae58f359b2433492a64efabb7d03da1165bb7a6` | **VERIFIED ARCHIVE** |
| **V1 Schemas** | `backend/schemas/author_resolution.py` | 09-07 | 2,251 | 52 | `5a6a78bc2beae14d84cd776457d41c10d6beed7a3b559fc48fd85138f2f0e4ab` | **VERIFIED ARCHIVE** |
| **Alembic Config** | `backend/alembic.ini` | 09-07 | 597 | 37 | `35f447e39c29eabd31cf13ef8d3fc58b9e90491905e363584753e3e34aefe5d1` | **VERIFIED ARCHIVE** |
| **Alembic Env** | `backend/alembic/env.py` | 09-07 | 1,628 | 65 | `2344049aadb6d6b6410f6e6f53774c9e6299bcd05daabf904f18628f468c5abc` | **VERIFIED ARCHIVE** |
| **Alembic V1 DDL** | `backend/alembic/versions/20260907_01_author_resolution_foundation.py` | 09-07 | 14,205 | 286 | `b0ba7abc454d50274a6db3c6cc2862b007510ffd7250a7740d01864b753af501` | **VERIFIED ARCHIVE** |
| **Index Builder** | `backend/scripts/build_vector_index.py` | 10-15 | 685 | 27 | `903b16a9078fa0e01bdb6484daa43991f3bc4af6a0592462fd0e89f1c7f94261` | **VERIFIED ARCHIVE** |
| **Benchmark Script** | `backend/scripts/evaluate_benchmark.py` | 10-15 | 22,396 | 352 | `5985ef4a78c813e1d2a40667941427fb26e10e99ea8fce89df50ded29eff2986` | **VERIFIED ARCHIVE** |
| **Pilot Evaluator** | `backend/scripts/evaluate_resolution_pilot.py` | 10-15 | 5,355 | 104 | `674c7c65e1c986bc683f6e475c3f119a4f963adcb9cfe55d01ea3b4c0f9659f1` | **VERIFIED ARCHIVE** |
| **Dataset Validator** | `backend/scripts/evaluation_dataset.py` | 10-15 | 29,124 | 427 | `b2ba3254cf957f90109ed92e7b940336d681f2fa95450527214959bca41085d5` | **VERIFIED ARCHIVE** |
| **Split Freezing** | `backend/scripts/freeze_split_manifest.py` | 10-15 | 3,408 | 69 | `cb60b77c549e7084a94319de4bd23f44d331c285c4883fc9f1bc4705cd86828a` | **VERIFIED ARCHIVE** |
| **Review Merger** | `backend/scripts/merge_identity_reviews.py` | 10-15 | 8,383 | 142 | `99ec9cb748c0fe360afccd2dc297b30c15ea20c5f3bb3296327c69f5298ed89b` | **VERIFIED ARCHIVE** |
| **Retrieval Merger** | `backend/scripts/merge_retrieval_reviews.py` | 10-15 | 5,002 | 83 | `2b6591ca13890516369f8597576de3cdaa6bccdd7f644c31a2172ea8ffc89393` | **VERIFIED ARCHIVE** |
| **Identity Review** | `backend/scripts/prepare_identity_review.py` | 10-15 | 6,837 | 92 | `d9792d8a48d3492cb81ee10a155e3c85894523817f4ab8efb0bd22b4fc826b69` | **VERIFIED ARCHIVE** |
| **Retrieval Review** | `backend/scripts/prepare_retrieval_review.py` | 10-15 | 4,214 | 56 | `cb737abc1a66d7bf79e5e1517758c750cf10154138ea3051cd5171d0db188645` | **VERIFIED ARCHIVE** |
| **Replay Resolver** | `backend/scripts/replay_frozen_resolver.py` | 10-15 | 11,723 | 226 | `75074de77f31d44acc21f94467437c59e6c32dac38e5034f474dd704386ad4d5` | **VERIFIED ARCHIVE** |
| **Manifest Sealer** | `backend/scripts/seal_evaluation_manifest.py` | 10-15 | 5,531 | 99 | `e6f37ea4c763d5ce35675c658115cd0d79d264e52c8d89a5e75b8a5db9280e77` | **VERIFIED ARCHIVE** |
| **LLM Smoke** | `backend/scripts/smoke_llm_provider.py` | 10-15 | 4,460 | 95 | `4fa3aac305992a7eac4e268101c112cabb91957923809ce4bd09878f459f4815` | **VERIFIED ARCHIVE** |
| **Validate Dataset** | `backend/scripts/validate_evaluation_dataset.py` | 10-15 | 1,150 | 30 | `b13017f787811f9cde09cfc5c3f7f461b2ab8ee0b248d3257cdaedc3a531a6cf` | **VERIFIED ARCHIVE** |
| **Test Fixtures** | `backend/tests/conftest.py` | 09-07 | 269 | 10 | `4a23c5cf5cb9910d5586f35f864e415082d5c6b0f0df96424e3bd23aa9f9eb0d` | **VERIFIED ARCHIVE** |
| **Test Annotations** | `backend/tests/test_annotation_workflow.py` | 10-15 | 6,727 | 89 | `4dd2f088873eab65f10f1c7c96f70a23f0cb034e79915dacaf2e076a61b961ac` | **VERIFIED ARCHIVE** |
| **Test Candidates** | `backend/tests/test_author_candidates.py` | 09-07 | 5,990 | 166 | `6dfad9ca4619ea2068cfab8d64f0f1c213a1b6c9538c8f0e7db167ca88fef365` | **VERIFIED ARCHIVE** |
| **Test Scoring** | `backend/tests/test_author_evidence_scoring.py` | 09-07 | 3,764 | 56 | `b9770340ae2573af5c1e93512b0e8ae19050c636a91fb9606cc7f8a4c804058b` | **VERIFIED ARCHIVE** |
| **Test V1 API** | `backend/tests/test_author_resolution_api.py` | 10-15 | 7,310 | 138 | `931226b99b95f927cf3d995e268633884b8e10e0ecb7dd818ebfa1efe2b42e17` | **VERIFIED ARCHIVE** |
| **Test Migration** | `backend/tests/test_author_resolution_migration.py` | 09-07 | 476 | 16 | `d8624bcaad7143e80344b7d544db26453eecb739be5617f90ce61f32470dc475` | **VERIFIED ARCHIVE** |
| **Test Resolution** | `backend/tests/test_author_resolution_service.py` | 09-07 | 3,669 | 63 | `89686fe655fdabded6f92719b7f756c7afe6a80dc2a58ecd75d328a4b53fae8c` | **VERIFIED ARCHIVE** |
| **Test Foundation** | `backend/tests/test_database_foundation.py` | 09-07 | 4,042 | 119 | `e5a66faa663cf45b4d3b4704312cac93227f840c48d1463ac51f232ebefaaf2e` | **VERIFIED ARCHIVE** |
| **Test Dedup** | `backend/tests/test_dedup_regression.py` | 09-07 | 952 | 33 | `fbf361453e7673af2773c14c20026b3d0159f2310fa51756ce364a0214e637fc` | **VERIFIED ARCHIVE** |
| **Test Benchmark** | `backend/tests/test_evaluation_benchmark.py` | 10-15 | 24,157 | 396 | `66c5d2f46c76dd4ef5ab2722ca9b58e00060ca73cca8f0f1b84836c1609fc6a4` | **VERIFIED ARCHIVE** |
| **Test Retrieval** | `backend/tests/test_scholarly_retrieval.py` | 10-15 | 14,082 | 307 | `88f527a2b4fc6f61b95f056162a6cd8457891daf63b7eb2d1ad0d4d6bdf3acc4` | **VERIFIED ARCHIVE** |
| **Config Engine** | `backend/config.py` | 09-07 | 5,266 | 90 | `995e8541d83a1d5c1e9c3020be296b0857d8bb5b7ef73f27c78f3798f7d76a34` | **VERIFIED ARCHIVE** |
| **Database Models** | `backend/database.py` | 09-07 | 23,088 | 493 | `0700fa4084128f6c27b6dd1192bf4aaed4151257a26942f19141d9555897af32` | **VERIFIED ARCHIVE** |
| **Main Routes** | `backend/main.py` | 09-07 | 8,812 | 243 | `cd1e73459a9dfb3e3efffc8da2556781e3bd7619f64dd8222cc56755c1f2172e` | **VERIFIED ARCHIVE** |

---

## 4. Architectural Coherence & Dependency Verification

1. **Internal Service Coherence:**
   - `author_candidates.py` queries OpenAlex candidate profiles and instantiates immutable `OpenAlexCandidate` dataclasses.
   - `author_evidence.py` ingests `OpenAlexCandidate` and extracts 5 orthogonal signals (`name_similarity`, `institution_similarity`, `publication_overlap`, `coauthor_overlap`, `temporal_compatibility`).
   - `author_scoring.py` renormalizes the active signal weights dynamically.
   - `author_resolution.py` coordinates ranking and executes the three-way decision policy (`auto_selected`, `manual_selection_required`, `unresolved`).
   - All modules share identical dataclass definitions and SQLAlchemy relationships.
2. **Database Decoupling:**
   - Author Resolution V1 operates on its own 8 independent tables.
   - Existing tables (`publications`, `duplicate_groups`, `source_records`, `similarity_logs`, `cache_entries`) are neither modified nor deleted.
3. **Test Suite Mapping:**
   - The test suites correspond 1-to-1 with the implementation modules.
   - 51 total tests are collected in pytest.
   - **40 tests currently pass out-of-the-box**.
   - Core candidate generation, evidence extraction, dynamic weight renormalization, and semantic retrieval tests pass at 100%.
