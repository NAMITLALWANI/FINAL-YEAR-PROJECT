import json
from pathlib import Path
from log_config import get_logger

logger = get_logger(__name__)

MAPPINGS_FILE = Path(__file__).parent.parent.parent.parent / "scholar_profiles.json"

def get_scholar_profile_url(author_name: str) -> str | None:
    """
    Looks up the author's name in the manual scholar_profiles.json mapping.
    Avoids dynamic searching to prevent immediate CAPTCHA bans.
    """
    if not MAPPINGS_FILE.exists():
        logger.warning(f"Scholar profiles mapping not found at {MAPPINGS_FILE}")
        return None

    try:
        mappings = json.loads(MAPPINGS_FILE.read_text())
        # Normalize name for lookup
        name_key = author_name.strip().lower()
        
        # Try exact match
        if name_key in mappings:
            return mappings[name_key]
            
        # Try loose match (e.g. if user searched "Hinton" and we have "Geoffrey Hinton")
        for key, url in mappings.items():
            if name_key in key or key in name_key:
                return url
                
    except Exception as e:
        logger.error(f"Failed to read scholar profiles: {e}")
        
    return None
