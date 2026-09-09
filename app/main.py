from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.dependecies import rabbitmq_client, kafka_client, redis_cache, s3_client
from app.api.routers.v1 import router as file_router
from app.api.routers.internal import router as internal_router
from app.core.config import settings
from app.core.health import router as health_router
from app.core.logging import configure_logging
from app.core.metrics import setup_metrics
from app.db.session import engine_dispose
from app.exceptions import AppError, RedisNotConnectedError

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await s3_client.ensure_bucket()
        await rabbitmq_client.connect()
        await kafka_client.connect_producer()
        try:
            await redis_cache.connect()
        except RedisNotConnectedError:
            logger.warning("Starting without Redis cache")
        yield
    finally:
        await rabbitmq_client.close()
        await kafka_client.close()
        await redis_cache.close()
        await engine_dispose()


app = FastAPI(title="File Service", lifespan=lifespan)
app.include_router(health_router)
app.include_router(file_router)
app.include_router(internal_router)
setup_metrics(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.middleware.allow_origins,
    allow_methods=settings.middleware.allow_methods,
    allow_headers=settings.middleware.allow_headers,
    allow_credentials=settings.middleware.allow_credentials,
)


@app.exception_handler(AppError)
async def app_errors_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning("Application error path=%s detail=%s", request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
