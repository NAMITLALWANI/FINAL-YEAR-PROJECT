"""Replay the same frozen inputs twice and byte-compare every generated output."""
import argparse
import asyncio
import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.dont_write_bytecode = True

from hammer_pilot.reproducibility import verify_reproducibility


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-dir", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True, help="new empty directory for run_a and run_b")
    args = parser.parse_args()
    result = await verify_reproducibility(args.pilot_dir, args.work_dir)
    print(result)
    return 0 if result["identical"] else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
