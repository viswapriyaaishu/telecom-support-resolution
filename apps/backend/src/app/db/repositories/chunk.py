from collections.abc import Iterator
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload
from telecom_support_database.models.chunk import ConversationChunk
from telecom_support_database.models.conversation import Conversation


class ChunkRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def stream_conversations(
        self,
        *,
        source_dataset: str,
        dataset_version: str,
        batch_size: int = 100,
    ) -> Iterator[list[Conversation]]:
        statement = (
            select(Conversation)
            .where(
                Conversation.source_dataset == source_dataset,
                Conversation.dataset_version == dataset_version,
            )
            .options(selectinload(Conversation.turns))
            .order_by(Conversation.id)
        )

        result = self.session.execute(statement)

        batch: list[Conversation] = []

        for conversation in result.scalars().yield_per(batch_size):
            batch.append(conversation)

            if len(batch) >= batch_size:
                yield batch
                batch = []

        if batch:
            yield batch

    def create_many(
        self,
        chunks: list[ConversationChunk],
    ) -> None:
        if not chunks:
            return

        values = [
            {
                "id": chunk.id or uuid4(),
                "conversation_id": chunk.conversation_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
            }
            for chunk in chunks
        ]

        statement = insert(ConversationChunk).values(values)

        statement = statement.on_conflict_do_nothing(
            constraint="uq_conversation_chunks_conversation_index",
        )

        self.session.execute(statement)