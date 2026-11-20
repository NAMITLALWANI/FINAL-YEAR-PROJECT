"""Capture R0/R2 author candidates and enrichment responses for a frozen pilot seed set.

Live network use requires the explicit --allow-network flag (and an already configured non-personal mailto).
No secret is written to any file.
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")   # never touch the application database
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.dont_write_bytecode = True

import httpx

import config
from hammer_pilot.capture import run_capture
from hammer_pilot.guarded_transport import GuardStop, GuardedTransport


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-dir", type=Path, required=True)
    parser.add_argument("--budget", type=int, required=True, help="maximum number of new HTTP requests")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--allow-network", action="store_true", help="required to contact OpenAlex")
    parser.add_argument("--cost-ceiling-usd", type=float, default=None, help="stop before the next request once 80%% of this provider-reported cost is reached")
    args = parser.parse_args()
    if not args.allow_network:
        print("Refusing to contact the provider without --allow-network")
        return 2
    mailto = config.OPENALEX_MAILTO
    if any(x in mailto for x in ("gmail", "yahoo", "outlook", "hotmail")):
        print("Configured mailto looks personal; stop.")
        return 2
    guarded = GuardedTransport(httpx.AsyncHTTPTransport(), cost_ceiling_usd=args.cost_ceiling_usd)
    try:
        result = await run_capture(args.pilot_dir, inner_transport=guarded, budget=args.budget, resume=args.resume,
                                   mailto=mailto, api_key=config.OPENALEX_API_KEY or None)
    except GuardStop as stop:
        print(f"{stop}. Responses so far are saved and hashed; start a new capture directory or resume deliberately.")
        return 4
    print(f"cases completed: {len(result.completed_cases)}; requests made: {result.requests_made}; budget exhausted: {result.budget_exhausted}; provider stop: {result.provider_stop_status}")
    if result.provider_stop_status:
        return 3
    return 1 if result.budget_exhausted else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
