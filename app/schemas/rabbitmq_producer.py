from pydantic import BaseModel


class ProcessCommandEvent(BaseModel):
    file_id: str
    original_key: str