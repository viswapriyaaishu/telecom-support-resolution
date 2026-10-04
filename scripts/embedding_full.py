from app.db.session import SessionLocal
from app.services.embedding import EmbeddingService


def main() -> None:
    with SessionLocal() as session:
        service = EmbeddingService(session)

        result = service.process(
            batch_size=4,
            max_chunks=None,
        )

        print(
            f"Processed: {result.chunks_processed:,} | "
            f"Embedded: {result.chunks_embedded:,}"
        )


if __name__ == "__main__":
    main()