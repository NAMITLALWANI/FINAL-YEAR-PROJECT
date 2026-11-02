from pathlib import Path

import pytest


def test_author_resolution_migration_is_available():
    """The actual upgrade is exercised only in an isolated database once Alembic is installed."""
    pytest.importorskip("alembic")
    migration = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "20260907_01_author_resolution_foundation.py"
    )
    assert migration.exists()
    assert "op.create_table" in migration.read_text()