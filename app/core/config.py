from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    file_service_url: str = "http://localhost:8001"
    analytics_service_url: str = "http://localhost:8003"
    timeout_seconds: float = 30
    max_body_size: int = 11 * 1024 * 1024
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_CONFIG__", extra="ignore")


settings = Settings()
