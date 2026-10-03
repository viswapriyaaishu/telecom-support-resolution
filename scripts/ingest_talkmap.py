
from app.services.conversation import ConversationTurnInput
from processed import ProcessedConversation
from quality import QualityStatus as IngestionQualityStatus
from resolution import ResolutionStatus as IngestionResolutionStatus
from telecom_support_database.models.conversation import (
    QualityStatus,
    ResolutionStatus,
    Speaker,
)


def map_speaker(value: str) -> Speaker:
    normalized = value.strip().lower()

    if normalized == "client":
        return Speaker.CLIENT

    if normalized == "agent":
        return Speaker.AGENT

    raise ValueError(f"Unsupported speaker: {value!r}")


def map_quality_status(value: IngestionQualityStatus) -> QualityStatus:
    if value == IngestionQualityStatus.VALID:
        return QualityStatus.VALID

    return QualityStatus.INVALID


def map_resolution_status(
    value: IngestionResolutionStatus,
) -> ResolutionStatus:
    return ResolutionStatus(value.value)


def build_turn_inputs(
    processed: ProcessedConversation,
) -> list[ConversationTurnInput]:
    return [
        ConversationTurnInput(
            turn_index=turn.turn_index,
            speaker=map_speaker(turn.speaker),
            timestamp=turn.date_time,
            text=turn.text,
        )
        for turn in processed.conversation.turns
    ]


def build_conversation_inputs(
    processed: ProcessedConversation,
) -> dict[str, object]:
    return {
        "external_id": processed.conversation.conversation_id,
        "source_dataset": processed.ingestion.source_dataset,
        "dataset_version": processed.ingestion.dataset_version,
        "quality_status": map_quality_status(processed.quality_status),
        "resolution_status": map_resolution_status(
            processed.resolution_status
        ),
        "turns": build_turn_inputs(processed),
    }