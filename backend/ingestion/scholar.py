from ingestion.base import BaseConnector
from ingestion.scrapers.scholar.profile_lookup import get_scholar_profile_url
from ingestion.scrapers.scholar.profile_scraper import fetch_scholar_profile

class ScholarConnector(BaseConnector):
    source_name = "scholar"

    # We need access to the db session for caching.
    # We will pass it via kwargs from search_service.
    async def _fetch_impl(self, author_name: str, **kwargs) -> list[dict]:
        db = kwargs.get("db")
        if not db:
            raise ValueError("ScholarConnector requires a db session for caching")
            
        profile_url = get_scholar_profile_url(author_name)
        if not profile_url:
            # We don't have a manual mapping. We could fall back to dynamic search here in Phase 2,
            # but for now, we return empty to avoid immediate CAPTCHA bans.
            return []
            
        records, status = await fetch_scholar_profile(profile_url, db)
        
        # If status is failed, maybe bubble it up, but for now we just return records
        return records
