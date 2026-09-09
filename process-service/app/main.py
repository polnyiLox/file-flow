from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.broker.kafka import KafkaProducer
from app.broker.rabbitmq import RabbitMQConsumer
from app.core.config import settings
from app.core.file_client import FileClient
from app.core.s3_client import S3Client
from app.core.logging import configure_logging
from app.core.metrics import setup_metrics
from app.services.process import ProcessService

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    file_client = FileClient(settings.file_service_url)
    kafka_producer = KafkaProducer(settings.kafka)
    service = ProcessService(S3Client(settings.s3), file_client, kafka_producer, settings.thumbnail_size)
    consumer = RabbitMQConsumer(settings.rabbitmq, service)
    try:
        await kafka_producer.connect()
        await consumer.connect()
        yield
    finally:
        await consumer.close()
        await kafka_producer.close()
        await file_client.close()


app = FastAPI(title="Processor Service", lifespan=lifespan)
setup_metrics(app)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
