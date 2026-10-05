"""make conversation chunks unique

Revision ID: c3877fc121ae
Revises: c428420bc910
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c3877fc121ae"
down_revision: str | Sequence[str] | None = "c428420bc910"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_conversation_chunks_conversation_index",
        "conversation_chunks",
        ["conversation_id", "chunk_index"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_conversation_chunks_conversation_index",
        "conversation_chunks",
        type_="unique",
    )