from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.broker import RabbitMQProducer, RabbitMQClient, RabbitMQExchanges, KafkaClient
from app.cache import RedisCache
from app.core.config import settings
from app.core.s3_client import (S3Client)
from app.db.session import get_session
from app.repositories import FileRepository
from app.services import FileService


s3_client = S3Client(
    settings=settings.s3
)


redis_cache = RedisCache(
    settings=settings.redis,
)


kafka_client = KafkaClient(
    settings=settings.kafka
)

rabbitmq_client = RabbitMQClient(
    settings=settings.rabbitmq
)


async def build_rabbitmq_exchanges(
        f_rabbitmq_client: RabbitMQClient
) -> RabbitMQExchanges:
    rabbitmq_exchanges = RabbitMQExchanges(
        settings=settings.rabbitmq,
        channel=await f_rabbitmq_client.get_channel(),
    )
    return rabbitmq_exchanges


async def build_rabbitmq_producer(
        f_rabbitmq_client: RabbitMQClient
) -> RabbitMQProducer:
    rabbitmq_producer = RabbitMQProducer(
        rabbitmq_exchanges=await build_rabbitmq_exchanges(
            f_rabbitmq_client=f_rabbitmq_client
        ),
        routing_keys_settings=settings.rabbitmq_routing_keys
    )
    return rabbitmq_producer


async def get_file_repository(
        session: AsyncSession,
) -> FileRepository:
    return FileRepository(session)


async def get_file_service(
        session: AsyncSession = Depends(get_session),
) -> FileService:
    return FileService(
        file_repo=await get_file_repository(session=session),
        rabbitmq_producer=await build_rabbitmq_producer(
            f_rabbitmq_client=rabbitmq_client
        ),
        s3_client=s3_client,
        session=session,
        redis_cache=redis_cache
    )