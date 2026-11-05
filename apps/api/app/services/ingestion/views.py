"""Build API responses from stored ingestion jobs."""

import math
import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, IngestionIssue, IngestionJob, Recipe
from app.models.enums import IngestionStatus, IssueSeverity, RecipeType
from app.schemas.common import Page
from app.schemas.submission import (
    AgentRef,
    Analysis,
    IssueRead,
    LineRead,
    RecipeSubmission,
    SubmissionDetail,
    SubmissionListItem,
    SubmissionResult,
)


async def _issues(session: AsyncSession, job_id: uuid.UUID) -> list[IssueRead]:
    rows = await session.scalars(
        select(IngestionIssue)
        .where(IngestionIssue.job_id == job_id)
        .order_by(IngestionIssue.severity, IngestionIssue.code, IngestionIssue.field_path)
    )
    ordered = sorted(
        rows.all(),
        key=lambda i: (
            [IssueSeverity.ERROR, IssueSeverity.WARNING, IssueSeverity.INFO].index(i.severity),
            i.code,
            i.field_path or "",
        ),
    )
    return [
        IssueRead(severity=i.severity, code=i.code, message=i.message, field_path=i.field_path)
        for i in ordered
    ]


async def _recipe_slug(session: AsyncSession, job: IngestionJob) -> str | None:
    if job.result_recipe_id is None:
        return None
    return await session.scalar(select(Recipe.slug).where(Recipe.id == job.result_recipe_id))


def _analysis(job: IngestionJob) -> Analysis | None:
    return Analysis.model_validate(job.analysis) if job.analysis else None


async def result_of(session: AsyncSession, job: IngestionJob, outcome: Any) -> SubmissionResult:
    issues = await _issues(session, job.id)
    return SubmissionResult(
        id=job.id,
        status=job.status,
        outcome=outcome,
        issues=issues,
        blocking_issues=sum(1 for i in issues if i.severity == IssueSeverity.ERROR),
        analysis=_analysis(job),
        review_notes=job.review_notes,
        recipe_slug=await _recipe_slug(session, job),
    )


def _agent_ref(agent: Agent | None) -> AgentRef | None:
    if agent is None:
        return None
    return AgentRef(id=agent.id, name=agent.name, provider=agent.provider.value)


async def detail_of(session: AsyncSession, job: IngestionJob) -> SubmissionDetail:
    assert job.payload is not None
    submission = RecipeSubmission.model_validate(job.payload["submission"])
    recipe = submission.recipe
    base = await result_of(session, job, "unchanged")
    agent = await session.get(Agent, job.agent_id) if job.agent_id else None
    return SubmissionDetail(
        **base.model_dump(),
        title=recipe.title,
        recipe_type=recipe.recipe_type,
        source=submission.source,
        description=recipe.description,
        tips=recipe.tips,
        servings=recipe.servings,
        preparation_time_minutes=recipe.preparation_time_minutes,
        cooking_time_minutes=recipe.cooking_time_minutes,
        categories=list(job.payload["resolved"].get("categories", [])),
        lines=[LineRead.model_validate(line) for line in job.payload["lines"]],
        steps=list(recipe.steps),
        drink=recipe.drink,
        agent_notes=submission.agent_notes,
        agent=_agent_ref(agent),
        created_at=job.created_at,
        reviewed_at=job.reviewed_at,
    )


async def list_jobs(
    session: AsyncSession,
    *,
    status: IngestionStatus | None,
    agent_id: uuid.UUID | None,
    recipe_type: RecipeType | None,
    page: int,
    page_size: int,
) -> Page[SubmissionListItem]:
    stmt = select(IngestionJob).where(IngestionJob.payload.is_not(None))
    if status:
        stmt = stmt.where(IngestionJob.status == status)
    if agent_id:
        stmt = stmt.where(IngestionJob.agent_id == agent_id)
    if recipe_type:
        stmt = stmt.where(
            IngestionJob.payload["submission"]["recipe"]["recipe_type"].astext == recipe_type.value
        )
    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    jobs: Sequence[IngestionJob] = (
        await session.scalars(
            stmt.order_by(IngestionJob.created_at.desc(), IngestionJob.id)
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
    ).all()

    counts: dict[tuple[uuid.UUID, IssueSeverity], int] = {}
    agents: dict[uuid.UUID, Agent] = {}
    if jobs:
        rows = await session.execute(
            select(IngestionIssue.job_id, IngestionIssue.severity, func.count())
            .where(IngestionIssue.job_id.in_([j.id for j in jobs]))
            .group_by(IngestionIssue.job_id, IngestionIssue.severity)
        )
        counts = {(job_id, severity): n for job_id, severity, n in rows.all()}
        agent_ids = {j.agent_id for j in jobs if j.agent_id}
        if agent_ids:
            agents = {
                a.id: a
                for a in (await session.scalars(select(Agent).where(Agent.id.in_(agent_ids)))).all()
            }

    items = []
    for job in jobs:
        assert job.payload is not None
        recipe = job.payload["submission"]["recipe"]
        analysis = job.analysis or {}
        items.append(
            SubmissionListItem(
                id=job.id,
                status=job.status,
                title=recipe["title"],
                recipe_type=RecipeType(recipe["recipe_type"]),
                agent=_agent_ref(agents.get(job.agent_id)) if job.agent_id else None,
                difficulty_score=(analysis.get("difficulty") or {}).get("score"),
                errors=counts.get((job.id, IssueSeverity.ERROR), 0),
                warnings=counts.get((job.id, IssueSeverity.WARNING), 0),
                created_at=job.created_at,
            )
        )
    return Page[SubmissionListItem](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )
