import json
import httpx
from pathlib import Path
from connectors.base import BaseConnector
from config import OPENALEX_API_KEY, OPENALEX_MAILTO, USE_MOCK_DATA
from log_config import get_logger

logger = get_logger(__name__)

MOCK_PATH = Path(__file__).parent.parent / "mock_data" / "openalex_hinton.json"
BASE_URL = "https://api.openalex.org"


class OpenAlexConnector(BaseConnector):
    source_name = "openalex"

    async def search_authors(self, author_name: str, institution_hint: str = None) -> list[dict]:
        """Fetch candidate authors from OpenAlex, using institution to boost score if provided."""
        if USE_MOCK_DATA and MOCK_PATH.exists():
            return [] # Mock doesn't support candidate search yet

        params = {
            "mailto": OPENALEX_MAILTO,
            **({"api_key": OPENALEX_API_KEY} if OPENALEX_API_KEY else {}),
            "filter": f"display_name.search:{author_name}",
            "per-page": 10
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{BASE_URL}/authors", params=params)
            resp.raise_for_status()
            results = resp.json().get("results", [])

        candidates = []
        for a in results:
            # Extract institution details
            affil = a.get("last_known_institutions", [])
            inst_name = affil[0].get("display_name") if affil else "Unknown Institution"
            country_code = affil[0].get("country_code") if affil else ""

            # Base score from OpenAlex relevance
            base_score = a.get("relevance_score", 0.0)
            works_count = a.get("works_count", 0)
            
            # Normalise works count slightly to contribute to score
            normalized_works = min(works_count / 1000.0, 1.0)
            
            # Boost score if institution hint matches
            inst_score = 0.0
            if institution_hint and institution_hint.lower() in inst_name.lower():
                inst_score = 1.0

            # Combined score
            final_score = (0.6 * min(base_score / 100.0, 1.0)) + (0.3 * inst_score) + (0.1 * normalized_works)

            candidates.append({
                "candidate_id": a["id"].split("/")[-1],
                "source": "openalex",
                "display_name": a.get("display_name"),
                "institution": inst_name,
                "country": country_code,
                "works_count": works_count,
                "cited_by_count": a.get("cited_by_count", 0),
                "score": final_score
            })
        
        # Sort candidates by the new hybrid score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates

    async def _fetch_impl(self, query: str, **kwargs) -> list[dict]:
        """
        If author_id is provided, fetches directly by ID.
        If query is provided and no author_id, fetches using the old method (first match).
        """
        author_id = kwargs.get("author_id")
        
        # ── Mock data shortcut ───────────────────────────────────
        if USE_MOCK_DATA and MOCK_PATH.exists():
            return json.loads(MOCK_PATH.read_text())

        params_base = {"mailto": OPENALEX_MAILTO}
        if OPENALEX_API_KEY:
            params_base["api_key"] = OPENALEX_API_KEY

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if not author_id:
                # Fallback to name search if no ID provided (legacy flow)
                author_resp = await client.get(
                    f"{BASE_URL}/authors",
                    params={**params_base, "filter": f"display_name.search:{query}"},
                )
                author_resp.raise_for_status()
                author_results = author_resp.json().get("results", [])
                if not author_results:
                    return []
                author_id = author_results[0]["id"].split("/")[-1]

            # Step 2: fetch works for that author
            works_resp = await client.get(
                f"{BASE_URL}/works",
                params={
                    **params_base,
                    "filter":   f"author.id:{author_id}",
                    "per-page": 25,
                    "sort":     "cited_by_count:desc",
                },
            )
            works_resp.raise_for_status()
            works = works_resp.json().get("results", [])

        records = []
        for w in works:
            primary_loc  = w.get("primary_location") or {}
            source_info  = primary_loc.get("source") or {}
            venue        = source_info.get("display_name") or ""
            raw_doi = w.get("doi") or ""
            doi = raw_doi.replace("https://doi.org/", "").replace("http://doi.org/", "")

            records.append({
                "source":    "openalex",
                "source_id": (w.get("id") or "").split("/")[-1],
                "title":     w.get("display_name") or w.get("title") or "",
                "authors": [
                    a["author"]["display_name"]
                    for a in w.get("authorships", [])
                    if (a.get("author") or {}).get("display_name")
                ],
                "year":      w.get("publication_year"),
                "doi":       doi,
                "abstract":  w.get("abstract") or "",
                "venue":     venue,
                "citations": w.get("cited_by_count") or 0,
                "url":       w.get("id") or "",
                "raw_json":  json.dumps(w),
            })

        return records
