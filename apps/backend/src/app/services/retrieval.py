from dataclasses import dataclass
from uuid import UUID

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from app.services.hybrid_retrieval import HybridRetrievalService


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    conversation_id: UUID
    text: str
    semantic_score: float | None
    fts_score: float | None
    score: float


class RetrievalService:
    def __init__(
        self,
        session: Session,
        *,
        model_name: str = "BAAI/bge-large-en-v1.5",
    ) -> None:
        self.hybrid_service = HybridRetrievalService(session)
        self.model = SentenceTransformer(model_name)

    def search(
        self,
        query: str,
        *,
        top_k: int = 10,
        candidate_k: int = 20,
    ) -> list[RetrievedChunk]:
        query = query.strip()

        if not query:
            raise ValueError("query cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        if candidate_k <= 0:
            raise ValueError("candidate_k must be greater than zero.")

        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        results = self.hybrid_service.search(
            query,
            query_embedding,
            top_k=top_k,
            candidate_k=candidate_k,
        )

        return [
            RetrievedChunk(
                chunk_id=result.chunk_id,
                conversation_id=result.conversation_id,
                text=result.text,
                semantic_score=result.semantic_score,
                fts_score=result.fts_score,
                score=result.rrf_score,
            )
            for result in results
        ]