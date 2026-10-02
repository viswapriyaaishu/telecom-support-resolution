from enum import StrEnum

from models import Conversation


class ResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    UNRESOLVED = "UNRESOLVED"
    UNKNOWN = "UNKNOWN"


class ResolutionEvidence(StrEnum):
    CUSTOMER_CONFIRMED = "CUSTOMER_CONFIRMED"
    AGENT_CONFIRMED = "AGENT_CONFIRMED"
    ESCALATION_REQUIRED = "ESCALATION_REQUIRED"
    UNSUCCESSFUL_ATTEMPT = "UNSUCCESSFUL_ATTEMPT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


_ESCALATION_PHRASES = (
    "transfer you",
    "transfer to",
    "dedicated support",
    "technician",
    "further assistance",
    "escalate",
    "escalation",
    "unable to resolve",
    "cannot resolve",
)

_CUSTOMER_CONFIRMATION_PHRASES = (
    "that fixed it",
    "that solved it",
    "it's working now",
    "it is working now",
    "problem is resolved",
    "issue is resolved",
    "working again",
    "works now",
)

_UNSUCCESSFUL_PHRASES = (
    "didn't help",
    "did not help",
    "still not working",
    "still doesn't work",
    "still does not work",
    "hasn't helped",
    "have not helped",
    "not working",
)


def classify_resolution(
    conversation: Conversation,
) -> tuple[ResolutionStatus, ResolutionEvidence]:
    text = " ".join(
        turn.text.lower()
        for turn in conversation.turns
    )

    if any(
        phrase in text
        for phrase in _ESCALATION_PHRASES
    ):
        return (
            ResolutionStatus.ESCALATED,
            ResolutionEvidence.ESCALATION_REQUIRED,
        )

    if any(
        phrase in text
        for phrase in _CUSTOMER_CONFIRMATION_PHRASES
    ):
        return (
            ResolutionStatus.RESOLVED,
            ResolutionEvidence.CUSTOMER_CONFIRMED,
        )

    if any(
        phrase in text
        for phrase in _UNSUCCESSFUL_PHRASES
    ):
        return (
            ResolutionStatus.UNRESOLVED,
            ResolutionEvidence.UNSUCCESSFUL_ATTEMPT,
        )

    return (
        ResolutionStatus.UNKNOWN,
        ResolutionEvidence.INSUFFICIENT_EVIDENCE,
    )