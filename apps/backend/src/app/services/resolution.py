import time
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
        total_start = time.perf_counter()

        complaint = complaint.strip()

        if not complaint:
            raise ValueError("complaint cannot be empty.")

        # =========================================================
        # 1. Evidence Retrieval
        # =========================================================

        retrieval_start = time.perf_counter()

        evidence = self.evidence_service.search(
            complaint,
            historical_top_k=5,
            kb_top_k=5,
            candidate_k=20,
        )

        retrieval_ms = (
            time.perf_counter() - retrieval_start
        ) * 1000

        print(
            f"[TIMING] Evidence Retrieval: "
            f"{retrieval_ms:.2f} ms"
        )

        # =========================================================
        # 2. Evidence Policy Selection
        # =========================================================

        policy_start = time.perf_counter()

        evidence = self.evidence_policy.select(evidence)

        policy_ms = (
            time.perf_counter() - policy_start
        ) * 1000

        print(
            f"[TIMING] Evidence Policy: "
            f"{policy_ms:.2f} ms"
        )

        print(
            f"[TIMING] Evidence Count: "
            f"{len(evidence)}"
        )

        # =========================================================
        # 3. Grounded Prompt Construction
        # =========================================================

        prompt_start = time.perf_counter()

        prompt = build_resolution_prompt(
            complaint=complaint,
            intelligence=intelligence,
            evidence=evidence,
        )

        prompt_ms = (
            time.perf_counter() - prompt_start
        ) * 1000

        print(
            f"[TIMING] Prompt Construction: "
            f"{prompt_ms:.2f} ms"
        )

        print(
            f"[TIMING] Prompt Length: "
            f"{len(prompt)} characters"
        )

        # =========================================================
        # 4. Resolution LLM
        # =========================================================

        llm_start = time.perf_counter()

        response = await self.llm_provider.generate(
            prompt,
            ResolutionResponse,
        )

        llm_ms = (
            time.perf_counter() - llm_start
        ) * 1000

        print(
            f"[TIMING] Resolution LLM: "
            f"{llm_ms:.2f} ms"
        )

        # =========================================================
        # 5. Grounding Validation
        # =========================================================

        grounding_start = time.perf_counter()

        grounding = self.grounding_validator.validate(
            response,
            evidence,
        )

        grounding_ms = (
            time.perf_counter() - grounding_start
        ) * 1000

        print(
            f"[TIMING] Grounding Validation: "
            f"{grounding_ms:.2f} ms"
        )

        # =========================================================
        # 6. Safety Fallback
        # =========================================================

        fallback_start = time.perf_counter()

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
                confidence=min(
                    response.confidence,
                    0.50,
                ),
                citations=response.citations,
            )

        fallback_ms = (
            time.perf_counter() - fallback_start
        ) * 1000

        print(
            f"[TIMING] Safety Fallback: "
            f"{fallback_ms:.2f} ms"
        )

        # =========================================================
        # 7. Total Resolution Service Time
        # =========================================================

        total_ms = (
            time.perf_counter() - total_start
        ) * 1000

        print(
            f"[TIMING] Resolution Service Total: "
            f"{total_ms:.2f} ms"
        )

        return ResolutionExecution(
            response=response,
            grounding=grounding,
            retrieval_count=len(evidence),
        )