import json
import httpx
from pathlib import Path
from connectors.base import BaseConnector
from config import USE_MOCK_DATA, CROSSREF_MAILTO

MOCK_PATH = Path(__file__).parent.parent / "mock_data" / "crossref_hinton.json"
BASE_URL = "https://api.crossref.org/works"


class CrossrefConnector(BaseConnector):
    source_name = "crossref"

    async def _fetch_impl(self, author_name: str, **kwargs) -> list[dict]:
        if USE_MOCK_DATA and MOCK_PATH.exists():
            return json.loads(MOCK_PATH.read_text())

        headers = {
            "User-Agent": f"AcademiQ/1.0 (mailto:{CROSSREF_MAILTO})"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
            resp = await client.get(
                BASE_URL,
                params={
                    "query.author": author_name,
                    "rows": 30,
                    "sort": "is-referenced-by-count",
                    "order": "desc",
                },
            )
            resp.raise_for_status()
            items = resp.json().get("message", {}).get("items", [])

        records = []
        for item in items:
            # Extract authors list
            authors = []
            for a in item.get("author", []):
                given = a.get("given", "")
                family = a.get("family", "")
                if family:
                    authors.append(f"{given} {family}".strip())

            # Extract year from created or published-print
            year = None
            date_parts = item.get("published-print", {}).get("date-parts", [])
            if not date_parts:
                date_parts = item.get("created", {}).get("date-parts", [])
            
            if date_parts and date_parts[0]:
                year = int(date_parts[0][0])

            records.append({
                "source":    "crossref",
                "source_id": item.get("DOI") or item.get("URL") or "",
                "title":     item.get("title", [""])[0],
                "authors":   authors,
                "year":      year,
                "doi":       item.get("DOI") or "",
                "venue":     item.get("container-title", [""])[0],
                "citations": item.get("is-referenced-by-count", 0),
                "url":       item.get("URL") or f"https://doi.org/{item.get('DOI')}",
                "raw_json":  json.dumps(item),
            })

        return records
