from collections.abc import Iterator

from sqlalchemy import select
from sqlalchemy.orm import Session
from telecom_support_database.models.chunk import ConversationChunk


class EmbeddingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def stream_unembedded_chunks(
        self,
        *,
        batch_size: int = 100,
    ) -> Iterator[list[ConversationChunk]]:
        statement = (
            select(ConversationChunk)
            .where(ConversationChunk.embedding.is_(None))
            .order_by(ConversationChunk.id)
        )

        result = self.session.execute(statement)

        batch: list[ConversationChunk] = []

        for chunk in result.scalars().yield_per(batch_size):
            batch.append(chunk)

            if len(batch) >= batch_size:
                yield batch
                batch = []

        if batch:
            yield batch

    def update_embeddings(
        self,
        chunks: list[ConversationChunk],
        embeddings: list[list[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have the same length.")

        for chunk, embedding in zip(chunks, embeddings, strict=True):
            chunk.embedding = embedding
