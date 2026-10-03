from datetime import UTC
from unittest.mock import Mock
from uuid import uuid4

import pytest
from telecom_support_database.models.ingestion import (
    IngestionRun,
    IngestionRunStatus,
)

from app.db.repositories.ingestion_run import IngestionRunRepository
from app.services.ingestion_run import IngestionRunService


@pytest.fixture
def repository() -> Mock:
    return Mock(spec=IngestionRunRepository)


@pytest.fixture
def service(repository: Mock) -> IngestionRunService:
    return IngestionRunService(repository)


@pytest.fixture
def running_run() -> IngestionRun:
    return IngestionRun(
        id=uuid4(),
        dataset_name="talkmap",
        dataset_version="v1",
        pipeline_version="0.1.0",
        status=IngestionRunStatus.RUNNING,
    )


def test_start_run_creates_running_run(
    service: IngestionRunService,
    repository: Mock,
) -> None:
    ingestion_run = IngestionRun(
    dataset_name="talkmap",
    dataset_version="v1",
    pipeline_version="0.1.0",
    status=IngestionRunStatus.RUNNING,
    )
    repository.create.return_value = ingestion_run

    result = service.start_run(
        dataset_name="talkmap",
        dataset_version="v1",
        pipeline_version="0.1.0",
    )

    assert result is ingestion_run
    assert result.status == IngestionRunStatus.RUNNING
    repository.create.assert_called_once()


def test_get_run_delegates_to_repository(
    service: IngestionRunService,
    repository: Mock,
) -> None:
    ingestion_run_id = uuid4()
    ingestion_run = IngestionRun(
        id=ingestion_run_id,
        dataset_name="talkmap",
        dataset_version="v1",
        pipeline_version="0.1.0",
    )
    repository.get_by_id.return_value = ingestion_run

    result = service.get_run(ingestion_run_id)

    assert result is ingestion_run
    repository.get_by_id.assert_called_once_with(ingestion_run_id)


def test_update_progress(
    service: IngestionRunService,
    repository: Mock,
    running_run: IngestionRun,
) -> None:
    repository.update_counters.return_value = running_run

    result = service.update_progress(
        running_run,
        records_read=100,
        records_valid=90,
        records_rejected=10,
        records_redacted=5,
        records_deduplicated=2,
    )

    assert result is running_run
    repository.update_counters.assert_called_once_with(
        running_run,
        records_read=100,
        records_valid=90,
        records_rejected=10,
        records_redacted=5,
        records_deduplicated=2,
    )


def test_complete_run_sets_status_and_completed_at(
    service: IngestionRunService,
    repository: Mock,
    running_run: IngestionRun,
) -> None:
    repository.update_status.return_value = running_run

    result = service.complete_run(running_run)

    assert result is running_run
    assert result.status == IngestionRunStatus.RUNNING
    assert result.completed_at is not None
    assert result.completed_at.tzinfo == UTC

    repository.update_status.assert_called_once_with(
        running_run,
        IngestionRunStatus.COMPLETED,
    )


def test_fail_run_sets_status_and_completed_at(
    service: IngestionRunService,
    repository: Mock,
    running_run: IngestionRun,
) -> None:
    repository.update_status.return_value = running_run

    result = service.fail_run(running_run)

    assert result is running_run
    assert result.status == IngestionRunStatus.RUNNING
    assert result.completed_at is not None
    assert result.completed_at.tzinfo == UTC

    repository.update_status.assert_called_once_with(
        running_run,
        IngestionRunStatus.FAILED,
    )


@pytest.mark.parametrize(
    ("method_name", "arguments"),
    [
        ("update_progress", {
            "records_read": 100,
            "records_valid": 90,
            "records_rejected": 10,
            "records_redacted": 5,
            "records_deduplicated": 2,
        }),
        ("complete_run", {}),
        ("fail_run", {}),
    ],
)
@pytest.mark.parametrize(
    "status",
    [
        IngestionRunStatus.COMPLETED,
        IngestionRunStatus.FAILED,
    ],
)
def test_terminal_run_cannot_be_modified(
    service: IngestionRunService,
    repository: Mock,
    method_name: str,
    arguments: dict[str, int],
    status: IngestionRunStatus,
) -> None:
    ingestion_run = IngestionRun(
        id=uuid4(),
        dataset_name="talkmap",
        dataset_version="v1",
        pipeline_version="0.1.0",
        status=status,
    )

    with pytest.raises(
        ValueError,
        match="Ingestion run must be RUNNING",
    ):
        getattr(service, method_name)(ingestion_run, **arguments)

    repository.update_counters.assert_not_called()
    repository.update_status.assert_not_called()
