from pydantic import Field

from .kafka_base import BaseEventMessage, BaseEventMessagePayload


class ProcessorEventMessagePayload(BaseEventMessagePayload):
    processing_time_ms: int
    thumbnail_key: str | None = None


class ProcessorEventMessage(BaseEventMessage):
    producer: str = Field(default="processor-service")

    payload: ProcessorEventMessagePayload