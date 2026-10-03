from datetime import UTC, datetime

import pytest
from app.services.conversation import ConversationTurnInput
from models import Conversation, ConversationTurn
from processed import IngestionMetadata, ProcessedConversation
from quality import QualityStatus as IngestionQualityStatus
from resolution import (
    ResolutionEvidence,
)
from resolution import (
    ResolutionStatus as IngestionResolutionStatus,
)
from telecom_support_database.models.conversation import (
    QualityStatus,
    ResolutionStatus,
    Speaker,
)

from scripts.ingest_talkmap import (
    build_conversation_inputs,
    build_turn_inputs,
    map_quality_status,
    map_resolution_status,
    map_speaker,
)


def test_map_speaker_maps_supported_values() -> None:
    assert map_speaker("client") == Speaker.CLIENT
    assert map_speaker("CLIENT") == Speaker.CLIENT
    assert map_speaker("agent") == Speaker.AGENT
    assert map_speaker(" AGENT ") == Speaker.AGENT


def test_map_speaker_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="Unsupported speaker"):
        map_speaker("unknown")


def test_map_quality_status() -> None:
    assert (
        map_quality_status(IngestionQualityStatus.VALID)
        == QualityStatus.VALID
    )
    assert (
        map_quality_status(IngestionQualityStatus.INVALID)
        == QualityStatus.INVALID
    )


def test_map_resolution_status() -> None:
    assert (
        map_resolution_status(IngestionResolutionStatus.RESOLVED)
        == ResolutionStatus.RESOLVED
    )
    assert (
        map_resolution_status(IngestionResolutionStatus.UNRESOLVED)
        == ResolutionStatus.UNRESOLVED
    )


def test_build_turn_inputs() -> None:
    processed = ProcessedConversation(
        conversation=Conversation(
            conversation_id="conversation-001",
            turns=[
                ConversationTurn(
                    turn_index=0,
                    speaker="client",
                    date_time=datetime(
                        2026,
                        10,
                        3,
                        10,
                        0,
                        tzinfo=UTC,
                    ),
                    text="My internet keeps dropping.",
                ),
                ConversationTurn(
                    turn_index=1,
                    speaker="agent",
                    date_time=datetime(
                        2026,
                        10,
                        3,
                        10,
                        1,
                        tzinfo=UTC,
                    ),
                    text="I will check the connection.",
                ),
            ],
        ),
        ingestion=IngestionMetadata(
            source_dataset="talkmap-telecom-conversation-corpus",
            dataset_version="telecom_200k",
            pipeline_version="0.1.0",
            ingested_at=datetime(
                2026,
                10,
                3,
                10,
                0,
                tzinfo=UTC,
            ),
        ),
        quality_status=IngestionQualityStatus.VALID,
        resolution_status=IngestionResolutionStatus.RESOLVED,
        resolution_evidence=ResolutionEvidence.CUSTOMER_CONFIRMED,
    )

    result = build_turn_inputs(processed)

    assert result == [
        ConversationTurnInput(
            turn_index=0,
            speaker=Speaker.CLIENT,
            timestamp=datetime(
                2026,
                10,
                3,
                10,
                0,
                tzinfo=UTC,
            ),
            text="My internet keeps dropping.",
        ),
        ConversationTurnInput(
            turn_index=1,
            speaker=Speaker.AGENT,
            timestamp=datetime(
                2026,
                10,
                3,
                10,
                1,
                tzinfo=UTC,
            ),
            text="I will check the connection.",
        ),
    ]


def test_build_conversation_inputs() -> None:
    processed = ProcessedConversation(
        conversation=Conversation(
            conversation_id="conversation-001",
            turns=[],
        ),
        ingestion=IngestionMetadata(
            source_dataset="talkmap-telecom-conversation-corpus",
            dataset_version="telecom_200k",
            pipeline_version="0.1.0",
            ingested_at=datetime(
                2026,
                10,
                3,
                10,
                0,
                tzinfo=UTC,
            ),
        ),
        quality_status=IngestionQualityStatus.VALID,
        resolution_status=IngestionResolutionStatus.RESOLVED,
        resolution_evidence=ResolutionEvidence.CUSTOMER_CONFIRMED,
    )

    result = build_conversation_inputs(processed)

    assert result["external_id"] == "conversation-001"
    assert result["source_dataset"] == "talkmap-telecom-conversation-corpus"
    assert result["dataset_version"] == "telecom_200k"
    assert result["quality_status"] == QualityStatus.VALID
    assert result["resolution_status"] == ResolutionStatus.RESOLVED
    assert result["turns"] == []