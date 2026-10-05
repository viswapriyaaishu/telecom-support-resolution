from telecom_support_schemas import ComplaintIntelligence

from app.services.llm import LLMProvider

INTELLIGENCE_PROMPT = """
You are a telecom customer-support complaint classifier.

Analyze the customer's complaint and return ONLY valid JSON.

Use these exact values when applicable:

intent:
- Connectivity
- Mobile
- Billing
- Account
- Outage
- Other

severity:
- LOW
- MEDIUM
- HIGH
- CRITICAL
- UNKNOWN

sentiment:
- POSITIVE
- NEUTRAL
- NEGATIVE
- UNKNOWN

Important classification rules:
- A video call, online meeting, streaming, browsing, or internet freezing
  is NOT automatically a mobile-phone issue.
- Determine the product from the actual complaint.
- If the complaint describes broadband/Wi-Fi/router/internet connectivity,
  prefer product "Broadband".
- "Dropped Calls" means cellular/telephone calls being disconnected,
  not video calls freezing because of internet problems.
- Do not invent entities that are not supported by the complaint.
- Confidence must be between 0 and 1.

Return exactly this JSON structure:

{
  "intent": "...",
  "sub_intent": "...",
  "product": "...",
  "severity": "...",
  "sentiment": "...",
  "entities": {},
  "confidence": 0.0,
  "model_version": "llm-intelligence-v1"
}

Customer complaint:
"""


class ComplaintIntelligenceService:
    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    async def analyze(
        self,
        complaint: str,
    ) -> ComplaintIntelligence:
        complaint = complaint.strip()

        if not complaint:
            raise ValueError("complaint cannot be empty.")

        prompt = (
            INTELLIGENCE_PROMPT
            + complaint
        )

        return await self.llm_provider.generate(
            prompt,
            ComplaintIntelligence,
        )