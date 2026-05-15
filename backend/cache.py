import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import CacheEntry
from config import CACHE_TTL_HOURS


def _make_key(author_name: str, sources: list[str]) -> str:
    normalized = author_name.lower().strip()
    source_str = ",".join(sorted(sources)) if sources else "all"
    return f"{normalized}::{source_str}"


async def get_cached(author_name: str, sources: list[str], db: AsyncSession) -> dict | None:
    key = _make_key(author_name, sources)
    result = await db.execute(select(CacheEntry).where(CacheEntry.query_key == key))
    entry = result.scalar_one_or_none()
    if entry and datetime.now(timezone.utc).replace(tzinfo=None) < entry.expires_at:
        return json.loads(entry.result_json)
    return None


async def set_cached(
    author_name: str,
    sources: list[str],
    data: dict,
    db: AsyncSession,
    ttl_hours: int = CACHE_TTL_HOURS,
) -> None:
    key = _make_key(author_name, sources)
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    result = await db.execute(select(CacheEntry).where(CacheEntry.query_key == key))
    entry = result.scalar_one_or_none()
    if entry:
        entry.result_json = json.dumps(data)
        entry.expires_at = expires_at
    else:
        db.add(CacheEntry(query_key=key, result_json=json.dumps(data), expires_at=expires_at))
    await db.commit()
