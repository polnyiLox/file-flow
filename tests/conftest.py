from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from testcontainers.community.mongodb import MongoDbContainer


@pytest.fixture(scope="session")
def mongodb_container() -> Generator[MongoDbContainer, None, None]:
    with MongoDbContainer(
            image="mongo:8.0",
            username="test",
            password="test",
            dbname="test",
    ) as mongodb:
        yield mongodb


@pytest_asyncio.fixture(
    scope="session",
    loop_scope="session",
)
async def database(
        mongodb_container: MongoDbContainer,
) -> AsyncGenerator[AsyncDatabase, None]:
    client = AsyncMongoClient(mongodb_container.get_connection_url())
    database = client["test"]
    await database.command("ping")

    try:
        yield database
    finally:
        await client.drop_database("test")
        await client.close()
