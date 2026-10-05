import asyncio

from app.db.session import SessionLocal
from app.services.evidence_retrieval import EvidenceRetrievalService
from app.services.intelligence import ComplaintIntelligenceService
from app.services.llm import create_llm_provider
from app.services.resolution import ResolutionService

COMPLAINT = (
    "My broadband drops every evening around 8 and "
    "I've already restarted the router twice. "
    "I work from home and this is costing me."
)


async def main() -> None:
    llm_provider = create_llm_provider()

    intelligence_service = ComplaintIntelligenceService(
        llm_provider=llm_provider,
    )

    intelligence = await intelligence_service.analyze(
        COMPLAINT,
    )

    with SessionLocal() as session:
        evidence_service = EvidenceRetrievalService(session)

        resolution_service = ResolutionService(
            llm_provider=llm_provider,
            evidence_service=evidence_service,
        )

        execution = await resolution_service.resolve(
            complaint=COMPLAINT,
            intelligence=intelligence,
        )

        print("\n=== COMPLAINT INTELLIGENCE ===")
        print(intelligence.model_dump_json(indent=2))

        print("\n=== RESOLUTION ===")
        print(execution.response.model_dump_json(indent=2))

        print("\n=== GROUNDING ===")
        print(execution.grounding)

        print(
            "\nRetrieved evidence count:",
            execution.retrieval_count,
        )


if __name__ == "__main__":
    asyncio.run(main())