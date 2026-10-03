from datetime import UTC, datetime

from telecom_support_ingestion.models import Conversation, ConversationTurn
from telecom_support_ingestion.resolution import (
    ResolutionEvidence,
    ResolutionStatus,
    classify_resolution,
)


def make_conversation(texts: list[str]) -> Conversation:
    return Conversation(
        conversation_id="conversation-1",
        turns=[
            ConversationTurn(
                turn_index=index,
                speaker="client" if index % 2 == 0 else "agent",
                date_time=datetime(
                    2026,
                    9,
                    30,
                    10,
                    index,
                    tzinfo=UTC,
                ),
                text=text,
            )
            for index, text in enumerate(texts)
        ],
    )


def test_customer_confirmation_is_resolved() -> None:
    conversation = make_conversation(
        [
            "My internet is not working.",
            "Please restart your router.",
            "That fixed it, thank you.",
        ]
    )

    status, evidence = classify_resolution(conversation)

    assert status == ResolutionStatus.RESOLVED
    assert evidence == ResolutionEvidence.CUSTOMER_CONFIRMED


def test_escalation_is_classified_as_escalated() -> None:
    conversation = make_conversation(
        [
            "My broadband is still not working.",
            "I will transfer you to a technician.",
        ]
    )

    status, evidence = classify_resolution(conversation)

    assert status == ResolutionStatus.ESCALATED
    assert evidence == ResolutionEvidence.ESCALATION_REQUIRED


def test_unsuccessful_attempt_is_unresolved() -> None:
    conversation = make_conversation(
        [
            "My connection is slow.",
            "Please restart the router.",
            "I restarted it but it did not help.",
        ]
    )

    status, evidence = classify_resolution(conversation)

    assert status == ResolutionStatus.UNRESOLVED
    assert evidence == ResolutionEvidence.UNSUCCESSFUL_ATTEMPT


def test_no_resolution_evidence_is_unknown() -> None:
    conversation = make_conversation(
        [
            "My internet is slow.",
            "Please restart your router.",
        ]
    )

    status, evidence = classify_resolution(conversation)

    assert status == ResolutionStatus.UNKNOWN
    assert evidence == ResolutionEvidence.INSUFFICIENT_EVIDENCE


def test_resolution_matching_is_case_insensitive() -> None:
    conversation = make_conversation(
        [
            "The issue was happening earlier.",
            "It's Working Now.",
        ]
    )

    status, evidence = classify_resolution(conversation)

    assert status == ResolutionStatus.RESOLVED
    assert evidence == ResolutionEvidence.CUSTOMER_CONFIRMED


def test_escalation_takes_precedence() -> None:
    conversation = make_conversation(
        [
            "The issue is resolved for now.",
            "However, I will transfer you to a technician.",
        ]
    )

    status, evidence = classify_resolution(conversation)

    assert status == ResolutionStatus.ESCALATED
    assert evidence == ResolutionEvidence.ESCALATION_REQUIRED


def test_initial_not_working_followed_by_fix_is_resolved() -> None:
    conversation = make_conversation(
        [
            "My internet was not working.",
            "Please restart the router.",
            "That fixed it. It is working now.",
        ]
    )

    status, evidence = classify_resolution(conversation)

    assert status == ResolutionStatus.RESOLVED
    assert evidence == ResolutionEvidence.CUSTOMER_CONFIRMED