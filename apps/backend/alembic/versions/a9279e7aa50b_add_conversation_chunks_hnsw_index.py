"""add conversation chunks hnsw index

Revision ID: a9279e7aa50b
Revises: 001460d0a331
Create Date: 2026-10-04
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a9279e7aa50b"
down_revision: str | None = "001460d0a331"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_conversation_chunks_embedding_hnsw
        ON conversation_chunks
        USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_conversation_chunks_embedding_hnsw
        """
    )