from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    status,
    Query
)

from app.api.dependecies import get_file_service
from app.schemas import FileReadSchema, DownloadFileSchema
from app.services import FileService

router = APIRouter(
    prefix="/files",
    tags=["Файлы"]
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=FileReadSchema
)
async def upload_file(
        file: UploadFile,
        file_service: FileService = Depends(get_file_service),
) -> FileReadSchema:
    return await file_service.upload_file(file)


@router.get("", response_model=list[FileReadSchema])
async def get_files_history(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(10, ge=1, le=100, description="Page size"),
        file_service: FileService = Depends(get_file_service),
) -> list[FileReadSchema]:
    return await file_service.get_files_history(page, page_size)


@router.get("/{file_id}", response_model=FileReadSchema)
async def get_file(
        file_id: str,
        file_service: FileService = Depends(get_file_service)
) -> FileReadSchema:
    return await file_service.get_file_by_id(file_id)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
        file_id: str,
        file_service: FileService = Depends(get_file_service)
) -> None:
    await file_service.delete_file(file_id)


@router.get("/{file_id}/download", response_model=DownloadFileSchema)
async def download_file(
        file_id: str,
        file_service: FileService = Depends(get_file_service)
) -> DownloadFileSchema:
    return await file_service.download_file(file_id)
