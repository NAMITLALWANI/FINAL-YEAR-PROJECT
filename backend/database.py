from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
)
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
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



# ââ Author resolution models ââââââââââââââââââââââââââââââââââââ
# These tables are intentionally independent from publication deduplication.
# Alembic owns their creation; init_db() continues to provision only the
# pre-existing application tables for backwards compatibility.

class Author(Base):
    """Canonical internal author identity created after a resolution decision."""
    __tablename__ = "authors"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid4())
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    resolution_state: Mapped[str] = mapped_column(
        Text, nullable=False, default="provisional"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    external_ids: Mapped[list["AuthorExternalId"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )
    aliases: Mapped[list["AuthorAlias"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )
    affiliations: Mapped[list["AuthorAffiliation"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )
    resolutions: Mapped[list["AuthorResolution"]] = relationship(
        back_populates="author"
    )
    publication_authorships: Mapped[list["PublicationAuthorship"]] = relationship(
        back_populates="author"
    )

    __table_args__ = (
        CheckConstraint(
            "resolution_state IN ('resolved', 'provisional', 'unresolved')",
            name="ck_authors_resolution_state",
        ),
    )


class AuthorExternalId(Base):
    """Source-scoped external identifiers with explicit provenance."""
    __tablename__ = "author_external_ids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[str] = mapped_column(
        Text, ForeignKey("authors.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    external_url: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    provenance_json: Mapped[Optional[str]] = mapped_column(Text)

    author: Mapped["Author"] = relationship(back_populates="external_ids")

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_author_external_ids_source_id"),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_author_external_ids_confidence"),
        Index("ix_author_external_ids_author_source", "author_id", "source"),
    )


class AuthorAlias(Base):
    """Observed name variants for a canonical author."""
    __tablename__ = "author_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[str] = mapped_column(
        Text, ForeignKey("authors.id", ondelete="CASCADE"), nullable=False
    )
    alias: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_alias: Mapped[str] = mapped_column(Text, nullable=False)
    alias_type: Mapped[str] = mapped_column(Text, nullable=False, default="source_observed")
    source: Mapped[str] = mapped_column(Text, nullable=False, default="manual")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    author: Mapped["Author"] = relationship(back_populates="aliases")

    __table_args__ = (
        UniqueConstraint(
            "author_id", "normalized_alias", "source", name="uq_author_aliases_author_alias_source"
        ),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_author_aliases_confidence"),
        Index("ix_author_aliases_normalized_alias", "normalized_alias"),
    )


class AuthorAffiliation(Base):
    """Time-aware affiliation evidence for a canonical author."""
    __tablename__ = "author_affiliations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[str] = mapped_column(
        Text, ForeignKey("authors.id", ondelete="CASCADE"), nullable=False
    )
    institution_name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_institution: Mapped[str] = mapped_column(Text, nullable=False)
    institution_external_id: Mapped[Optional[str]] = mapped_column(Text)
    department: Mapped[Optional[str]] = mapped_column(Text)
    country_code: Mapped[Optional[str]] = mapped_column(Text)
    start_year: Mapped[Optional[int]] = mapped_column(Integer)
    end_year: Mapped[Optional[int]] = mapped_column(Integer)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_ref: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    author: Mapped["Author"] = relationship(back_populates="affiliations")

    __table_args__ = (
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_author_affiliations_confidence"),
        CheckConstraint(
            "start_year IS NULL OR end_year IS NULL OR start_year <= end_year",
            name="ck_author_affiliations_year_range",
        ),
        Index("ix_author_affiliations_author", "author_id"),
        Index("ix_author_affiliations_institution_country", "normalized_institution", "country_code"),
    )


class AuthorCandidate(Base):
    """Immutable source candidate snapshot generated for an author query."""
    __tablename__ = "author_candidates"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid4())
    )
    query_original: Mapped[str] = mapped_column(Text, nullable=False)
    query_normalized: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_author_id: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False)
    aliases_json: Mapped[Optional[str]] = mapped_column(Text)
    institution_summary: Mapped[Optional[str]] = mapped_column(Text)
    affiliations_json: Mapped[Optional[str]] = mapped_column(Text)
    works_count: Mapped[Optional[int]] = mapped_column(Integer)
    citation_count: Mapped[Optional[int]] = mapped_column(Integer)
    sample_publications_json: Mapped[Optional[str]] = mapped_column(Text)
    topics_json: Mapped[Optional[str]] = mapped_column(Text)
    coauthor_summary_json: Mapped[Optional[str]] = mapped_column(Text)
    years_active_start: Mapped[Optional[int]] = mapped_column(Integer)
    years_active_end: Mapped[Optional[int]] = mapped_column(Integer)
    raw_payload_json: Mapped[Optional[str]] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    selected_by_resolutions: Mapped[list["AuthorResolution"]] = relationship(
        back_populates="selected_candidate", foreign_keys="AuthorResolution.selected_candidate_id"
    )
    evidence_rows: Mapped[list["AuthorResolutionEvidence"]] = relationship(
        back_populates="candidate"
    )
    publication_authorships: Mapped[list["PublicationAuthorship"]] = relationship(
        back_populates="author_candidate"
    )

    __table_args__ = (
        CheckConstraint(
            "years_active_start IS NULL OR years_active_end IS NULL OR years_active_start <= years_active_end",
            name="ck_author_candidates_year_range",
        ),
        Index("ix_author_candidates_query_expires", "query_normalized", "expires_at"),
        Index("ix_author_candidates_source_author", "source", "source_author_id"),
    )


class AuthorResolution(Base):
    """Persisted automatic, manual, or unresolved author identity decision."""
    __tablename__ = "author_resolutions"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid4())
    )
    query_original: Mapped[str] = mapped_column(Text, nullable=False)
    query_normalized: Mapped[str] = mapped_column(Text, nullable=False)
    institution_hint: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    selected_candidate_id: Mapped[Optional[str]] = mapped_column(
        Text, ForeignKey("author_candidates.id", ondelete="SET NULL")
    )
    author_id: Mapped[Optional[str]] = mapped_column(
        Text, ForeignKey("authors.id", ondelete="SET NULL")
    )
    top_score: Mapped[Optional[float]] = mapped_column(Float)
    second_score: Mapped[Optional[float]] = mapped_column(Float)
    dominance_ratio: Mapped[Optional[float]] = mapped_column(Float)
    score_margin: Mapped[Optional[float]] = mapped_column(Float)
    confidence_level: Mapped[Optional[str]] = mapped_column(Text)
    decision_reason: Mapped[Optional[str]] = mapped_column(Text)
    resolver_version: Mapped[str] = mapped_column(Text, nullable=False)
    scoring_version: Mapped[str] = mapped_column(Text, nullable=False)
    threshold_version: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    author: Mapped[Optional["Author"]] = relationship(back_populates="resolutions")
    selected_candidate: Mapped[Optional["AuthorCandidate"]] = relationship(
        back_populates="selected_by_resolutions",
        foreign_keys=[selected_candidate_id],
    )
    evidence_rows: Mapped[list["AuthorResolutionEvidence"]] = relationship(
        back_populates="resolution", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('auto_selected', 'manual_selected', 'manual_selection_required', 'unresolved', 'expired')",
            name="ck_author_resolutions_status",
        ),
        CheckConstraint(
            "top_score IS NULL OR (top_score >= 0.0 AND top_score <= 1.0)",
            name="ck_author_resolutions_top_score",
        ),
        CheckConstraint(
            "second_score IS NULL OR (second_score >= 0.0 AND second_score <= 1.0)",
            name="ck_author_resolutions_second_score",
        ),
        Index("ix_author_resolutions_query_status", "query_normalized", "status"),
        Index("ix_author_resolutions_author", "author_id"),
        Index("ix_author_resolutions_expires", "expires_at"),
    )


class AuthorResolutionEvidence(Base):
    """Signal-level score and provenance for each candidate in a resolution."""
    __tablename__ = "author_resolution_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resolution_id: Mapped[str] = mapped_column(
        Text, ForeignKey("author_resolutions.id", ondelete="CASCADE"), nullable=False
    )
    candidate_id: Mapped[str] = mapped_column(
        Text, ForeignKey("author_candidates.id", ondelete="CASCADE"), nullable=False
    )
    signal_name: Mapped[str] = mapped_column(Text, nullable=False)
    raw_value_json: Mapped[Optional[str]] = mapped_column(Text)
    normalized_score: Mapped[Optional[float]] = mapped_column(Float)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    weighted_contribution: Mapped[Optional[float]] = mapped_column(Float)
    availability: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    source_provenance_json: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    resolution: Mapped["AuthorResolution"] = relationship(back_populates="evidence_rows")
    candidate: Mapped["AuthorCandidate"] = relationship(back_populates="evidence_rows")

    __table_args__ = (
        UniqueConstraint(
            "resolution_id", "candidate_id", "signal_name", name="uq_author_resolution_evidence_signal"
        ),
        CheckConstraint(
            "normalized_score IS NULL OR (normalized_score >= 0.0 AND normalized_score <= 1.0)",
            name="ck_author_resolution_evidence_score",
        ),
        CheckConstraint(
            "weight IS NULL OR weight >= 0.0", name="ck_author_resolution_evidence_weight"
        ),
        CheckConstraint(
            "availability IN ('available', 'unavailable', 'not_applicable')",
            name="ck_author_resolution_evidence_availability",
        ),
        Index("ix_author_resolution_evidence_resolution_candidate", "resolution_id", "candidate_id"),
    )


class PublicationAuthorship(Base):
    """Per-source authorship provenance without changing publication deduplication."""
    __tablename__ = "publication_authorships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    publication_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("publications.id", ondelete="CASCADE"), nullable=False
    )
    source_record_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("source_records.id", ondelete="SET NULL")
    )
    author_id: Mapped[Optional[str]] = mapped_column(
        Text, ForeignKey("authors.id", ondelete="SET NULL")
    )
    author_candidate_id: Mapped[Optional[str]] = mapped_column(
        Text, ForeignKey("author_candidates.id", ondelete="SET NULL")
    )
    author_position: Mapped[int] = mapped_column(Integer, nullable=False)
    author_name_raw: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_author_name: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_author_id: Mapped[Optional[str]] = mapped_column(Text)
    identity_strength: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    provenance_json: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    author: Mapped[Optional["Author"]] = relationship(back_populates="publication_authorships")
    author_candidate: Mapped[Optional["AuthorCandidate"]] = relationship(
        back_populates="publication_authorships"
    )

    __table_args__ = (
        CheckConstraint(
            "identity_strength IN ('source_identified', 'linked', 'name_based', 'unresolved')",
            name="ck_publication_authorships_identity_strength",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)",
            name="ck_publication_authorships_confidence",
        ),
        UniqueConstraint(
            "publication_id", "source_record_id", "author_position", name="uq_publication_authorships_source_position"
        ),
        Index("ix_publication_authorships_author", "author_id"),
        Index("ix_publication_authorships_source_author", "source", "source_author_id"),
        Index("ix_publication_authorships_source_record", "source_record_id"),
    )



# ── Engine & session factory ─────────────────────────────────────

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        # The legacy tables retain their historical create_all behaviour.
        # Author-resolution tables are deliberately created by Alembic only.
        legacy_tables = [
            SourceRecord.__table__,
            Publication.__table__,
            DuplicateGroup.__table__,
            SimilarityLog.__table__,
            CacheEntry.__table__,
            ScholarCache.__table__,
            CircuitBreakerState.__table__,
        ]
        await conn.run_sync(Base.metadata.create_all, tables=legacy_tables)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
