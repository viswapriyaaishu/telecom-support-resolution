from dataclasses import dataclass
from datetime import datetime

from telecom_support_database.models.conversation import (
    Conversation,
    ConversationTurn,
    QualityStatus,
    ResolutionStatus,
    Speaker,
)

from app.db.repositories.conversation import ConversationRepository


@dataclass(frozen=True)
class ConversationTurnInput:
    turn_index: int
    speaker: Speaker
    timestamp: datetime
    text: str


class ConversationService:
    def __init__(self, repository: ConversationRepository) -> None:
        self.repository = repository

    def get_or_create(
        self,
        *,
        external_id: str,
        source_dataset: str,
        dataset_version: str,
        product: str | None = None,
    ) -> Conversation:
        existing = self.repository.get_by_external_id(
            source_dataset=source_dataset,
            dataset_version=dataset_version,
            external_id=external_id,
        )

        if existing is not None:
            return existing

        conversation = Conversation(
            external_id=external_id,
            source_dataset=source_dataset,
            dataset_version=dataset_version,
            product=product,
        )

        return self.repository.create(conversation)

    def create_with_turns(
        self,
        *,
        external_id: str,
        source_dataset: str,
        dataset_version: str,
        turns: list[ConversationTurnInput],
        product: str | None = None,
        quality_status: QualityStatus = QualityStatus.REVIEW,
        resolution_status: ResolutionStatus = ResolutionStatus.UNKNOWN,
    ) -> Conversation:
        conversation = Conversation(
            external_id=external_id,
            source_dataset=source_dataset,
            dataset_version=dataset_version,
            product=product,
            quality_status=quality_status,
            resolution_status=resolution_status,
        )

        conversation.turns = [
            ConversationTurn(
                turn_index=turn.turn_index,
                speaker=turn.speaker,
                timestamp=turn.timestamp,
                text=turn.text,
            )
            for turn in turns
        ]

        return self.repository.create(conversation)