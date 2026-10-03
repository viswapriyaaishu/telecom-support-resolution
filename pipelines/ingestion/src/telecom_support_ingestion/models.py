from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TalkmapRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: str
    speaker: str
    date_time: datetime
    text: str


class ConversationTurn(BaseModel):
    turn_index: int
    speaker: str
    date_time: datetime
    text: str


class Conversation(BaseModel):
    conversation_id: str
    turns: list[ConversationTurn]
