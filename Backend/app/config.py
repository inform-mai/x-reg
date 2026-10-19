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

    org_structure_base_url: str | None = None
    org_structure_token: str | None = None
    org_structure_timeout_seconds: float = 60.0

    api_host: str = "0.0.0.0"
    api_port: int = 8159


@lru_cache
def get_settings() -> Settings:
    return Settings()
