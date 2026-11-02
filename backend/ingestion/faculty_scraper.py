import json
import re
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from ingestion.base import BaseConnector
from utils.security import is_url_safe
from log_config import get_logger

logger = get_logger(__name__)

PROFILES_DIR = Path(__file__).parent.parent / "site_profiles"


class FacultyScraper(BaseConnector):
    source_name = "faculty_page"

    def __init__(self, profile_name: str = "kjsomaiya"):
        super().__init__()
        self.profile_name = profile_name
        self.profile = self._load_profile(profile_name)

    def _load_profile(self, name: str) -> dict:
        path = PROFILES_DIR / f"{name}.json"
        if not path.exists():
            logger.error(f"Profile {name} not found")
            return {}
        return json.loads(path.read_text())

    async def _fetch_impl(self, author_name: str, **kwargs) -> list[dict]:
        """
        Scrapes a specific faculty page. 
        In Phase 1, we assume the URL is provided via an environment variable 
        or a search for the author within the institution domain.
        For this demo, we use a hardcoded target if defined in the profile.
        """
        target_url = self.profile.get("base_url")
        if not target_url:
            # Fallback: simple search on the domain if possible, 
            # but for Phase 1 demo we expect a target.
            return []

        if not await is_url_safe(target_url):
            logger.error(f"Target URL {target_url} blocked by SSRF protection")
            return []

        records = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
                
                # Wait for container
                container_sel = self.profile.get("publication_container")
                await page.wait_for_selector(container_sel, timeout=5000)
                
                # Extract all matching elements
                elements = await page.query_selector_all(container_sel)
                
                title_sel = self.profile.get("title_selector")
                author_sel = self.profile.get("author_selector")
                year_pat = self.profile.get("year_pattern", r"\b(19|20)\d{2}\b")

                for el in elements:
                    title_el = await el.query_selector(title_sel) if title_sel else el
                    title = await title_el.inner_text() if title_el else ""
                    
                    # Clean title
                    title = title.strip().split("\n")[0]
                    if not title: continue

                    full_text = await el.inner_text()
                    
                    # Extract year using regex
                    year_match = re.search(year_pat, full_text)
                    year = int(year_match.group(0)) if year_match else None

                    # Extract authors (simple split if available)
                    authors = []
                    if author_sel:
                        auth_el = await el.query_selector(author_sel)
                        if auth_el:
                            auth_text = await auth_el.inner_text()
                            authors = [a.strip() for a in re.split(r"[,;]| and ", auth_text) if a.strip()]

                    records.append({
                        "source":    "faculty_page",
                        "source_id": f"{self.profile_name}_{hash(title)}",
                        "title":     title,
                        "authors":   authors,
                        "year":      year,
                        "venue":     self.profile.get("institution_name", "Faculty Page"),
                        "url":       target_url,
                        "raw_json":  json.dumps({"text": full_text}),
                    })

            except Exception as e:
                logger.error(f"Scraping failed for {target_url}: {e}")
            finally:
                await browser.close()

        return records
