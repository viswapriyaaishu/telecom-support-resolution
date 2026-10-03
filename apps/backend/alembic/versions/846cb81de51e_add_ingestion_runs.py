"""add ingestion runs

Revision ID: 846cb81de51e
Revises: 836d8c8028d8
Create Date: 2026-10-03 19:36:55.757041

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "846cb81de51e"
down_revision: str | Sequence[str] | None = "836d8c8028d8"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create the ingestion runs table."""
    ingestion_run_status = sa.Enum(
        "RUNNING",
        "COMPLETED",
        "FAILED",
        name="ingestion_run_status",
    )
    ingestion_run_status.create(op.get_bind(), checkfirst=True)

    ingestion_run_status_column = sa.Enum(
        "RUNNING",
        "COMPLETED",
        "FAILED",
        name="ingestion_run_status",
        create_type=False,
    )

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("dataset_name", sa.String(length=100), nullable=False),
        sa.Column("dataset_version", sa.String(length=100), nullable=False),
        sa.Column("pipeline_version", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            ingestion_run_status_column,
            server_default="RUNNING",
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "records_read",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "records_valid",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "records_rejected",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "records_redacted",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "records_deduplicated",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop the ingestion runs table and its enum type."""
    op.drop_table("ingestion_runs")

    ingestion_run_status = sa.Enum(
        "RUNNING",
        "COMPLETED",
        "FAILED",
        name="ingestion_run_status",
    )
    ingestion_run_status.drop(op.get_bind(), checkfirst=True)