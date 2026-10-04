from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.repositories.kb import KBRepository
from app.db.repositories.kb_fts import KBFTSRepository


@dataclass(frozen=True)
class KBHybridRetrievalResult:
    chunk_id: UUID
    document_id: UUID
    document_key: str
    section: str
    text: str
    semantic_score: float | None
    fts_score: float | None
    rrf_score: float


class KBHybridRetrievalService:
    def __init__(self, session: Session) -> None:
        self.semantic_repository = KBRepository(session)
        self.fts_repository = KBFTSRepository(session)

    def search(
        self,
        query: str,
        query_embedding: list[float],
        *,
        top_k: int = 5,
        candidate_k: int = 5,
        rrf_k: int = 60,
    ) -> list[KBHybridRetrievalResult]:
        query = query.strip()

        if not query:
            raise ValueError("query cannot be empty.")

        if not query_embedding:
            raise ValueError("query_embedding cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        if candidate_k <= 0:
            raise ValueError("candidate_k must be greater than zero.")

        if rrf_k <= 0:
            raise ValueError("rrf_k must be greater than zero.")

        semantic_results = self.semantic_repository.semantic_search(
            query_embedding,
            top_k=candidate_k,
        )

        fts_results = self.fts_repository.search(
            query,
            top_k=candidate_k,
        )

        results: dict[UUID, dict] = {}

        for rank, result in enumerate(semantic_results, start=1):
            results[result.chunk_id] = {
                "chunk_id": result.chunk_id,
                "document_id": result.document_id,
                "document_key": result.document_key,
                "section": result.section,
                "text": result.text,
                "semantic_score": result.score,
                "fts_score": None,
                "rrf_score": 1.0 / (rrf_k + rank),
            }

        for rank, result in enumerate(fts_results, start=1):
            if result.chunk_id not in results:
                results[result.chunk_id] = {
                    "chunk_id": result.chunk_id,
                    "document_id": result.document_id,
                    "document_key": result.document_key,
                    "section": result.section,
                    "text": result.text,
                    "semantic_score": None,
                    "fts_score": result.score,
                    "rrf_score": 0.0,
                }

            results[result.chunk_id]["fts_score"] = result.score
            results[result.chunk_id]["rrf_score"] += (
                1.0 / (rrf_k + rank)
            )

        ranked_results = sorted(
            results.values(),
            key=lambda result: result["rrf_score"],
            reverse=True,
        )

        return [
            KBHybridRetrievalResult(**result)
            for result in ranked_results[:top_k]
        ]