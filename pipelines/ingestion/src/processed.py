from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models import Conversation
from quality import QualityIssue, QualityStatus
from resolution import ResolutionEvidence, ResolutionStatus


class IngestionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_dataset: str
    dataset_version: str
    pipeline_version: str
    ingested_at: datetime


class ProcessedConversation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation: Conversation
    ingestion: IngestionMetadata
    quality_status: QualityStatus
    quality_issues: list[QualityIssue] = Field(default_factory=list)
    resolution_status: ResolutionStatus
    resolution_evidence: ResolutionEvidence