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

    def _search_terms(
        self,
        terms: list[str],
        *,
        top_k: int,
    ) -> list[FTSResult]:
        if not terms:
            return []

        search_vector = func.to_tsvector(
            "english",
            ConversationChunk.text,
        )

        search_query = func.websearch_to_tsquery(
            "english",
            " ".join(terms),
        )

        rank = func.ts_rank(
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

        terms = re.findall(r"[A-Za-z0-9]+", query.lower())

        if not terms:
            return []

        stopwords = {
            "a",
            "an",
            "and",
            "are",
            "been",
            "does",
            "every",
            "for",
            "has",
            "have",
            "i",
            "in",
            "is",
            "it",
            "my",
            "not",
            "of",
            "on",
            "or",
            "the",
            "this",
            "to",
            "twice",
            "with",
        }

        meaningful_terms = [
            term
            for term in terms
            if term not in stopwords
        ]

        if not meaningful_terms:
            return []

        search_attempts: list[list[str]] = []

        if len(meaningful_terms) >= 3:
            search_attempts.append(
                [
                    meaningful_terms[0],
                    meaningful_terms[-2],
                    meaningful_terms[-1],
                ]
            )

        if len(meaningful_terms) >= 2:
            search_attempts.append(
                [
                    meaningful_terms[0],
                    meaningful_terms[-1],
                ]
            )

        if len(meaningful_terms) == 1:
            search_attempts.append(meaningful_terms)

        seen: set[tuple[str, ...]] = set()

        for attempt in search_attempts:
            key = tuple(attempt)

            if key in seen:
                continue

            seen.add(key)

            results = self._search_terms(
                attempt,
                top_k=top_k,
            )

            if results:
                return results

        return []