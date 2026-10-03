import csv
from collections.abc import Iterator
from pathlib import Path

from .models import Conversation, ConversationTurn, TalkmapRow


def load_talkmap_rows(path: Path) -> Iterator[TalkmapRow]:
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for raw_row in reader:
            yield TalkmapRow.model_validate(raw_row)


def iter_conversations(
    rows: Iterator[TalkmapRow],
) -> Iterator[Conversation]:
    current_conversation_id: str | None = None
    current_turns: list[ConversationTurn] = []

    for row in rows:
        if current_conversation_id is None:
            current_conversation_id = row.conversation_id

        if row.conversation_id != current_conversation_id:
            yield Conversation(
                conversation_id=current_conversation_id,
                turns=current_turns,
            )

            current_conversation_id = row.conversation_id
            current_turns = []

        current_turns.append(
            ConversationTurn(
                turn_index=len(current_turns),
                speaker=row.speaker,
                date_time=row.date_time,
                text=row.text,
            )
        )

    if current_conversation_id is not None:
        yield Conversation(
            conversation_id=current_conversation_id,
            turns=current_turns,
        )
