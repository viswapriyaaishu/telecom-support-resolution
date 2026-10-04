import re
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from telecom_support_database.models.kb import KBDocument, KBChunk


@dataclass(frozen=True)
class KBFTSResult:
    chunk_id: UUID
    document_id: UUID
    document_key: str
    section: str
    text: str
    score: float


class KBFTSRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def search(
        self,
        query: str,
        *,
        top_k: int = 10,
    ) -> list[KBFTSResult]:
        query = query.strip()

        if not query:
            raise ValueError("query cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        search_vector = func.to_tsvector(
            "english",
            KBChunk.text,
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
                KBChunk.id,
                KBChunk.document_id,
                KBDocument.document_id.label("document_key"),
                KBChunk.section,
                KBChunk.text,
                rank.label("rank"),
            )
            .join(
                KBDocument,
                KBDocument.id == KBChunk.document_id,
            )
            .where(
                search_vector.op("@@")(search_query),
            )
            .order_by(rank.desc())
            .limit(top_k)
        )

        rows = self.session.execute(statement).all()

        return [
            KBFTSResult(
                chunk_id=row.id,
                document_id=row.document_id,
                document_key=row.document_key,
                section=row.section,
                text=row.text,
                score=float(row.rank),
            )
            for row in rows
        ]