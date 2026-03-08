"""Verify that all ORM model changes have a corresponding Alembic migration."""

from pathlib import Path
from unittest.mock import patch

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

import sharetree.models.all  # noqa: F401 — registers all models on Base.metadata
from sharetree.db import Base

_ALEMBIC_INI = Path(__file__).parents[3] / "alembic.ini"


def test_no_missing_migrations(tmp_path: Path) -> None:
    """Fail if any ORM model change is not captured in a migration file."""
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    temp_engine = create_engine(db_url)

    # migrations/env.py uses sharetree.db.engine directly; redirect it to our temp DB.
    with patch("sharetree.db.engine", temp_engine):
        alembic_cfg = Config(str(_ALEMBIC_INI))
        command.upgrade(alembic_cfg, "head")

        with temp_engine.connect() as conn:
            ctx = MigrationContext.configure(conn)
            diff = compare_metadata(ctx, Base.metadata)

    assert not diff, (
        f"Found {len(diff)} pending migration(s) — run `make migration msg=...` to generate:\n"
        + "\n".join(str(d) for d in diff)
    )
