import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel

from app.core.config import RabbitMQConnectionSettings


class RabbitMQClient:
    def __init__(
            self,
            settings: RabbitMQConnectionSettings
    ) -> None:
        self._settings = settings
        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractRobustChannel | None = None

    async def connect(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            return

        connection = await aio_pika.connect_robust(
            url=self._settings.url
        )

        self._channel = await connection.channel()
        self._connection = connection

    async def get_channel(self) -> AbstractRobustChannel:
        await self.connect()
        assert self._channel is not None
        return self._channel

    async def close(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()

        self._connection = None
        self._channel = None