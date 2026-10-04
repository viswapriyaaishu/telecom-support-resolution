from dataclasses import dataclass

from telecom_support_schemas import (
    ComplaintIntelligence,
    ResolutionResponse,
)

from app.services.evidence_policy import EvidencePolicy
from app.services.evidence_retrieval import EvidenceRetrievalService
from app.services.grounding_validator import (
    GroundingValidationResult,
    GroundingValidator,
)
from app.services.llm import LLMProvider
from app.services.resolution_prompt import build_resolution_prompt


@dataclass(frozen=True)
class ResolutionExecution:
    response: ResolutionResponse
    grounding: GroundingValidationResult
    retrieval_count: int


class ResolutionService:
    def __init__(
        self,
        llm_provider: LLMProvider,
        evidence_service: EvidenceRetrievalService,
        evidence_policy: EvidencePolicy | None = None,
        grounding_validator: GroundingValidator | None = None,
    ) -> None:
        self.llm_provider = llm_provider
        self.evidence_service = evidence_service
        self.evidence_policy = (
            evidence_policy or EvidencePolicy()
        )
        self.grounding_validator = (
            grounding_validator or GroundingValidator()
        )

    async def resolve(
        self,
        complaint: str,
        intelligence: ComplaintIntelligence,
    ) -> ResolutionExecution:
        complaint = complaint.strip()

        if not complaint:
            raise ValueError("complaint cannot be empty.")

        evidence = self.evidence_service.search(
            complaint,
            historical_top_k=5,
            kb_top_k=5,
            candidate_k=20,
        )

        evidence = self.evidence_policy.select(evidence)

        prompt = build_resolution_prompt(
            complaint=complaint,
            intelligence=intelligence,
            evidence=evidence,
        )

        response = await self.llm_provider.generate(
            prompt,
            ResolutionResponse,
        )

        grounding = self.grounding_validator.validate(
            response,
            evidence,
        )

        if not grounding.is_grounded:
            response = ResolutionResponse(
                summary=response.summary,
                diagnosis=response.diagnosis,
                recommended_steps=[
                    (
                        "The generated troubleshooting steps could not "
                        "be fully verified against the authoritative "
                        "knowledge base."
                    )
                ],
                escalation_required=True,
                confidence=min(response.confidence, 0.50),
                citations=response.citations,
            )

        return ResolutionExecution(
            response=response,
            grounding=grounding,
            retrieval_count=len(evidence),
        )