from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.api.routers.v1 import router
from app.broker.consumer import KafkaConsumer
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.metrics import setup_metrics
from app.db.mongodb import mongodb_client
from app.repositories.analytics import AnalyticsRepository
from app.services.analytics import AnalyticsService

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer = None
    try:
        await mongodb_client.connect()
        repository = AnalyticsRepository(mongodb_client.database)
        await repository.create_indexes()
        app.state.analytics_service = AnalyticsService(repository)
        consumer = KafkaConsumer(settings.kafka, repository)
        await consumer.connect()
        app.state.consumer = consumer
        yield
    finally:
        if consumer is not None:
            await consumer.close()
        await mongodb_client.close()


app = FastAPI(title="Analytics Service", lifespan=lifespan)
app.include_router(router)
setup_metrics(app)


@app.get("/health")
async def health() -> dict:
    if not app.state.consumer.healthy:
        raise HTTPException(503, "Kafka consumer stopped")
    return {"status": "ok"}
