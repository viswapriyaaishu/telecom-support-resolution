from datetime import UTC, datetime
from uuid import UUID

from telecom_support_database.models.ingestion import (
    IngestionRun,
    IngestionRunStatus,
)

from app.repositories.ingestion_run import IngestionRunRepository


class IngestionRunService:
    def __init__(self, repository: IngestionRunRepository) -> None:
        self.repository = repository

    def start_run(
        self,
        *,
        dataset_name: str,
        dataset_version: str,
        pipeline_version: str,
    ) -> IngestionRun:
        ingestion_run = IngestionRun(
            dataset_name=dataset_name,
            dataset_version=dataset_version,
            pipeline_version=pipeline_version,
            status=IngestionRunStatus.RUNNING,
        )
        return self.repository.create(ingestion_run)

    def get_run(self, ingestion_run_id: UUID) -> IngestionRun | None:
        return self.repository.get_by_id(ingestion_run_id)

    def update_progress(
        self,
        ingestion_run: IngestionRun,
        *,
        records_read: int,
        records_valid: int,
        records_rejected: int,
        records_redacted: int,
        records_deduplicated: int,
    ) -> IngestionRun:
        self._ensure_running(ingestion_run)

        return self.repository.update_counters(
            ingestion_run,
            records_read=records_read,
            records_valid=records_valid,
            records_rejected=records_rejected,
            records_redacted=records_redacted,
            records_deduplicated=records_deduplicated,
        )

    def complete_run(self, ingestion_run: IngestionRun) -> IngestionRun:
        self._ensure_running(ingestion_run)

        ingestion_run.completed_at = datetime.now(UTC)

        return self.repository.update_status(
            ingestion_run,
            IngestionRunStatus.COMPLETED,
        )

    def fail_run(self, ingestion_run: IngestionRun) -> IngestionRun:
        self._ensure_running(ingestion_run)

        ingestion_run.completed_at = datetime.now(UTC)

        return self.repository.update_status(
            ingestion_run,
            IngestionRunStatus.FAILED,
        )

    @staticmethod
    def _ensure_running(ingestion_run: IngestionRun) -> None:
        if ingestion_run.status != IngestionRunStatus.RUNNING:
            raise ValueError(
                "Ingestion run must be RUNNING for this operation."
            )