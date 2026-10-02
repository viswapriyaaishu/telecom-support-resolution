from datetime import UTC, datetime
from pathlib import Path

from loader import iter_conversations, load_talkmap_rows
from models import TalkmapRow


def test_iter_conversations_groups_contiguous_rows() -> None:
    rows = [
        TalkmapRow(
            conversation_id="conversation-1",
            speaker="agent",
            date_time=datetime(2023, 9, 9, 15, 8, 3, tzinfo=UTC),
            text="How can I help you?",
        ),
        TalkmapRow(
            conversation_id="conversation-1",
            speaker="client",
            date_time=datetime(2023, 9, 9, 15, 8, 10, tzinfo=UTC),
            text="I am having connection problems.",
        ),
        TalkmapRow(
            conversation_id="conversation-2",
            speaker="client",
            date_time=datetime(2023, 9, 9, 16, 0, tzinfo=UTC),
            text="My data is slow.",
        ),
    ]

    conversations = iter_conversations(iter(rows))

    first = next(conversations)

    assert first.conversation_id == "conversation-1"
    assert len(first.turns) == 2

    assert first.turns[0].speaker == "agent"
    assert first.turns[1].speaker == "client"

    assert first.turns[0].turn_index == 0
    assert first.turns[1].turn_index == 1

    second = next(conversations)

    assert second.conversation_id == "conversation-2"
    assert len(second.turns) == 1

    assert second.turns[0].speaker == "client"
    assert second.turns[0].turn_index == 0


def test_load_talkmap_rows_streams_validated_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "talkmap.csv"

    csv_path.write_text(
        "conversation_id,speaker,date_time,text\n"
        "conversation-1,agent,2023-09-09T15:08:03+00:00,"
        '"How can I help you?"\n'
        "conversation-1,client,2023-09-09T15:08:10+00:00,"
        '"My internet is slow."\n',
        encoding="utf-8",
    )

    rows = load_talkmap_rows(csv_path)

    assert not isinstance(rows, list)

    first = next(rows)

    assert first.conversation_id == "conversation-1"
    assert first.speaker == "agent"
    assert first.text == "How can I help you?"

    second = next(rows)

    assert second.speaker == "client"
    assert second.text == "My internet is slow."