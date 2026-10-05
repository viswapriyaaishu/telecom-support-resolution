"""add conversation chunks fts gin index

Revision ID: 758e73172ba8
Revises: a9279e7aa50b
Create Date: 2026-10-04
"""

from collections.abc import Sequence

from alembic import op

revision: str = "758e73172ba8"
down_revision: str | None = "a9279e7aa50b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_conversation_chunks_text_fts_gin
        ON conversation_chunks
        USING gin (to_tsvector('english', text))
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_conversation_chunks_text_fts_gin
        """
    )