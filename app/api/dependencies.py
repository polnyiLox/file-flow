from pymongo.asynchronous.database import AsyncDatabase

from app.db import mongodb_client


def get_database() -> AsyncDatabase:
    return mongodb_client.database
