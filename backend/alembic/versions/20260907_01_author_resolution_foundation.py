"""Add the author-resolution foundation tables.

This migration is additive.  It deliberately does not alter the legacy
publication, source-record, cache, or deduplication tables.  Run it only after
backing up and explicitly selecting the intended SQLite database file.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260907_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "authors",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.Column("resolution_state", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "resolution_state IN ('resolved', 'provisional', 'unresolved')",
            name="ck_authors_resolution_state",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_authors_normalized_name", "authors", ["normalized_name"])

    op.create_table(
        "author_candidates",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("query_original", sa.Text(), nullable=False),
        sa.Column("query_normalized", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_author_id", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.Column("aliases_json", sa.Text()),
        sa.Column("institution_summary", sa.Text()),
        sa.Column("affiliations_json", sa.Text()),
        sa.Column("works_count", sa.Integer()),
        sa.Column("citation_count", sa.Integer()),
        sa.Column("sample_publications_json", sa.Text()),
        sa.Column("topics_json", sa.Text()),
        sa.Column("coauthor_summary_json", sa.Text()),
        sa.Column("years_active_start", sa.Integer()),
        sa.Column("years_active_end", sa.Integer()),
        sa.Column("raw_payload_json", sa.Text()),
        sa.Column("retrieved_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime()),
        sa.CheckConstraint(
            "years_active_start IS NULL OR years_active_end IS NULL OR years_active_start <= years_active_end",
            name="ck_author_candidates_year_range",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_author_candidates_query_expires", "author_candidates", ["query_normalized", "expires_at"]
    )
    op.create_index(
        "ix_author_candidates_source_author", "author_candidates", ["source", "source_author_id"]
    )

    op.create_table(
        "author_external_ids",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("author_id", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("external_id", sa.Text(), nullable=False),
        sa.Column("external_url", sa.Text()),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("verified_at", sa.DateTime()),
        sa.Column("provenance_json", sa.Text()),
        sa.CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_author_external_ids_confidence"),
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "external_id", name="uq_author_external_ids_source_id"),
    )
    op.create_index(
        "ix_author_external_ids_author_source", "author_external_ids", ["author_id", "source"]
    )

    op.create_table(
        "author_aliases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("author_id", sa.Text(), nullable=False),
        sa.Column("alias", sa.Text(), nullable=False),
        sa.Column("normalized_alias", sa.Text(), nullable=False),
        sa.Column("alias_type", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_author_aliases_confidence"),
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "author_id", "normalized_alias", "source", name="uq_author_aliases_author_alias_source"
        ),
    )
    op.create_index("ix_author_aliases_normalized_alias", "author_aliases", ["normalized_alias"])

    op.create_table(
        "author_affiliations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("author_id", sa.Text(), nullable=False),
        sa.Column("institution_name", sa.Text(), nullable=False),
        sa.Column("normalized_institution", sa.Text(), nullable=False),
        sa.Column("institution_external_id", sa.Text()),
        sa.Column("department", sa.Text()),
        sa.Column("country_code", sa.Text()),
        sa.Column("start_year", sa.Integer()),
        sa.Column("end_year", sa.Integer()),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_record_ref", sa.Text()),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_author_affiliations_confidence"),
        sa.CheckConstraint(
            "start_year IS NULL OR end_year IS NULL OR start_year <= end_year",
            name="ck_author_affiliations_year_range",
        ),
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_author_affiliations_author", "author_affiliations", ["author_id"])
    op.create_index(
        "ix_author_affiliations_institution_country",
        "author_affiliations",
        ["normalized_institution", "country_code"],
    )

    op.create_table(
        "author_resolutions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("query_original", sa.Text(), nullable=False),
        sa.Column("query_normalized", sa.Text(), nullable=False),
        sa.Column("institution_hint", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("selected_candidate_id", sa.Text()),
        sa.Column("author_id", sa.Text()),
        sa.Column("top_score", sa.Float()),
        sa.Column("second_score", sa.Float()),
        sa.Column("dominance_ratio", sa.Float()),
        sa.Column("score_margin", sa.Float()),
        sa.Column("confidence_level", sa.Text()),
        sa.Column("decision_reason", sa.Text()),
        sa.Column("resolver_version", sa.Text(), nullable=False),
        sa.Column("scoring_version", sa.Text(), nullable=False),
        sa.Column("threshold_version", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime()),
        sa.Column("expires_at", sa.DateTime()),
        sa.CheckConstraint(
            "status IN ('auto_selected', 'manual_selected', 'manual_selection_required', 'unresolved', 'expired')",
            name="ck_author_resolutions_status",
        ),
        sa.CheckConstraint(
            "top_score IS NULL OR (top_score >= 0.0 AND top_score <= 1.0)",
            name="ck_author_resolutions_top_score",
        ),
        sa.CheckConstraint(
            "second_score IS NULL OR (second_score >= 0.0 AND second_score <= 1.0)",
            name="ck_author_resolutions_second_score",
        ),
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["selected_candidate_id"], ["author_candidates.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_author_resolutions_query_status", "author_resolutions", ["query_normalized", "status"]
    )
    op.create_index("ix_author_resolutions_author", "author_resolutions", ["author_id"])
    op.create_index("ix_author_resolutions_expires", "author_resolutions", ["expires_at"])

    op.create_table(
        "author_resolution_evidence",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resolution_id", sa.Text(), nullable=False),
        sa.Column("candidate_id", sa.Text(), nullable=False),
        sa.Column("signal_name", sa.Text(), nullable=False),
        sa.Column("raw_value_json", sa.Text()),
        sa.Column("normalized_score", sa.Float()),
        sa.Column("weight", sa.Float()),
        sa.Column("weighted_contribution", sa.Float()),
        sa.Column("availability", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("source_provenance_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "normalized_score IS NULL OR (normalized_score >= 0.0 AND normalized_score <= 1.0)",
            name="ck_author_resolution_evidence_score",
        ),
        sa.CheckConstraint("weight IS NULL OR weight >= 0.0", name="ck_author_resolution_evidence_weight"),
        sa.CheckConstraint(
            "availability IN ('available', 'unavailable', 'not_applicable')",
            name="ck_author_resolution_evidence_availability",
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["author_candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolution_id"], ["author_resolutions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "resolution_id", "candidate_id", "signal_name", name="uq_author_resolution_evidence_signal"
        ),
    )
    op.create_index(
        "ix_author_resolution_evidence_resolution_candidate",
        "author_resolution_evidence",
        ["resolution_id", "candidate_id"],
    )

    op.create_table(
        "publication_authorships",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("publication_id", sa.Integer(), nullable=False),
        sa.Column("source_record_id", sa.Integer()),
        sa.Column("author_id", sa.Text()),
        sa.Column("author_candidate_id", sa.Text()),
        sa.Column("author_position", sa.Integer(), nullable=False),
        sa.Column("author_name_raw", sa.Text(), nullable=False),
        sa.Column("normalized_author_name", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_author_id", sa.Text()),
        sa.Column("identity_strength", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("provenance_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "identity_strength IN ('source_identified', 'linked', 'name_based', 'unresolved')",
            name="ck_publication_authorships_identity_strength",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)",
            name="ck_publication_authorships_confidence",
        ),
        sa.ForeignKeyConstraint(["author_candidate_id"], ["author_candidates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["publication_id"], ["publications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_record_id"], ["source_records.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "publication_id", "source_record_id", "author_position",
            name="uq_publication_authorships_source_position",
        ),
    )
    op.create_index("ix_publication_authorships_author", "publication_authorships", ["author_id"])
    op.create_index(
        "ix_publication_authorships_source_author", "publication_authorships", ["source", "source_author_id"]
    )
    op.create_index(
        "ix_publication_authorships_source_record", "publication_authorships", ["source_record_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_publication_authorships_source_record", table_name="publication_authorships")
    op.drop_index("ix_publication_authorships_source_author", table_name="publication_authorships")
    op.drop_index("ix_publication_authorships_author", table_name="publication_authorships")
    op.drop_table("publication_authorships")
    op.drop_index(
        "ix_author_resolution_evidence_resolution_candidate", table_name="author_resolution_evidence"
    )
    op.drop_table("author_resolution_evidence")
    op.drop_index("ix_author_resolutions_expires", table_name="author_resolutions")
    op.drop_index("ix_author_resolutions_author", table_name="author_resolutions")
    op.drop_index("ix_author_resolutions_query_status", table_name="author_resolutions")
    op.drop_table("author_resolutions")
    op.drop_index("ix_author_affiliations_institution_country", table_name="author_affiliations")
    op.drop_index("ix_author_affiliations_author", table_name="author_affiliations")
    op.drop_table("author_affiliations")
    op.drop_index("ix_author_aliases_normalized_alias", table_name="author_aliases")
    op.drop_table("author_aliases")
    op.drop_index("ix_author_external_ids_author_source", table_name="author_external_ids")
    op.drop_table("author_external_ids")
    op.drop_index("ix_author_candidates_source_author", table_name="author_candidates")
    op.drop_index("ix_author_candidates_query_expires", table_name="author_candidates")
    op.drop_table("author_candidates")
    op.drop_index("ix_authors_normalized_name", table_name="authors")
    op.drop_table("authors")