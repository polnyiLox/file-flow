from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataBaseSettings(BaseModel):
    user: str
    password: str
    host: str
    port: int
    name: str


class ApiSettings(BaseModel):
    v1_prefix: str
    host: str
    port: int
    reload: bool


class Settings(BaseSettings):
    db: DataBaseSettings
    api: ApiSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_CONFIG__",
        env_nested_delimiter="__",
        case_sensitive=False
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()