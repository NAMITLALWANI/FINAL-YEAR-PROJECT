"""Architectural Role: DBLP Bibliographic Connector with Automated WAF Clearance.

Fetches computer science publication records from DBLP's public search API.
Includes autonomous session cookie negotiation via Playwright to clear DBLP's
Anubis Proof-of-Work bot challenge, enabling reliable, live JSON querying.
"""
import asyncio
import json
import time
from pathlib import Path
import httpx
from ingestion.base import BaseConnector
from config import USE_MOCK_DATA
from log_config import get_logger

logger = get_logger(__name__)

MOCK_PATH = Path(__file__).parent.parent / "mock_data" / "dblp_hinton.json"
BASE_URL = "https://dblp.org/search"
DEFAULT_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# In-memory session cookies cache with expiration
_SESSION_COOKIES: dict[str, str] = {}
_COOKIES_EXPIRES_AT: float = 0.0
_SESSION_LOCK = asyncio.Lock()


async def _get_dblp_session_cookies() -> dict[str, str]:
    """Acquires and caches DBLP verification cookies by completing the Anubis challenge via Playwright."""
    global _SESSION_COOKIES, _COOKIES_EXPIRES_AT
    now = time.time()
    if _SESSION_COOKIES and now < _COOKIES_EXPIRES_AT:
        return _SESSION_COOKIES

    async with _SESSION_LOCK:
        # Double check after acquiring lock
        if _SESSION_COOKIES and time.time() < _COOKIES_EXPIRES_AT:
            return _SESSION_COOKIES

        try:
            from playwright.async_api import async_playwright
            logger.info("Clearing DBLP Anubis challenge via Playwright browser session...")
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                context = await browser.new_context(user_agent=DEFAULT_UA)
                page = await context.new_page()
                await page.goto("https://dblp.org", wait_until="domcontentloaded")
                # Allow Anubis JavaScript Proof-of-Work to compute (approx 4-5s)
                await page.wait_for_timeout(5000)
                cookies = await context.cookies()
                await browser.close()

            new_cookies = {c["name"]: c["value"] for c in cookies if "dblp_org" in c["name"]}
            if new_cookies:
                _SESSION_COOKIES = new_cookies
                # Cache for 45 minutes (token expiration is usually 1 hour)
                _COOKIES_EXPIRES_AT = time.time() + 2700
                logger.info(f"DBLP session cookies established: {list(_SESSION_COOKIES.keys())}")
                return _SESSION_COOKIES
        except Exception as e:
            logger.warning(f"Failed to acquire DBLP browser cookies: {e}")

        return {}


class DBLPConnector(BaseConnector):
    source_name = "dblp"

    async def _fetch_impl(self, author_name: str, **kwargs) -> list[dict]:
        if USE_MOCK_DATA and MOCK_PATH.exists():
            return json.loads(MOCK_PATH.read_text())

        cookies = await _get_dblp_session_cookies()
        headers = {
            "User-Agent": DEFAULT_UA,
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout, headers=headers, cookies=cookies, follow_redirects=True) as client:
            search_query = f"author:{author_name}:"
            pub_resp = await client.get(
                f"{BASE_URL}/publ/api",
                params={"q": search_query, "format": "json", "h": 50},
            )
            
            # If 202 is returned, cookie expired or missing
            if pub_resp.status_code == 202 or "text/html" in pub_resp.headers.get("content-type", ""):
                logger.warning("DBLP returned challenge HTML (202). Retrying with refreshed cookies...")
                global _COOKIES_EXPIRES_AT
                _COOKIES_EXPIRES_AT = 0.0
                cookies = await _get_dblp_session_cookies()
                pub_resp = await client.get(
                    f"{BASE_URL}/publ/api",
                    params={"q": search_query, "format": "json", "h": 50},
                    cookies=cookies
                )

            pub_resp.raise_for_status()
            data = pub_resp.json()
            pub_hits = data.get("result", {}).get("hits", {}).get("hit", [])

            if not pub_hits:
                pub_resp = await client.get(
                    f"{BASE_URL}/publ/api",
                    params={"q": f"author:{author_name}", "format": "json", "h": 50},
                    cookies=cookies
                )
                if pub_resp.status_code == 200 and "json" in pub_resp.headers.get("content-type", ""):
                    pub_hits = pub_resp.json().get("result", {}).get("hits", {}).get("hit", [])

        records = []
        for hit in pub_hits:
            info = hit.get("info", {})
            authors_raw = info.get("authors", {}).get("author", [])
            if isinstance(authors_raw, dict):
                authors_raw = [authors_raw]
            authors = [a.get("text") for a in authors_raw if a.get("text")]

            records.append({
                "source":    "dblp",
                "source_id": hit.get("@id") or info.get("key") or "",
                "title":     info.get("title") or "",
                "authors":   authors,
                "year":      int(info.get("year")) if str(info.get("year")).isdigit() else None,
                "doi":       info.get("doi") or "",
                "venue":     info.get("venue") or "",
                "url":       info.get("ee") or info.get("url") or "",
                "raw_json":  json.dumps(hit),
            })

        return records
