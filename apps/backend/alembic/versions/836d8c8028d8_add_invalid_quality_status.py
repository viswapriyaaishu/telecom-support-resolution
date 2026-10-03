"""add invalid quality status

Revision ID: 836d8c8028d8
Revises: c09dc44bcbe6
Create Date: 2026-10-03 15:00:04.816837

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "836d8c8028d8"
down_revision: str | Sequence[str] | None = "c09dc44bcbe6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add INVALID to the quality_status PostgreSQL enum."""
    op.execute(
        "ALTER TYPE quality_status ADD VALUE IF NOT EXISTS 'INVALID'"
    )


def downgrade() -> None:
    """PostgreSQL does not support removing an enum value directly."""
    raise NotImplementedError(
        "PostgreSQL does not support removing enum values directly."
    )