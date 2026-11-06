"""Facts about the existing learning paths, used to suggest where a new dish fits."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import LearningPath, PathStage, Recipe, RecipeIngredient, Skill, recipe_skill
from app.models.enums import RecipeType
from app.services.ingestion.difficulty import DifficultyInput, score_difficulty
from app.services.ingestion.placement import StageInfo


def recipe_difficulty_score(recipe: Recipe) -> int:
    """Score an existing recipe with the same formula used for submissions.

    Needs ``steps`` and ``ingredients`` (with ``ingredient``) loaded.
    """
    main = sum(
        1 for line in recipe.ingredients if not line.is_optional and not line.ingredient.is_staple
    )
    minutes = None
    if recipe.preparation_time_minutes is not None or recipe.cooking_time_minutes is not None:
        minutes = (recipe.preparation_time_minutes or 0) + (recipe.cooking_time_minutes or 0)
    return score_difficulty(
        DifficultyInput(
            steps=[step.description for step in recipe.steps],
            main_ingredients=main,
            total_minutes=minutes,
        )
    ).score


async def path_stage_infos(
    session: AsyncSession, discipline: RecipeType
) -> list[tuple[LearningPath, list[StageInfo]]]:
    paths = (
        await session.scalars(
            select(LearningPath)
            .where(LearningPath.discipline == discipline)
            .options(selectinload(LearningPath.stages).selectinload(PathStage.dishes))
            .order_by(LearningPath.title)
        )
    ).all()
    recipe_ids = {d.recipe_id for p in paths for s in p.stages for d in s.dishes}
    if not recipe_ids:
        return [(path, []) for path in paths]

    recipes = {
        r.id: r
        for r in (
            await session.scalars(
                select(Recipe)
                .where(Recipe.id.in_(recipe_ids))
                .options(
                    selectinload(Recipe.steps),
                    selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
                )
            )
        ).all()
    }
    skills_by_recipe: dict[object, set[str]] = {}
    rows = await session.execute(
        select(recipe_skill.c.recipe_id, Skill.slug)
        .join(Skill, Skill.id == recipe_skill.c.skill_id)
        .where(recipe_skill.c.recipe_id.in_(recipe_ids))
    )
    for recipe_id, slug in rows.all():
        skills_by_recipe.setdefault(recipe_id, set()).add(slug)

    result: list[tuple[LearningPath, list[StageInfo]]] = []
    for path in paths:
        stages = []
        for stage in path.stages:
            scores = [recipe_difficulty_score(recipes[d.recipe_id]) for d in stage.dishes]
            skills = frozenset(
                slug for d in stage.dishes for slug in skills_by_recipe.get(d.recipe_id, ())
            )
            stages.append(
                StageInfo(
                    position=stage.position,
                    title=stage.title,
                    max_score=max(scores, default=1),
                    skills=skills,
                )
            )
        result.append((path, stages))
    return result
