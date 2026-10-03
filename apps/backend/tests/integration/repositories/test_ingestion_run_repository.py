from uuid import uuid4

from sqlalchemy.orm import Session
from telecom_support_database.models.ingestion import (
    IngestionRun,
    IngestionRunStatus,
)

from app.db.repositories.ingestion_run import IngestionRunRepository


def test_create_returns_persisted_ingestion_run(
    db_session: Session,
) -> None:
    repository = IngestionRunRepository(db_session)

    ingestion_run = IngestionRun(
        dataset_name="talkmap",
        dataset_version="v1",
        pipeline_version="0.1.0",
    )

    result = repository.create(ingestion_run)

    assert result.id is not None
    assert result.status == IngestionRunStatus.RUNNING
    assert result.dataset_name == "talkmap"


def test_get_by_id_returns_ingestion_run(
    db_session: Session,
) -> None:
    repository = IngestionRunRepository(db_session)

    ingestion_run = IngestionRun(
        dataset_name="talkmap",
        dataset_version="v1",
        pipeline_version="0.1.0",
    )
    repository.create(ingestion_run)

    result = repository.get_by_id(ingestion_run.id)

    assert result is ingestion_run


def test_get_by_id_returns_none_for_missing_run(
    db_session: Session,
) -> None:
    repository = IngestionRunRepository(db_session)

    result = repository.get_by_id(uuid4())

    assert result is None


def test_update_counters(
    db_session: Session,
) -> None:
    repository = IngestionRunRepository(db_session)

    ingestion_run = IngestionRun(
        dataset_name="talkmap",
        dataset_version="v1",
        pipeline_version="0.1.0",
    )
    repository.create(ingestion_run)

    result = repository.update_counters(
        ingestion_run,
        records_read=100,
        records_valid=90,
        records_rejected=10,
        records_redacted=5,
        records_deduplicated=2,
    )

    assert result.records_read == 100
    assert result.records_valid == 90
    assert result.records_rejected == 10
    assert result.records_redacted == 5
    assert result.records_deduplicated == 2


def test_update_status(
    db_session: Session,
) -> None:
    repository = IngestionRunRepository(db_session)

    ingestion_run = IngestionRun(
        dataset_name="talkmap",
        dataset_version="v1",
        pipeline_version="0.1.0",
    )
    repository.create(ingestion_run)

    result = repository.update_status(
        ingestion_run,
        IngestionRunStatus.COMPLETED,
    )

    assert result.status == IngestionRunStatus.COMPLETED
