"""Day 5: End-to-end evaluation of production candidate generation with Day 5 normalization.

This script calls the PRODUCTION OpenAlexCandidateService.generate() method
(which now includes clean_query_name normalization, institutional input guard,
and initial-only search fallback) against all gold queries from the corrected
V2 benchmark, and measures retrieval metrics.

Includes local query caching to ensure OpenAlex API limits are strictly conserved.
It does NOT modify the database, ChromaDB, or benchmark files.
"""
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.author_candidates import (
    AuthorCandidateInput,
    OpenAlexCandidate,
    CandidateGenerationResult,
    OpenAlexCandidateService,
    clean_query_name,
    is_institutional_input,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BENCHMARK_PATH = PROJECT_ROOT / "docs/audit/phase4/results/author_resolution_benchmark_100_v2_corrected.json"
OUTPUT_DIR = PROJECT_ROOT / "docs/finalisation/week1/day5"


async def run_e2e_evaluation():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = OUTPUT_DIR / "candidate_query_cache.json"
    query_cache = {}
    if cache_file.exists():
        try:
            with open(cache_file) as cf:
                query_cache = json.load(cf)
            print(f"Loaded {len(query_cache)} cached queries from disk.")
        except Exception:
            query_cache = {}

    with open(BENCHMARK_PATH) as f:
        bench = json.load(f)

    results = bench["results"]
    gold_queries = [r for r in results if r.get("gold_id") is not None]
    all_queries = results

    print(f"=== DAY 5 END-TO-END PRODUCTION EVALUATION ===")
    print(f"Total benchmark queries: {len(all_queries)}")
    print(f"Gold-labeled queries:    {len(gold_queries)}")
    print()

    service = OpenAlexCandidateService()

    # Track metrics
    recall_at_1 = []
    recall_at_5 = []
    recall_at_10 = []
    mrr_list = []
    zero_cand_count = 0
    institutional_rejected = 0
    total_cands_list = []
    per_query_results = []

    for idx, q in enumerate(gold_queries):
        qid = q["id"]
        name = q["name"]
        inst = q.get("inst")
        gold_id = q["gold_id"]

        # Check institutional guard
        if is_institutional_input(name):
            institutional_rejected += 1
            per_query_results.append({
                "id": qid, "name": name, "gold_id": gold_id,
                "status": "institutional_rejected", "candidates": 0,
                "gold_rank": None
            })
            recall_at_1.append(0)
            recall_at_5.append(0)
            recall_at_10.append(0)
            mrr_list.append(0.0)
            zero_cand_count += 1
            total_cands_list.append(0)
            continue

        request = AuthorCandidateInput(author_name=name, institution_hint=inst)

        cached_data = query_cache.get(name)
        if cached_data is not None:
            cands = [OpenAlexCandidate(**c) for c in cached_data.get("candidates", [])]
            result = CandidateGenerationResult(
                request=request,
                status=cached_data.get("status", "success"),
                candidates=cands,
                source="openalex_cached",
                error_code=None,
                error_message=None,
                retrieved_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
        else:
            try:
                result = await service.generate(request)
                if result.status == "success":
                    query_cache[name] = {
                        "status": result.status,
                        "candidates": [
                            {
                                "source": c.source,
                                "source_author_id": c.source_author_id,
                                "display_name": c.display_name,
                                "affiliations": c.affiliations,
                                "external_ids": c.external_ids,
                                "works_count": c.works_count,
                                "cited_by_count": c.cited_by_count,
                                "h_index": c.h_index,
                                "raw_payload": {}
                            }
                            for c in result.candidates
                        ]
                    }
                    cache_file.write_text(json.dumps(query_cache, indent=2))
                # Rate limit safety delay
                await asyncio.sleep(0.35)
            except Exception as exc:
                print(f"  ERROR on {qid}: {exc}")
                per_query_results.append({
                    "id": qid, "name": name, "gold_id": gold_id,
                    "status": "error", "candidates": 0, "gold_rank": None,
                    "error": str(exc)
                })
                recall_at_1.append(0)
                recall_at_5.append(0)
                recall_at_10.append(0)
                mrr_list.append(0.0)
                zero_cand_count += 1
                total_cands_list.append(0)
                continue

        if result.status == "failed" and result.error_code:
            print(f"  [{qid}] Candidate generation returned {result.status}: {result.error_code} ({result.error_message})")

        cands = result.candidates
        total_cands_list.append(len(cands))

        if len(cands) == 0:
            zero_cand_count += 1

        # Find gold match
        hit_idx = None
        for ci, c in enumerate(cands):
            cid = c.source_author_id
            if cid == gold_id:
                hit_idx = ci
                break
            # Flexible match for OpenAlex IDs (A5xxx format)
            if cid.startswith("A") and gold_id.startswith("A"):
                if cid in gold_id or gold_id in cid:
                    hit_idx = ci
                    break

        if hit_idx is not None:
            recall_at_1.append(1 if hit_idx == 0 else 0)
            recall_at_5.append(1 if hit_idx < 5 else 0)
            recall_at_10.append(1 if hit_idx < 10 else 0)
            mrr_list.append(1.0 / (hit_idx + 1))
        else:
            recall_at_1.append(0)
            recall_at_5.append(0)
            recall_at_10.append(0)
            mrr_list.append(0.0)

        per_query_results.append({
            "id": qid, "name": name, "gold_id": gold_id,
            "normalized_query": clean_query_name(name),
            "status": result.status, "candidates": len(cands),
            "gold_rank": hit_idx,
            "candidate_ids": [c.source_author_id for c in cands[:5]]
        })

        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(gold_queries)} queries...")

    n = len(gold_queries)
    r1 = sum(recall_at_1) / n if n else 0
    r5 = sum(recall_at_5) / n if n else 0
    r10 = sum(recall_at_10) / n if n else 0
    mrr = sum(mrr_list) / n if n else 0
    avg_cands = sum(total_cands_list) / len(total_cands_list) if total_cands_list else 0

    # Identify recovered cases (baseline had zero-candidate queries like Q064, Q065)
    recovered = [r for r in per_query_results if r["gold_rank"] is not None and r["id"] in ("Q064", "Q065")]

    metrics = {
        "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        "benchmark_file": str(BENCHMARK_PATH.name),
        "gold_queries_evaluated": n,
        "candidate_recall_at_1": round(r1, 4),
        "candidate_recall_at_5": round(r5, 4),
        "candidate_recall_at_10": round(r10, 4),
        "mrr": round(mrr, 4),
        "zero_candidate_queries": zero_cand_count,
        "institutional_rejected": institutional_rejected,
        "avg_candidates_per_query": round(avg_cands, 2),
        "recovered_cases": [r["id"] for r in recovered],
    }

    baseline = {
        "candidate_recall_at_1": 0.5536,
        "candidate_recall_at_5": 0.7143,
        "candidate_recall_at_10": 0.7143,
        "mrr": 0.6152,
        "zero_candidate_queries": 10,
    }

    print()
    print("=== DAY 5 PRODUCTION E2E RESULTS ===")
    print(f"  Recall@1:  {r1:.4f}  (baseline: {baseline['candidate_recall_at_1']:.4f}, delta: {r1 - baseline['candidate_recall_at_1']:+.4f})")
    print(f"  Recall@5:  {r5:.4f}  (baseline: {baseline['candidate_recall_at_5']:.4f}, delta: {r5 - baseline['candidate_recall_at_5']:+.4f})")
    print(f"  Recall@10: {r10:.4f}  (baseline: {baseline['candidate_recall_at_10']:.4f}, delta: {r10 - baseline['candidate_recall_at_10']:+.4f})")
    print(f"  MRR:       {mrr:.4f}  (baseline: {baseline['mrr']:.4f}, delta: {mrr - baseline['mrr']:+.4f})")
    print(f"  Zero-cand: {zero_cand_count}      (baseline: {baseline['zero_candidate_queries']})")
    print(f"  Institutional rejected: {institutional_rejected}")
    print(f"  Avg cands/query: {avg_cands:.2f}")
    print(f"  Recovered: {[r['id'] for r in recovered]}")
    print()

    # Regression guard: must not lose any baseline recall
    if r5 < baseline["candidate_recall_at_5"]:
        print("WARNING: Recall@5 REGRESSION detected!")
    else:
        print("REGRESSION CHECK: Recall@5 is non-regressive. PASS.")

    # Save outputs
    out_metrics = OUTPUT_DIR / "e2e_evaluation_metrics.json"
    out_metrics.write_text(json.dumps(metrics, indent=2))
    print(f"\nSaved metrics to {out_metrics}")

    out_details = OUTPUT_DIR / "e2e_per_query_results.json"
    out_details.write_text(json.dumps(per_query_results, indent=2))
    print(f"Saved per-query details to {out_details}")

    # Save comparison summary
    comparison = {
        "baseline_day4": baseline,
        "day5_production": {k: v for k, v in metrics.items() if k in baseline},
        "delta": {k: round(metrics[k] - baseline[k], 4) for k in baseline if k in metrics},
    }
    out_comparison = OUTPUT_DIR / "baseline_vs_day5_comparison.json"
    out_comparison.write_text(json.dumps(comparison, indent=2))
    print(f"Saved comparison to {out_comparison}")


if __name__ == "__main__":
    asyncio.run(run_e2e_evaluation())
