from typing import Literal
from uuid import UUID
from pydantic import BaseModel


class ProcessCommandEvent(BaseModel):
    command_id: UUID
    command_type: Literal["image.process"]
    file_id: UUID
    original_key: str
