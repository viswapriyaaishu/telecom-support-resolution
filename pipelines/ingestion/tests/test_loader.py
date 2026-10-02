from datetime import UTC, datetime

from loader import reconstruct_conversations
from models import TalkmapRow


def test_reconstruct_conversations_groups_and_sorts_turns() -> None:
    rows = [
        TalkmapRow(
            conversation_id="conversation-1",
            speaker="client",
            date_time=datetime(2023, 9, 9, 15, 8, 10, tzinfo=UTC),
            text="I am having connection problems.",
        ),
        TalkmapRow(
            conversation_id="conversation-1",
            speaker="agent",
            date_time=datetime(2023, 9, 9, 15, 8, 3, tzinfo=UTC),
            text="How can I help you?",
        ),
        TalkmapRow(
            conversation_id="conversation-2",
            speaker="client",
            date_time=datetime(2023, 9, 9, 16, 0, tzinfo=UTC),
            text="My data is slow.",
        ),
    ]

    conversations = reconstruct_conversations(rows)

    assert len(conversations) == 2

    first = conversations[0]

    assert first.conversation_id == "conversation-1"
    assert len(first.turns) == 2

    assert first.turns[0].speaker == "agent"
    assert first.turns[1].speaker == "client"

    assert first.turns[0].turn_index == 0
    assert first.turns[1].turn_index == 1
