"""Review queue for moderators and admins."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import ModeratorUser, SessionDep
from app.core.errors import NotFoundError
from app.models import IngestionJob
from app.models.enums import IngestionStatus, RecipeType
from app.schemas.common import Page
from app.schemas.submission import (
    ApproveRequest,
    RejectRequest,
    SubmissionDetail,
    SubmissionListItem,
)
from app.services.ingestion import review, views

router = APIRouter(prefix="/review/submissions", tags=["review"])


@router.get("", response_model=Page[SubmissionListItem], summary="Submissions to review")
async def list_submissions(
    reviewer: ModeratorUser,
    session: SessionDep,
    status_filter: Annotated[IngestionStatus | None, Query(alias="status")] = (
        IngestionStatus.NEEDS_REVIEW
    ),
    agent_id: uuid.UUID | None = None,
    recipe_type: RecipeType | None = None,
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> Page[SubmissionListItem]:
    return await views.list_jobs(
        session,
        status=status_filter,
        agent_id=agent_id,
        recipe_type=recipe_type,
        page=page,
        page_size=page_size,
    )


@router.get("/{submission_id}", response_model=SubmissionDetail, summary="Submission detail")
async def get_submission(
    submission_id: uuid.UUID, reviewer: ModeratorUser, session: SessionDep
) -> SubmissionDetail:
    job = await session.scalar(select(IngestionJob).where(IngestionJob.id == submission_id))
    if job is None or job.payload is None:
        raise NotFoundError("Submission not found")
    return await views.detail_of(session, job)


@router.post(
    "/{submission_id}/approve",
    response_model=SubmissionDetail,
    summary="Approve and publish",
    description=(
        "Creates and PUBLISHES the recipe. Every ingredient line must map to a catalog "
        "ingredient (`ingredient_mappings`), at least one category is required, and an "
        "AI-generated cocktail can never be published as a documented classic."
    ),
)
async def approve_submission(
    submission_id: uuid.UUID, body: ApproveRequest, reviewer: ModeratorUser, session: SessionDep
) -> SubmissionDetail:
    job, _ = await review.approve(session, reviewer=reviewer, job_id=submission_id, body=body)
    return await views.detail_of(session, job)


@router.post(
    "/{submission_id}/reject",
    response_model=SubmissionDetail,
    summary="Reject",
    description="The reason is stored and the submitting agent can read it.",
)
async def reject_submission(
    submission_id: uuid.UUID, body: RejectRequest, reviewer: ModeratorUser, session: SessionDep
) -> SubmissionDetail:
    job = await review.reject(session, reviewer=reviewer, job_id=submission_id, body=body)
    return await views.detail_of(session, job)
