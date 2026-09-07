import logging
from pathlib import PurePath
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.broker import RabbitMQProducer, KafkaProducer
from app.cache import Cache
from app.core.s3_client import S3Client
from app.db.models import FileORM
from app.enums import (
    FileStatuses,
    FileEventsContentTypesEnum
)
from app.exceptions import (
    ForbiddenFileExtensionError,
    FilenameMissedError,
    InvalidFilenameError,
    InvalidFileFormatError,
    FileORMNotFoundError,
    RedisNotConnectedError,
    S3ServiceError,
    RabbitMQServiceError
)
from app.repositories import FileRepository
from app.schemas import (
    FileReadSchema,
    DownloadFileSchema,
    ProcessCommandEvent,
    FileEventMessage,
    FileEventMessagePayload
)


logger = logging.getLogger(__name__)


class FileService:
    def __init__(
            self,
            session: AsyncSession,
            file_repo: FileRepository,
            s3_client: S3Client,
            rabbitmq_producer: RabbitMQProducer,
            redis_cache: Cache,
            kafka_producer: KafkaProducer  
    ) -> None:
        self._session = session
        self._file_repo = file_repo
        self._s3_client = s3_client
        self._rabbitmq_producer = rabbitmq_producer
        self._redis_cache = redis_cache
        self._kafka_producer = kafka_producer  

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    @staticmethod
    def _verify_filename(filename: str | None) -> str:
        if filename is None or len(filename) == 0:
            logger.warning("File name is None")
            raise FilenameMissedError()

        if "." not in filename:
            logger.warning("Invalid file name")
            raise InvalidFilenameError()

        return filename

    @classmethod
    def _verify_file_extension(cls, filename: str) -> None:
        extension = filename.rsplit(".", maxsplit=1)[-1].lower()

        if extension not in cls.ALLOWED_EXTENSIONS:
            logger.warning("Not allowed file extension for filename=%s", filename)
            raise ForbiddenFileExtensionError()

    @staticmethod
    def _verify_file_size(size: int | None) -> int:
        if size is None:
            logger.warning("File size is None")
            raise InvalidFileFormatError("File size cannot be None")

        return size

    @staticmethod
    def _get_filename(file: UploadFile) -> str:
        assert file.filename is not None
        return PurePath(file.filename).name

    @classmethod
    def _verify_file(cls, file: UploadFile) -> None:
        filename = cls._verify_filename(file.filename)
        cls._verify_file_extension(filename)
        cls._verify_file_size(file.size)

    @staticmethod
    def _create_original_key(file_extension: str) -> str:
        return f"files/{uuid4()}/original.{file_extension}"

    @staticmethod
    def _get_file_extension(filename: str) -> str:
        return filename.rsplit(".", maxsplit=1)[-1].lower()

    async def _get_existing_file_by_id(self, file_id: str) -> FileORM:
        file = await self._file_repo.get_by_id(file_id)
        if file is None:
            logger.warning("File with id=%s not found", file_id)
            raise FileORMNotFoundError()
        return file

    @staticmethod
    def _create_redis_key(file_id: str) -> str:
        return f"file:{file_id}"

    async def update_file_status(self, file_id: str, new_status: FileStatuses) -> None:
        logger.info(
            "Starting to update file status file id=%s, new_status=%s",
            file_id,
            new_status.value
        )

        file = await self._file_repo.get_by_id(
            file_id
        )

        if file is None:
            logger.warning(
                "File with id=%s not found while updating file status (id from s3)",
                file_id
            )
            return

        try:
            await self._redis_cache.delete(
                self._create_redis_key(file_id)
            )
        except RedisNotConnectedError:
            logger.warning("Redis not connected")

        file.status = new_status
        await self._session.commit()

        await self._kafka_producer.publish_event(
            event=FileEventMessage(
                event_type=FileEventsContentTypesEnum.FILE_STATUS_UPDATED,
                payload=FileEventMessagePayload(
                    file_id=file.id,
                    size=file.size,
                    content_type=file.content_type
                )
            )
        )

        logger.info(
            "Status of file id=%s updated to %s",
            file_id,
            new_status.value
        )

    async def handle_process_completed(self, file_id: str, thumbnail_key: str) -> None:
        logger.info(
            "Starting to handle event - file processed, file_id=%s, thumbnail_key=%s",
            file_id,
            thumbnail_key
        )

        file = await self._file_repo.get_by_id(
            file_id
        )

        if file is None:
            logger.warning("File with id=%s not found while processing event (id from s3)", file_id)
            return

        try:
            await self._redis_cache.delete(
                self._create_redis_key(file_id)
            )
        except RedisNotConnectedError:
            logger.warning("Redis not connected")

        file.status = FileStatuses.PROCESSED
        file.thumbnail_key = thumbnail_key

        await self._session.commit()

        await self._kafka_producer.publish_event(
            event=FileEventMessage(
                event_type=FileEventsContentTypesEnum.FILE_PROCESSED,
                payload=FileEventMessagePayload(
                    file_id=file_id,
                    size=file.size,
                    content_type=file.content_type
                )
            )
        )

        logger.info(
            "Event - file processed for file id=%s, completed. New thumbnail_key=%s",
            file_id,
            thumbnail_key
        )

    async def upload_file(self, file: UploadFile) -> FileReadSchema:
        logger.info("Starting to upload file, filename=%s", file.filename)

        self._verify_file(file)

        filename = self._get_filename(file)

        file_orm = await self._file_repo.create(
            original_name=filename,
            content_type=file.content_type or "application/octet-stream",
            size=file.size,
            original_key=self._create_original_key(self._get_file_extension(filename)),
        )

        await self._session.commit()

        # Сохраняем файл в s3
        try:
            await self._s3_client.upload_file(
                body=await file.read(),
                key=file_orm.original_key
            )
        except Exception as e:
            logger.error("Exception: %s during upload file to s3", e)

            await self._kafka_producer.publish_event(
                                event=FileEventMessage(
                                    event_type=FileEventsContentTypesEnum.FILE_UPLOADING_FAILED,
                                    payload=FileEventMessagePayload(
                                        file_id=file_orm.id,
                                        size=file_orm.size,
                                        content_type=file_orm.content_type
                                    )
                                )
                            )

            raise S3ServiceError()

        # Отправляем сообщение в ProcessService
        try:
            await self._rabbitmq_producer.publish_event(
                event=ProcessCommandEvent(
                    file_id=file_orm.id,
                    original_key=file_orm.original_key
                )
            )
        except Exception as e:
            logger.error(
                "Exception: %s during publishing command to process-service with original key=%s to rabbitmq",
                e,
                file_orm.original_key
            )

            await self._kafka_producer.publish_event(
                                event=FileEventMessage(
                                    event_type=FileEventsContentTypesEnum.FILE_UPLOADING_FAILED,
                                    payload=FileEventMessagePayload(
                                        file_id=file_orm.id,
                                        size=file_orm.size,
                                        content_type=file_orm.content_type
                                    )
                                )
                            )

            raise RabbitMQServiceError()

        await self._kafka_producer.publish_event(
                    event=FileEventMessage(
                        event_type=FileEventsContentTypesEnum.FILE_UPLOADED,
                        payload=FileEventMessagePayload(
                            file_id=file_orm.id,
                            size=file_orm.size,
                            content_type=file_orm.content_type
                        )
                    )
                )

        logger.info(
            "File filename=%s uploaded. File id=%s",
            file.filename,
            file_orm.original_key
        )

        return FileReadSchema.model_validate(file_orm)

    async def get_files_history(self, page: int, per_page: int) -> list[FileReadSchema]:
        logger.info(
            "Starting to get files history, page=%d, per_page=%d",
            page,
            per_page
        )

        offset = (page - 1) * per_page
        files = await self._file_repo.get_all(offset=offset, limit=per_page)

        logger.info("Got %d files for history", len(files))

        return [FileReadSchema.model_validate(file) for file in files]

    async def get_file_by_id(self, file_id: str) -> FileReadSchema:
        logger.info("Starting to get file by id=%s", file_id)

        try:
            file_cached = await self._redis_cache.get(
                self._create_redis_key(file_id)
            )
        except RedisNotConnectedError:
            logger.warning("Redis not connected")
        else:
            if file_cached is not None:
                return FileReadSchema.model_validate_json(file_cached)

        file_orm = await self._get_existing_file_by_id(file_id)
        file_read = FileReadSchema.model_validate(file_orm)

        try:
            await self._redis_cache.set(
                key=self._create_redis_key(file_id),
                value=file_read.model_dump_json()
            )
        except RedisNotConnectedError:
            logger.warning("Redis not connected")

        logger.info("File id=%s got", file_id)

        return file_read

    async def download_file(self, file_id: str) -> DownloadFileSchema:
        logger.info("Starting to download file id=%s", file_id)

        file = await self._get_existing_file_by_id(file_id)

        try:
            original_url = await self._s3_client.create_presigned_url(
                key=file.original_key
            )
            thumbnail_url = await self._s3_client.create_presigned_url(
                key=file.thumbnail_key
            ) if file.thumbnail_key else None
        except Exception as e:
            logger.error("Exception: %s during creating presigned urls", e)

            await self._kafka_producer.publish_event(
                event=FileEventMessage(
                    event_type=FileEventsContentTypesEnum.FILE_DOWNLOADING_FAILED,
                    payload=FileEventMessagePayload(
                        file_id=file.id,
                        size=file.size,
                        content_type=file.content_type
                    )
                )
            )

            raise S3ServiceError()

        await self._kafka_producer.publish_event(
            event=FileEventMessage(
                event_type=FileEventsContentTypesEnum.FILE_DOWNLOADED,
                payload=FileEventMessagePayload(
                    file_id=file.id,
                    size=file.size,
                    content_type=file.content_type
                )
            )
        )

        logger.info("File id=%s downloaded", file_id)

        return DownloadFileSchema(
            original_url=original_url,
            thumbnail_url=thumbnail_url
        )

    async def delete_file(self, file_id: str) -> None:
        logger.info("Starting to delete file id=%s", file_id)

        file = await self._get_existing_file_by_id(file_id)

        try:
            await self._redis_cache.delete(
                self._create_redis_key(file_id)
            )
        except RedisNotConnectedError:
            logger.warning("Redis not connected")

        await self._file_repo.delete(file)

        await self._session.commit()

        try:
            await self._s3_client.delete_file(
                key=file.original_key
            )
            if file.thumbnail_key:
                await self._s3_client.delete_file(
                    key=file.thumbnail_key
                )
        except Exception as e:
            logger.error("Exception: %s during deleting file from s3", e)

            await self._kafka_producer.publish_event(
                event=FileEventMessage(
                    event_type=FileEventsContentTypesEnum.FILE_DELETING_FAILED,
                    payload=FileEventMessagePayload(
                        file_id=file.id,
                        size=file.size,
                        content_type=file.content_type
                    )
                )
            )

            raise S3ServiceError()

        await self._kafka_producer.publish_event(
            event=FileEventMessage(
                event_type=FileEventsContentTypesEnum.FILE_DELETED,
                payload=FileEventMessagePayload(
                    file_id=file.id,
                    size=file.size,
                    content_type=file.content_type
                )
            )
        )

        logger.info("File id=%s deleted", file_id)
