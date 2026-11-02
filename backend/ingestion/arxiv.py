import json
import httpx
import feedparser
import asyncio
from pathlib import Path
from ingestion.base import BaseConnector
from config import USE_MOCK_DATA, ARXIV_DELAY_SECONDS

MOCK_PATH = Path(__file__).parent.parent / "mock_data" / "arxiv_hinton.xml"
BASE_URL = "https://export.arxiv.org/api/query"

# Global lock to respect arXiv's 3-second delay policy
_arxiv_lock = asyncio.Lock()


class ArXivConnector(BaseConnector):
    source_name = "arxiv"

    async def _fetch_impl(self, author_name: str, **kwargs) -> list[dict]:
        if USE_MOCK_DATA and MOCK_PATH.exists():
            feed = await asyncio.to_thread(feedparser.parse, str(MOCK_PATH))
            return self._parse_feed(feed)

        async with _arxiv_lock:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                query_name = author_name.replace(" ", "_")
                resp = await client.get(
                    BASE_URL,
                    params={
                        "search_query": f"au:{query_name}",
                        "start": 0,
                        "max_results": 20,
                        "sort_by": "submittedDate",
                        "sort_order": "descending",
                    },
                )
                resp.raise_for_status()
                await asyncio.sleep(ARXIV_DELAY_SECONDS)

            feed = await asyncio.to_thread(feedparser.parse, resp.text)

        return self._parse_feed(feed)

    def _parse_feed(self, feed) -> list[dict]:
        records = []
        for entry in feed.entries:
            doi = ""
            for link in entry.get("links", []):
                if link.get("title") == "doi":
                    doi = link.get("href", "").replace("https://doi.org/", "")
                elif "doi.org" in link.get("href", ""):
                    doi = link.get("href", "").split("doi.org/")[-1]

            year = None
            if entry.get("published"):
                try:
                    year = int(entry.published[:4])
                except:
                    pass

            records.append({
                "source":    "arxiv",
                "source_id": entry.id.split("/abs/")[-1] if "/abs/" in entry.id else entry.id,
                "title":     entry.title,
                "authors":   [a.name for a in entry.get("authors", [])],
                "year":      year,
                "doi":       doi,
                "abstract":  entry.summary,
                "venue":     "arXiv",
                "url":       entry.id,
                "raw_json":  json.dumps(entry),
            })
        return records
