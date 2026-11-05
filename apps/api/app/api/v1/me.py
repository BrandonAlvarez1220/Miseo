from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.schemas.user import UserRead, UserUpdate
from app.services import users as user_service

router = APIRouter(prefix="/me", tags=["account"])


@router.get("", response_model=UserRead, summary="My profile")
async def read_me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("", response_model=UserRead, summary="Update my profile")
async def update_me(body: UserUpdate, user: CurrentUser, session: SessionDep) -> UserRead:
    updated = await user_service.update_display_name(session, user, body.display_name)
    return UserRead.model_validate(updated)
