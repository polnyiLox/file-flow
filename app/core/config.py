from functools import lru_cache
from urllib.parse import quote

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class MongoDBSettings(BaseModel):
    user: str = "analytics"
    password: str = "analytics"
    host: str = "localhost"
    port: int = 27017
    name: str = "analytics"
    auth_source: str = "admin"

    @property
    def url(self) -> str:
        return (
            f"mongodb://{quote(self.user, safe='')}:{quote(self.password, safe='')}"
            f"@{self.host}:{self.port}/?authSource={quote(self.auth_source, safe='')}"
        )


class KafkaSettings(BaseModel):
    bootstrap_servers: list[str] = ["localhost:9092"]
    client_id: str = "analytics-service"
    group_id: str = "analytics-service"
    file_events_topic: str = "file.events"


class Settings(BaseSettings):
    mongodb: MongoDBSettings = MongoDBSettings()
    kafka: KafkaSettings = KafkaSettings()
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="APP_CONFIG__", env_nested_delimiter="__",
        extra="ignore", case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
