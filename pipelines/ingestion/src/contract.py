from telecom_support_schemas.ingestion import (
    IngestionConversation,
    IngestionMetadata,
    IngestionTurn,
    ProcessedConversationContract,
)

from processed import ProcessedConversation


def to_contract(
    processed: ProcessedConversation,
) -> ProcessedConversationContract:
    return ProcessedConversationContract(
        conversation=IngestionConversation(
            conversation_id=processed.conversation.conversation_id,
            turns=[
                IngestionTurn(
                    turn_index=turn.turn_index,
                    speaker=turn.speaker,
                    timestamp=turn.date_time,
                    text=turn.text,
                )
                for turn in processed.conversation.turns
            ],
        ),
        ingestion=IngestionMetadata(
            source_dataset=processed.ingestion.source_dataset,
            dataset_version=processed.ingestion.dataset_version,
            pipeline_version=processed.ingestion.pipeline_version,
            ingested_at=processed.ingestion.ingested_at,
        ),
        quality_status=processed.quality_status.value,
        quality_issues=[
            issue.value for issue in processed.quality_issues
        ],
        resolution_status=processed.resolution_status.value,
        resolution_evidence=processed.resolution_evidence.value,
    )