from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import MongoDBSettings, settings


class MongoDBClient:
    def __init__(self, mongodb_settings: MongoDBSettings) -> None:
        self.settings = mongodb_settings
        self._client: AsyncMongoClient | None = None
        self._database: AsyncDatabase | None = None

    @property
    def database(self) -> AsyncDatabase:
        if self._database is None:
            raise RuntimeError("MongoDB client is not connected")
        return self._database

    async def connect(self) -> None:
        if self._client is not None:
            return

        client = AsyncMongoClient(self.settings.url)
        try:
            await client.admin.command("ping")
        except Exception:
            await client.close()
            raise

        self._client = client
        self._database = client[self.settings.name]

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()

        self._client = None
        self._database = None


mongodb_client = MongoDBClient(settings.mongodb)
