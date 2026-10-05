from datetime import UTC, datetime

from telecom_support_ingestion.chunk import chunk_conversation
from telecom_support_ingestion.models import Conversation, ConversationTurn


def test_chunk_conversation_splits_large_conversation() -> None:
    conversation = Conversation(
        conversation_id="conv-1",
        turns=[
            ConversationTurn(
                turn_index=0,
                speaker="CLIENT",
                date_time=datetime(2026, 1, 1, tzinfo=UTC),
                text="A" * 2000,
            ),
            ConversationTurn(
                turn_index=1,
                speaker="AGENT",
                date_time=datetime(2026, 1, 1, tzinfo=UTC),
                text="B" * 2000,
            ),
        ],
    )

    chunks = chunk_conversation(
        conversation,
        max_characters=2500,
        overlap_characters=200,
    )

    assert len(chunks) == 2
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1
    assert chunks[0].conversation_id == "conv-1"


def test_chunk_conversation_keeps_small_conversation_together() -> None:
    conversation = Conversation(
        conversation_id="conv-2",
        turns=[
            ConversationTurn(
                turn_index=0,
                speaker="CLIENT",
                date_time=datetime(2026, 1, 1, tzinfo=UTC),
                text="Internet is slow.",
            ),
            ConversationTurn(
                turn_index=1,
                speaker="AGENT",
                date_time=datetime(2026, 1, 1, tzinfo=UTC),
                text="Please restart the router.",
            ),
        ],
    )

    chunks = chunk_conversation(conversation)

    assert len(chunks) == 1
    assert "CLIENT: Internet is slow." in chunks[0].text
    assert "AGENT: Please restart the router." in chunks[0].text