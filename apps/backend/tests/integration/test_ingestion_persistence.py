from datetime import UTC, datetime

from sqlalchemy.orm import Session
from telecom_support_database.models.conversation import (
    QualityStatus,
    ResolutionStatus,
    Speaker,
)
from telecom_support_schemas.ingestion import (
    IngestionConversation,
    IngestionMetadata,
    IngestionTurn,
    ProcessedConversationContract,
)

from app.db.repositories.conversation import ConversationRepository
from app.services.conversation import ConversationService
from app.services.ingestion_mapper import build_conversation_inputs


def test_processed_conversation_persists_to_database(
    db_session: Session,
) -> None:
    processed = ProcessedConversationContract(
        conversation=IngestionConversation(
            conversation_id="integration-ingestion-001",
            turns=[
                IngestionTurn(
                    turn_index=0,
                    speaker="client",
                    timestamp=datetime(
                        2026,
                        10,
                        3,
                        10,
                        0,
                        tzinfo=UTC,
                    ),
                    text="My broadband keeps dropping.",
                ),
                IngestionTurn(
                    turn_index=1,
                    speaker="agent",
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
            ],
        ),
        ingestion=IngestionMetadata(
            source_dataset="talkmap-test",
            dataset_version="test-v1",
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
        quality_status="VALID",
        resolution_status="RESOLVED",
        resolution_evidence="CUSTOMER_CONFIRMED",
    )

    repository = ConversationRepository(db_session)
    service = ConversationService(repository)

    service.create_with_turns(
        **build_conversation_inputs(processed),
    )

    stored = repository.get_by_external_id(
        source_dataset="talkmap-test",
        dataset_version="test-v1",
        external_id="integration-ingestion-001",
    )

    assert stored is not None
    assert stored.quality_status == QualityStatus.VALID
    assert stored.resolution_status == ResolutionStatus.RESOLVED
    assert len(stored.turns) == 2

    assert stored.turns[0].speaker == Speaker.CLIENT
    assert stored.turns[0].text == "My broadband keeps dropping."

    assert stored.turns[1].speaker == Speaker.AGENT
    assert stored.turns[1].text == "I will check the connection."