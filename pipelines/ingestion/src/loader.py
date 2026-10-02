import csv
from collections import defaultdict
from pathlib import Path

from models import Conversation, ConversationTurn, TalkmapRow


def load_talkmap_rows(path: Path) -> list[TalkmapRow]:
    rows: list[TalkmapRow] = []

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for raw_row in reader:
            rows.append(TalkmapRow.model_validate(raw_row))

    return rows


def reconstruct_conversations(
    rows: list[TalkmapRow],
) -> list[Conversation]:
    grouped: dict[str, list[TalkmapRow]] = defaultdict(list)

    for row in rows:
        grouped[row.conversation_id].append(row)

    conversations: list[Conversation] = []

    for conversation_id, conversation_rows in grouped.items():
        ordered_rows = sorted(
            conversation_rows,
            key=lambda row: row.date_time,
        )

        turns = [
            ConversationTurn(
                turn_index=index,
                speaker=row.speaker,
                date_time=row.date_time,
                text=row.text,
            )
            for index, row in enumerate(ordered_rows)
        ]

        conversations.append(
            Conversation(
                conversation_id=conversation_id,
                turns=turns,
            )
        )

    return conversations