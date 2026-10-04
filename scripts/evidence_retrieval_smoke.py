from app.db.session import SessionLocal
from app.services.evidence_retrieval import EvidenceRetrievalService


def main() -> None:
    query = (
        "My broadband keeps disconnecting every evening "
        "and restarting the router does not fix it."
    )

    with SessionLocal() as session:
        service = EvidenceRetrievalService(session)

        results = service.search(
            query,
            historical_top_k=5,
            kb_top_k=5,
            candidate_k=20,
        )

        print(f"\nQuery: {query}\n")
        print(f"Retrieved evidence: {len(results)}\n")

        for index, result in enumerate(results, start=1):
            print(f"--- Evidence {index} ---")
            print(f"Source Type: {result.source_type}")
            print(f"Source ID: {result.source_id}")
            print(f"Section: {result.section}")
            print(f"Trust: {result.trust}")
            print(f"Score: {result.score:.4f}")
            print(result.text[:500])
            print()


if __name__ == "__main__":
    main()