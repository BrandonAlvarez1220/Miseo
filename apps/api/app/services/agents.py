import hashlib
import logging
import secrets
import uuid
from collections.abc import Sequence

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models import Agent, AppUser
from app.models.enums import AgentScope
from app.schemas.agent import AgentCreate

logger = logging.getLogger(__name__)

TOKEN_PREFIX = "mis_ag_"
_PREFIX_SHOWN = len(TOKEN_PREFIX) + 6


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_token() -> str:
    """256 bits of randomness, URL-safe, with a recognisable prefix (helps secret scanners)."""
    return TOKEN_PREFIX + secrets.token_urlsafe(32)


async def create_agent(
    session: AsyncSession, *, actor: AppUser, data: AgentCreate
) -> tuple[Agent, str]:
    token = generate_token()
    agent = Agent(
        name=data.name,
        provider=data.provider,
        description=data.description,
        token_prefix=token[:_PREFIX_SHOWN],
        token_hash=hash_token(token),
        scopes=[AgentScope.SUBMIT_RECIPES.value],
        created_by=actor.id,
    )
    session.add(agent)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError(f"An agent named '{data.name}' already exists") from exc
    logger.warning("AUDIT agent created: actor=%s agent=%s (%s)", actor.id, agent.id, agent.name)
    return agent, token


async def list_agents(session: AsyncSession) -> Sequence[Agent]:
    return (await session.scalars(select(Agent).order_by(Agent.created_at.desc()))).all()


async def revoke_agent(session: AsyncSession, *, actor: AppUser, agent_id: uuid.UUID) -> Agent:
    agent = await session.get(Agent, agent_id)
    if agent is None:
        raise NotFoundError("Agent not found")
    if agent.revoked_at is None:  # idempotent
        await session.execute(
            text("UPDATE agent SET revoked_at = now() WHERE id = :id"), {"id": agent.id}
        )
        await session.commit()
        await session.refresh(agent)
        logger.warning(
            "AUDIT agent revoked: actor=%s agent=%s (%s)", actor.id, agent.id, agent.name
        )
    return agent


async def authenticate(session: AsyncSession, token: str) -> Agent | None:
    """The active agent owning ``token``, or None. Revoked agents never authenticate."""
    if not token.startswith(TOKEN_PREFIX):
        return None
    agent = await session.scalar(select(Agent).where(Agent.token_hash == hash_token(token)))
    if agent is None or agent.revoked_at is not None:
        return None
    # Record usage at most once a minute, so reads do not turn into a write each.
    await session.execute(
        text(
            "UPDATE agent SET last_used_at = now() WHERE id = :id "
            "AND (last_used_at IS NULL OR last_used_at < now() - interval '1 minute')"
        ),
        {"id": agent.id},
    )
    await session.commit()
    return agent
