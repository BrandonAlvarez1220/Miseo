"""Local-development login. Only mounted when DEV_LOGIN_ENABLED=true (never in production).

It signs tokens with the same secret the verifier trusts, so everything downstream
(roles, agents, admin pages) behaves exactly as it will with Supabase.
"""

import logging
import time
import uuid

import jwt
from fastapi import APIRouter, Request

from app.api.deps import SessionDep
from app.core.security import Claims
from app.models.enums import UserRole
from app.schemas.dev import DevLoginRequest, DevLoginResponse
from app.schemas.user import UserRead
from app.services import users as user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dev", tags=["dev (local only)"])

TOKEN_TTL_SECONDS = 12 * 3600
_NAMESPACE = uuid.UUID("5d0e6a3e-4f0b-4f6e-9a57-0b7d2c9c6a11")


def dev_user_id(email: str) -> uuid.UUID:
    """Stable id per email, so the same address is the same user across restarts."""
    return uuid.uuid5(_NAMESPACE, email.strip().lower())


@router.post(
    "/login",
    response_model=DevLoginResponse,
    summary="Sign in without a password (local development only)",
)
async def dev_login(
    body: DevLoginRequest, request: Request, session: SessionDep
) -> DevLoginResponse:
    settings = request.app.state.settings
    email = body.email.lower()
    user_id = dev_user_id(email)
    claims = Claims(user_id=user_id, email=email, display_name=body.display_name)
    user = await user_service.get_or_provision(session, claims)
    if email in settings.dev_admin_emails and user.role != UserRole.ADMIN:
        user.role = UserRole.ADMIN
        await session.commit()

    payload: dict[str, object] = {
        "sub": str(user_id),
        "aud": settings.supabase_jwt_audience,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
        "email": email,
    }
    if settings.supabase_jwt_issuer:
        payload["iss"] = settings.supabase_jwt_issuer
    token = jwt.encode(payload, settings.supabase_jwt_secret.get_secret_value(), algorithm="HS256")
    logger.warning("DEV LOGIN for %s (%s)", email, user.role.value)
    return DevLoginResponse(
        access_token=token, expires_in=TOKEN_TTL_SECONDS, user=UserRead.model_validate(user)
    )
