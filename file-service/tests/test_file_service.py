from datetime import datetime, timezone
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from dotenv import load_dotenv
load_dotenv(".env.example", override=True)

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.enums import FileStatuses
from app.exceptions import InvalidFileFormatError, FileORMNotFoundError
from app.services.file import FileService


def make_file(status=FileStatuses.UPLOADED):
    return SimpleNamespace(
        id=str(uuid4()), original_name="image.png", content_type="image/png", size=8,
        original_key="files/original.png", thumbnail_key=None, status=status,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def service():
    return FileService(AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock())


@pytest.mark.asyncio
async def test_upload_persists_before_command(service):
    order = []
    async def create(**kwargs):
        file = make_file()
        file.id = kwargs["file_id"]
        file.original_key = kwargs["original_key"]
        return file
    service._file_repo.create.side_effect = create
    service._session.commit.side_effect = lambda: order.append("commit")
    service._rabbitmq_producer.publish_event.side_effect = lambda event: order.append("command")
    upload = UploadFile(BytesIO(b"png data"), filename="photo.png", size=8, headers=Headers({"content-type": "image/png"}))
    result = await service.upload_file(upload)
    assert order == ["commit", "command"]
    assert result.original_key == f"files/{result.id}/original.png"
    service._s3_client.upload_file.assert_awaited_once_with(b"png data", result.original_key, "image/png")


@pytest.mark.asyncio
async def test_rejects_oversize_even_with_incorrect_declared_size(service):
    upload = UploadFile(BytesIO(b"x" * (FileService.MAX_FILE_SIZE + 1)), filename="x.png", size=1, headers=Headers({"content-type": "image/png"}))
    with pytest.raises(InvalidFileFormatError):
        await service.upload_file(upload)
    service._s3_client.upload_file.assert_not_awaited()


@pytest.mark.asyncio
async def test_processed_invalidates_cache_after_commit(service):
    file = make_file()
    service._file_repo.get_by_id.return_value = file
    order = []
    service._session.commit.side_effect = lambda: order.append("commit")
    service._redis_cache.delete.side_effect = lambda key: order.append("invalidate")
    await service.handle_process_completed(file.id, f"files/{file.id}/thumbnail.jpg")
    assert file.status == FileStatuses.READY
    assert order == ["commit", "invalidate"]
    service._kafka_producer.publish_event.assert_not_awaited()


@pytest.mark.asyncio
async def test_late_processing_callback_does_not_reset_ready(service):
    file = make_file(FileStatuses.READY)
    service._file_repo.get_by_id.return_value = file
    await service.update_file_status(file.id, FileStatuses.PROCESSING)
    assert file.status == FileStatuses.READY


@pytest.mark.asyncio
async def test_missing_callback_returns_not_found(service):
    service._file_repo.get_by_id.return_value = None
    with pytest.raises(FileORMNotFoundError):
        await service.update_file_status(str(uuid4()), FileStatuses.PROCESSING)


@pytest.mark.asyncio
async def test_cache_hit_does_not_query_database(service):
    from app.schemas import FileReadSchema
    file = make_file()
    service._redis_cache.get.return_value = FileReadSchema.model_validate(file).model_dump_json()
    assert (await service.get_file_by_id(file.id)).id == file.id
    service._file_repo.get_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_removes_both_objects(service):
    file = make_file(FileStatuses.READY)
    file.thumbnail_key = f"files/{file.id}/thumbnail.jpg"
    service._file_repo.get_by_id.return_value = file
    await service.delete_file(file.id)
    assert service._s3_client.delete_file.await_count == 2
    service._redis_cache.delete.assert_awaited_once_with(f"file:{file.id}")


@pytest.mark.asyncio
async def test_delete_during_processing_is_rejected(service):
    service._file_repo.get_by_id.return_value = make_file(FileStatuses.PROCESSING)
    with pytest.raises(HTTPException) as exc:
        await service.delete_file(str(uuid4()))
    assert exc.value.status_code == 409
    service._s3_client.delete_file.assert_not_awaited()


@pytest.mark.asyncio
async def test_failed_database_insert_cleans_original(service):
    service._file_repo.create.side_effect = RuntimeError("database unavailable")
    upload = UploadFile(BytesIO(b"data"), filename="x.png", size=4, headers=Headers({"content-type": "image/png"}))
    with pytest.raises(RuntimeError):
        await service.upload_file(upload)
    service._session.rollback.assert_awaited_once()
    service._s3_client.delete_file.assert_awaited_once()
