import asyncio
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from log_config import get_logger

from ingestion.scrapers.scholar.browser import BrowserManager
from ingestion.scrapers.scholar.parser import parse_scholar_profile
from database import ScholarCache
from config import DEMO_MODE

logger = get_logger(__name__)

async def fetch_scholar_profile(url: str, db_session) -> tuple[list[dict], dict]:
    """
    Fetches a Google Scholar profile.
    Returns (records, status_dict)
    """
    if not url:
        return [], {"status": "failed", "reason": "no_url"}

    # ── 1. Check DB Cache ─────────────────────────────────────────
    cached = None
    try:
        cache_res = await db_session.execute(
            select(ScholarCache).where(ScholarCache.profile_url == url)
        )
        cached = cache_res.scalar_one_or_none()
        
        # Use naive UTC for comparison to avoid SQLite tz errors
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        
        if cached and cached.expires_at:
            expires = cached.expires_at.replace(tzinfo=None) if cached.expires_at.tzinfo else cached.expires_at
            if expires > now_naive:
                logger.info(f"Scholar Cache HIT for {url}")
                records = parse_scholar_profile(cached.html_content)
                return records, {"status": "ok", "cached": True, "demo_fallback": False}
    except Exception as e:
        logger.error(f"Error checking scholar cache: {e}")

    # ── 1.5. Demo Mode Guard ──────────────────────────────────────
    if DEMO_MODE:
        logger.warning(f"DEMO_MODE=True: Blocking live Playwright scrape for {url}. Returning empty fallback.")
        return [], {"status": "failed", "reason": "demo_mode_blocked", "cached": False, "demo_fallback": True}

    # ── 2. Fetch via Playwright ───────────────────────────────────
    manager = BrowserManager.get_instance()
    
    async with manager.semaphore:
        logger.info(f"Scholar Cache MISS. Scraping {url}")
        
        browser = await manager.get_browser()
        if not browser:
            return [], {"status": "failed", "reason": "browser_init_failed"}

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": random.randint(1024, 1920), "height": random.randint(768, 1080)}
        )
        page = await context.new_page()

        try:
            await asyncio.sleep(random.uniform(2.0, 4.0))
            response = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            
            if response.status == 429:
                return [], {"status": "failed", "reason": "captcha"}
                
            html = await page.content()
            
            if "sorry" in page.url or "captcha" in html.lower() or "unusual traffic" in html.lower():
                logger.warning(f"Scholar CAPTCHA detected for {url}")
                return [], {"status": "failed", "reason": "captcha"}
                
            records = parse_scholar_profile(html)
            
            # Save to Cache
            try:
                expires_naive = (datetime.now(timezone.utc) + timedelta(hours=24)).replace(tzinfo=None)
                if cached:
                    cached.html_content = html
                    cached.expires_at = expires_naive
                else:
                    new_cache = ScholarCache(
                        profile_url=url,
                        html_content=html,
                        expires_at=expires_naive
                    )
                    db_session.add(new_cache)
                await db_session.commit()
            except Exception as e:
                logger.error(f"Failed to save scholar cache: {e}")
                
            return records, {"status": "ok", "cached": False, "demo_fallback": False}

        except Exception as e:
            logger.error(f"Scholar scrape failed: {e}")
            return [], {"status": "failed", "reason": str(e)}
        finally:
            await page.close()
            await context.close()
