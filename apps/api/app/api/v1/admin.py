import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import AdminUser, SessionDep
from app.models.enums import UserRole
from app.schemas.agent import AgentCreate, AgentCreated, AgentRead
from app.schemas.common import Page
from app.schemas.user import RoleUpdate, UserRead
from app.services import agents as agent_service
from app.services import users as user_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=Page[UserRead], summary="List users (admin)")
async def list_users(
    admin: AdminUser,
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=100, description="Email or name")] = None,
    role: UserRole | None = None,
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> Page[UserRead]:
    users, total = await user_service.list_users(
        session, q=q, role=role, page=page, page_size=page_size
    )
    return Page[UserRead](
        items=[UserRead.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.put("/users/{user_id}/role", response_model=UserRead, summary="Change a user's role")
async def set_user_role(
    user_id: uuid.UUID, body: RoleUpdate, admin: AdminUser, session: SessionDep
) -> UserRead:
    user = await user_service.set_role(session, actor=admin, target_id=user_id, role=body.role)
    return UserRead.model_validate(user)


@router.get("/agents", response_model=list[AgentRead], summary="List ingestion agents")
async def list_agents(admin: AdminUser, session: SessionDep) -> list[AgentRead]:
    return [AgentRead.model_validate(a) for a in await agent_service.list_agents(session)]


@router.post(
    "/agents",
    response_model=AgentCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Connect an ingestion agent",
    description=(
        "Registers an agent (opencode, Claude, Gemini...) and returns its token **once**. "
        "Store it in the agent's configuration; it cannot be shown again."
    ),
)
async def create_agent(body: AgentCreate, admin: AdminUser, session: SessionDep) -> AgentCreated:
    agent, token = await agent_service.create_agent(session, actor=admin, data=body)
    return AgentCreated(**AgentRead.model_validate(agent).model_dump(), token=token)


@router.post("/agents/{agent_id}/revoke", response_model=AgentRead, summary="Revoke an agent")
async def revoke_agent(agent_id: uuid.UUID, admin: AdminUser, session: SessionDep) -> AgentRead:
    agent = await agent_service.revoke_agent(session, actor=admin, agent_id=agent_id)
    return AgentRead.model_validate(agent)
