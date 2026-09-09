import logging
from pathlib import PurePath
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.broker import KafkaProducer, RabbitMQProducer
from app.cache import Cache
from app.core.s3_client import S3Client
from app.db.models import FileORM
from app.enums import FileStatuses, FileEventsContentTypesEnum
from app.exceptions import (
    FilenameMissedError, InvalidFilenameError, ForbiddenFileExtensionError,
    InvalidFileFormatError, FileORMNotFoundError, RedisNotConnectedError, S3ServiceError,
)
from app.repositories import FileRepository
from app.schemas import (
    FileReadSchema, DownloadFileSchema, ProcessCommandEvent,
    FileEventMessage, FileEventMessagePayload,
)
from app.core.metrics import files_uploaded, files_deleted, commands_published

logger = logging.getLogger(__name__)


class FileService:
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def __init__(
        self, session: AsyncSession, file_repo: FileRepository,
        s3_client: S3Client, rabbitmq_producer: RabbitMQProducer,
        redis_cache: Cache, kafka_producer: KafkaProducer,
    ) -> None:
        self._session = session
        self._file_repo = file_repo
        self._s3_client = s3_client
        self._rabbitmq_producer = rabbitmq_producer
        self._redis_cache = redis_cache
        self._kafka_producer = kafka_producer

    @classmethod
    def _verify_file(cls, file: UploadFile) -> None:
        if not file.filename:
            raise FilenameMissedError()
        if "." not in file.filename:
            raise InvalidFilenameError()
        if file.filename.rsplit(".", 1)[-1].lower() not in cls.ALLOWED_EXTENSIONS:
            raise ForbiddenFileExtensionError()
        if file.content_type not in {"image/jpeg", "image/png"}:
            raise InvalidFileFormatError("Only JPEG and PNG images are allowed")
        if file.size is not None and not 0 < file.size <= cls.MAX_FILE_SIZE:
            raise InvalidFileFormatError("File size must be between 1 byte and 10 MiB")

    async def _get_existing_file_by_id(self, file_id: str) -> FileORM:
        file = await self._file_repo.get_by_id(file_id)
        if file is None:
            raise FileORMNotFoundError()
        return file

    async def _invalidate_cache(self, file_id: str) -> None:
        try:
            await self._redis_cache.delete(f"file:{file_id}")
        except RedisNotConnectedError:
            logger.warning("Redis not connected")

    async def _publish_event(self, file: FileORM, event_type: str) -> None:
        await self._kafka_producer.publish_event(FileEventMessage(
            event_type=event_type,
            payload=FileEventMessagePayload(
                file_id=file.id, size=file.size, content_type=file.content_type,
            ),
        ))

    async def update_file_status(self, file_id: str, new_status: FileStatuses) -> None:
        file = await self._get_existing_file_by_id(file_id)
        if file.status in {FileStatuses.READY, FileStatuses.FAILED}:
            return
        file.status = new_status
        await self._session.commit()
        await self._invalidate_cache(file_id)

    async def handle_process_completed(self, file_id: str, thumbnail_key: str) -> None:
        file = await self._get_existing_file_by_id(file_id)
        if thumbnail_key != f"files/{file_id}/thumbnail.jpg":
            raise InvalidFileFormatError("Unexpected thumbnail key")
        if file.status == FileStatuses.FAILED:
            raise HTTPException(409, "File processing already failed")
        file.status = FileStatuses.READY
        file.thumbnail_key = thumbnail_key
        await self._session.commit()
        await self._invalidate_cache(file_id)

    async def upload_file(self, file: UploadFile) -> FileReadSchema:
        self._verify_file(file)
        body = await file.read(self.MAX_FILE_SIZE + 1)
        if not 0 < len(body) <= self.MAX_FILE_SIZE:
            raise InvalidFileFormatError("File size must be between 1 byte and 10 MiB")
        filename = PurePath(file.filename.replace("\\", "/")).name
        file_id = str(uuid4())
        original_key = f"files/{file_id}/original.{filename.rsplit('.', 1)[-1].lower()}"
        try:
            await self._s3_client.upload_file(body, original_key, file.content_type)
        except Exception as exc:
            logger.exception("Original upload failed file_id=%s", file_id)
            raise S3ServiceError() from exc

        try:
            file_orm = await self._file_repo.create(
                original_name=filename, content_type=file.content_type,
                size=len(body), original_key=original_key, file_id=file_id,
            )
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            await self._s3_client.delete_file(original_key)
            raise

        # The row is committed before the processor can receive the command.
        await self._publish_event(file_orm, FileEventsContentTypesEnum.FILE_UPLOADED)
        try:
            await self._rabbitmq_producer.publish_event(ProcessCommandEvent(
                file_id=file_id, original_key=original_key,
            ))
            commands_published.inc()
        except Exception:
            # A publish timeout can mean that the broker accepted the command.
            # Keep UPLOADED so a delivered command can still finish processing.
            logger.exception("Command publication failed file_id=%s", file_id)
            raise HTTPException(503, f"Command delivery uncertain; check file {file_id}")
        files_uploaded.inc()
        logger.info("File uploaded file_id=%s", file_id)
        return FileReadSchema.model_validate(file_orm)

    async def get_files_history(self, page: int, per_page: int) -> list[FileReadSchema]:
        files = await self._file_repo.get_all(offset=(page - 1) * per_page, limit=per_page)
        return [FileReadSchema.model_validate(file) for file in files]

    async def get_file_by_id(self, file_id: str) -> FileReadSchema:
        try:
            cached = await self._redis_cache.get(f"file:{file_id}")
            if cached is not None:
                return FileReadSchema.model_validate_json(cached)
        except RedisNotConnectedError:
            logger.warning("Redis not connected")
        file = FileReadSchema.model_validate(await self._get_existing_file_by_id(file_id))
        try:
            await self._redis_cache.set(f"file:{file_id}", file.model_dump_json())
        except RedisNotConnectedError:
            logger.warning("Redis not connected")
        return file

    async def download_file(self, file_id: str) -> DownloadFileSchema:
        file = await self._get_existing_file_by_id(file_id)
        return DownloadFileSchema(
            original_url=await self._s3_client.create_presigned_url(file.original_key),
            thumbnail_url=await self._s3_client.create_presigned_url(file.thumbnail_key)
            if file.thumbnail_key else None,
        )

    async def delete_file(self, file_id: str) -> None:
        file = await self._get_existing_file_by_id(file_id)
        if file.status in {FileStatuses.UPLOADED, FileStatuses.PROCESSING}:
            raise HTTPException(409, "Wait until file processing finishes")
        await self._s3_client.delete_file(file.original_key)
        if file.thumbnail_key:
            await self._s3_client.delete_file(file.thumbnail_key)
        await self._file_repo.delete(file)
        await self._session.commit()
        await self._invalidate_cache(file_id)
        await self._publish_event(file, FileEventsContentTypesEnum.FILE_DELETED)
        files_deleted.inc()
        logger.info("File deleted file_id=%s", file_id)
