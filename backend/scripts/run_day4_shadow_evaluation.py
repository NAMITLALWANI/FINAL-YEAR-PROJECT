import asyncio
import json
import re
import unicodedata
from pathlib import Path
import httpx
from backend.config import OPENALEX_MAILTO, SOURCE_TIMEOUT
from backend.services.author_candidates import (
    CandidateGenerationResult,
    AuthorCandidateInput,
    AuthorCandidateProfile,
    _clean_text,
    _parse_affiliations,
    _parse_external_ids
)

def clean_and_normalize_author_name(raw_name: str) -> str:
    """Conservative safe normalization for author candidate query."""
    if not raw_name:
        return ""
    # 1. Unicode NFC normalization
    name = unicodedata.normalize("NFC", raw_name)
    # 2. Normalize whitespace
    name = re.sub(r"\s+", " ", name).strip()
    # 3. Narrow compound-surname normalization: 'Le Cun' -> 'LeCun'
    parts = name.split()
    if len(parts) >= 2:
        new_parts = []
        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and parts[i].lower() in {"le", "la"} and parts[i+1][0].isupper() and len(parts[i+1]) > 2:
                combined = parts[i].capitalize() + parts[i+1]
                new_parts.append(combined)
                i += 2
            else:
                new_parts.append(parts[i])
                i += 1
        name = " ".join(new_parts)
    return name

async def fetch_candidates_shadow(request: AuthorCandidateInput) -> list[AuthorCandidateProfile]:
    raw_name = request.author_name.strip()
    cleaned_name = clean_and_normalize_author_name(raw_name)
    if not cleaned_name:
        return []
    
    # 1. Primary query: filter=display_name.search:{cleaned_name}
    url = "https://api.openalex.org/authors"
    params = {
        "mailto": OPENALEX_MAILTO,
        "filter": f"display_name.search:{cleaned_name}",
        "per-page": 10
    }
    
    candidates = []
    async with httpx.AsyncClient(timeout=SOURCE_TIMEOUT) as client:
        try:
            r = await client.get(url, params=params)
            if r.status_code == 200:
                results = r.json().get("results", [])
                for item in results:
                    pid = item.get("id") or ""
                    clean_id = pid.rsplit("/", 1)[-1]
                    name = item.get("display_name") or ""
                    affils = _parse_affiliations(item.get("affiliations"))
                    c = AuthorCandidateProfile(
                        source="openalex",
                        source_author_id=clean_id,
                        display_name=name,
                        source_author_url=pid,
                        affiliations=affils,
                        works_count=item.get("works_count"),
                        cited_by_count=item.get("cited_by_count"),
                        summary_stats=item.get("summary_stats"),
                        external_ids=_parse_external_ids(item.get("ids")),
                        retrieved_at=None,
                        provenance=None
                    )
                    candidates.append(c)
        except Exception:
            pass

        # 2. If 0 candidates returned and name contains initial (e.g. 'Y. LeCun'), fallback to search={cleaned_name}
        if not candidates and (re.search(r"\b[A-Za-z]\.\s*", cleaned_name) or "." in cleaned_name):
            fallback_params = {
                "mailto": OPENALEX_MAILTO,
                "search": cleaned_name,
                "per-page": 10
            }
            try:
                r_fb = await client.get(url, params=fallback_params)
                if r_fb.status_code == 200:
                    results = r_fb.json().get("results", [])
                    for item in results:
                        pid = item.get("id") or ""
                        clean_id = pid.rsplit("/", 1)[-1]
                        name = item.get("display_name") or ""
                        affils = _parse_affiliations(item.get("affiliations"))
                        c = AuthorCandidateProfile(
                            source="openalex",
                            source_author_id=clean_id,
                            display_name=name,
                            source_author_url=pid,
                            affiliations=affils,
                            works_count=item.get("works_count"),
                            cited_by_count=item.get("cited_by_count"),
                            summary_stats=item.get("summary_stats"),
                            external_ids=_parse_external_ids(item.get("ids")),
                            retrieved_at=None,
                            provenance=None
                        )
                        candidates.append(c)
            except Exception:
                pass

    return candidates

async def run_shadow_eval():
    with open("docs/audit/phase4/results/author_resolution_benchmark_100_v2_corrected.json") as f:
        bench = json.load(f)
    
    results = bench["results"]
    gold_queries = [r for r in results if r["gold_id"] is not None]
    
    print(f"Running shadow candidate retrieval evaluation across {len(gold_queries)} gold queries...")
    
    recovered_cases = []
    recalls_at_1 = []
    recalls_at_5 = []
    recalls_at_10 = []
    mrr_list = []
    zero_cand_count = 0
    total_cands_list = []
    
    for q in gold_queries:
        qid = q["id"]
        name = q["name"]
        inst = q["inst"]
        gold_id = q["gold_id"]
        
        cands = await fetch_candidates_shadow(AuthorCandidateInput(author_name=name, institution_hint=inst))
        total_cands_list.append(len(cands))
        if len(cands) == 0:
            zero_cand_count += 1
            
        cand_ids = [c.source_author_id for c in cands]
        hit_idx = None
        for idx, cid in enumerate(cand_ids):
            if cid == gold_id or (cid.startswith("A5") and gold_id.startswith("A5") and (cid in gold_id or gold_id in cid)):
                hit_idx = idx
                break
                
        if hit_idx is not None:
            recalls_at_1.append(1 if hit_idx == 0 else 0)
            recalls_at_5.append(1 if hit_idx < 5 else 0)
            recalls_at_10.append(1 if hit_idx < 10 else 0)
            mrr_list.append(1.0 / (hit_idx + 1))
            if qid in ("Q064", "Q065"):
                recovered_cases.append((qid, name, hit_idx, cands[hit_idx].display_name, cands[hit_idx].source_author_id))
        else:
            recalls_at_1.append(0)
            recalls_at_5.append(0)
            recalls_at_10.append(0)
            mrr_list.append(0.0)
            
    n_gold = len(gold_queries)
    r1 = sum(recalls_at_1) / n_gold
    r5 = sum(recalls_at_5) / n_gold
    r10 = sum(recalls_at_10) / n_gold
    mrr = sum(mrr_list) / n_gold
    avg_cands = sum(total_cands_list) / len(total_cands_list)
    
    shadow_metrics = {
        "candidate_recall_at_1": round(r1, 4),
        "candidate_recall_at_5": round(r5, 4),
        "candidate_recall_at_10": round(r10, 4),
        "mrr": round(mrr, 4),
        "zero_candidate_queries": zero_cand_count,
        "avg_candidates_per_query": round(avg_cands, 2),
        "recovered_cases": recovered_cases
    }
    
    print("\n=== SHADOW RETRIEVAL EVALUATION RESULTS ===")
    print(f"Recall@1:  {r1:.4f} (Baseline: 0.5536)")
    print(f"Recall@5:  {r5:.4f} (Baseline: 0.7143)")
    print(f"Recall@10: {r10:.4f} (Baseline: 0.7143)")
    print(f"MRR:       {mrr:.4f} (Baseline: 0.6152)")
    print(f"Zero cand queries: {zero_cand_count} (Baseline: 10)")
    print(f"Avg candidates/query: {avg_cands:.2f}")
    print(f"Recovered gold queries: {recovered_cases}")
    
    out_file = Path("docs/finalisation/week1/day4/shadow_evaluation_results.json")
    out_file.write_text(json.dumps(shadow_metrics, indent=2))
    print(f"Saved results to {out_file}")

asyncio.run(run_shadow_eval())
