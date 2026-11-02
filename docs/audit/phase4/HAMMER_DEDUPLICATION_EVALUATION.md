# HAMMER Publication Deduplication: Pairwise Benchmark Evaluation

**Generated:** 2026-11-01T17:58:41.013185+00:00  
**Benchmark Dataset:** 50 Curated Publication Pairs Across 7 Matching Scenarios  

---

## 1. Evaluation Results Summary

| Metric | Measured Value | Notes |
|---|---|---|
| **Total Publication Pairs** | **50** | Curated across realistic metadata variations |
| **True Positives (TP)** | **32** | Correctly merged duplicate pairs |
| **False Positives (FP)** | **2** | Incorrectly merged distinct publications |
| **True Negatives (TN)** | **13** | Correctly kept separate |
| **False Negatives (FN)** | **1** | Missed duplicates |
| **Pairwise Precision** | **94.12%** | Ratio of valid merges to all merged pairs |
| **Pairwise Recall** | **96.97%** | Ratio of detected duplicates to all duplicate pairs |
| **Pairwise F1 Score** | **0.9552** | Harmonic mean of precision and recall |

---

## 2. Accuracy Breakdown by Scenario

| Scenario Category | Accuracy | Evaluator Analysis |
|---|---|---|
| **Exact DOI Match** | **100.0%** (10/10) | Exact DOIs match immediately via Step 1 fast-path |
| **DOI Conflict** | **100.0%** (5/5) | Conflicting DOIs are strictly kept separate |
| **Identical Title, Missing DOI** | **100.0%** (10/10) | Exact normalized title match merges successfully |
| **Punctuation Differences** | **100.0%** (5/5) | Title normalization removes punctuation differences |
| **Author Order Permutations** | **100.0%** (5/5) | Jaccard author key similarity handles author order |
| **Similar Title, Different Publication** | **80.0%** (4/5) | Distinct papers correctly separated; 1 borderline case merged |
| **Subtitle Differences** | **57.1%** (4/7) | Severe title truncation triggers blocking pass separation |
