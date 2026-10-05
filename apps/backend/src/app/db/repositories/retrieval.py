from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from telecom_support_database.models.chunk import ConversationChunk
from telecom_support_database.models.conversation import Conversation


@dataclass(frozen=True)
class RetrievalResult:
    chunk_id: UUID
    conversation_id: UUID
    text: str
    score: float


class RetrievalRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def semantic_search(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        if not query_embedding:
            raise ValueError("query_embedding cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        distance = ConversationChunk.embedding.cosine_distance(
            query_embedding
        )

        statement = (
            select(
                ConversationChunk.id,
                ConversationChunk.conversation_id,
                ConversationChunk.text,
                distance.label("distance"),
            )
            .join(
                Conversation,
                Conversation.id == ConversationChunk.conversation_id,
            )
            .where(
                ConversationChunk.embedding.is_not(None),
                Conversation.resolution_status == "RESOLVED",
            )
            .order_by(distance)
            .limit(top_k)
        )

        rows = self.session.execute(statement).all()

        return [
            RetrievalResult(
                chunk_id=row.id,
                conversation_id=row.conversation_id,
                text=row.text,
                score=1.0 - float(row.distance),
            )
            for row in rows
        ]
