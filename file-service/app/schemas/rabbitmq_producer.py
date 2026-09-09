from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ProcessCommandEvent(BaseModel):
    command_id: str = Field(default_factory=lambda: str(uuid4()))
    command_type: Literal["image.process"] = "image.process"
    file_id: str
    original_key: str
