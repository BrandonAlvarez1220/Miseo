"""Helpers to forge access tokens the way Supabase would sign them."""

import time
import uuid
from typing import Any

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppUser
from app.models.enums import UserRole
from tests.conftest import TEST_JWT_SECRET


def make_token(
    user_id: uuid.UUID | str | None = None,
    *,
    email: str | None = "ana@example.com",
    secret: str = TEST_JWT_SECRET,
    algorithm: str = "HS256",
    audience: str | None = "authenticated",
    expires_in: int = 3600,
    extra: dict[str, Any] | None = None,
    key: Any = None,
) -> str:
    payload: dict[str, Any] = {
        "sub": str(user_id or uuid.uuid4()),
        "exp": int(time.time()) + expires_in,
        "email": email,
    }
    if audience is not None:
        payload["aud"] = audience
    payload.update(extra or {})
    return jwt.encode(payload, key if key is not None else secret, algorithm=algorithm)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def make_user(
    session: AsyncSession,
    role: UserRole = UserRole.USER,
    *,
    email: str | None = None,
    name: str = "Test",
) -> tuple[AppUser, dict[str, str]]:
    """Insert a profile with ``role`` and return it with valid auth headers."""
    user_id = uuid.uuid4()
    user = AppUser(
        id=user_id, email=email or f"{user_id.hex[:8]}@example.com", display_name=name, role=role
    )
    session.add(user)
    await session.commit()
    return user, bearer(make_token(user_id, email=user.email))
