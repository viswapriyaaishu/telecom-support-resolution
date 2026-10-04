from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from telecom_support_database.models.kb import KBDocument, KBChunk


@dataclass(frozen=True)
class KBRetrievalResult:
    chunk_id: UUID
    document_id: UUID
    document_key: str
    section: str
    text: str
    score: float


class KBRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def semantic_search(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 5,
    ) -> list[KBRetrievalResult]:
        if not query_embedding:
            raise ValueError("query_embedding cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        distance = KBChunk.embedding.cosine_distance(
            query_embedding
        )

        statement = (
            select(
                KBChunk.id,
                KBChunk.document_id,
                KBDocument.document_id.label("document_key"),
                KBChunk.section,
                KBChunk.text,
                distance.label("distance"),
            )
            .join(
                KBDocument,
                KBDocument.id == KBChunk.document_id,
            )
            .where(KBChunk.embedding.is_not(None))
            .order_by(distance)
            .limit(top_k)
        )

        rows = self.session.execute(statement).all()

        return [
            KBRetrievalResult(
                chunk_id=row.id,
                document_id=row.document_id,
                document_key=row.document_key,
                section=row.section,
                text=row.text,
                score=1.0 - float(row.distance),
            )
            for row in rows
        ]