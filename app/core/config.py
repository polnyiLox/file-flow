from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_CONFIG__",
        env_nested_delimiter="__",
        case_sensitive=False
    )