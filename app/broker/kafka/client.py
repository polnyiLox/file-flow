from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

from app.core.config import KafkaSettings


class KafkaClient:
    def __init__(self, settings: KafkaSettings) -> None:
        self._settings = settings
        self._producer: AIOKafkaProducer | None = None
        self._consumer: AIOKafkaConsumer | None = None

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

    async def connect_consumer(self, *topics: str) -> None:
        if self._consumer is not None:
            return

        consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self._settings.bootstrap_servers,
            client_id=self._settings.client_id,
        )

        await consumer.start()

        self._consumer = consumer

    async def get_consumer(self, *topics: str) -> AIOKafkaConsumer:
        await self.connect_consumer(*topics)
        assert self._consumer is not None
        return self._consumer

    async def close_consumer(self) -> None:
        if self._consumer is not None:
            await self._consumer.stop()

        self._consumer = None

    async def connect(self) -> None:
        await self.connect_producer()
        await self.connect_consumer()

    async def close(self) -> None:
        await self.close_consumer()
        await self.close_producer()
