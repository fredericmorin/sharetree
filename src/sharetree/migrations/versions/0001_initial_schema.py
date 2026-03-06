"""initial schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-03-06

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "access_codes",
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("patterns", sa.String(), nullable=False),
        sa.Column("nick", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("code"),
    )


def downgrade() -> None:
    op.drop_table("access_codes")
