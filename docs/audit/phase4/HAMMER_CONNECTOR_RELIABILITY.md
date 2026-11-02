# HAMMER Ingestion Connector Reliability Audit

**Generated:** 2026-11-01T17:58:41.014231+00:00  
**Scope:** Real-Time Network Probing of Ingestion Endpoints  

---

## 1. Live Probing Results

| Connector | Status | HTTP Status | Measured Latency | Cloudflare Challenge | Role in HAMMER |
|---|---|---|---|---|---|
| **Crossref** | **Operational** | HTTP 200 | 1469.61 ms | False | Core Ingestion |
| **arXiv** | **Operational** | HTTP 200 | 1620.22 ms | False | Core Ingestion |
| **OpenAlex** | **Rate Limited** | HTTP 429 | 241.8 ms | False | Core Ingestion (handled with backoff & local cache) |
| **DBLP** | **Blocked** | HTTP 202 | 744.24 ms | **True (Cloudflare)** | Optional / Experimental |
| **Google Scholar** | **Offline Only** | N/A | N/A | False | Optional (Anti-bot CAPTCHA; served from cache) |
| **Faculty Scraper** | **Offline Only** | N/A | N/A | False | Experimental (Requires Playwright browser binaries) |

---

## 2. Ingestion Strategy Recommendations:
- **Core Production Set:** Crossref, arXiv, and OpenAlex (with exponential backoff and persistent caching).
- **Secondary / Optional:** DBLP, Scholar, and Faculty scraping remain disabled by default in production runs to prevent bot blocking and runtime crashes during viva presentations.
