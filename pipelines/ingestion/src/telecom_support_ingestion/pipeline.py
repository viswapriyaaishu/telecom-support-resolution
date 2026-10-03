from collections.abc import Iterator
from pathlib import Path

from .loader import iter_conversations, load_talkmap_rows
from .models import Conversation
from .normalize import normalize_text
from .processed import IngestionMetadata, ProcessedConversation
from .quality import validate_conversation
from .redact import redact_sensitive_data
from .resolution import classify_resolution


def process_conversation(
    conversation: Conversation,
    ingestion: IngestionMetadata,
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
        ingestion=ingestion,
        quality_status=quality_status,
        quality_issues=quality_issues,
        resolution_status=resolution_status,
        resolution_evidence=resolution_evidence,
    )


def process_talkmap_file(
    path: Path,
    ingestion: IngestionMetadata,
) -> Iterator[ProcessedConversation]:
    rows = load_talkmap_rows(path)
    conversations = iter_conversations(rows)

    for conversation in conversations:
        yield process_conversation(conversation, ingestion)
