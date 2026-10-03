"""enable pgvector extension

Revision ID: 31a3f4afe9e4
Revises:
Create Date: 2026-10-03 12:37:15.671132

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "31a3f4afe9e4"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enable the pgvector PostgreSQL extension."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Disable the pgvector PostgreSQL extension."""
    op.execute("DROP EXTENSION IF EXISTS vector")