import time
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenVerifier
from app.main import create_app
from app.models import AppUser
from app.models.enums import UserRole
from tests.auth_helpers import bearer, make_token, make_user
from tests.conftest import TEST_JWT_SECRET


async def test_me_requires_a_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "unauthorized"


async def test_valid_token_provisions_a_user_with_the_user_role(
    client: AsyncClient, session: AsyncSession
) -> None:
    user_id = uuid.uuid4()
    token = make_token(
        user_id, email="ana@example.com", extra={"user_metadata": {"full_name": "  Ana   María "}}
    )

    response = await client.get("/api/v1/me", headers=bearer(token))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(user_id)
    assert body["role"] == "user"
    assert body["email"] == "ana@example.com"
    assert body["display_name"] == "Ana María"
    assert await session.get(AppUser, user_id) is not None


async def test_role_claims_in_the_token_are_ignored(client: AsyncClient) -> None:
    token = make_token(
        extra={
            "role": "admin",
            "app_metadata": {"role": "admin"},
            "user_metadata": {"role": "admin"},
        }
    )

    body = (await client.get("/api/v1/me", headers=bearer(token))).json()

    assert body["role"] == "user"


async def test_repeated_requests_do_not_duplicate_the_profile(
    client: AsyncClient, session: AsyncSession
) -> None:
    token = make_token()
    for _ in range(3):
        assert (await client.get("/api/v1/me", headers=bearer(token))).status_code == 200

    from sqlalchemy import func, select

    assert await session.scalar(select(func.count()).select_from(AppUser)) == 1


async def test_email_is_refreshed_from_the_token(
    client: AsyncClient, session: AsyncSession
) -> None:
    user_id = uuid.uuid4()
    await client.get("/api/v1/me", headers=bearer(make_token(user_id, email="old@example.com")))
    body = (
        await client.get("/api/v1/me", headers=bearer(make_token(user_id, email="new@example.com")))
    ).json()
    assert body["email"] == "new@example.com"


@pytest.mark.parametrize(
    "token_kwargs",
    [
        {"expires_in": -60},
        {"audience": "someone-else"},
        {"audience": None},
        {"secret": "a-different-secret-that-is-long-enough!!"},
        {"user_id": "not-a-uuid"},
    ],
    ids=["expired", "wrong-audience", "no-audience", "bad-signature", "non-uuid-sub"],
)
async def test_invalid_tokens_are_rejected(
    client: AsyncClient, token_kwargs: dict[str, object]
) -> None:
    response = await client.get("/api/v1/me", headers=bearer(make_token(**token_kwargs)))  # type: ignore[arg-type]
    assert response.status_code == 401


async def test_token_without_sub_is_rejected(client: AsyncClient) -> None:
    token = jwt.encode(
        {"exp": int(time.time()) + 60, "aud": "authenticated"}, TEST_JWT_SECRET, algorithm="HS256"
    )
    assert (await client.get("/api/v1/me", headers=bearer(token))).status_code == 401


async def test_token_without_expiry_is_rejected(client: AsyncClient) -> None:
    token = jwt.encode(
        {"sub": str(uuid.uuid4()), "aud": "authenticated"}, TEST_JWT_SECRET, algorithm="HS256"
    )
    assert (await client.get("/api/v1/me", headers=bearer(token))).status_code == 401


async def test_alg_none_is_rejected(client: AsyncClient) -> None:
    token = jwt.encode(
        {"sub": str(uuid.uuid4()), "aud": "authenticated", "exp": int(time.time()) + 60},
        None,
        algorithm="none",
    )
    assert (await client.get("/api/v1/me", headers=bearer(token))).status_code == 401


async def test_garbage_and_wrong_scheme_are_rejected(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/me", headers=bearer("not.a.jwt"))).status_code == 401
    basic = {"Authorization": f"Basic {make_token()}"}
    assert (await client.get("/api/v1/me", headers=basic)).status_code == 401


async def test_auth_not_configured_only_affects_protected_endpoints(
    unconfigured_client: AsyncClient,
) -> None:
    protected = await unconfigured_client.get("/api/v1/me", headers=bearer(make_token()))
    public = await unconfigured_client.get("/api/v1/recipes")

    assert protected.status_code == 503
    assert protected.json()["error"]["code"] == "auth_unavailable"
    assert public.status_code == 200


# --- Asymmetric keys (Supabase JWKS) ---------------------------------------------------


class _FakeResolver:
    def __init__(self, public_key: object) -> None:
        self._public_key = public_key

    def resolve(self, token: str) -> object:
        return self._public_key


def _ec_pair() -> tuple[bytes, object]:
    private = ec.generate_private_key(ec.SECP256R1())
    pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return pem, private.public_key()


async def test_asymmetric_tokens_verify_with_the_resolved_key(
    settings,
    session_factory,  # type: ignore[no-untyped-def]
) -> None:
    pem, public = _ec_pair()
    app = create_app(settings.model_copy(update={"supabase_jwt_secret": None}))
    app.state.session_factory = session_factory
    app.state.token_verifier = TokenVerifier(key_resolver=_FakeResolver(public))
    from httpx import ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        good = make_token(algorithm="ES256", key=pem)
        assert (await client.get("/api/v1/me", headers=bearer(good))).status_code == 200

        # An HS256 token must not be accepted when only a JWKS is configured.
        hs = make_token(secret=TEST_JWT_SECRET)
        assert (await client.get("/api/v1/me", headers=bearer(hs))).status_code == 401

        # Signed by a different key.
        other_pem, _ = _ec_pair()
        forged = make_token(algorithm="ES256", key=other_pem)
        assert (await client.get("/api/v1/me", headers=bearer(forged))).status_code == 401


def test_algorithm_confusion_attack_fails() -> None:
    """Signing HS256 with the server's PUBLIC key as the secret must not authenticate."""
    _, public = _ec_pair()
    public_pem = public.public_bytes(  # type: ignore[attr-defined]
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    # PyJWT refuses PEM keys as HMAC secrets, so forge the token by hand, as an attacker would.
    forged = _hand_forged_hs256(public_pem)

    verifier = TokenVerifier(
        hs256_secret=None, key_resolver=_FakeResolver(public), audience="authenticated"
    )
    with pytest.raises(Exception, match="Invalid or expired token"):
        verifier.verify(forged)

    # Even with a shared secret configured, the public key is not the secret.
    verifier = TokenVerifier(
        hs256_secret=TEST_JWT_SECRET, key_resolver=_FakeResolver(public), audience="authenticated"
    )
    with pytest.raises(Exception, match="Invalid or expired token"):
        verifier.verify(forged)


def _hand_forged_hs256(secret: bytes) -> str:
    import base64
    import hashlib
    import hmac
    import json

    def b64(data: bytes) -> bytes:
        return base64.urlsafe_b64encode(data).rstrip(b"=")

    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = b64(
        json.dumps(
            {"sub": str(uuid.uuid4()), "aud": "authenticated", "exp": int(time.time()) + 60}
        ).encode()
    )
    signing_input = header + b"." + body
    signature = b64(hmac.new(secret, signing_input, hashlib.sha256).digest())
    return (signing_input + b"." + signature).decode()


async def test_issuer_is_enforced_when_configured(
    settings,
    session_factory,  # type: ignore[no-untyped-def]
) -> None:
    app = create_app(
        settings.model_copy(update={"supabase_jwt_issuer": "https://project.supabase.co/auth/v1"})
    )
    app.state.session_factory = session_factory
    from httpx import ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        ok = make_token(extra={"iss": "https://project.supabase.co/auth/v1"})
        wrong = make_token(extra={"iss": "https://evil.example/auth/v1"})
        missing = make_token()
        assert (await client.get("/api/v1/me", headers=bearer(ok))).status_code == 200
        assert (await client.get("/api/v1/me", headers=bearer(wrong))).status_code == 401
        assert (await client.get("/api/v1/me", headers=bearer(missing))).status_code == 401


# --- Profile ---------------------------------------------------------------------------


async def test_update_display_name(client: AsyncClient, session: AsyncSession) -> None:
    _, headers = await make_user(session)

    response = await client.patch(
        "/api/v1/me", headers=headers, json={"display_name": "  Chef   Ana "}
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Chef Ana"


@pytest.mark.parametrize("name", ["", "   ", "a" * 81, "bad\u0000name", "bell\u0007"])
async def test_invalid_display_names_are_rejected(
    client: AsyncClient, session: AsyncSession, name: str
) -> None:
    _, headers = await make_user(session)
    response = await client.patch("/api/v1/me", headers=headers, json={"display_name": name})
    assert response.status_code == 422


async def test_whitespace_in_display_names_is_collapsed(
    client: AsyncClient, session: AsyncSession
) -> None:
    _, headers = await make_user(session)
    response = await client.patch(
        "/api/v1/me", headers=headers, json={"display_name": "line\nbreak\ttab"}
    )
    assert response.json()["display_name"] == "line break tab"


async def test_users_cannot_change_their_role_through_the_profile(
    client: AsyncClient, session: AsyncSession
) -> None:
    user, headers = await make_user(session)

    await client.patch("/api/v1/me", headers=headers, json={"display_name": "Ana", "role": "admin"})

    await session.refresh(user)
    assert user.role == UserRole.USER


# --- RBAC ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("role", "expected"),
    [(UserRole.USER, 403), (UserRole.MODERATOR, 403), (UserRole.ADMIN, 200)],
)
async def test_admin_endpoints_require_the_admin_role(
    client: AsyncClient, session: AsyncSession, role: UserRole, expected: int
) -> None:
    _, headers = await make_user(session, role)

    users = await client.get("/api/v1/admin/users", headers=headers)
    agents = await client.get("/api/v1/admin/agents", headers=headers)

    assert users.status_code == expected
    assert agents.status_code == expected
    if expected == 403:
        assert users.json()["error"]["code"] == "forbidden"


async def test_admin_endpoints_require_authentication(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/admin/users")).status_code == 401
    assert (
        await client.put(f"/api/v1/admin/users/{uuid.uuid4()}/role", json={"role": "admin"})
    ).status_code == 401


async def test_admin_can_change_roles_and_the_change_applies_immediately(
    client: AsyncClient, session: AsyncSession
) -> None:
    _, admin_headers = await make_user(session, UserRole.ADMIN)
    target, target_headers = await make_user(session)
    assert (await client.get("/api/v1/admin/users", headers=target_headers)).status_code == 403

    response = await client.put(
        f"/api/v1/admin/users/{target.id}/role", headers=admin_headers, json={"role": "admin"}
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    # Roles live in the database, so the very same token now has the new permissions.
    assert (await client.get("/api/v1/admin/users", headers=target_headers)).status_code == 200


async def test_admin_cannot_change_their_own_role(
    client: AsyncClient, session: AsyncSession
) -> None:
    admin, headers = await make_user(session, UserRole.ADMIN)

    response = await client.put(
        f"/api/v1/admin/users/{admin.id}/role", headers=headers, json={"role": "user"}
    )

    assert response.status_code == 403
    await session.refresh(admin)
    assert admin.role == UserRole.ADMIN


async def test_role_change_validates_input_and_target(
    client: AsyncClient, session: AsyncSession
) -> None:
    _, headers = await make_user(session, UserRole.ADMIN)
    target, _ = await make_user(session)

    bad_role = await client.put(
        f"/api/v1/admin/users/{target.id}/role", headers=headers, json={"role": "superuser"}
    )
    missing = await client.put(
        f"/api/v1/admin/users/{uuid.uuid4()}/role", headers=headers, json={"role": "moderator"}
    )

    assert bad_role.status_code == 422
    assert missing.status_code == 404


async def test_moderator_cannot_promote_anyone(client: AsyncClient, session: AsyncSession) -> None:
    _, headers = await make_user(session, UserRole.MODERATOR)
    target, _ = await make_user(session)

    response = await client.put(
        f"/api/v1/admin/users/{target.id}/role", headers=headers, json={"role": "admin"}
    )

    assert response.status_code == 403


async def test_admin_user_listing_filters_and_paginates(
    client: AsyncClient, session: AsyncSession
) -> None:
    _, headers = await make_user(session, UserRole.ADMIN, email="boss@example.com")
    await make_user(session, UserRole.MODERATOR, email="mod@example.com")
    for n in range(3):
        await make_user(session, email=f"cook{n}@example.com")

    everyone = (
        await client.get("/api/v1/admin/users", headers=headers, params={"page_size": 2})
    ).json()
    mods = (
        await client.get("/api/v1/admin/users", headers=headers, params={"role": "moderator"})
    ).json()
    cooks = (await client.get("/api/v1/admin/users", headers=headers, params={"q": "COOK"})).json()
    wildcard = (await client.get("/api/v1/admin/users", headers=headers, params={"q": "%"})).json()

    assert everyone["total"] == 5
    assert everyone["pages"] == 3
    assert len(everyone["items"]) == 2
    assert [u["email"] for u in mods["items"]] == ["mod@example.com"]
    assert cooks["total"] == 3
    assert wildcard["total"] == 0
