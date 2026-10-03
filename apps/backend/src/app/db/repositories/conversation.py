from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.conversation import Conversation


class ConversationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        statement = select(Conversation).where(
            Conversation.id == conversation_id
        )
        return self.session.scalar(statement)

    def get_by_external_id(
        self,
        source_dataset: str,
        dataset_version: str,
        external_id: str,
    ) -> Conversation | None:
        statement = select(Conversation).where(
            Conversation.source_dataset == source_dataset,
            Conversation.dataset_version == dataset_version,
            Conversation.external_id == external_id,
        )
        return self.session.scalar(statement)

    def create(self, conversation: Conversation) -> Conversation:
        self.session.add(conversation)
        self.session.flush()
        return conversation