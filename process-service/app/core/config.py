from functools import lru_cache
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseModel):
    bootstrap_servers: list[str] = ["localhost:9092"]
    client_id: str = "processor-service"
    file_events_topic: str = "file.events"


class S3Settings(BaseModel):
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    endpoint_url: str = "http://localhost:9000"
    public_endpoint_url: str = "http://localhost:9000"
    bucket_name: str = "files"
    presigned_url_ttl_seconds: int = 3600


class RabbitMQSettings(BaseModel):
    url: str = "amqp://guest:guest@localhost:5672/"
    exchange: str = "image.commands"
    queue: str = "image.process"
    routing_key: str = "image.process"
    prefetch_count: int = 1


class Settings(BaseSettings):
    kafka: KafkaSettings = KafkaSettings()
    s3: S3Settings = S3Settings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    file_service_url: str = "http://localhost:8001"
    thumbnail_size: int = Field(default=400, ge=1, le=4096)

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="APP_CONFIG__", env_nested_delimiter="__",
        extra="ignore", case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
