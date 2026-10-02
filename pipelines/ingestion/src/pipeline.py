from collections.abc import Iterator
from pathlib import Path

from loader import iter_conversations, load_talkmap_rows
from models import Conversation
from normalize import normalize_text
from quality import QualityIssue, QualityStatus, validate_conversation
from redact import redact_sensitive_data
from resolution import ResolutionEvidence, ResolutionStatus, classify_resolution


class ProcessedConversation:
    def __init__(
        self,
        *,
        conversation: Conversation,
        quality_status: QualityStatus,
        quality_issues: list[QualityIssue],
        resolution_status: ResolutionStatus,
        resolution_evidence: ResolutionEvidence,
    ) -> None:
        self.conversation = conversation
        self.quality_status = quality_status
        self.quality_issues = quality_issues
        self.resolution_status = resolution_status
        self.resolution_evidence = resolution_evidence


def process_conversation(
    conversation: Conversation,
) -> ProcessedConversation:
    normalized_turns = []

    for turn in conversation.turns:
        normalized_text = normalize_text(turn.text)

        redacted_text = redact_sensitive_data(normalized_text)

        normalized_turns.append(
            turn.model_copy(
                update={"text": redacted_text},
            )
        )

    processed_conversation = conversation.model_copy(
        update={"turns": normalized_turns},
    )

    quality_status, quality_issues = validate_conversation(
        processed_conversation,
    )

    resolution_status, resolution_evidence = classify_resolution(
        processed_conversation,
    )

    return ProcessedConversation(
        conversation=processed_conversation,
        quality_status=quality_status,
        quality_issues=quality_issues,
        resolution_status=resolution_status,
        resolution_evidence=resolution_evidence,
    )


def process_talkmap_file(
    path: Path,
) -> Iterator[ProcessedConversation]:
    rows = load_talkmap_rows(path)
    conversations = iter_conversations(rows)

    for conversation in conversations:
        yield process_conversation(conversation)