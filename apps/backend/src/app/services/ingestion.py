from collections.abc import Iterable

from sqlalchemy.orm import Session
from telecom_support_database.models.ingestion import IngestionRun
from telecom_support_schemas.ingestion import ProcessedConversationContract

from app.db.repositories.conversation import ConversationRepository
from app.db.repositories.ingestion_run import IngestionRunRepository
from app.services.conversation import ConversationService
from app.services.ingestion_mapper import build_conversation_inputs
from app.services.ingestion_run import IngestionRunService


class IngestionService:
    def __init__(
        self,
        session: Session,
        conversation_repository: ConversationRepository,
        ingestion_run_repository: IngestionRunRepository,
    ) -> None:
        self.session = session
        self.conversation_service = ConversationService(
            conversation_repository,
        )
        self.ingestion_run_service = IngestionRunService(
            ingestion_run_repository,
        )
        self.conversation_repository = conversation_repository

    def ingest(
        self,
        conversations: Iterable[ProcessedConversationContract],
        *,
        dataset_name: str,
        dataset_version: str,
        pipeline_version: str,
        batch_size: int = 100,
    ) -> IngestionRun:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")

        ingestion_run = self.ingestion_run_service.start_run(
            dataset_name=dataset_name,
            dataset_version=dataset_version,
            pipeline_version=pipeline_version,
        )

        self.session.commit()

        records_read = 0
        records_valid = 0
        records_rejected = 0
        records_redacted = 0
        records_deduplicated = 0

        batch: list[ProcessedConversationContract] = []

        try:
            for processed in conversations:
                batch.append(processed)

                if len(batch) >= batch_size:
                    (
                        records_read,
                        records_valid,
                        records_rejected,
                        records_redacted,
                        records_deduplicated,
                    ) = self._process_batch(
                        batch,
                        records_read=records_read,
                        records_valid=records_valid,
                        records_rejected=records_rejected,
                        records_redacted=records_redacted,
                        records_deduplicated=records_deduplicated,
                        ingestion_run=ingestion_run,
                    )

                    self.session.commit()
                    batch.clear()

            if batch:
                (
                    records_read,
                    records_valid,
                    records_rejected,
                    records_redacted,
                    records_deduplicated,
                ) = self._process_batch(
                    batch,
                    records_read=records_read,
                    records_valid=records_valid,
                    records_rejected=records_rejected,
                    records_redacted=records_redacted,
                    records_deduplicated=records_deduplicated,
                    ingestion_run=ingestion_run,
                )

                self.session.commit()

            self.ingestion_run_service.complete_run(ingestion_run)
            self.session.commit()

            return ingestion_run

        except Exception:
            self.session.rollback()

            failed_run = self.ingestion_run_service.get_run(
                ingestion_run.id,
            )

            if failed_run is not None:
                self.ingestion_run_service.fail_run(failed_run)
                self.session.commit()

            raise

    def _process_batch(
        self,
        batch: list[ProcessedConversationContract],
        *,
        records_read: int,
        records_valid: int,
        records_rejected: int,
        records_redacted: int,
        records_deduplicated: int,
        ingestion_run: IngestionRun,
    ) -> tuple[int, int, int, int, int]:
        for processed in batch:
            records_read += 1

            if processed.quality_status != "VALID":
                records_rejected += 1
                continue

            records_valid += 1

            if processed.redaction_applied:
                records_redacted += 1

            existing = self.conversation_repository.get_by_external_id(
                source_dataset=processed.ingestion.source_dataset,
                dataset_version=processed.ingestion.dataset_version,
                external_id=processed.conversation.conversation_id,
            )

            if existing is not None:
                records_deduplicated += 1
                continue

            inputs = build_conversation_inputs(processed)

            self.conversation_service.create_with_turns(
                **inputs,
            )

        self.ingestion_run_service.update_progress(
            ingestion_run,
            records_read=records_read,
            records_valid=records_valid,
            records_rejected=records_rejected,
            records_redacted=records_redacted,
            records_deduplicated=records_deduplicated,
        )

        return (
            records_read,
            records_valid,
            records_rejected,
            records_redacted,
            records_deduplicated,
        )