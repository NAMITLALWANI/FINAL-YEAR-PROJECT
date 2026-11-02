import json
import httpx
from pathlib import Path
from ingestion.base import BaseConnector
from config import USE_MOCK_DATA

MOCK_PATH = Path(__file__).parent.parent / "mock_data" / "dblp_hinton.json"
BASE_URL = "https://dblp.org/search"


class DBLPConnector(BaseConnector):
    source_name = "dblp"

    async def _fetch_impl(self, author_name: str, **kwargs) -> list[dict]:
        if USE_MOCK_DATA and MOCK_PATH.exists():
            return json.loads(MOCK_PATH.read_text())

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            # Step 1: Find author pid (optional but good for precision)
            # We'll try a direct publication search with author:Name first as it's more reliable
            # than the multi-step PID dance if names are unique enough.
            search_query = f"author:{author_name}:"  # colon at end handles exact match in DBLP
            
            pub_resp = await client.get(
                f"{BASE_URL}/publ/api",
                params={"q": search_query, "format": "json", "h": 50},
            )
            pub_resp.raise_for_status()
            
            data = pub_resp.json()
            pub_hits = data.get("result", {}).get("hits", {}).get("hit", [])

            # If no hits, try without the trailing colon
            if not pub_hits:
                pub_resp = await client.get(
                    f"{BASE_URL}/publ/api",
                    params={"q": f"author:{author_name}", "format": "json", "h": 50},
                )
                pub_hits = pub_resp.json().get("result", {}).get("hits", {}).get("hit", [])

        records = []
        for hit in pub_hits:
            info = hit.get("info", {})
            
            # Extract authors list
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
