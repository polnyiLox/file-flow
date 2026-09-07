from app.broker.kafka.client import KafkaClient
from app.core.config import KafkaSettings
from app.schemas.kafka_producer import FileEventMessage


class KafkaProducer:
    def __init__(
            self,
            kafka_client: KafkaClient,
            settings: KafkaSettings
    ) -> None:
        self._kafka_client = kafka_client
        self._settings = settings

    async def publish_event(
            self,
            event: FileEventMessage,
            topic: str | None = None
    ) -> None:
        producer = await self._kafka_client.get_producer()

        await producer.send_and_wait(
            topic=topic or self._settings.file_events_topic,
            value=event.model_dump_json().encode(),
        )
