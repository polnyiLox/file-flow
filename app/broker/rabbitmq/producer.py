import aio_pika

from app.core.config import RabbitMQRoutingKeysSettings
from app.schemas import ProcessCommandEvent

from .exchanges import RabbitMQExchanges


class RabbitMQProducer:
    def __init__(
            self,
            rabbitmq_exchanges: RabbitMQExchanges,
            routing_keys_settings: RabbitMQRoutingKeysSettings
    ) -> None:
        self._rabbitmq_exchanges = rabbitmq_exchanges
        self._routing_keys_settings = routing_keys_settings

    async def publish_event(self, event: ProcessCommandEvent) -> None:
        exchange = await self._rabbitmq_exchanges.declare_process_commands_exchange()

        await exchange.publish(
            message=aio_pika.Message(
                body=event.model_dump_json().encode()
            ),
            routing_key=self._routing_keys_settings.process_file_routing_keys
        )