from app.db.session import SessionLocal
from app.services.chunking import ChunkingService


def main() -> None:
    with SessionLocal() as session:
        service = ChunkingService(session)

        result = service.process(
            source_dataset="talkmap",
            dataset_version="talkmap-v1",
            batch_size=100,
            max_characters=3500,
            overlap_characters=500,
            max_conversations=None,
        )

        print(
            f"Processed: {result.conversations_processed:,} | "
            f"Chunks: {result.chunks_created:,}"
        )


if __name__ == "__main__":
    main()