from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class BaseEventMessagePayload(BaseModel):
    file_id: str


class BaseEventMessage(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    producer: str

    payload: BaseEventMessagePayload