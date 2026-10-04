from app.db.session import SessionLocal
from app.services.fts import FTSService


def main() -> None:
    query = (
        "My broadband keeps disconnecting every evening "
        "and restarting the router does not fix it."
    )

    with SessionLocal() as session:
        service = FTSService(session)

        results = service.search(
            query,
            top_k=5,
        )

        print(f"\nQuery: {query}\n")
        print(f"Retrieved: {len(results)} results\n")

        for index, result in enumerate(results, start=1):
            print(f"--- Result {index} ---")
            print(f"Score: {result.score:.4f}")
            print(f"Conversation ID: {result.conversation_id}")
            print(f"Chunk ID: {result.chunk_id}")
            print(result.text[:1000])
            print()


if __name__ == "__main__":
    main()