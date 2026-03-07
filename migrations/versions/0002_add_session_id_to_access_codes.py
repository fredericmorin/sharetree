"""add session_id to access_codes

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-03-07

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a1"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("access_codes", sa.Column("session_id", sa.String(), nullable=True))
    op.create_index("ix_access_codes_session_id", "access_codes", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_access_codes_session_id", "access_codes")
    op.drop_column("access_codes", "session_id")
