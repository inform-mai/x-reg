from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/x_reg"

    dev_user_email: str = "admin"
    dev_user_full_name: str = "Админ"

    api_host: str = "0.0.0.0"
    api_port: int = 8159

    log_dir: str = "logs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
