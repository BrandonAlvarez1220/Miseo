import logging
import uuid
from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, NotFoundError
from app.core.security import Claims
from app.models import AppUser
from app.models.enums import UserRole

logger = logging.getLogger(__name__)

MAX_DISPLAY_NAME = 80


def _default_display_name(claims: Claims) -> str:
    candidate = claims.display_name or (claims.email.split("@")[0] if claims.email else "")
    return " ".join(candidate.split())[:MAX_DISPLAY_NAME] or "Usuario"


async def get_or_provision(session: AsyncSession, claims: Claims) -> AppUser:
    """Profile for a verified identity, created on first sight with the USER role.

    Roles are only ever changed by an admin (or the CLI), never derived from the token.
    """
    user = await session.get(AppUser, claims.user_id)
    if user is None:
        # ON CONFLICT DO NOTHING makes concurrent first requests safe.
        await session.execute(
            insert(AppUser)
            .values(
                id=claims.user_id,
                email=claims.email,
                display_name=_default_display_name(claims),
                role=UserRole.USER,
            )
            .on_conflict_do_nothing(index_elements=["id"])
        )
        await session.commit()
        user = await session.get(AppUser, claims.user_id, populate_existing=True)
        if user is None:  # pragma: no cover - the insert above guarantees the row
            raise RuntimeError("User provisioning failed")
        logger.info("Provisioned user %s", user.id)
    elif claims.email and user.email != claims.email:
        user.email = claims.email
        await session.commit()
    return user


async def update_display_name(session: AsyncSession, user: AppUser, display_name: str) -> AppUser:
    user.display_name = display_name
    await session.commit()
    return user


async def list_users(
    session: AsyncSession,
    *,
    q: str | None,
    role: UserRole | None,
    page: int,
    page_size: int,
) -> tuple[Sequence[AppUser], int]:
    stmt = select(AppUser)
    if q:
        term = q.strip()
        stmt = stmt.where(
            or_(
                AppUser.email.icontains(term, autoescape=True),
                AppUser.display_name.icontains(term, autoescape=True),
            )
        )
    if role:
        stmt = stmt.where(AppUser.role == role)
    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await session.scalars(
        stmt.order_by(AppUser.created_at.desc(), AppUser.id)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return rows.all(), total


async def set_role(
    session: AsyncSession, *, actor: AppUser, target_id: uuid.UUID, role: UserRole
) -> AppUser:
    if target_id == actor.id:
        # Prevents an admin from locking everyone out by demoting themselves.
        raise ForbiddenError("You cannot change your own role")
    target = await session.get(AppUser, target_id)
    if target is None:
        raise NotFoundError("User not found")
    previous = target.role
    target.role = role
    await session.commit()
    logger.warning(
        "AUDIT role change: actor=%s target=%s %s -> %s", actor.id, target.id, previous, role
    )
    return target
