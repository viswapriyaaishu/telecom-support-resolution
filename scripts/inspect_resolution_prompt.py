from app.db.session import SessionLocal
from app.services.evidence_policy import EvidencePolicy
from app.services.evidence_retrieval import EvidenceRetrievalService
from app.services.intelligence import ComplaintIntelligenceService
from app.services.llm import create_llm_provider
from app.services.resolution_prompt import build_resolution_prompt

COMPLAINT = (
    "My broadband drops every evening around 8 and "
    "I've already restarted the router twice. "
    "I work from home and this is costing me."
)

import asyncio


async def main() -> None:
    intelligence = await ComplaintIntelligenceService(
        llm_provider=create_llm_provider(),
    ).analyze(COMPLAINT)

    with SessionLocal() as session:
        evidence_service = EvidenceRetrievalService(session)

        evidence = evidence_service.search(
            COMPLAINT,
            historical_top_k=5,
            kb_top_k=5,
            candidate_k=20,
        )

        selected = EvidencePolicy().select(evidence)

        print(f"Total evidence: {len(selected)}")
        print()

        for index, item in enumerate(selected, start=1):
            print(
                f"{index}. {item.source_type} | "
                f"score={item.score:.6f} | "
                f"chars={len(item.text)} | "
                f"source={item.source_key}"
            )

        prompt = build_resolution_prompt(
            complaint=COMPLAINT,
            intelligence=intelligence,
            evidence=selected,
        )

        print()
        print(f"Prompt length: {len(prompt)} characters")


if __name__ == "__main__":
    asyncio.run(main())
