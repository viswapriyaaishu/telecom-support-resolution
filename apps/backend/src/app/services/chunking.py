from dataclasses import dataclass

from sqlalchemy.orm import Session

from telecom_support_database.models.chunk import ConversationChunk

from app.db.repositories.chunk import ChunkRepository
from telecom_support_ingestion.chunk import chunk_conversation
from telecom_support_ingestion.models import Conversation as IngestionConversation
from telecom_support_ingestion.models import ConversationTurn as IngestionTurn


@dataclass(frozen=True)
class ChunkingResult:
    conversations_processed: int
    chunks_created: int


class ChunkingService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = ChunkRepository(session)

    def process(
        self,
        *,
        source_dataset: str,
        dataset_version: str,
        batch_size: int = 100,
        max_characters: int = 3500,
        overlap_characters: int = 500,
        max_conversations: int | None = None,
    ) -> ChunkingResult:
        conversations_processed = 0
        chunks_created = 0

        for batch in self.repository.stream_conversations(
            source_dataset=source_dataset,
            dataset_version=dataset_version,
            batch_size=batch_size,
        ):
            db_chunks: list[ConversationChunk] = []

            for conversation in batch:
                if (
                    max_conversations is not None
                    and conversations_processed >= max_conversations
                ):
                    break

                ingestion_conversation = IngestionConversation(
                    conversation_id=str(conversation.id),
                    turns=[
                        IngestionTurn(
                            turn_index=turn.turn_index,
                            speaker=turn.speaker.value,
                            date_time=turn.timestamp,
                            text=turn.text,
                        )
                        for turn in conversation.turns
                    ],
                )

                chunks = chunk_conversation(
                    ingestion_conversation,
                    max_characters=max_characters,
                    overlap_characters=overlap_characters,
                )

                db_chunks.extend(
                    ConversationChunk(
                        conversation_id=conversation.id,
                        chunk_index=chunk.chunk_index,
                        text=chunk.text,
                    )
                    for chunk in chunks
                )

                conversations_processed += 1
                chunks_created += len(chunks)

            if db_chunks:
                self.repository.create_many(db_chunks)
                self.session.commit()

                print(
                    f"Chunked conversations: "
                    f"{conversations_processed:,} | "
                    f"chunks created: {chunks_created:,}"
                )

            if (
                max_conversations is not None
                and conversations_processed >= max_conversations
            ):
                break

        return ChunkingResult(
            conversations_processed=conversations_processed,
            chunks_created=chunks_created,
        )