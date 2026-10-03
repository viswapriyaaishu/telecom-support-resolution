from datetime import UTC, datetime

from telecom_support_ingestion.models import Conversation, ConversationTurn
from telecom_support_ingestion.pipeline import process_conversation
from telecom_support_ingestion.processed import IngestionMetadata
from telecom_support_ingestion.quality import QualityStatus
from telecom_support_ingestion.resolution import ResolutionStatus

INGESTION_METADATA = IngestionMetadata(
    source_dataset="talkmap-telecom-conversation-corpus",
    dataset_version="telecom_200k",
    pipeline_version="0.1.0",
    ingested_at=datetime(
        2026,
        9,
        30,
        12,
        0,
        tzinfo=UTC,
    ),
)


def test_process_conversation_normalizes_and_redacts() -> None:
    conversation = Conversation(
        conversation_id="conversation-1",
        turns=[
            ConversationTurn(
                turn_index=0,
                speaker="client",
                date_time=datetime(
                    2026,
                    9,
                    30,
                    10,
                    0,
                    tzinfo=UTC,
                ),
                text=(
                    "  My account number is 123456789. "
                    "Email me at customer@example.com.  "
                ),
            ),
            ConversationTurn(
                turn_index=1,
                speaker="agent",
                date_time=datetime(
                    2026,
                    9,
                    30,
                    10,
                    1,
                    tzinfo=UTC,
                ),
                text="That fixed it, thank you.",
            ),
        ],
    )

    result = process_conversation(
        conversation,
        INGESTION_METADATA,
    )

    assert result.conversation.turns[0].text == (
        "My account number is [ACCOUNT_NUMBER]. "
        "Email me at [EMAIL]."
    )

    assert result.quality_status == QualityStatus.VALID
    assert result.quality_issues == []

    assert result.resolution_status == ResolutionStatus.RESOLVED


def test_process_conversation_preserves_conversation_metadata() -> None:
    conversation = Conversation(
        conversation_id="conversation-42",
        turns=[
            ConversationTurn(
                turn_index=0,
                speaker="client",
                date_time=datetime(
                    2026,
                    9,
                    30,
                    11,
                    0,
                    tzinfo=UTC,
                ),
                text="My broadband is slow.",
            ),
        ],
    )

    result = process_conversation(
        conversation,
        INGESTION_METADATA,
    )

    assert result.conversation.conversation_id == "conversation-42"
    assert result.conversation.turns[0].turn_index == 0
    assert result.conversation.turns[0].speaker == "client"


def test_process_conversation_runs_quality_validation() -> None:
    conversation = Conversation(
        conversation_id="conversation-1",
        turns=[
            ConversationTurn(
                turn_index=0,
                speaker="unknown",
                date_time=datetime(
                    2026,
                    9,
                    30,
                    10,
                    0,
                    tzinfo=UTC,
                ),
                text="My internet is slow.",
            ),
        ],
    )

    result = process_conversation(
        conversation,
        INGESTION_METADATA,
    )

    assert result.quality_status == QualityStatus.INVALID
    assert result.quality_issues


def test_process_conversation_runs_resolution_classification() -> None:
    conversation = Conversation(
        conversation_id="conversation-1",
        turns=[
            ConversationTurn(
                turn_index=0,
                speaker="client",
                date_time=datetime(
                    2026,
                    9,
                    30,
                    10,
                    0,
                    tzinfo=UTC,
                ),
                text="My internet is still not working.",
            ),
        ],
    )

    result = process_conversation(
        conversation,
        INGESTION_METADATA,
    )

    assert result.resolution_status == ResolutionStatus.UNRESOLVED

def test_process_conversation_preserves_ingestion_metadata() -> None:
    conversation = Conversation(
        conversation_id="conversation-99",
        turns=[
            ConversationTurn(
                turn_index=0,
                speaker="client",
                date_time=datetime(
                    2026,
                    9,
                    30,
                    12,
                    0,
                    tzinfo=UTC,
                ),
                text="My broadband is slow.",
            ),
        ],
    )

    result = process_conversation(
        conversation,
        INGESTION_METADATA,
    )

    assert result.ingestion == INGESTION_METADATA
    assert result.ingestion.source_dataset == (
        "talkmap-telecom-conversation-corpus"
    )
    assert result.ingestion.dataset_version == "telecom_200k"
    assert result.ingestion.pipeline_version == "0.1.0"
