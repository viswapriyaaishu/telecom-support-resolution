import asyncio

from app.services.llm import create_llm_provider
from telecom_support_schemas import ResolutionResponse


async def main() -> None:
    provider = create_llm_provider()

    response = await provider.generate(
        """Return a valid JSON resolution object with:
summary='Groq connection OK',
diagnosis='Provider test',
recommended_steps=['No action required'],
escalation_required=false,
confidence=1.0,
citations=[]""",
        ResolutionResponse,
    )

    print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())