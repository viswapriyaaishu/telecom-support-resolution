from dataclasses import dataclass

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from app.db.repositories.embedding import EmbeddingRepository


@dataclass(frozen=True)
class EmbeddingResult:
    chunks_processed: int
    chunks_embedded: int


class EmbeddingService:
    def __init__(
        self,
        session: Session,
        *,
        model_name: str = "BAAI/bge-large-en-v1.5",
    ) -> None:
        self.session = session
        self.repository = EmbeddingRepository(session)
        self.model = SentenceTransformer(model_name)

    def process(
        self,
        *,
        batch_size: int = 16,
        max_chunks: int | None = None,
    ) -> EmbeddingResult:
        chunks_processed = 0
        chunks_embedded = 0

        for chunks in self.repository.stream_unembedded_chunks(
            batch_size=batch_size,
        ):
            if max_chunks is not None:
                remaining = max_chunks - chunks_processed
                if remaining <= 0:
                    break

                chunks = chunks[:remaining]

            texts = [chunk.text for chunk in chunks]

            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

            embedding_lists = embeddings.tolist()

            self.repository.update_embeddings(
                chunks,
                embedding_lists,
            )

            self.session.commit()

            chunks_processed += len(chunks)
            chunks_embedded += len(chunks)

            print(
                f"Embedded chunks: "
                f"{chunks_embedded:,}"
            )

            if (
                max_chunks is not None
                and chunks_processed >= max_chunks
            ):
                break

        return EmbeddingResult(
            chunks_processed=chunks_processed,
            chunks_embedded=chunks_embedded,
        )