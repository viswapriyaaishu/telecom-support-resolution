from unittest.mock import Mock

from app.db.models.conversation import Conversation
from app.db.repositories.conversation import ConversationRepository
from app.services.conversation import ConversationService


def test_get_or_create_returns_existing_conversation() -> None:
    repository = Mock(spec=ConversationRepository)
    existing = Conversation(
        external_id="existing-001",
        source_dataset="talkmap",
        dataset_version="test-v1",
        product="broadband",
    )

    repository.get_by_external_id.return_value = existing

    service = ConversationService(repository)

    result = service.get_or_create(
        external_id="existing-001",
        source_dataset="talkmap",
        dataset_version="test-v1",
        product="broadband",
    )

    assert result is existing
    repository.get_by_external_id.assert_called_once_with(
        source_dataset="talkmap",
        dataset_version="test-v1",
        external_id="existing-001",
    )
    repository.create.assert_not_called()


def test_get_or_create_creates_missing_conversation() -> None:
    repository = Mock(spec=ConversationRepository)
    repository.get_by_external_id.return_value = None

    created = Conversation(
        external_id="new-001",
        source_dataset="talkmap",
        dataset_version="test-v1",
        product="broadband",
    )
    repository.create.return_value = created

    service = ConversationService(repository)

    result = service.get_or_create(
        external_id="new-001",
        source_dataset="talkmap",
        dataset_version="test-v1",
        product="broadband",
    )

    assert result is created

    repository.get_by_external_id.assert_called_once_with(
        source_dataset="talkmap",
        dataset_version="test-v1",
        external_id="new-001",
    )

    repository.create.assert_called_once()

    created_argument = repository.create.call_args.args[0]

    assert created_argument.external_id == "new-001"
    assert created_argument.source_dataset == "talkmap"
    assert created_argument.dataset_version == "test-v1"
    assert created_argument.product == "broadband"