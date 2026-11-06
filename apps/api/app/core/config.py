"""Typed application settings.

Settings are read from environment variables (and an optional ``.env`` file).
Validation happens at startup so a misconfigured deployment fails fast with a
clear message instead of failing on the first request.
"""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, PostgresDsn, SecretStr, field_validator, model_validator
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

    # Supabase Auth. The API only VERIFIES access tokens; it never needs the
    # service-role key. Configure at least one of:
    #  - SUPABASE_JWKS_URL: projects with asymmetric signing keys (recommended), or
    #  - SUPABASE_JWT_SECRET: projects using the legacy shared HS256 secret.
    # With neither, public endpoints work and protected ones answer 503.
    supabase_jwt_secret: SecretStr | None = None
    supabase_jwks_url: str | None = None
    supabase_jwt_audience: str = "authenticated"
    supabase_jwt_issuer: str | None = None

    # Limits for ingestion agents (counted in the database: no extra infrastructure).
    agent_max_submissions_per_hour: int = Field(default=60, ge=1)
    agent_max_pending: int = Field(default=200, ge=1)
    agent_max_revisions: int = Field(default=5, ge=0)

    # LOCAL DEVELOPMENT ONLY. Exposes POST /api/v1/dev/login, which hands out a
    # token for any email without a password, so you can work without Supabase.
    # The app refuses to start with it enabled in production.
    dev_login_enabled: bool = False
    # Emails promoted to admin when they sign in through the dev login.
    dev_admin_emails: Annotated[list[str], NoDecode] = []

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

    @field_validator("dev_admin_emails", mode="before")
    @classmethod
    def _split_admin_emails(cls, value: object) -> object:
        if isinstance(value, str):
            return [email.strip().lower() for email in value.split(",") if email.strip()]
        if isinstance(value, list):
            return [str(email).strip().lower() for email in value]
        return value

    @model_validator(mode="after")
    def _dev_login_is_safe(self) -> "Settings":
        if self.dev_login_enabled and self.environment == "production":
            raise ValueError("DEV_LOGIN_ENABLED must never be true in production")
        if self.dev_login_enabled and self.supabase_jwt_secret is None:
            raise ValueError("DEV_LOGIN_ENABLED requires SUPABASE_JWT_SECRET (it signs the tokens)")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    # Values come from the environment; pydantic validates required fields at runtime.
    return Settings()
