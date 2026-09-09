from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EventPayload(BaseModel):
    file_id: UUID
    content_type: str | None = None
    size: int | None = Field(default=None, ge=0)
    processing_time_ms: int | None = Field(default=None, ge=0)
    thumbnail_key: str | None = None


class EventMessage(BaseModel):
    event_id: UUID
    event_type: str
    occurred_at: datetime
    producer: str
    payload: EventPayload
