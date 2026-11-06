"""Endpoints used by ingestion agents (authenticated with an agent token)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response, status
from sqlalchemy import select

from app.api.deps import SessionDep, SubmitterAgent
from app.core.errors import NotFoundError
from app.models import IngestionJob
from app.models.enums import IngestionStatus
from app.schemas.common import Page
from app.schemas.submission import (
    RecipeSubmission,
    SubmissionListItem,
    SubmissionResult,
)
from app.services.ingestion import pipeline, views

router = APIRouter(prefix="/agent/submissions", tags=["agent"])


@router.post(
    "",
    response_model=SubmissionResult,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a recipe for review",
    description=(
        "Never publishes: the recipe waits for a human reviewer. Idempotent: the same "
        "source URL (or title + source name) always maps to one submission. While it is "
        "still in review, the same agent can resubmit to fix issues (`outcome: updated`); "
        "otherwise the existing submission is returned (`outcome: unchanged`). "
        "Read `issues` and `analysis` in the response and fix errors before resubmitting."
    ),
    responses={200: {"description": "Updated or already submitted (see `outcome`)."}},
)
async def submit_recipe(
    body: RecipeSubmission,
    agent: SubmitterAgent,
    session: SessionDep,
    request: Request,
    response: Response,
) -> SubmissionResult:
    job, outcome = await pipeline.submit(session, request.app.state.settings, agent, body)
    if outcome != "created":
        response.status_code = status.HTTP_200_OK
    return await views.result_of(session, job, outcome)


@router.get("", response_model=Page[SubmissionListItem], summary="My submissions")
async def list_my_submissions(
    agent: SubmitterAgent,
    session: SessionDep,
    status_filter: Annotated[IngestionStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> Page[SubmissionListItem]:
    return await views.list_jobs(
        session,
        status=status_filter,
        agent_id=agent.id,
        recipe_type=None,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{submission_id}",
    response_model=SubmissionResult,
    summary="Status of one of my submissions",
    description=(
        "Includes the reviewer's notes when it was rejected, and the recipe slug once published."
    ),
)
async def get_my_submission(
    submission_id: uuid.UUID, agent: SubmitterAgent, session: SessionDep
) -> SubmissionResult:
    job = await session.scalar(
        select(IngestionJob).where(
            IngestionJob.id == submission_id, IngestionJob.agent_id == agent.id
        )
    )
    if job is None:
        raise NotFoundError("Submission not found")
    return await views.result_of(session, job, "unchanged")
