import asyncio

from app.services.intelligence import ComplaintIntelligenceService
from app.services.llm import create_llm_provider

COMPLAINT = (
    "My broadband drops every evening around 8 and "
    "I've already restarted the router twice, "
    "I work from home and this is costing me."
)


async def main() -> None:
    llm_provider = create_llm_provider()

    service = ComplaintIntelligenceService(
        llm_provider=llm_provider,
    )

    result = await service.analyze(COMPLAINT)

    print("\nComplaint:")
    print(COMPLAINT)

    print("\nIntelligence:")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())