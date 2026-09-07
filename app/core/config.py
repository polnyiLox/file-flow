from functools import lru_cache
import logging
import sys

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataBaseSettings(BaseModel):
    user: str
    password: str
    host: str
    port: int
    name: str

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class ApiSettings(BaseModel):
    v1_prefix: str
    host: str
    port: int
    reload: bool


class MIddlewareSettings(BaseModel):
    allow_origins: list[str]
    allow_methods: list[str]
    allow_headers: list[str]
    allow_credentials: bool


class KafkaSettings(BaseModel):
    bootstrap_servers: list[str]
    client_id: str
    acks: str = "all"
    file_events_topic: str = "file.events"
    processor_events_topic: str = "processor.events"


class RabbitMQConnectionSettings(BaseModel):
    user: str
    password: str
    host: str
    port: int
    vhost: str

    @property
    def url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/{self.vhost}"


class RabbitMQExchangesSettings(BaseModel):
    process_service_commands_name: str = "process.commands"
    process_service_commands_type: str = "topic"


class RabbitMQQueueSettings(BaseModel):
    process_file_queue = "process.file.queue"


class RabbitMQRoutingKeysSettings(BaseModel):
    process_file_routing_keys = "file.process"


class S3Settings(BaseModel):
    access_key: str
    secret_key: str
    endpoint_url: str
    bucket_name: str
    presigned_url_ttl_seconds: int = 3600


class LoggingSettings(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    handlers: list = [logging.StreamHandler(sys.stdout)]


class RedisSettings(BaseModel):
    user: str = "file"
    password: str
    host: str = "localhost"
    port: int = 6379
    db: int = 1
    ttl_seconds: int = 3600

    @property
    def url(self) -> str:
        return f"redis://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class Settings(BaseSettings):
    db: DataBaseSettings
    api: ApiSettings
    middleware: MIddlewareSettings
    kafka: KafkaSettings
    rabbitmq_connection: RabbitMQConnectionSettings
    rabbitmq_exchanges: RabbitMQExchangesSettings = RabbitMQExchangesSettings()
    rabbitmq_queues: RabbitMQQueueSettings = RabbitMQQueueSettings()
    rabbitmq_routing_keys: RabbitMQRoutingKeysSettings = RabbitMQRoutingKeysSettings()
    s3: S3Settings
    logging: LoggingSettings
    redis: RedisSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_CONFIG__",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
