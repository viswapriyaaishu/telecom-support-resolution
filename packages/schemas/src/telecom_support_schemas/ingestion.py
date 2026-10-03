from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IngestionTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_index: int
    speaker: str
    timestamp: datetime
    text: str


class IngestionConversation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: str
    turns: list[IngestionTurn]


class IngestionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_dataset: str
    dataset_version: str
    pipeline_version: str
    ingested_at: datetime


class ProcessedConversationContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation: IngestionConversation
    ingestion: IngestionMetadata
    quality_status: str
    quality_issues: list[str] = Field(default_factory=list)
    resolution_status: str
    resolution_evidence: str