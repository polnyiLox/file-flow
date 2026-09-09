import asyncio
import logging

from aiokafka import AIOKafkaConsumer
from pydantic import ValidationError

from app.schemas.event import EventMessage
from app.core.metrics import events_processed, kafka_failures

logger = logging.getLogger(__name__)


class KafkaConsumer:
    def __init__(self, settings, repository) -> None:
        self._settings = settings
        self._repository = repository
        self._consumer = None
        self._task = None

    async def connect(self) -> None:
        self._consumer = AIOKafkaConsumer(
            self._settings.file_events_topic,
            bootstrap_servers=self._settings.bootstrap_servers,
            client_id=self._settings.client_id,
            group_id=self._settings.group_id,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )
        await self._consumer.start()
        self._task = asyncio.create_task(self.consume())

    async def handle_message(self, message) -> None:
        try:
            event = EventMessage.model_validate_json(message.value)
        except ValidationError:
            kafka_failures.inc()
            logger.exception("Invalid Kafka event partition=%s offset=%s", message.partition, message.offset)
            return
        if await self._repository.save_event(event):
            events_processed.inc()
            logger.info("Event saved event_id=%s file_id=%s", event.event_id, event.payload.file_id)

    async def consume(self) -> None:
        async for message in self._consumer:
            while True:
                try:
                    await self.handle_message(message)
                    # Save first. Redelivery is safe because event_id is unique.
                    await self._consumer.commit()
                    break
                except Exception:
                    kafka_failures.inc()
                    logger.exception("Event storage or offset commit failed; retrying")
                    await asyncio.sleep(2)

    @property
    def healthy(self) -> bool:
        return self._task is not None and not self._task.done()

    async def close(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._consumer is not None:
            await self._consumer.stop()
