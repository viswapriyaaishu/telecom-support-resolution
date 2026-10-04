import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from telecom_support_schemas import (
    ComplaintIntelligence,
    ResolutionResponse,
)

from app.db.repositories.resolution_log import (
    ResolutionLogRepository,
)
from app.db.session import get_db
from app.services.evidence_retrieval import EvidenceRetrievalService
from app.services.intelligence import ComplaintIntelligenceService
from app.services.llm import create_llm_provider
from app.services.resolution import ResolutionService


router = APIRouter(
    prefix="/resolve",
    tags=["resolution"],
)


class ResolveRequest(BaseModel):
    complaint: str = Field(
        min_length=1,
        max_length=10_000,
    )


class GroundingMetadata(BaseModel):
    is_grounded: bool
    unsupported_steps: list[str]
    authoritative_evidence_count: int


class ResolveResponse(BaseModel):
    complaint: str
    intelligence: ComplaintIntelligence
    resolution: ResolutionResponse
    grounding: GroundingMetadata


@router.post(
    "",
    response_model=ResolveResponse,
)
async def resolve_complaint(
    request: ResolveRequest,
    session: Session = Depends(get_db),
) -> ResolveResponse:
    start_time = time.perf_counter()

    intelligence = None

    try:
        intelligence_service = ComplaintIntelligenceService()

        intelligence = intelligence_service.analyze(
            request.complaint,
        )

        evidence_service = EvidenceRetrievalService(
            session,
        )

        resolution_service = ResolutionService(
            llm_provider=create_llm_provider(),
            evidence_service=evidence_service,
        )

        execution = await resolution_service.resolve(
            complaint=request.complaint,
            intelligence=intelligence,
        )

        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        ResolutionLogRepository(session).create(
            complaint=request.complaint,
            intent=intelligence.intent.value,
            sub_intent=intelligence.sub_intent,
            product=intelligence.product,
            severity=intelligence.severity.value,
            sentiment=intelligence.sentiment.value,
            retrieval_count=execution.retrieval_count,
            authoritative_evidence_count=(
                execution.grounding.authoritative_evidence_count
            ),
            grounded=execution.grounding.is_grounded,
            unsupported_steps=(
                execution.grounding.unsupported_steps
            ),
            resolution_confidence=(
                execution.response.confidence
            ),
            resolution_summary=(
                execution.response.summary
            ),
            latency_ms=latency_ms,
        )

        session.commit()

        return ResolveResponse(
            complaint=request.complaint,
            intelligence=intelligence,
            resolution=execution.response,
            grounding=GroundingMetadata(
                is_grounded=execution.grounding.is_grounded,
                unsupported_steps=(
                    execution.grounding.unsupported_steps
                ),
                authoritative_evidence_count=(
                    execution.grounding.authoritative_evidence_count
                ),
            ),
        )

    except ValueError as exc:
        session.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        try:
            if intelligence is not None:
                ResolutionLogRepository(session).create(
                    complaint=request.complaint,
                    intent=intelligence.intent.value,
                    sub_intent=intelligence.sub_intent,
                    product=intelligence.product,
                    severity=intelligence.severity.value,
                    sentiment=intelligence.sentiment.value,
                    retrieval_count=0,
                    authoritative_evidence_count=0,
                    grounded=False,
                    unsupported_steps=[],
                    resolution_confidence=0.0,
                    resolution_summary=(
                        "Resolution failed before completion."
                    ),
                    latency_ms=latency_ms,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )

                session.commit()
        except Exception:
            session.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to resolve the support complaint.",
        ) from exc