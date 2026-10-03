import argparse
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.repositories.conversation import ConversationRepository
from app.db.repositories.ingestion_run import IngestionRunRepository
from app.db.session import SessionLocal
from app.services.ingestion import IngestionService
from telecom_support_ingestion.contract import to_contract
from telecom_support_ingestion.pipeline import process_talkmap_file
from telecom_support_ingestion.processed import IngestionMetadata
from telecom_support_schemas.ingestion import ProcessedConversationContract


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest Talkmap telecom conversations."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=PROJECT_ROOT / "data" / "raw" / "telecom_200k.csv",
        help="Path to the Talkmap CSV file.",
    )
    parser.add_argument(
        "--dataset-version",
        default="talkmap-v1",
        help="Version identifier for the source dataset.",
    )
    parser.add_argument(
        "--pipeline-version",
        default="0.1.0",
        help="Version identifier for the ingestion pipeline.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of conversations persisted per batch.",
    )
    return parser.parse_args()


def track_progress(
    contracts: Iterable[ProcessedConversationContract],
    *,
    interval: int = 1_000,
) -> Iterable[ProcessedConversationContract]:
    count = 0

    for contract in contracts:
        yield contract
        count += 1

        if count % interval == 0:
            print(f"Processed conversations: {count:,}")


def ingest_with_session(
    session: Session,
    contracts: Iterable[ProcessedConversationContract],
    *,
    dataset_version: str,
    pipeline_version: str,
    batch_size: int,
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
        dataset_version=dataset_version,
        pipeline_version=pipeline_version,
        batch_size=batch_size,
    )

    print(f"Ingestion completed: {run.id}")
    print(f"Records read: {run.records_read}")
    print(f"Records valid: {run.records_valid}")
    print(f"Records rejected: {run.records_rejected}")
    print(f"Records redacted: {run.records_redacted}")
    print(f"Records deduplicated: {run.records_deduplicated}")


def main() -> None:
    args = parse_args()

    dataset_path = args.dataset
    if not dataset_path.is_absolute():
        dataset_path = PROJECT_ROOT / dataset_path

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}"
        )

    if args.batch_size <= 0:
        raise ValueError("batch-size must be greater than zero.")

    ingestion_metadata = IngestionMetadata(
        source_dataset="talkmap",
        dataset_version=args.dataset_version,
        pipeline_version=args.pipeline_version,
        ingested_at=datetime.now(UTC),
    )

    processed_conversations = process_talkmap_file(
        dataset_path,
        ingestion_metadata,
    )

    contracts = track_progress(
        (
            to_contract(processed)
            for processed in processed_conversations
        )
    )

    print("Starting Talkmap ingestion...")
    print(f"Dataset: {dataset_path}")
    print(f"Dataset version: {args.dataset_version}")
    print(f"Batch size: {args.batch_size}")

    with SessionLocal() as session:
        ingest_with_session(
            session,
            contracts,
            dataset_version=args.dataset_version,
            pipeline_version=args.pipeline_version,
            batch_size=args.batch_size,
        )


if __name__ == "__main__":
    main()