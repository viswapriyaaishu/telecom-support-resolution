from app.db.models.conversation import Conversation
from app.db.repositories.conversation import ConversationRepository


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