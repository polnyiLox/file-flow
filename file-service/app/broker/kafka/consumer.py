import json
import logging

from pydantic import ValidationError

from app.core.config import KafkaSettings
from app.enums import ProcessorEventTypes, FileStatuses
from app.exceptions import AppError
from app.schemas import ProcessorEventMessage
from app.services import FileService

from .client import KafkaClient


logger = logging.getLogger(__name__)


class KafkaConsumer:
    def __init__(
            self,
            kafka_client: KafkaClient,
            settings: KafkaSettings,
            file_service: FileService,
    ) -> None:
        self._kafka_client = kafka_client
        self._settings = settings
        self._file_service = file_service

    async def start_consuming(self) -> None:
        consumer = await self._kafka_client.get_consumer(
            self._settings.processor_events_topic
        )

        async for message in consumer:
            try:
                event = ProcessorEventMessage.model_validate(json.loads(message.value.decode()))
            except ValidationError:
                logger.exception(
                    "Message from kafka is not in correct format: %s",
                    message.value.decode()
                )
                raise AppError()
            else:
                if event.event_type == ProcessorEventTypes.PROCESSING_STARTED:
                    await (self._file_service.update_file_status(
                        file_id=event.payload.file_id,
                        new_status=FileStatuses.PROCESSING,
                    ))
                elif event.event_type == ProcessorEventTypes.PROCESSING_COMPLETED:
                    if event.payload.thumbnail_key is None:
                        logger.warning(
                            "Thumbnail key not found in payload: %s for message - process completed",
                            event.payload.thumbnail_key
                        )
                        await self._file_service.update_file_status(
                            file_id=event.payload.file_id,
                            new_status=FileStatuses.READY,
                        )
                    else:
                        await self._file_service.handle_process_completed(
                            file_id=event.payload.file_id,
                            thumbnail_key=event.payload.thumbnail_key,
                        )
                elif event.event_type == ProcessorEventTypes.PROCESSING_FAILED:
                    await self._file_service.update_file_status(
                        file_id=event.payload.file_id,
                        new_status=FileStatuses.FAILED,
                    )
