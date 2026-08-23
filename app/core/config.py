from functools import lru_cache
from urllib.parse import quote

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class MongoDBSettings(BaseModel):
    user: str
    password: str
    host: str
    port: int
    name: str
    auth_source: str = "admin"

    @property
    def url(self) -> str:
        user = quote(self.user, safe="")
        password = quote(self.password, safe="")
        auth_source = quote(self.auth_source, safe="")
        return (
            f"mongodb://{user}:{password}@{self.host}:{self.port}/"
            f"?authSource={auth_source}"
        )


class ApiSettings(BaseModel):
    v1_prefix: str
    host: str
    port: int
    reload: bool


class MiddlewareSettings(BaseModel):
    allow_origins: list[str]
    allow_methods: list[str]
    allow_headers: list[str]
    allow_credentials: bool


class Settings(BaseSettings):
    mongodb: MongoDBSettings
    api: ApiSettings
    middleware: MiddlewareSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_CONFIG__",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
