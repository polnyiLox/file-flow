from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.dependecies import (
    rabbitmq_client,
    kafka_client,
    redis_cache
)
from app.core.config import settings
from app.core.health import router as health_router
from app.core.logging import configure_logging
from app.exceptions import AppError, RedisNotConnectedError

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting app")
    try:
        await rabbitmq_client.connect()
        await kafka_client.connect()

        try:
            await redis_cache.connect()
        except RedisNotConnectedError:
            logger.error("Impossible to connect to Redis")

        logger.info("App started")
        yield

    finally:
        logger.info("Stopping app")
        await rabbitmq_client.close()
        await kafka_client.close()
        await redis_cache.close()
        logger.info("App stopped")


app = FastAPI(lifespan=lifespan)

app.include_router(health_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.middleware.allow_origins,
    allow_methods=settings.middleware.allow_methods,
    allow_headers=settings.middleware.allow_headers,
    allow_credentials=settings.middleware.allow_credentials
)


@app.exception_handler(AppError)
async def app_errors_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning(
        "Application error during %s %s: %s",
        request.method,
        request.url.path,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail
        }
    )
