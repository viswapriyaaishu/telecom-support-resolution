from enum import StrEnum

from pydantic import BaseModel, Field


class Intent(StrEnum):
    CONNECTIVITY = "Connectivity"
    MOBILE = "Mobile"
    BILLING = "Billing"
    ACCOUNT = "Account"
    OUTAGE = "Outage"
    OTHER = "Other"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class Sentiment(StrEnum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    UNKNOWN = "UNKNOWN"


class ComplaintIntelligence(BaseModel):
    intent: Intent
    sub_intent: str = Field(min_length=1)
    product: str = Field(min_length=1)
    severity: Severity
    sentiment: Sentiment
    entities: dict[str, str] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str = Field(min_length=1)