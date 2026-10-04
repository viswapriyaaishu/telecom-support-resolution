import re
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from telecom_support_database.models.chunk import ConversationChunk


@dataclass(frozen=True)
class FTSResult:
    chunk_id: UUID
    conversation_id: UUID
    text: str
    score: float


class FTSRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def search(
        self,
        query: str,
        *,
        top_k: int = 10,
    ) -> list[FTSResult]:
        query = query.strip()

        if not query:
            raise ValueError("query cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        search_vector = func.to_tsvector(
            "english",
            ConversationChunk.text,
        )

        terms = re.findall(r"[A-Za-z0-9]+", query)

        if not terms:
            return []

        search_query_text = " OR ".join(terms)

        search_query = func.websearch_to_tsquery(
            "english",
            search_query_text,
        )

        rank = func.ts_rank_cd(
            search_vector,
            search_query,
        )

        statement = (
            select(
                ConversationChunk.id,
                ConversationChunk.conversation_id,
                ConversationChunk.text,
                rank.label("rank"),
            )
            .where(
                search_vector.op("@@")(search_query),
            )
            .order_by(rank.desc())
            .limit(top_k)
        )

        rows = self.session.execute(statement).all()

        return [
            FTSResult(
                chunk_id=row.id,
                conversation_id=row.conversation_id,
                text=row.text,
                score=float(row.rank),
            )
            for row in rows
        ]