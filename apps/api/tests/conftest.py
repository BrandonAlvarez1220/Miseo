"""Test fixtures.

Tests run against a real PostgreSQL database (``TEST_DATABASE_URL``) because the
schema relies on PostgreSQL features (pg_trgm, NULLS NOT DISTINCT,
gen_random_uuid). The schema is built by running the Alembic migrations, which
also verifies that the migrations work.
"""

import os
from collections.abc import AsyncIterator

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.db.base import Base
from app.db.session import create_engine, create_session_factory
from app.main import create_app

TEST_JWT_SECRET = "test-secret-with-at-least-thirty-two-bytes!"

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://miseo:miseo@localhost:5432/miseo_test"
)


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(
        environment="test",
        database_url=TEST_DATABASE_URL,  # type: ignore[arg-type]
        cors_origins=["http://testserver.local"],
        supabase_jwt_secret=TEST_JWT_SECRET,  # type: ignore[arg-type]
        log_level="WARNING",
    )


@pytest.fixture(scope="session")
def migrated_database() -> None:
    config = Config("alembic.ini")
    config.attributes["configure_logger"] = False
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.downgrade(config, "base")
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
async def engine(settings: Settings, migrated_database: None) -> AsyncIterator[AsyncEngine]:
    engine = create_engine(settings)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return create_session_factory(engine)


@pytest.fixture(autouse=True)
async def _clean_tables(engine: AsyncEngine) -> AsyncIterator[None]:
    yield
    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(
    settings: Settings, session_factory: async_sessionmaker[AsyncSession]
) -> AsyncIterator[AsyncClient]:
    app = create_app(settings)
    # ASGITransport does not run the lifespan; inject the shared test factory.
    app.state.session_factory = session_factory
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
async def unconfigured_client(
    settings: Settings, session_factory: async_sessionmaker[AsyncSession]
) -> AsyncIterator[AsyncClient]:
    """An API with no auth configured: public endpoints work, protected ones say 503."""
    app = create_app(settings.model_copy(update={"supabase_jwt_secret": None}))
    app.state.session_factory = session_factory
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client
