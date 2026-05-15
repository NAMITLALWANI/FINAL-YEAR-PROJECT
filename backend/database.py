from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import Integer, Text, Float, Boolean, DateTime
from datetime import datetime, timezone
from typing import Optional
from config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class SourceRecord(Base):
    """Raw record as returned by a single source (API or scraper)."""
    __tablename__ = "source_records"

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    source:      Mapped[str]           = mapped_column(Text, nullable=False)
    source_id:   Mapped[Optional[str]] = mapped_column(Text)
    title:       Mapped[Optional[str]] = mapped_column(Text)
    authors_raw: Mapped[Optional[str]] = mapped_column(Text)       # JSON list string
    year:        Mapped[Optional[int]] = mapped_column(Integer)
    venue:       Mapped[Optional[str]] = mapped_column(Text)
    doi:         Mapped[Optional[str]] = mapped_column(Text, index=True)
    abstract:    Mapped[Optional[str]] = mapped_column(Text)
    citations:   Mapped[Optional[int]] = mapped_column(Integer, default=0)
    url:         Mapped[Optional[str]] = mapped_column(Text)
    raw_json:    Mapped[Optional[str]] = mapped_column(Text)        # full original response
    ingested_at: Mapped[datetime]      = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class Publication(Base):
    """Canonical merged record — one row per unique paper."""
    __tablename__ = "publications"

    id:               Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_id:     Mapped[str]           = mapped_column(Text, unique=True, index=True)
    title:            Mapped[Optional[str]] = mapped_column(Text)
    authors:          Mapped[Optional[str]] = mapped_column(Text)  # JSON list string
    year:             Mapped[Optional[int]] = mapped_column(Integer)
    abstract:         Mapped[Optional[str]] = mapped_column(Text)
    abstract_source:  Mapped[Optional[str]] = mapped_column(Text)
    doi:              Mapped[Optional[str]] = mapped_column(Text)
    doi_source:       Mapped[Optional[str]] = mapped_column(Text)
    venue:            Mapped[Optional[str]] = mapped_column(Text)
    venue_source:     Mapped[Optional[str]] = mapped_column(Text)
    citations:        Mapped[Optional[int]] = mapped_column(Integer, default=0)
    citations_source: Mapped[Optional[str]] = mapped_column(Text)
    best_source:      Mapped[Optional[str]] = mapped_column(Text)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, default=1.0)
    source_count:     Mapped[int]           = mapped_column(Integer, default=1)
    source_list:      Mapped[Optional[str]] = mapped_column(Text)  # JSON list string
    scholar_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    merged_at:        Mapped[datetime]      = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class DuplicateGroup(Base):
    """Maps a set of source_record IDs → the merged publication."""
    __tablename__ = "duplicate_groups"

    id:                Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    publication_id:    Mapped[int]           = mapped_column(Integer, index=True)
    source_record_ids: Mapped[Optional[str]] = mapped_column(Text)  # JSON list of source_ids (strings)


class SimilarityLog(Base):
    """Audit trail for pairwise dedup comparisons (score > threshold only)."""
    __tablename__ = "similarity_logs"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    record1_id: Mapped[str]           = mapped_column(Text) # changed from int to text
    record2_id: Mapped[str]           = mapped_column(Text) # changed from int to text
    title_sim:  Mapped[Optional[float]] = mapped_column(Float)
    author_sim: Mapped[Optional[float]] = mapped_column(Float)
    year_match: Mapped[Optional[bool]]  = mapped_column(Boolean)
    score:      Mapped[Optional[float]] = mapped_column(Float)
    decision:   Mapped[Optional[str]]   = mapped_column(Text)  # "MERGED" | "SEPARATE"
    timestamp:  Mapped[datetime]        = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class CacheEntry(Base):
    """Cached final merged search responses."""
    __tablename__ = "cache_entries"

    query_key:   Mapped[str]      = mapped_column(Text, primary_key=True)
    result_json: Mapped[str]      = mapped_column(Text)
    expires_at:  Mapped[datetime] = mapped_column(DateTime)


class ScholarCache(Base):
    """Persistent DB cache for Google Scholar HTML responses to prevent CAPTCHA blocks."""
    __tablename__ = "scholar_cache"

    profile_url: Mapped[str]      = mapped_column(Text, primary_key=True)
    html_content: Mapped[str]     = mapped_column(Text)
    expires_at:  Mapped[datetime] = mapped_column(DateTime)


class CircuitBreakerState(Base):
    """Tracks per-source failure counts and cooldown windows."""
    __tablename__ = "circuit_breaker_state"

    source:         Mapped[str]           = mapped_column(Text, primary_key=True)
    failure_count:  Mapped[int]           = mapped_column(Integer, default=0)
    disabled_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


# ── Engine & session factory ─────────────────────────────────────

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
