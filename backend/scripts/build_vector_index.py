"""Reconcile Chroma's retrieval projection from the selected relational DB.

Run from backend/: ../.venv/bin/python scripts/build_vector_index.py
"""
import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import AsyncSessionLocal, engine
from services.scholarly_retrieval import build_index


async def main() -> None:
    try:
        async with AsyncSessionLocal() as session:
            result = await build_index(session)
        print(result)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())