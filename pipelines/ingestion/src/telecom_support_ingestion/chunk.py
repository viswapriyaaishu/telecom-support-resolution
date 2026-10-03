from dataclasses import dataclass

from telecom_support_ingestion.models import Conversation


@dataclass(frozen=True)
class ConversationChunkInput:
    conversation_id: str
    chunk_index: int
    text: str


def chunk_conversation(
    conversation: Conversation,
    *,
    max_characters: int = 3500,
    overlap_characters: int = 500,
) -> list[ConversationChunkInput]:
    if max_characters <= 0:
        raise ValueError("max_characters must be greater than zero.")

    if overlap_characters < 0:
        raise ValueError("overlap_characters cannot be negative.")

    if overlap_characters >= max_characters:
        raise ValueError(
            "overlap_characters must be smaller than max_characters."
        )

    chunks: list[ConversationChunkInput] = []
    current_parts: list[str] = []
    current_length = 0

    for turn in conversation.turns:
        part = f"{turn.speaker}: {turn.text}".strip()

        if current_parts and current_length + len(part) + 1 > max_characters:
            text = "\n".join(current_parts)

            chunks.append(
                ConversationChunkInput(
                    conversation_id=conversation.conversation_id,
                    chunk_index=len(chunks),
                    text=text,
                )
            )

            overlap = text[-overlap_characters:]
            current_parts = [overlap, part]
            current_length = len(overlap) + len(part) + 1
        else:
            current_parts.append(part)
            current_length += len(part) + 1

    if current_parts:
        chunks.append(
            ConversationChunkInput(
                conversation_id=conversation.conversation_id,
                chunk_index=len(chunks),
                text="\n".join(current_parts),
            )
        )

    return chunks