import asyncio

from aiokafka import AIOKafkaProducer

from app.core.config import KafkaSettings


class KafkaClient:
    def __init__(self, settings: KafkaSettings) -> None:
        self._settings = settings
        self._producer: AIOKafkaProducer | None = None
        self._connect_lock = asyncio.Lock()

    async def connect_producer(self) -> None:
        if self._producer is not None:
            return

        producer = AIOKafkaProducer(
            bootstrap_servers=self._settings.bootstrap_servers,
            client_id=self._settings.client_id,
            acks=self._settings.acks,
        )

        await producer.start()

        self._producer = producer

    async def get_producer(self) -> AIOKafkaProducer:
        await self.connect_producer()
        assert self._producer is not None
        return self._producer

    async def close_producer(self) -> None:
        if self._producer is not None:
          await self._producer.stop()

        self._producer = None