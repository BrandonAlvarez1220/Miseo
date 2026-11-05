import hashlib
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli import grant_role
from app.models import Agent
from app.models.enums import UserRole
from tests.auth_helpers import bearer, make_token, make_user


async def _admin(session: AsyncSession) -> dict[str, str]:
    _, headers = await make_user(session, UserRole.ADMIN)
    return headers


async def _connect(client: AsyncClient, headers: dict[str, str], name: str, provider: str) -> dict:
    response = await client.post(
        "/api/v1/admin/agents", headers=headers, json={"name": name, "provider": provider}
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_admin_connects_an_agent_and_sees_the_token_once(
    client: AsyncClient, session: AsyncSession
) -> None:
    headers = await _admin(session)

    created = await _connect(client, headers, "Claude recetas MX", "claude")

    assert created["token"].startswith("mis_ag_")
    assert len(created["token"]) > 40
    assert created["token_prefix"] == created["token"][:13]
    assert created["scopes"] == ["submit_recipes"]
    assert created["is_active"] is True
    listing = (await client.get("/api/v1/admin/agents", headers=headers)).json()
    assert len(listing) == 1
    assert "token" not in listing[0]


async def test_only_the_hash_of_the_token_is_stored(
    client: AsyncClient, session: AsyncSession
) -> None:
    headers = await _admin(session)
    created = await _connect(client, headers, "Gemini", "gemini")

    stored = await session.scalar(select(Agent).where(Agent.name == "Gemini"))

    assert stored is not None
    assert stored.token_hash == hashlib.sha256(created["token"].encode()).hexdigest()
    assert created["token"] not in (stored.token_hash, stored.token_prefix)
    dump = await session.execute(text("SELECT * FROM agent"))
    assert created["token"] not in str(dump.all())


async def test_three_agents_have_independent_tokens(
    client: AsyncClient, session: AsyncSession
) -> None:
    headers = await _admin(session)
    agents = {
        name: await _connect(client, headers, name, provider)
        for name, provider in [("OpenCode", "opencode"), ("Claude", "claude"), ("Gemini", "gemini")]
    }

    assert len({a["token"] for a in agents.values()}) == 3
    for agent in agents.values():
        response = await client.get("/api/v1/agent/me", headers=bearer(agent["token"]))
        assert response.status_code == 200
        assert response.json()["id"] == agent["id"]


async def test_revoking_one_agent_leaves_the_others_working(
    client: AsyncClient, session: AsyncSession
) -> None:
    headers = await _admin(session)
    claude = await _connect(client, headers, "Claude", "claude")
    gemini = await _connect(client, headers, "Gemini", "gemini")

    revoked = await client.post(f"/api/v1/admin/agents/{gemini['id']}/revoke", headers=headers)
    again = await client.post(f"/api/v1/admin/agents/{gemini['id']}/revoke", headers=headers)

    assert revoked.status_code == 200
    assert revoked.json()["is_active"] is False
    assert again.status_code == 200  # idempotent
    assert (
        await client.get("/api/v1/agent/me", headers=bearer(gemini["token"]))
    ).status_code == 401
    assert (
        await client.get("/api/v1/agent/me", headers=bearer(claude["token"]))
    ).status_code == 200


@pytest.mark.parametrize("token", ["", "mis_ag_wrong", "mis_ag_" + "x" * 43, "Bearer", "abc"])
async def test_unknown_agent_tokens_are_rejected(client: AsyncClient, token: str) -> None:
    response = await client.get("/api/v1/agent/me", headers=bearer(token))
    assert response.status_code == 401


async def test_agent_endpoint_needs_a_token(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/agent/me")).status_code == 401


async def test_user_tokens_and_agent_tokens_are_not_interchangeable(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin_headers = await _admin(session)
    agent = await _connect(client, admin_headers, "Claude", "claude")

    # A user's JWT is not an agent token...
    assert (await client.get("/api/v1/agent/me", headers=admin_headers)).status_code == 401
    # ...and an agent token is not a user (it cannot reach /me or any admin endpoint).
    for path in ("/api/v1/me", "/api/v1/admin/users", "/api/v1/admin/agents"):
        response = await client.get(path, headers=bearer(agent["token"]))
        assert response.status_code == 401, path


async def test_agent_usage_is_recorded_but_not_on_every_request(
    client: AsyncClient, session: AsyncSession
) -> None:
    headers = await _admin(session)
    agent = await _connect(client, headers, "Claude", "claude")
    assert agent["last_used_at"] is None

    await client.get("/api/v1/agent/me", headers=bearer(agent["token"]))
    first = await session.scalar(
        text("SELECT last_used_at FROM agent WHERE id = :id"), {"id": agent["id"]}
    )
    await client.get("/api/v1/agent/me", headers=bearer(agent["token"]))
    second = await session.scalar(
        text("SELECT last_used_at FROM agent WHERE id = :id"), {"id": agent["id"]}
    )

    assert first is not None
    assert second == first  # throttled: no write within the same minute


@pytest.mark.parametrize("role", [UserRole.USER, UserRole.MODERATOR])
async def test_only_admins_can_manage_agents(
    client: AsyncClient, session: AsyncSession, role: UserRole
) -> None:
    _, headers = await make_user(session, role)

    create = await client.post(
        "/api/v1/admin/agents", headers=headers, json={"name": "Sneaky", "provider": "claude"}
    )
    revoke = await client.post(f"/api/v1/admin/agents/{uuid.uuid4()}/revoke", headers=headers)

    assert create.status_code == 403
    assert revoke.status_code == 403


async def test_agent_validation_and_duplicates(client: AsyncClient, session: AsyncSession) -> None:
    headers = await _admin(session)
    await _connect(client, headers, "Claude", "claude")

    duplicate = await client.post(
        "/api/v1/admin/agents", headers=headers, json={"name": "Claude", "provider": "claude"}
    )
    bad_provider = await client.post(
        "/api/v1/admin/agents", headers=headers, json={"name": "X agent", "provider": "skynet"}
    )
    bad_name = await client.post(
        "/api/v1/admin/agents", headers=headers, json={"name": "<script>", "provider": "other"}
    )
    missing = await client.post(f"/api/v1/admin/agents/{uuid.uuid4()}/revoke", headers=headers)

    assert duplicate.status_code == 409
    assert bad_provider.status_code == 422
    assert bad_name.status_code == 422
    assert missing.status_code == 404


async def test_database_rejects_agents_without_valid_scopes(session: AsyncSession) -> None:
    with pytest.raises(IntegrityError, match="scopes_known"):
        await session.execute(
            text(
                "INSERT INTO agent (name, provider, token_prefix, token_hash, scopes) "
                "VALUES ('x1', 'claude', 'p', 'h1', ARRAY['delete_everything'])"
            )
        )


async def test_cli_grant_role(session: AsyncSession) -> None:
    user, _ = await make_user(session, email="owner@example.com")

    promoted = await grant_role(
        session, role=UserRole.ADMIN, email="owner@example.com", user_id=None
    )

    assert promoted.id == user.id
    assert promoted.role == UserRole.ADMIN


async def test_cli_grant_role_rejects_unknown_and_ambiguous_input(session: AsyncSession) -> None:
    with pytest.raises(SystemExit, match="No such user"):
        await grant_role(session, role=UserRole.ADMIN, email="ghost@example.com", user_id=None)
    with pytest.raises(SystemExit, match="exactly one"):
        await grant_role(session, role=UserRole.ADMIN, email=None, user_id=None)


async def test_admin_made_by_cli_can_use_the_api(
    client: AsyncClient, session: AsyncSession
) -> None:
    user_id = uuid.uuid4()
    token = make_token(user_id, email="owner@example.com")
    assert (await client.get("/api/v1/admin/users", headers=bearer(token))).status_code == 403

    await grant_role(session, role=UserRole.ADMIN, email="owner@example.com", user_id=None)

    assert (await client.get("/api/v1/admin/users", headers=bearer(token))).status_code == 200
