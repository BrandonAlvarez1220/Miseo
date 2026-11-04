"""Load the recipes the matcher needs to score (published only)."""

import uuid
from collections.abc import Collection

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Ingredient, IngredientAlternative, Recipe, RecipeIngredient
from app.models.enums import RecipeStatus, RecipeType
from app.services.matching import Alternative, Candidate, IngredientInfo, RecipeLine


def _info(ingredient: Ingredient) -> IngredientInfo:
    return IngredientInfo(
        id=ingredient.id, name=ingredient.name, slug=ingredient.slug, is_staple=ingredient.is_staple
    )


async def load_candidates(
    session: AsyncSession,
    available_ids: Collection[uuid.UUID],
    *,
    recipe_type: RecipeType | None = None,
) -> list[Candidate]:
    """Recipes that use one of the available ingredients or something they can replace."""
    replaceable = select(IngredientAlternative.ingredient_id).where(
        IngredientAlternative.alternative_ingredient_id.in_(available_ids)
    )
    touching = select(RecipeIngredient.recipe_id).where(
        or_(
            RecipeIngredient.ingredient_id.in_(available_ids),
            RecipeIngredient.ingredient_id.in_(replaceable),
        )
    )
    stmt = (
        select(Recipe)
        .where(Recipe.status == RecipeStatus.PUBLISHED, Recipe.id.in_(touching))
        .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient))
    )
    if recipe_type is not None:
        stmt = stmt.where(Recipe.recipe_type == recipe_type)
    recipes = (await session.scalars(stmt)).all()

    ingredient_ids = {line.ingredient_id for r in recipes for line in r.ingredients}
    alternatives: dict[uuid.UUID, list[Alternative]] = {}
    if ingredient_ids:
        rows = await session.scalars(
            select(IngredientAlternative)
            .where(IngredientAlternative.ingredient_id.in_(ingredient_ids))
            .options(selectinload(IngredientAlternative.alternative_ingredient))
        )
        for alt in rows.all():
            alternatives.setdefault(alt.ingredient_id, []).append(
                Alternative(
                    ingredient=_info(alt.alternative_ingredient),
                    substitution_type=alt.substitution_type,
                    ratio=alt.ratio,
                    notes=alt.equivalence_notes,
                )
            )

    candidates = []
    for recipe in recipes:
        own = {line.ingredient_id for line in recipe.ingredients}
        total = None
        if recipe.preparation_time_minutes is not None or recipe.cooking_time_minutes is not None:
            total = (recipe.preparation_time_minutes or 0) + (recipe.cooking_time_minutes or 0)
        candidates.append(
            Candidate(
                recipe_id=recipe.id,
                title=recipe.title,
                total_time_minutes=total,
                lines=tuple(
                    RecipeLine(ingredient=_info(line.ingredient), is_optional=line.is_optional)
                    for line in recipe.ingredients
                ),
                alternatives={k: tuple(v) for k, v in alternatives.items() if k in own},
            )
        )
    return candidates
