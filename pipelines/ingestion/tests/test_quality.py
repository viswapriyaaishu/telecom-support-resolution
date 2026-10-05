from datetime import UTC, datetime

from telecom_support_ingestion.models import Conversation, ConversationTurn
from telecom_support_ingestion.quality import (
    QualityIssue,
    QualityStatus,
    validate_conversation,
)


def make_turn(
    *,
    speaker: str = "client",
    text: str = "My internet is slow.",
    minute: int = 0,
) -> ConversationTurn:
    return ConversationTurn(
        turn_index=0,
        speaker=speaker,
        date_time=datetime(
            2026,
            9,
            30,
            10,
            minute,
            tzinfo=UTC,
        ),
        text=text,
    )


def test_valid_conversation() -> None:
    conversation = Conversation(
        conversation_id="conversation-1",
        turns=[
            make_turn(speaker="client", minute=0),
            make_turn(
                speaker="agent",
                text="I can help troubleshoot that.",
                minute=1,
            ),
        ],
    )

    status, issues = validate_conversation(conversation)

    assert status == QualityStatus.VALID
    assert issues == []


def test_missing_conversation_id_is_invalid() -> None:
    conversation = Conversation(
        conversation_id="   ",
        turns=[make_turn()],
    )

    status, issues = validate_conversation(conversation)

    assert status == QualityStatus.INVALID
    assert QualityIssue.MISSING_CONVERSATION_ID in issues


def test_no_turns_is_invalid() -> None:
    conversation = Conversation(
        conversation_id="conversation-1",
        turns=[],
    )

    status, issues = validate_conversation(conversation)

    assert status == QualityStatus.INVALID
    assert QualityIssue.NO_TURNS in issues


def test_invalid_speaker_is_invalid() -> None:
    conversation = Conversation(
        conversation_id="conversation-1",
        turns=[make_turn(speaker="unknown")],
    )

    status, issues = validate_conversation(conversation)

    assert status == QualityStatus.INVALID
    assert QualityIssue.INVALID_SPEAKER in issues


def test_empty_text_is_invalid() -> None:
    conversation = Conversation(
        conversation_id="conversation-1",
        turns=[make_turn(text="   ")],
    )

    status, issues = validate_conversation(conversation)

    assert status == QualityStatus.INVALID
    assert QualityIssue.EMPTY_TEXT in issues


def test_out_of_order_timestamps_are_invalid() -> None:
    conversation = Conversation(
        conversation_id="conversation-1",
        turns=[
            make_turn(minute=2),
            make_turn(
                speaker="agent",
                text="Let me help.",
                minute=1,
            ),
        ],
    )

    status, issues = validate_conversation(conversation)

    assert status == QualityStatus.INVALID
    assert QualityIssue.INVALID_TIMESTAMP_ORDER in issues


def test_multiple_identical_issues_are_deduplicated() -> None:
    conversation = Conversation(
        conversation_id="conversation-1",
        turns=[
            make_turn(text=""),
            make_turn(
                speaker="unknown",
                text="",
            ),
        ],
    )

    status, issues = validate_conversation(conversation)

    assert status == QualityStatus.INVALID
    assert issues.count(QualityIssue.EMPTY_TEXT) == 1
    assert issues.count(QualityIssue.INVALID_SPEAKER) == 1


def test_single_turn_conversation_can_be_valid() -> None:
    conversation = Conversation(
        conversation_id="conversation-1",
        turns=[make_turn()],
    )

    status, issues = validate_conversation(conversation)

    assert status == QualityStatus.VALID
    assert issues == []
