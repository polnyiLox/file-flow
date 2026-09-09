from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import FileStatuses


class FileReadSchema(BaseModel):
    id: str
    original_name: str
    content_type: str
    size: int

    original_key: str
    thumbnail_key: str | None

    status: FileStatuses

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class DownloadFileSchema(BaseModel):
    original_url: str
    thumbnail_url: str | None = None
