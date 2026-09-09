from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependecies import get_file_service
from app.enums import FileStatuses
from app.services import FileService

router = APIRouter(prefix="/internal/v1/files", tags=["Processing"])


class ProcessedSchema(BaseModel):
    thumbnail_key: str


@router.patch("/{file_id}/processing", status_code=204)
async def processing(file_id: UUID, service: FileService = Depends(get_file_service)) -> None:
    await service.update_file_status(str(file_id), FileStatuses.PROCESSING)


@router.patch("/{file_id}/processed", status_code=204)
async def processed(file_id: UUID, data: ProcessedSchema, service: FileService = Depends(get_file_service)) -> None:
    await service.handle_process_completed(str(file_id), data.thumbnail_key)


@router.patch("/{file_id}/failed", status_code=204)
async def failed(file_id: UUID, service: FileService = Depends(get_file_service)) -> None:
    await service.update_file_status(str(file_id), FileStatuses.FAILED)
