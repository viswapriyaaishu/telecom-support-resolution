from app.db.repositories.kb_fts import KBFTSRepository
from app.db.session import SessionLocal


def main() -> None:
    query = (
        "broadband disconnecting every evening "
        "router restart"
    )

    with SessionLocal() as session:
        repository = KBFTSRepository(session)

        results = repository.search(
            query,
            top_k=5,
        )

        print(f"\nQuery: {query}\n")
        print(f"Retrieved: {len(results)} results\n")

        for index, result in enumerate(results, start=1):
            print(f"--- Result {index} ---")
            print(f"Score: {result.score:.4f}")
            print(f"Section: {result.section}")
            print(result.text[:500])
            print()


if __name__ == "__main__":
    main()