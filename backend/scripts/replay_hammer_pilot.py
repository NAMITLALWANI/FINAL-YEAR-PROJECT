"""Offline replay of frozen pilot captures (no network, no database, no Chroma)."""
import argparse
import asyncio
import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.dont_write_bytecode = True

from hammer_pilot.pipeline import run_pipeline


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    print(await run_pipeline(args.pilot_dir, args.out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
