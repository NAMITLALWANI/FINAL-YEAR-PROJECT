from bs4 import BeautifulSoup
from log_config import get_logger

logger = get_logger(__name__)

def parse_scholar_profile(html: str) -> list[dict]:
    """
    Parses the HTML of a Google Scholar profile page.
    Returns a list of extracted publication dictionaries.
    """
    soup = BeautifulSoup(html, 'html.parser')
    records = []
    
    rows = soup.select('tr.gsc_a_tr')
    for row in rows:
        try:
            # Title
            title_tag = row.select_one('a.gsc_a_at')
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            
            # Authors and Venue (both are in div.gs_gray)
            gray_divs = row.select('div.gs_gray')
            authors_str = gray_divs[0].get_text(strip=True) if len(gray_divs) > 0 else ""
            venue_str = gray_divs[1].get_text(strip=True) if len(gray_divs) > 1 else ""
            
            # Clean authors string into list
            authors = [a.strip() for a in authors_str.split(',') if a.strip()]
            
            # Citations
            cites_tag = row.select_one('a.gsc_a_ac')
            citations = 0
            if cites_tag and cites_tag.get_text(strip=True).isdigit():
                citations = int(cites_tag.get_text(strip=True))
                
            # Year
            year_tag = row.select_one('span.gsc_a_h')
            year = None
            if year_tag and year_tag.get_text(strip=True).isdigit():
                year = int(year_tag.get_text(strip=True))
                
            # ID (from href)
            href = title_tag.get('href', '')
            source_id = href.split('citation_for_view=')[-1] if 'citation_for_view=' in href else href
            
            records.append({
                "source": "scholar",
                "source_id": source_id,
                "title": title,
                "authors": authors,
                "year": year,
                "venue": venue_str,
                "citations": citations,
                "url": f"https://scholar.google.com{href}" if href.startswith('/') else href,
                "doi": "", # Scholar doesn't typically show DOIs on the profile list page
                "abstract": "", # Not on the list page
            })
        except Exception as e:
            logger.debug(f"Failed to parse a scholar row: {e}")
            
    return records
