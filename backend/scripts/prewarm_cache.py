import asyncio
import json
import time
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Force config overrides BEFORE loading backend modules
import config
config.DEMO_MODE = False
config.ENABLE_SCHOLAR = True

from database import init_db, AsyncSessionLocal
from services.search_service import search, get_author_candidates
from connectors.scrapers.scholar.browser import BrowserManager
from log_config import get_logger

logger = get_logger(__name__)

async def main():
    await init_db()
    
    # Need to start the browser singleton for Scholar
    manager = BrowserManager.get_instance()
    await manager.start()
    
    authors_file = os.path.join(os.path.dirname(__file__), '..', 'demo_authors.json')
    with open(authors_file, 'r') as f:
        authors = json.load(f)
        
    logger.info(f"Starting cache pre-warm for {len(authors)} authors.")
    
    async with AsyncSessionLocal() as db:
        for author in authors:
            logger.info(f"Pre-warming: {author}")
            start_time = time.time()
            
            # Step 1: Trigger candidate search (populates OpenAlex cache internally if we added it, 
            # or just warms DNS). We don't have explicit candidate caching right now, but it's good to prime it.
            cands = await get_author_candidates(author)
            logger.info(f"  -> Found {len(cands.get('candidates', []))} candidates")
            
            # Step 2: Trigger full fan-out search with use_cache=False to force DB storage
            # This fetches from Scholar via Playwright and saves to ScholarCache, 
            # and fetches from APIs and saves to SourceRecord & merged CacheEntry.
            # We want to emulate the exact query keys that will be generated in demo mode
            # which is: "{author_name.lower().strip()}_none_False"
            
            # For ambiguous names, if we don't provide candidate_id, it will return multiple_candidates=True
            # and NOT fan out! So we MUST fetch candidates, pick the top one, and fan out using that candidate ID.
            
            candidate_id = None
            if cands.get("multiple_candidates") and cands["candidates"]:
                # Pick the top one as the one we'll click in the demo
                candidate_id = cands["candidates"][0].get("id")
                logger.info(f"  -> Selected candidate ID: {candidate_id}")
                
            try:
                res = await search(
                    author_name=author,
                    db=db,
                    author_id=candidate_id,
                    requested_sources=None,
                    use_cache=False, # Force re-fetch and re-cache
                    disable_dedup=False
                )
                
                dur = time.time() - start_time
                logger.info(f"  -> SUCCESS: Merged {res.get('total')} papers in {dur:.2f}s")
            except Exception as e:
                logger.error(f"  -> FAILED for {author}: {e}")

    await manager.stop()
    logger.info("Pre-warming complete. You may now run the app in DEMO_MODE.")

if __name__ == "__main__":
    asyncio.run(main())
