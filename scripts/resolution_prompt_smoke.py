from app.db.session import SessionLocal
from app.services.evidence_retrieval import EvidenceRetrievalService
from app.services.intelligence import ComplaintIntelligenceService
from app.services.resolution_prompt import build_resolution_prompt


def main() -> None:
    complaint = (
        "My broadband drops every evening around 8 and "
        "I've already restarted the router twice, "
        "I work from home and this is costing me."
    )

    intelligence_service = ComplaintIntelligenceService()

    intelligence = intelligence_service.analyze(
        complaint
    )

    with SessionLocal() as session:
        evidence_service = EvidenceRetrievalService(session)

        evidence = evidence_service.search(
            complaint,
            historical_top_k=5,
            kb_top_k=5,
            candidate_k=20,
        )

    prompt = build_resolution_prompt(
        complaint,
        intelligence,
        evidence,
    )

    print(prompt)


if __name__ == "__main__":
    main()