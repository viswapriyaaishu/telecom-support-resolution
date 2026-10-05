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
from app.services.llm import (
    LLMRateLimitError,
    create_llm_provider,
)
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
    session: Session = Depends(get_db), # noqa: B008
) -> ResolveResponse:
    start_time = time.perf_counter()

    intelligence = None

    try:
        # -----------------------------
        # 1. Intelligence classification
        # -----------------------------
        intelligence_start = time.perf_counter()

        intelligence_service = ComplaintIntelligenceService(
            llm_provider=create_llm_provider(),
        )

        intelligence = await intelligence_service.analyze(
            request.complaint,
        )

        intelligence_ms = (
            time.perf_counter() - intelligence_start
        ) * 1000

        print(
            f"[TIMING] Intelligence: "
            f"{intelligence_ms:.2f} ms"
        )

        # -----------------------------
        # 2. Retrieval + resolution
        # -----------------------------
        retrieval_resolution_start = time.perf_counter()

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

        retrieval_resolution_ms = (
            time.perf_counter()
            - retrieval_resolution_start
        ) * 1000

        print(
            f"[TIMING] Retrieval + Resolution: "
            f"{retrieval_resolution_ms:.2f} ms"
        )

        # -----------------------------
        # 3. Total request latency
        # -----------------------------
        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        print(
            f"[TIMING] Total: "
            f"{latency_ms:.2f} ms"
        )

        # -----------------------------
        # 4. Persist resolution log
        # -----------------------------
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

        # -----------------------------
        # 5. Return response
        # -----------------------------
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

    except LLMRateLimitError as exc:
        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        print(
            f"[TIMING] Rate-limited request total: "
            f"{latency_ms:.2f} ms"
        )

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
                        "Resolution unavailable because the "
                        "LLM provider rate limit was reached."
                    ),
                    latency_ms=latency_ms,
                    error_type="LLMRateLimitError",
                    error_message=str(exc),
                )

                session.commit()

        except Exception:
            session.rollback()

        retry_after = (
            max(
                int(exc.retry_after_seconds),
                1,
            )
            if exc.retry_after_seconds is not None
            else 5
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "The resolution service is temporarily "
                "rate-limited. Please retry shortly."
            ),
            headers={
                "Retry-After": str(retry_after),
            },
        ) from exc

    except Exception as exc:
        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        print(
            f"[TIMING] Failed request total: "
            f"{latency_ms:.2f} ms"
        )

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