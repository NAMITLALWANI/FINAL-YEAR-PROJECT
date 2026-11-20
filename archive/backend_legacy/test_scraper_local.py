import asyncio
import json
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from connectors.faculty_scraper import FacultyScraper

async def test_scraper():
    scraper = FacultyScraper("kjsomaiya")
    # Author name doesn't matter much for this scraper in Phase 1
    records = await scraper._fetch_impl("Test Author")
    print(f"Found {len(records)} records")
    for r in records[:5]:
        print(f" - {r['title']} ({r['year']})")

if __name__ == "__main__":
    asyncio.run(test_scraper())
