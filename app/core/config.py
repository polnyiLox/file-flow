from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataBaseSettings(BaseModel):
    user: str
    password: str
    host: str
    port: int
    name: str


class Settings(BaseSettings):
    db: DataBaseSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_CONFIG__",
        env_nested_delimiter="__",
        case_sensitive=False
    )