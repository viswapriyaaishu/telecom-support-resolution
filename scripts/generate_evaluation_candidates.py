import json
import random
from pathlib import Path

from app.db.session import SessionLocal
from sqlalchemy import select
from telecom_support_database.models.chunk import ConversationChunk
from telecom_support_database.models.conversation import Conversation

OUTPUT = Path("data/evaluation/resolved_candidates.json")
SAMPLE_SIZE = 50
RANDOM_SEED = 42


def main() -> None:
    random.seed(RANDOM_SEED)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as session:
        conversations = session.execute(
            select(
                Conversation.id,
                Conversation.external_id,
            )
            .where(Conversation.resolution_status == "RESOLVED")
        ).all()

        selected = random.sample(
            conversations,
            min(SAMPLE_SIZE, len(conversations)),
        )

        conversation_ids = [row.id for row in selected]

        chunks = session.execute(
            select(
                ConversationChunk.conversation_id,
                ConversationChunk.chunk_index,
                ConversationChunk.text,
            )
            .where(
                ConversationChunk.conversation_id.in_(conversation_ids)
            )
            .order_by(
                ConversationChunk.conversation_id,
                ConversationChunk.chunk_index,
            )
        ).all()

        grouped: dict = {}

        for conversation_id, chunk_index, text in chunks:
            grouped.setdefault(conversation_id, []).append(
                (chunk_index, text)
            )

        results = []

        for conversation_id, external_id in selected:
            conversation_chunks = grouped.get(conversation_id, [])

            full_text = "\n".join(
                text for _, text in conversation_chunks
            )

            results.append(
                {
                    "conversation_id": str(conversation_id),
                    "external_id": external_id,
                    "text_preview": " ".join(full_text.split())[:700],
                }
            )

    results.sort(key=lambda item: item["external_id"])

    OUTPUT.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Generated {len(results)} evaluation candidates.")
    print(f"Saved to: {OUTPUT}")


if __name__ == "__main__":
    main()
