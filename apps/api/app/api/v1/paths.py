from typing import Annotated

from fastapi import APIRouter, Path

from app.api.deps import SessionDep
from app.schemas.learning import PathDetail, PathSummary
from app.services import learning as learning_service

router = APIRouter(prefix="/paths", tags=["learning paths"])


@router.get("", response_model=list[PathSummary], summary="List learning paths")
async def list_paths(session: SessionDep) -> list[PathSummary]:
    return await learning_service.list_paths(session)


@router.get(
    "/{slug}",
    response_model=PathDetail,
    summary="A learning path: stages of dishes, easy to complex",
    description=(
        "Each dish lists the skills it teaches; `is_new` marks the first dish to teach one."
    ),
)
async def get_path(
    session: SessionDep, slug: Annotated[str, Path(max_length=100, pattern=r"^[a-z0-9-]+$")]
) -> PathDetail:
    return await learning_service.get_path(session, slug)
