from datetime import UTC, datetime
from unittest.mock import Mock

from app.db.models.conversation import Conversation, Speaker
from app.db.repositories.conversation import ConversationRepository
from app.services.conversation import (
    ConversationService,
    ConversationTurnInput,
)


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

def test_create_with_turns_builds_conversation_and_turns() -> None:
    repository = Mock(spec=ConversationRepository)
    repository.create.side_effect = lambda conversation: conversation

    service = ConversationService(repository)

    timestamp = datetime(2026, 10, 3, 10, 0, tzinfo=UTC)

    result = service.create_with_turns(
        external_id="conversation-001",
        source_dataset="talkmap",
        dataset_version="test-v1",
        product="broadband",
        turns=[
            ConversationTurnInput(
                turn_index=0,
                speaker=Speaker.CLIENT,
                timestamp=timestamp,
                text="My broadband keeps dropping.",
            ),
            ConversationTurnInput(
                turn_index=1,
                speaker=Speaker.AGENT,
                timestamp=timestamp,
                text="I will check the connection.",
            ),
        ],
    )

    repository.create.assert_called_once()

    created_conversation = repository.create.call_args.args[0]

    assert result is created_conversation
    assert created_conversation.external_id == "conversation-001"
    assert created_conversation.source_dataset == "talkmap"
    assert created_conversation.dataset_version == "test-v1"
    assert created_conversation.product == "broadband"

    assert len(created_conversation.turns) == 2

    assert created_conversation.turns[0].turn_index == 0
    assert created_conversation.turns[0].speaker == Speaker.CLIENT
    assert created_conversation.turns[0].text == "My broadband keeps dropping."

    assert created_conversation.turns[1].turn_index == 1
    assert created_conversation.turns[1].speaker == Speaker.AGENT
    assert created_conversation.turns[1].text == "I will check the connection."