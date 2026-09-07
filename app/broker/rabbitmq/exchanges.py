from aio_pika.abc import AbstractRobustChannel, AbstractRobustExchange

from app.core.config import RabbitMQExchangesSettings


class RabbitMQExchanges:
    def __init__(
            self,
            channel: AbstractRobustChannel,
            settings: RabbitMQExchangesSettings
    ) -> None:
        self._channel = channel
        self._settings = settings

    async def declare_process_commands_exchange(self) -> AbstractRobustExchange:
        return await self._channel.declare_exchange(
            self._settings.process_service_commands_name,
            self._settings.process_service_commands_type,
            durable=True,
        )