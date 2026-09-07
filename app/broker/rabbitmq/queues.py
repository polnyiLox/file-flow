from aio_pika.abc import AbstractRobustChannel, AbstractRobustQueue, AbstractRobustExchange

from app.core.config import RabbitMQRoutingKeysSettings, RabbitMQQueueSettings


class RabbitMQQueues:
    def __init__(
            self,
            channel: AbstractRobustChannel,
            queue_settings: RabbitMQQueueSettings,
            routing_keys_settings: RabbitMQRoutingKeysSettings
    ) -> None:
        self._channel = channel
        self._queue_settings = queue_settings
        self._routing_keys_settings = routing_keys_settings

    async def declare_process_file_queue(
            self,
            process_commands_exchange: AbstractRobustExchange
    ) -> AbstractRobustQueue:
        queue = await self._channel.declare_queue(
            self._queue_settings.process_file_queue
        )

        await queue.bind(
            exchange=process_commands_exchange,
            routing_key=self._routing_keys_settings.process_file_routing_keys
        )

        return queue