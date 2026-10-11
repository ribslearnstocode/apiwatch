from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://apiwatch:apiwatch@localhost:5433/apiwatch"
    scheduler_enabled: bool = True
    cors_origins: list[str] = ["http://localhost:5178", "http://127.0.0.1:5178"]
    model_config = SettingsConfigDict(env_file=Path(__file__).parents[1] / ".env")

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value):
        if value.startswith(("postgres://", "postgresql://")):
            return "postgresql+psycopg://" + value.split("://", 1)[1]
        return value


settings = Settings()
