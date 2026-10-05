from app.db.repositories.kb import KBRepository
from app.db.session import SessionLocal
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-large-en-v1.5"


def main() -> None:
    query = (
        "My broadband keeps disconnecting every evening "
        "and restarting the router does not fix it."
    )

    model = SentenceTransformer(MODEL_NAME)

    embedding = model.encode(
        query,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).tolist()

    with SessionLocal() as session:
        repository = KBRepository(session)

        results = repository.semantic_search(
            embedding,
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