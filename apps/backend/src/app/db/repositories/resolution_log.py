from uuid import UUID

from sqlalchemy.orm import Session

from telecom_support_database.models import ResolutionLog


class ResolutionLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        complaint: str,
        intent: str,
        sub_intent: str,
        product: str,
        severity: str,
        sentiment: str,
        retrieval_count: int,
        authoritative_evidence_count: int,
        grounded: bool,
        unsupported_steps: list[str],
        resolution_confidence: float,
        resolution_summary: str,
        latency_ms: float,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> UUID:
        log = ResolutionLog(
            complaint=complaint,
            intent=intent,
            sub_intent=sub_intent,
            product=product,
            severity=severity,
            sentiment=sentiment,
            retrieval_count=retrieval_count,
            authoritative_evidence_count=(
                authoritative_evidence_count
            ),
            grounded=grounded,
            unsupported_steps=unsupported_steps,
            resolution_confidence=resolution_confidence,
            resolution_summary=resolution_summary,
            latency_ms=latency_ms,
            error_type=error_type,
            error_message=error_message,
        )

        self.session.add(log)
        self.session.flush()

        return log.id