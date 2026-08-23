from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import v1_router
from app.db import mongodb_client


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await mongodb_client.connect()
    try:
        yield
    finally:
        await mongodb_client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(v1_router)
