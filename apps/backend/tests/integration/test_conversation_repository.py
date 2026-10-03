from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from telecom_support_database.models.conversation import Conversation, Speaker

from app.db.repositories.conversation import ConversationRepository
from app.services.conversation import (
    ConversationService,
    ConversationTurnInput,
)


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


def test_create_conversation_with_turns_persists_relationship(
    db_session,
) -> None:
    repository = ConversationRepository(db_session)
    service = ConversationService(repository)

    timestamp = datetime(2026, 10, 3, 10, 0, tzinfo=UTC)

    conversation = service.create_with_turns(
        external_id="conversation-with-turns-001",
        source_dataset="talkmap",
        dataset_version="test-v1",
        product="broadband",
        turns=[
            ConversationTurnInput(
                turn_index=0,
                speaker=Speaker.CLIENT,
                timestamp=timestamp,
                text="My broadband keeps dropping every evening.",
            ),
            ConversationTurnInput(
                turn_index=1,
                speaker=Speaker.AGENT,
                timestamp=timestamp,
                text="I will check the connection.",
            ),
        ],
    )

    db_session.flush()
    db_session.expire_all()

    persisted = repository.get_by_id(conversation.id)

    assert persisted is not None
    assert persisted.external_id == "conversation-with-turns-001"
    assert persisted.product == "broadband"

    assert len(persisted.turns) == 2

    assert persisted.turns[0].turn_index == 0
    assert persisted.turns[0].speaker == Speaker.CLIENT
    assert persisted.turns[0].text == (
        "My broadband keeps dropping every evening."
    )

    assert persisted.turns[1].turn_index == 1
    assert persisted.turns[1].speaker == Speaker.AGENT
    assert persisted.turns[1].text == "I will check the connection."

def test_create_with_duplicate_turn_index_rolls_back_conversation(
    db_session,
) -> None:
    repository = ConversationRepository(db_session)
    service = ConversationService(repository)

    timestamp = datetime(2026, 10, 3, 10, 0, tzinfo=UTC)

    with pytest.raises(IntegrityError):
        with db_session.begin():
            service.create_with_turns(
                external_id="conversation-atomicity-001",
                source_dataset="talkmap",
                dataset_version="test-v1",
                turns=[
                    ConversationTurnInput(
                        turn_index=0,
                        speaker=Speaker.CLIENT,
                        timestamp=timestamp,
                        text="My broadband keeps dropping.",
                    ),
                    ConversationTurnInput(
                        turn_index=0,
                        speaker=Speaker.AGENT,
                        timestamp=timestamp,
                        text="I will investigate.",
                    ),
                ],
            )

    persisted = repository.get_by_external_id(
        source_dataset="talkmap",
        dataset_version="test-v1",
        external_id="conversation-atomicity-001",
    )

    assert persisted is None
