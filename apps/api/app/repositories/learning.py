import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import LearningPath, PathDish, PathStage, Skill, recipe_skill


async def list_paths(session: AsyncSession) -> Sequence[LearningPath]:
    stmt = (
        select(LearningPath)
        .options(selectinload(LearningPath.stages).selectinload(PathStage.dishes))
        .order_by(LearningPath.discipline, LearningPath.title)
    )
    return (await session.scalars(stmt)).all()


async def get_path(session: AsyncSession, slug: str) -> LearningPath | None:
    stmt = (
        select(LearningPath)
        .where(LearningPath.slug == slug)
        .options(selectinload(LearningPath.stages).selectinload(PathStage.dishes))
    )
    return await session.scalar(stmt)


async def skills_by_recipe(
    session: AsyncSession, recipe_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, list[Skill]]:
    if not recipe_ids:
        return {}
    stmt = (
        select(recipe_skill.c.recipe_id, Skill)
        .join(Skill, Skill.id == recipe_skill.c.skill_id)
        .where(recipe_skill.c.recipe_id.in_(recipe_ids))
        .order_by(Skill.name)
    )
    result: dict[uuid.UUID, list[Skill]] = {}
    for recipe_id, skill in (await session.execute(stmt)).all():
        result.setdefault(recipe_id, []).append(skill)
    return result


async def memberships(
    session: AsyncSession, recipe_id: uuid.UUID
) -> Sequence[tuple[LearningPath, PathStage]]:
    stmt = (
        select(LearningPath, PathStage)
        .join(PathStage, PathStage.path_id == LearningPath.id)
        .join(PathDish, PathDish.stage_id == PathStage.id)
        .where(PathDish.recipe_id == recipe_id)
        .order_by(LearningPath.title)
    )
    return (await session.execute(stmt)).all()
