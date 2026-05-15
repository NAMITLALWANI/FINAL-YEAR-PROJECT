from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import CircuitBreakerState
from config import CIRCUIT_BREAKER_THRESHOLD, CIRCUIT_BREAKER_TIMEOUT_MINUTES


async def is_source_available(source: str, db: AsyncSession) -> bool:
    result = await db.execute(
        select(CircuitBreakerState).where(CircuitBreakerState.source == source)
    )
    state = result.scalar_one_or_none()
    if state is None:
        return True
    
    if state.disabled_until:
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        expires = state.disabled_until.replace(tzinfo=None) if state.disabled_until.tzinfo else state.disabled_until
        if now_naive < expires:
            return False
            
    return True


async def record_failure(source: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(CircuitBreakerState).where(CircuitBreakerState.source == source)
    )
    state = result.scalar_one_or_none()
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    
    if state is None:
        db.add(CircuitBreakerState(source=source, failure_count=1))
    else:
        state.failure_count = (state.failure_count or 0) + 1
        if state.failure_count >= CIRCUIT_BREAKER_THRESHOLD:
            state.disabled_until = now_naive + timedelta(
                minutes=CIRCUIT_BREAKER_TIMEOUT_MINUTES
            )
    await db.commit()


async def record_success(source: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(CircuitBreakerState).where(CircuitBreakerState.source == source)
    )
    state = result.scalar_one_or_none()
    if state:
        state.failure_count = 0
        state.disabled_until = None
        await db.commit()


async def get_all_statuses(db: AsyncSession) -> dict:
    result = await db.execute(select(CircuitBreakerState))
    states = result.scalars().all()
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    
    return {
        s.source: {
            "status": "open" if (s.disabled_until and now_naive < s.disabled_until.replace(tzinfo=None)) else "closed",
            "failure_count": s.failure_count,
            "disabled_until": s.disabled_until.isoformat() if s.disabled_until else None,
        }
        for s in states
    }
