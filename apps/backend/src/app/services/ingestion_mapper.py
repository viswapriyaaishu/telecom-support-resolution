from typing import TypedDict

from telecom_support_database.models.conversation import (
    QualityStatus,
    ResolutionStatus,
    Speaker,
)
from telecom_support_schemas.ingestion import ProcessedConversationContract

from app.services.conversation import ConversationTurnInput


class ConversationInputs(TypedDict):
    external_id: str
    source_dataset: str
    dataset_version: str
    turns: list[ConversationTurnInput]
    quality_status: QualityStatus
    resolution_status: ResolutionStatus


def map_speaker(value: str) -> Speaker:
    normalized = value.strip().lower()

    if normalized == "client":
        return Speaker.CLIENT

    if normalized == "agent":
        return Speaker.AGENT

    raise ValueError(f"Unsupported speaker: {value!r}")


def map_quality_status(value: str) -> QualityStatus:
    try:
        return QualityStatus(value)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported quality status: {value!r}"
        ) from exc


def map_resolution_status(value: str) -> ResolutionStatus:
    try:
        return ResolutionStatus(value)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported resolution status: {value!r}"
        ) from exc


def build_turn_inputs(
    processed: ProcessedConversationContract,
) -> list[ConversationTurnInput]:
    return [
        ConversationTurnInput(
            turn_index=turn.turn_index,
            speaker=map_speaker(turn.speaker),
            timestamp=turn.timestamp,
            text=turn.text,
        )
        for turn in processed.conversation.turns
    ]


def build_conversation_inputs(
    processed: ProcessedConversationContract,
) -> ConversationInputs:
    return {
        "external_id": processed.conversation.conversation_id,
        "source_dataset": processed.ingestion.source_dataset,
        "dataset_version": processed.ingestion.dataset_version,
        "quality_status": map_quality_status(processed.quality_status),
        "resolution_status": map_resolution_status(
            processed.resolution_status,
        ),
        "turns": build_turn_inputs(processed),
    }