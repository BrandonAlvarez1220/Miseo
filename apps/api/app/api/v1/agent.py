from fastapi import APIRouter

from app.api.deps import SubmitterAgent
from app.schemas.agent import AgentRead

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get(
    "/me",
    response_model=AgentRead,
    summary="Who am I? (for agents)",
    description="Lets an agent check that its token works and see its scopes.",
)
async def agent_me(agent: SubmitterAgent) -> AgentRead:
    return AgentRead.model_validate(agent)
