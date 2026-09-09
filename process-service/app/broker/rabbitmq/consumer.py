import asyncio
import logging

import aio_pika
from pydantic import ValidationError

from app.schemas.rabbitmq_consumer import ProcessCommandEvent
from app.core.metrics import rabbitmq_failures

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    def __init__(self, settings, process_service) -> None:
        self._settings = settings
        self._service = process_service
        self._connection = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._settings.url)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=self._settings.prefetch_count)
        exchange = await channel.declare_exchange(
            self._settings.exchange, aio_pika.ExchangeType.TOPIC, durable=True,
        )
        queue = await channel.declare_queue(self._settings.queue, durable=True)
        await queue.bind(exchange, self._settings.routing_key)
        await queue.consume(self.handle_message)

    async def handle_message(self, message) -> None:
        try:
            command = ProcessCommandEvent.model_validate_json(message.body)
            await self._service.process_image(command)
        except (ValidationError, ValueError):
            rabbitmq_failures.inc()
            logger.exception("Invalid processing command")
            await message.reject(requeue=False)
        except Exception:
            rabbitmq_failures.inc()
            logger.exception("Processing dependency failed; command will be retried")
            await asyncio.sleep(2)
            await message.nack(requeue=True)
        else:
            await message.ack()

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
