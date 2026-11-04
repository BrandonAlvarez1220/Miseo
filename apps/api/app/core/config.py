"""Typed application settings.

Settings are read from environment variables (and an optional ``.env`` file).
Validation happens at startup so a misconfigured deployment fails fast with a
clear message instead of failing on the first request.
"""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Miseo API"
    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # SQLAlchemy URL using the psycopg 3 driver, e.g.
    # postgresql+psycopg://miseo:miseo@localhost:5432/miseo
    database_url: PostgresDsn
    # Supabase's transaction pooler (PgBouncer) does not support server-side
    # prepared statements; disable them when connecting through it.
    database_disable_prepared_statements: bool = False
    database_pool_size: int = Field(default=5, ge=1, le=50)

    # Comma separated list of allowed browser origins.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    @field_validator("database_url")
    @classmethod
    def _require_psycopg_driver(cls, value: PostgresDsn) -> PostgresDsn:
        if value.scheme != "postgresql+psycopg":
            raise ValueError("DATABASE_URL must use the 'postgresql+psycopg://' scheme")
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    # Values come from the environment; pydantic validates required fields at runtime.
    return Settings()
