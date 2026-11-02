# HAMMER Academic Source Connector Failure Analysis & Reliability Assessment

**Audit Phase:** Phase 3B — Connector Diagnostics  
**Date:** November 2026  
**Auditor:** External API Systems & Network Forensics  
**Status:** Completed  

---

## 1. Executive Summary

HAMMER is designed to ingest academic metadata across six distinct connector modules: OpenAlex, Crossref, arXiv, DBLP, Google Scholar, and Faculty Scraper.

Phase 3 benchmark testing revealed stark differences in reliability:
- **Tier 1 (Production Core):** OpenAlex, Crossref, arXiv achieved **100% request success**.
- **Tier 2 (Broken / Blocked):** DBLP, Google Scholar, Faculty Scraper experienced **100% failure rates**.

This report investigates the specific technical failure modes for the Tier 2 connectors, assesses whether they can be remediated with modest effort, and provides architectural recommendations on whether they should remain optional.

---

## 2. Connector-by-Connector Technical Failure Analysis

### 1. DBLP Connector (`connectors/dblp.py`)
- **Observed Error:** `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`
- **Network Forensic Investigation:**
  We executed a low-level HTTP request to `https://dblp.org/search/publ/api` using `httpx`:
  ```
  HTTP Status: 202 Accepted
  Content-Type: text/html; charset=utf-8
  Payload Preview: <!doctype html><html lang="en"><head><title>Making sure you're not a bot!</title>...
  ```
- **Root Cause:** DBLP deployed Cloudflare Bot Management / CAPTCHA challenge protection on its public search API against automated python client requests (`User-Agent: python-httpx`). Because the endpoint returns HTML rather than JSON, `.json()` throws `JSONDecodeError`.
- **Remediation Assessment:** Bypassing Cloudflare requires browser-like TLS fingerprinting (e.g. `curl_cffi`, residential proxies, or headless browsers), which introduces severe latency (5–10s) and instability.
- **Recommendation:** **Explicitly mark DBLP as OPTIONAL (`ENABLE_DBLP=false`).** OpenAlex and Crossref provide comprehensive coverage of DBLP's computer science index without bot challenges.

### 2. Google Scholar Connector (`connectors/scholar.py`)
- **Observed Error 1:** `ValueError: ScholarConnector requires a db session for caching`
  - *Cause:* When instantiated standalone in evaluation scripts, `kwargs.get("db")` was None.
  - *Fix:* Supply an `AsyncSessionLocal()` instance when testing.
- **Observed Error 2:** `playwright._impl._errors.Error: Executable doesn't exist at /Users/nileshlalwani/Library/Caches/ms-playwright/chromium_headless_shell-1217/...`
  - *Cause:* The Playwright Python library is installed in `backend/venv`, but the browser binaries were never downloaded to the local user cache.
- **Remediation Assessment:** Running `playwright install chromium` downloads the missing executable. However, Google Scholar actively CAPTCHA-bans automated Playwright browser instances after 2 to 5 requests.
- **Recommendation:** **Retain Google Scholar as OPTIONAL with local SQLite cache fallback.** Live scraping should not be relied upon during a live project viva.

### 3. Faculty Scraper (`connectors/faculty_scraper.py`)
- **Observed Error:** `BrowserType.launch: Executable doesn't exist`
- **Root Cause:** Shares the exact Playwright browser dependency as Google Scholar. Additionally, its scraping logic is hardcoded specifically to the KJ Somaiya faculty profile directory structure.
- **Recommendation:** **Mark as OPTIONAL / Experimental profile connector.**

---

## 3. Verification of Connector Latency Telemetry

In `docs/audit/phase3_evaluation/results/ingestion_evaluation_raw.json`, connector latencies were recorded across 4 distinct live author queries. We verified whether these latencies reflect real network round trips:

| Connector | Query 1 (s) | Query 2 (s) | Query 3 (s) | Query 4 (s) | Mean Latency | Verified Nature of Latency |
|---|---|---|---|---|---|---|
| **OpenAlex** | 3.299s | 2.428s | 2.253s | 4.839s | **3.205s** | **Real Outbound HTTPS API Calls** to `api.openalex.org` |
| **Crossref** | 2.740s | 2.312s | 2.571s | 3.020s | **2.661s** | **Real Outbound HTTPS API Calls** to `api.crossref.org` |
| **arXiv** | 3.565s | 3.412s | 3.620s | 3.663s | **3.565s** | **Real Outbound HTTPS API Calls** to `export.arxiv.org` |
| **DBLP** | 0.594s | 0.582s | 0.611s | 0.589s | **0.594s** | **Real Outbound HTTPS Call** aborted early by Cloudflare 202 response |
| **Scholar** | 0.000s | 0.000s | 0.000s | 0.000s | **0.000s** | Local assertion failure before network call |
| **Faculty** | 0.619s | 0.279s | 0.246s | 0.238s | **0.346s** | Local OS subprocess launch failure before network call |

**Conclusion:** The reported latencies for OpenAlex, Crossref, and arXiv are 100% genuine network round trips reflecting the real-world responsiveness of those public academic APIs.