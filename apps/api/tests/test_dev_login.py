import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.main import create_app
from tests.auth_helpers import bearer
from tests.conftest import TEST_DATABASE_URL, TEST_JWT_SECRET


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "environment": "development",
        "database_url": TEST_DATABASE_URL,
        "supabase_jwt_secret": TEST_JWT_SECRET,
        "log_level": "WARNING",
        "dev_login_enabled": True,
        "dev_admin_emails": "Boss@Example.com, other@example.com",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


@pytest.fixture
async def dev_client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    app = create_app(_settings())
    app.state.session_factory = session_factory
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        yield client


def test_dev_login_is_refused_in_production() -> None:
    with pytest.raises(ValidationError, match="never be true in production"):
        _settings(environment="production")


def test_dev_login_needs_the_signing_secret() -> None:
    with pytest.raises(ValidationError, match="requires SUPABASE_JWT_SECRET"):
        _settings(supabase_jwt_secret=None)


def test_admin_emails_are_normalized() -> None:
    assert _settings().dev_admin_emails == ["boss@example.com", "other@example.com"]


async def test_endpoint_does_not_exist_unless_enabled(client: AsyncClient) -> None:
    response = await client.post("/api/v1/dev/login", json={"email": "ana@example.com"})
    assert response.status_code == 404


async def test_dev_login_returns_a_token_the_api_accepts(dev_client: AsyncClient) -> None:
    login = await dev_client.post(
        "/api/v1/dev/login", json={"email": "Ana@Example.com", "display_name": "Ana"}
    )

    assert login.status_code == 200
    body = login.json()
    assert body["user"]["role"] == "user"
    assert body["user"]["email"] == "ana@example.com"
    me = await dev_client.get("/api/v1/me", headers=bearer(body["access_token"]))
    assert me.json()["id"] == body["user"]["id"]
    assert me.json()["display_name"] == "Ana"


async def test_same_email_is_the_same_user(dev_client: AsyncClient) -> None:
    first = (await dev_client.post("/api/v1/dev/login", json={"email": "ana@example.com"})).json()
    again = (await dev_client.post("/api/v1/dev/login", json={"email": "ANA@example.com"})).json()
    other = (await dev_client.post("/api/v1/dev/login", json={"email": "bob@example.com"})).json()

    assert first["user"]["id"] == again["user"]["id"]
    assert first["user"]["id"] != other["user"]["id"]
    assert uuid.UUID(first["user"]["id"])


async def test_configured_dev_admins_are_promoted(dev_client: AsyncClient) -> None:
    boss = (await dev_client.post("/api/v1/dev/login", json={"email": "boss@example.com"})).json()
    cook = (await dev_client.post("/api/v1/dev/login", json={"email": "cook@example.com"})).json()

    assert boss["user"]["role"] == "admin"
    assert cook["user"]["role"] == "user"
    admin_area = await dev_client.get("/api/v1/admin/agents", headers=bearer(boss["access_token"]))
    assert admin_area.status_code == 200


@pytest.mark.parametrize("email", ["", "not-an-email", "a@b", "x" * 300 + "@example.com"])
async def test_dev_login_validates_the_email(dev_client: AsyncClient, email: str) -> None:
    response = await dev_client.post("/api/v1/dev/login", json={"email": email})
    assert response.status_code == 422
