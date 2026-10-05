import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from telecom_support_database.base import Base


class ResolutionLog(Base):
    __tablename__ = "resolution_logs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    complaint: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    intent: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    sub_intent: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    product: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    sentiment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    retrieval_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    authoritative_evidence_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    grounded: Mapped[bool] = mapped_column(
        nullable=False,
    )

    unsupported_steps: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    resolution_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    resolution_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    latency_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    error_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )