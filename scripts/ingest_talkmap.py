from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from app.db.repositories.conversation import ConversationRepository
from app.db.repositories.ingestion_run import IngestionRunRepository
from app.db.session import SessionLocal
from app.services.ingestion import IngestionService
from sqlalchemy.orm import Session
from telecom_support_ingestion.contract import to_contract
from telecom_support_ingestion.pipeline import process_talkmap_file
from telecom_support_ingestion.processed import IngestionMetadata
from telecom_support_schemas.ingestion import ProcessedConversationContract

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def ingest_with_session(
    session: Session,
    contracts: Iterable[ProcessedConversationContract],
) -> None:
    conversation_repository = ConversationRepository(session)
    ingestion_run_repository = IngestionRunRepository(session)

    service = IngestionService(
        session=session,
        conversation_repository=conversation_repository,
        ingestion_run_repository=ingestion_run_repository,
    )

    run = service.ingest(
        contracts,
        dataset_name="talkmap",
        dataset_version="sample-v1",
        pipeline_version="0.1.0",
        batch_size=100,
    )

    print(f"Ingestion completed: {run.id}")
    print(f"Records read: {run.records_read}")
    print(f"Records valid: {run.records_valid}")
    print(f"Records rejected: {run.records_rejected}")
    print(f"Records deduplicated: {run.records_deduplicated}")


def main() -> None:
    dataset_path = (
        PROJECT_ROOT
        / "pipelines"
        / "ingestion"
        / "tests"
        / "fixtures"
        / "talkmap_sample.csv"
    )

    ingestion_metadata = IngestionMetadata(
        source_dataset="talkmap",
        dataset_version="sample-v1",
        pipeline_version="0.1.0",
        ingested_at=datetime.now(UTC),
    )

    processed_conversations = process_talkmap_file(
        dataset_path,
        ingestion_metadata,
    )

    contracts = (
        to_contract(processed)
        for processed in processed_conversations
    )

    with SessionLocal() as session:
        ingest_with_session(session, contracts)


if __name__ == "__main__":
    main()