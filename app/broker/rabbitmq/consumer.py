from typing import Callable, Any

from aio_pika.abc import AbstractRobustQueue


class RabbitMQConsumer:
    def __init__(self):
        ...

    @staticmethod
    async def start_consuming(
            queue: AbstractRobustQueue,
            callback: Callable[[Any], None],
    ) -> None:
        await queue.consume(
            callback=callback
        )