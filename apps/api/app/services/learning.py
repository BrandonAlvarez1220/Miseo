"""Assemble learning paths: stages with dishes and what each dish teaches."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import LearningPath
from app.repositories import learning as learning_repo
from app.schemas.learning import (
    DishSkill,
    PathDetail,
    PathDishRead,
    PathStageRead,
    PathSummary,
)
from app.services import recipes as recipe_service


async def list_paths(session: AsyncSession) -> list[PathSummary]:
    paths = await learning_repo.list_paths(session)
    recipe_ids = [d.recipe_id for p in paths for s in p.stages for d in s.dishes]
    skills = await learning_repo.skills_by_recipe(session, recipe_ids)
    return [
        PathSummary(
            slug=p.slug,
            title=p.title,
            discipline=p.discipline,
            description=p.description,
            stage_count=len(p.stages),
            dish_count=sum(len(s.dishes) for s in p.stages),
            skill_count=len(
                {
                    skill.slug
                    for s in p.stages
                    for d in s.dishes
                    for skill in skills.get(d.recipe_id, [])
                }
            ),
        )
        for p in paths
    ]


async def get_path(session: AsyncSession, slug: str) -> PathDetail:
    path: LearningPath | None = await learning_repo.get_path(session, slug)
    if path is None:
        raise NotFoundError(f"Learning path '{slug}' not found")

    recipe_ids = [d.recipe_id for s in path.stages for d in s.dishes]
    # Only published recipes are returned (summaries_in_order filters the rest).
    summaries = {r.id: r for r in await recipe_service.summaries_in_order(session, recipe_ids)}
    skills = await learning_repo.skills_by_recipe(session, recipe_ids)

    seen: set[str] = set()
    stages: list[PathStageRead] = []
    for stage in path.stages:
        dishes: list[PathDishRead] = []
        for dish in stage.dishes:
            summary = summaries.get(dish.recipe_id)
            if summary is None:
                continue
            dish_skills = []
            for skill in skills.get(dish.recipe_id, []):
                dish_skills.append(
                    DishSkill(
                        slug=skill.slug,
                        name=skill.name,
                        tip=skill.tip,
                        is_new=skill.slug not in seen,
                    )
                )
            seen.update(s.slug for s in dish_skills)
            dishes.append(PathDishRead(recipe=summary, skills=dish_skills))
        stages.append(
            PathStageRead(
                position=stage.position,
                title=stage.title,
                description=stage.description,
                dishes_to_unlock=min(stage.dishes_to_unlock, len(dishes)),
                dishes=dishes,
            )
        )

    return PathDetail(
        slug=path.slug,
        title=path.title,
        discipline=path.discipline,
        description=path.description,
        stage_count=len(stages),
        dish_count=sum(len(s.dishes) for s in stages),
        skill_count=len(seen),
        stages=stages,
    )
