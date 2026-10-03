from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from telecom_support_database.models.ingestion import (
    IngestionRun,
    IngestionRunStatus,
)


class IngestionRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, ingestion_run_id: UUID) -> IngestionRun | None:
        statement = select(IngestionRun).where(
            IngestionRun.id == ingestion_run_id,
        )
        return self.session.scalar(statement)

    def create(self, ingestion_run: IngestionRun) -> IngestionRun:
        self.session.add(ingestion_run)
        self.session.flush()
        return ingestion_run

    def update_counters(
        self,
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

        self.session.flush()
        return ingestion_run

    def update_status(
        self,
        ingestion_run: IngestionRun,
        status: IngestionRunStatus,
    ) -> IngestionRun:
        ingestion_run.status = status
        self.session.flush()
        return ingestion_run