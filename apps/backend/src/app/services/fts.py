from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.repositories.fts import FTSRepository


@dataclass(frozen=True)
class FTSRetrievedChunk:
    chunk_id: UUID
    conversation_id: UUID
    text: str
    score: float


class FTSService:
    def __init__(self, session: Session) -> None:
        self.repository = FTSRepository(session)

    def search(
        self,
        query: str,
        *,
        top_k: int = 10,
    ) -> list[FTSRetrievedChunk]:
        results = self.repository.search(
            query,
            top_k=top_k,
        )

        return [
            FTSRetrievedChunk(
                chunk_id=result.chunk_id,
                conversation_id=result.conversation_id,
                text=result.text,
                score=result.score,
            )
            for result in results
        ]