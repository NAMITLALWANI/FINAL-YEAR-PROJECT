import asyncio
import httpx
import time
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"

async def test_health():
    print("\n--- SECTION 1: CORE SYSTEM VALIDATION ---")
    async with httpx.AsyncClient() as client:
        # Health
        start = time.time()
        res = await client.get(f"{BASE_URL}/health")
        print(f"GET /health -> Status: {res.status_code}, Time: {(time.time()-start)*1000:.1f}ms")
        print("Response:", json.dumps(res.json(), indent=2))
        
        # Metrics
        start = time.time()
        res = await client.get(f"{BASE_URL}/metrics")
        print(f"GET /metrics -> Status: {res.status_code}, Time: {(time.time()-start)*1000:.1f}ms")
        print("Response:", json.dumps(res.json(), indent=2))

async def test_candidates():
    print("\n--- SECTION 2: AUTHOR CANDIDATE SELECTION TESTING ---")
    async with httpx.AsyncClient(timeout=30.0) as client:
        test_cases = [
            ("Geoffrey Hinton", None),
            ("Andrew Ng", None),
            ("Yann LeCun", None),
            ("Fei-Fei Li", None),
            ("Rajesh Kumar", None),
            ("A Sharma", None),
            ("S Patel", None),
            ("Amit Kumar", None),
            ("P Singh", None),
            ("Rajesh Kumar", "K J Somaiya"),
            ("Rajesh Kumar", "IIT Bombay"),
        ]
        
        results = []
        for name, inst in test_cases:
            params = {"name": name}
            if inst: params["institution"] = inst
            
            print(f"\nQuerying candidates for: '{name}' (Institution: {inst})")
            start = time.time()
            res = await client.get(f"{BASE_URL}/search/candidates", params=params)
            duration = (time.time() - start) * 1000
            
            if res.status_code != 200:
                print(f"ERROR: {res.status_code} - {res.text}")
                continue
                
            data = res.json()
            cands = data.get("candidates", [])
            multiple = data.get("multiple_candidates")
            auto = data.get("auto_selected")
            
            print(f"Candidates Found: {len(cands)} | Multiple? {multiple} | Auto-selected? {bool(auto)} | Time: {duration:.1f}ms")
            
            if cands:
                top = cands[0]
                print(f"  Top Candidate: {top['display_name']} ({top.get('institution', 'N/A')}) | Score: {top['score']:.2f} | Conf: {top['confidence']}")
            
            results.append({
                "name": name,
                "institution": inst,
                "count": len(cands),
                "multiple": multiple,
                "auto_selected": auto,
                "top": cands[0] if cands else None,
                "time": duration
            })
            
        with open("candidates_test_results.json", "w") as f:
            json.dump(results, f, indent=2)

async def test_scholar():
    print("\n--- SECTION 4: GOOGLE SCHOLAR SCRAPER VALIDATION ---")
    async with httpx.AsyncClient(timeout=60.0) as client:
        authors = ["Geoffrey Hinton", "Andrew Ng"]
        for author in authors:
            print(f"\nTesting Scholar Scraper for '{author}'")
            start = time.time()
            res = await client.get(f"{BASE_URL}/debug/raw-response", params={"source": "scholar", "query": author})
            duration = (time.time() - start) * 1000
            print(f"Status: {res.status_code} | Time: {duration:.1f}ms")
            
            try:
                data = res.json()
                records = data.get("records", [])
                print(f"Extracted {len(records)} records from Scholar.")
                if records:
                    print(f"Top 2: {json.dumps(records[:2], indent=2)}")
            except Exception as e:
                print(f"Failed to parse JSON. Raw response: {res.text[:500]}")

async def test_dedup():
    print("\n--- SECTION 3: DEDUPLICATION VALIDATION ---")
    async with httpx.AsyncClient(timeout=60.0) as client:
        # We will use "Geoffrey Hinton" to test dedup with disable_dedup=true vs false
        name = "Geoffrey Hinton"
        print(f"\nTesting /search for '{name}' with disable_dedup=False (Warm Cache)")
        res = await client.get(f"{BASE_URL}/search", params={"name": name, "use_cache": False, "disable_dedup": False})
        
        if res.status_code != 200:
            print(f"ERROR: {res.status_code} - {res.text}")
            return
            
        dedup_data = res.json()
        print(f"Raw Records: {dedup_data.get('raw_records')} -> Merged Publications: {dedup_data.get('total')}")
        
        print(f"\nTesting /search for '{name}' with disable_dedup=True")
        res = await client.get(f"{BASE_URL}/search", params={"name": name, "use_cache": False, "disable_dedup": True})
        nodedup_data = res.json()
        print(f"Raw Records: {nodedup_data.get('raw_records')} -> Unmerged Publications: {nodedup_data.get('total')}")
        
        # Test similar titles / false merges could be checked in the dedup logs via /similarity-log/{pub_id}
        if dedup_data.get("papers"):
            top_pub = dedup_data["papers"][0]
            print(f"\nFetching similarity log for top publication ID: {top_pub['id']} ('{top_pub['title']}')")
            log_res = await client.get(f"{BASE_URL}/similarity-log/{top_pub['id']}")
            print("Similarity Log:", json.dumps(log_res.json(), indent=2)[:500] + "...")

async def test_cache():
    print("\n--- SECTION 5: CACHE VALIDATION ---")
    async with httpx.AsyncClient(timeout=60.0) as client:
        name = "Yann LeCun"
        print(f"Query: '{name}'")
        
        # Cold Cache
        start = time.time()
        res1 = await client.get(f"{BASE_URL}/search", params={"name": name, "use_cache": True})
        dur1 = (time.time() - start) * 1000
        data1 = res1.json()
        print(f"Cold Cache -> Time: {dur1:.1f}ms | Cache Hit: {data1.get('cache_hit')}")
        
        # Warm Cache
        start = time.time()
        res2 = await client.get(f"{BASE_URL}/search", params={"name": name, "use_cache": True})
        dur2 = (time.time() - start) * 1000
        data2 = res2.json()
        print(f"Warm Cache -> Time: {dur2:.1f}ms | Cache Hit: {data2.get('cache_hit')}")

async def main():
    await test_health()
    await test_candidates()
    await test_scholar()
    await test_dedup()
    await test_cache()

if __name__ == "__main__":
    asyncio.run(main())
