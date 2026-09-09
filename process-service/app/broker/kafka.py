from datetime import datetime, timezone
from uuid import UUID, uuid5

from aiokafka import AIOKafkaProducer


class KafkaProducer:
    def __init__(self, settings) -> None:
        self._settings = settings
        self._producer = None

    async def connect(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._settings.bootstrap_servers,
            client_id=self._settings.client_id, acks="all",
        )
        await self._producer.start()

    async def publish_event(self, command, event_type: str, **payload) -> None:
        import json
        # Stable ID prevents duplicate analytics when RabbitMQ redelivers a command.
        event = {
            "event_id": str(uuid5(UUID(str(command.command_id)), event_type)),
            "event_type": event_type,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "producer": "processor-service",
            "payload": {"file_id": str(command.file_id), **payload},
        }
        await self._producer.send_and_wait(
            self._settings.file_events_topic,
            value=json.dumps(event).encode(),
            key=str(command.file_id).encode(),
        )

    async def close(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
