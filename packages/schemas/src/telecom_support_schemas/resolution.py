from pydantic import BaseModel, Field


class ResolutionCitation(BaseModel):
    source_id: str = Field(min_length=1)
    section: str | None = None


class ResolutionResponse(BaseModel):
    summary: str = Field(min_length=1)
    diagnosis: str = Field(min_length=1)
    recommended_steps: list[str] = Field(min_length=1)
    escalation_required: bool
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[ResolutionCitation] = Field(default_factory=list)