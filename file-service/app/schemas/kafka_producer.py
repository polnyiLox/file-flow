from pydantic import Field

from .kafka_base import BaseEventMessage, BaseEventMessagePayload


class FileEventMessagePayload(BaseEventMessagePayload):
    content_type: str = Field(default="multipart/form-data")
    size: int


class FileEventMessage(BaseEventMessage):
    producer: str = Field(default="file-service")

    payload: FileEventMessagePayload