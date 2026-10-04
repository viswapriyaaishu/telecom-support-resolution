from sentence_transformers import SentenceTransformer

from app.db.session import SessionLocal
from app.services.kb_hybrid_retrieval import KBHybridRetrievalService


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
        service = KBHybridRetrievalService(session)

        results = service.search(
            query,
            embedding,
            top_k=5,
            candidate_k=5,
        )

        print(f"\nQuery: {query}\n")
        print(f"Retrieved: {len(results)} results\n")

        for index, result in enumerate(results, start=1):
            print(f"--- Result {index} ---")
            print(f"RRF Score: {result.rrf_score:.4f}")
            print(
                f"Semantic Score: "
                f"{result.semantic_score:.4f}"
                if result.semantic_score is not None
                else "Semantic Score: None"
            )
            print(
                f"FTS Score: "
                f"{result.fts_score:.4f}"
                if result.fts_score is not None
                else "FTS Score: None"
            )
            print(f"Section: {result.section}")
            print(result.text[:500])
            print()


if __name__ == "__main__":
    main()