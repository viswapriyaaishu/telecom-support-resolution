from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from telecom_support_database.base import Base


class ResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    UNRESOLVED = "UNRESOLVED"
    UNKNOWN = "UNKNOWN"


class QualityStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    INCOMPLETE = "INCOMPLETE"
    DUPLICATE = "DUPLICATE"
    LOW_QUALITY = "LOW_QUALITY"
    SENSITIVE = "SENSITIVE"
    REVIEW = "REVIEW"


class Speaker(StrEnum):
    CLIENT = "CLIENT"
    AGENT = "AGENT"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    product: Mapped[str | None] = mapped_column(String(100))
    intent: Mapped[str | None] = mapped_column(String(100))
    sub_intent: Mapped[str | None] = mapped_column(String(100))
    sentiment: Mapped[str | None] = mapped_column(String(50))
    severity: Mapped[str | None] = mapped_column(String(50))

    resolution_status: Mapped[ResolutionStatus] = mapped_column(
        Enum(ResolutionStatus, name="resolution_status"),
        nullable=False,
        default=ResolutionStatus.UNKNOWN,
        server_default=ResolutionStatus.UNKNOWN.value,
    )

    quality_status: Mapped[QualityStatus] = mapped_column(
        Enum(QualityStatus, name="quality_status"),
        nullable=False,
        default=QualityStatus.REVIEW,
        server_default=QualityStatus.REVIEW.value,
    )

    source_dataset: Mapped[str] = mapped_column(String(100), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    turns: Mapped[list["ConversationTurn"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationTurn.turn_index",
    )

    __table_args__ = (
        UniqueConstraint(
            "source_dataset",
            "dataset_version",
            "external_id",
            name="uq_conversations_source_version_external",
        ),
        Index("ix_conversations_intent", "intent"),
        Index("ix_conversations_product", "product"),
        Index("ix_conversations_resolution_status", "resolution_status"),
    )


class ConversationTurn(Base):
    __tablename__ = "conversation_turns"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    conversation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )

    turn_index: Mapped[int] = mapped_column(nullable=False)

    speaker: Mapped[Speaker] = mapped_column(
        Enum(Speaker, name="speaker"),
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    conversation: Mapped[Conversation] = relationship(
        back_populates="turns",
    )

    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "turn_index",
            name="uq_conversation_turns_conversation_index",
        ),
        Index("ix_conversation_turns_conversation_id", "conversation_id"),
    )
