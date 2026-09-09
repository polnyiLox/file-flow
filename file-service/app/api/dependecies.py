from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.broker import KafkaClient, KafkaProducer, RabbitMQClient, RabbitMQProducer
from app.broker.rabbitmq import RabbitMQExchanges, RabbitMQQueues
from app.cache import RedisCache
from app.core.config import settings
from app.core.s3_client import S3Client
from app.db.session import get_session
from app.repositories import FileRepository
from app.services import FileService

s3_client = S3Client(settings.s3)
redis_cache = RedisCache(settings.redis)
kafka_client = KafkaClient(settings.kafka)
rabbitmq_client = RabbitMQClient(settings.rabbitmq_connection)
kafka_producer = KafkaProducer(kafka_client, settings.kafka)


async def build_rabbitmq_producer() -> RabbitMQProducer:
    channel = await rabbitmq_client.get_channel()
    exchanges = RabbitMQExchanges(channel, settings.rabbitmq_exchanges)
    queues = RabbitMQQueues(settings.rabbitmq_queues, settings.rabbitmq_routing_keys, channel)
    await queues.declare_process_file_queue(await exchanges.declare_process_commands_exchange())
    return RabbitMQProducer(exchanges, settings.rabbitmq_routing_keys)


async def get_file_service(session: AsyncSession = Depends(get_session)) -> FileService:
    return FileService(
        session=session,
        file_repo=FileRepository(session),
        s3_client=s3_client,
        rabbitmq_producer=await build_rabbitmq_producer(),
        redis_cache=redis_cache,
        kafka_producer=kafka_producer,
    )
