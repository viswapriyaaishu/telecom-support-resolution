import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models.conversation import Conversation
from app.db.repositories.conversation import ConversationRepository


def test_create_and_get_conversation(db_session) -> None:
    repository = ConversationRepository(db_session)

    conversation = Conversation(
        external_id="test-conversation-001",
        source_dataset="talkmap",
        dataset_version="test-v1",
        product="broadband",
    )

    created = repository.create(conversation)

    assert created.id is not None

    db_session.flush()

    fetched = repository.get_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.external_id == "test-conversation-001"
    assert fetched.product == "broadband"


def test_get_by_external_id(db_session) -> None:
    repository = ConversationRepository(db_session)

    conversation = Conversation(
        external_id="test-conversation-002",
        source_dataset="talkmap",
        dataset_version="test-v1",
    )

    repository.create(conversation)
    db_session.flush()

    fetched = repository.get_by_external_id(
        source_dataset="talkmap",
        dataset_version="test-v1",
        external_id="test-conversation-002",
    )

    assert fetched is not None
    assert fetched.id == conversation.id

def test_duplicate_external_id_is_rejected(db_session) -> None:
    repository = ConversationRepository(db_session)

    first = Conversation(
        external_id="duplicate-001",
        source_dataset="talkmap",
        dataset_version="test-v1",
    )

    second = Conversation(
        external_id="duplicate-001",
        source_dataset="talkmap",
        dataset_version="test-v1",
    )

    repository.create(first)

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            repository.create(second)
