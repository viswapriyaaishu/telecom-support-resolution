from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from telecom_support_database.models.ingestion import (
    IngestionRun,
    IngestionRunStatus,
)
from telecom_support_schemas.ingestion import (
    IngestionConversation,
    IngestionMetadata,
    IngestionTurn,
    ProcessedConversationContract,
)

from app.db.repositories.conversation import ConversationRepository
from app.db.repositories.ingestion_run import IngestionRunRepository
from app.services.ingestion import IngestionService


def make_processed(
    *,
    conversation_id: str = "conv-001",
    quality_status: str = "VALID",
    resolution_status: str = "RESOLVED",
    redaction_applied: bool = False,
) -> ProcessedConversationContract:
    return ProcessedConversationContract(
        conversation=IngestionConversation(
            conversation_id=conversation_id,
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
                    text="My internet is not working.",
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
                    text="Please restart your router.",
                ),
            ],
        ),
        ingestion=IngestionMetadata(
            source_dataset="talkmap",
            dataset_version="v1",
            pipeline_version="v1",
            ingested_at=datetime.now(UTC),
        ),
        quality_status=quality_status,
        quality_issues=[],
        resolution_status=resolution_status,
        resolution_evidence="CUSTOMER_CONFIRMED",
        redaction_applied=redaction_applied,
    )


def make_service() -> tuple[
    IngestionService,
    MagicMock,
    MagicMock,
    MagicMock,
]:
    session = MagicMock()
    conversation_repository = MagicMock(spec=ConversationRepository)
    ingestion_run_repository = MagicMock(spec=IngestionRunRepository)

    def update_counters(
        ingestion_run: IngestionRun,
        *,
        records_read: int,
        records_valid: int,
        records_rejected: int,
        records_redacted: int,
        records_deduplicated: int,
    ) -> IngestionRun:
        ingestion_run.records_read = records_read
        ingestion_run.records_valid = records_valid
        ingestion_run.records_rejected = records_rejected
        ingestion_run.records_redacted = records_redacted
        ingestion_run.records_deduplicated = records_deduplicated
        return ingestion_run

    def update_status(
        ingestion_run: IngestionRun,
        status: IngestionRunStatus,
    ) -> IngestionRun:
        ingestion_run.status = status
        return ingestion_run

    ingestion_run_repository.update_counters.side_effect = update_counters
    ingestion_run_repository.update_status.side_effect = update_status

    service = IngestionService(
        session=session,
        conversation_repository=conversation_repository,
        ingestion_run_repository=ingestion_run_repository,
    )

    return (
        service,
        session,
        conversation_repository,
        ingestion_run_repository,
    )


def make_ingestion_run() -> IngestionRun:
    return IngestionRun(
        dataset_name="talkmap",
        dataset_version="v1",
        pipeline_version="v1",
        status=IngestionRunStatus.RUNNING,
    )


def test_ingest_persists_valid_conversation() -> None:
    (
        service,
        session,
        conversation_repository,
        ingestion_run_repository,
    ) = make_service()

    ingestion_run = make_ingestion_run()

    ingestion_run_repository.create.return_value = ingestion_run
    ingestion_run_repository.get_by_id.return_value = ingestion_run
    conversation_repository.get_by_external_id.return_value = None

    processed = make_processed()

    result = service.ingest(
        [processed],
        dataset_name="talkmap",
        dataset_version="v1",
        pipeline_version="v1",
    )

    assert result.status == IngestionRunStatus.COMPLETED
    conversation_repository.get_by_external_id.assert_called_once()
    session.commit.assert_called()
    assert ingestion_run.records_read == 1
    assert ingestion_run.records_valid == 1
    assert ingestion_run.records_rejected == 0
    assert ingestion_run.records_deduplicated == 0


def test_ingest_rejects_invalid_conversation() -> None:
    (
        service,
        session,
        conversation_repository,
        ingestion_run_repository,
    ) = make_service()

    ingestion_run = make_ingestion_run()

    ingestion_run_repository.create.return_value = ingestion_run

    processed = make_processed(quality_status="INVALID")

    result = service.ingest(
        [processed],
        dataset_name="talkmap",
        dataset_version="v1",
        pipeline_version="v1",
    )

    assert result.status == IngestionRunStatus.COMPLETED
    conversation_repository.get_by_external_id.assert_not_called()
    assert ingestion_run.records_read == 1
    assert ingestion_run.records_valid == 0
    assert ingestion_run.records_rejected == 1
    assert session.commit.call_count >= 2


def test_ingest_counts_duplicate_conversation() -> None:
    (
        service,
        session,
        conversation_repository,
        ingestion_run_repository,
    ) = make_service()

    ingestion_run = make_ingestion_run()

    ingestion_run_repository.create.return_value = ingestion_run
    conversation_repository.get_by_external_id.return_value = MagicMock()

    processed = make_processed()

    result = service.ingest(
        [processed],
        dataset_name="talkmap",
        dataset_version="v1",
        pipeline_version="v1",
    )

    assert result.status == IngestionRunStatus.COMPLETED
    assert ingestion_run.records_read == 1
    assert ingestion_run.records_valid == 1
    assert ingestion_run.records_deduplicated == 1


def test_ingest_processes_multiple_batches() -> None:
    (
        service,
        session,
        conversation_repository,
        ingestion_run_repository,
    ) = make_service()

    ingestion_run = make_ingestion_run()

    ingestion_run_repository.create.return_value = ingestion_run
    conversation_repository.get_by_external_id.return_value = None

    conversations = [
        make_processed(conversation_id="conv-001"),
        make_processed(conversation_id="conv-002"),
        make_processed(conversation_id="conv-003"),
    ]

    result = service.ingest(
        conversations,
        dataset_name="talkmap",
        dataset_version="v1",
        pipeline_version="v1",
        batch_size=2,
    )

    assert result.status == IngestionRunStatus.COMPLETED
    assert ingestion_run.records_read == 3
    assert ingestion_run.records_valid == 3
    assert conversation_repository.get_by_external_id.call_count == 3
    assert session.commit.call_count >= 3


def test_ingest_rejects_invalid_batch_size() -> None:
    service, _, _, _ = make_service()

    with pytest.raises(ValueError, match="batch_size"):
        service.ingest(
            [],
            dataset_name="talkmap",
            dataset_version="v1",
            pipeline_version="v1",
            batch_size=0,
        )


def test_ingest_marks_run_failed_when_batch_fails() -> None:
    (
        service,
        session,
        conversation_repository,
        ingestion_run_repository,
    ) = make_service()

    ingestion_run = make_ingestion_run()

    ingestion_run_repository.create.return_value = ingestion_run
    ingestion_run_repository.get_by_id.return_value = ingestion_run

    conversation_repository.get_by_external_id.side_effect = RuntimeError(
        "database failure"
    )

    processed = make_processed()

    with pytest.raises(RuntimeError, match="database failure"):
        service.ingest(
            [processed],
            dataset_name="talkmap",
            dataset_version="v1",
            pipeline_version="v1",
        )

    session.rollback.assert_called_once()
    assert ingestion_run.status == IngestionRunStatus.FAILED
    assert ingestion_run.completed_at is not None


def test_ingest_counts_redacted_conversation() -> None:
    (
        service,
        session,
        conversation_repository,
        ingestion_run_repository,
    ) = make_service()

    ingestion_run = make_ingestion_run()

    ingestion_run_repository.create.return_value = ingestion_run
    conversation_repository.get_by_external_id.return_value = None

    processed = make_processed(redaction_applied=True)

    result = service.ingest(
        [processed],
        dataset_name="talkmap",
        dataset_version="v1",
        pipeline_version="v1",
    )

    assert result.status == IngestionRunStatus.COMPLETED
    assert ingestion_run.records_read == 1
    assert ingestion_run.records_valid == 1
    assert ingestion_run.records_redacted == 1
    assert ingestion_run.records_deduplicated == 0