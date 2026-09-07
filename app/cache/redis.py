import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import RedisSettings
from app.exceptions import RedisNotConnectedError

from .base import Cache


logger = logging.getLogger(__name__)


class RedisCache(Cache):
    def __init__(
            self,
            settings: RedisSettings
    ) -> None:
        self._settings = settings
        self._redis: Redis | None = None

    async def connect(self) -> None:
        if self._redis is not None:
            return

        redis = Redis.from_url(
            url=self._settings.url,
            decode_responses=True
        )

        try:
            await redis.ping()
        except RedisError as e:
            logger.error("Redis error during connection: %s", e)
            await redis.close()
            raise RedisNotConnectedError()

        self._redis = redis

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()

        self._redis = None

    async def get(self, key: str) -> str | None:
        if self._redis is None:
            logger.error(
                "Redis connection is None. Impossible to get data for key=%s",
                key
            )
            raise RedisNotConnectedError()

        try:
            return await self._redis.get(key)
        except RedisError as e:
            logger.error("Redis error during getting data: %s", e)
            return None

    async def set(
            self,
            key: str,
            value: str,
            ttl_seconds: int | None = None
    ) -> None:
        if self._redis is None:
            logger.error(
                "Redis connection is None. Impossible to set data with key=%s, value=%s",
                key,
                value
            )
            raise RedisNotConnectedError()

        try:
            await self._redis.set(
                name=key,
                value=value,
                ex=ttl_seconds or self._settings.ttl_seconds
            )
        except RedisError as e:
            logger.error(
                "Redis error during setting data with key=%s: %s",
                key,
                e
            )

    async def delete(self, *key: str) -> None:
        if self._redis is None:
            logger.error(
                "Redis connection is None. Impossible to delete data for key=%s",
                key
            )
            raise RedisNotConnectedError()

        try:
            await self._redis.delete(*key)
        except RedisError as e:
            logger.error("Redis error during deleting data: %s", e)
