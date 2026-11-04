from collections.abc import Sequence
from enum import StrEnum

from sqlalchemy import case, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models import Ingredient, IngredientAlias, Recipe, RecipeIngredient
from app.models.enums import RecipeStatus, RecipeType
from app.services.normalization import normalize_text

NAME_SIMILARITY_THRESHOLD = 0.35


class IngredientSort(StrEnum):
    NAME = "name"
    POPULAR = "popular"


def _recipe_count(recipe_type: RecipeType | None) -> ColumnElement[int]:
    stmt = (
        select(func.count(func.distinct(RecipeIngredient.recipe_id)))
        .join(Recipe, Recipe.id == RecipeIngredient.recipe_id)
        .where(
            RecipeIngredient.ingredient_id == Ingredient.id,
            Recipe.status == RecipeStatus.PUBLISHED,
        )
        .correlate(Ingredient)
    )
    if recipe_type is not None:
        stmt = stmt.where(Recipe.recipe_type == recipe_type)
    return stmt.scalar_subquery()


async def search_ingredients(
    session: AsyncSession,
    *,
    q: str | None = None,
    slugs: Sequence[str] = (),
    recipe_type: RecipeType | None = None,
    include_staples: bool = True,
    sort: IngredientSort = IngredientSort.NAME,
    limit: int = 20,
) -> Sequence[tuple[Ingredient, int]]:
    """Ingredients with how many published recipes use them.

    With ``recipe_type``, only ingredients used by at least one published recipe
    of that type are returned (so the selector never offers dead ends).
    """
    recipe_count = _recipe_count(recipe_type)
    stmt = select(Ingredient, recipe_count).options(selectinload(Ingredient.category))

    if slugs:
        stmt = stmt.where(Ingredient.slug.in_(slugs))
    if recipe_type is not None:
        stmt = stmt.where(recipe_count > 0)
    if not include_staples:
        stmt = stmt.where(Ingredient.is_staple.is_(False))

    term = normalize_text(q) if q else ""
    if term:
        alias_match = (
            exists()
            .where(IngredientAlias.ingredient_id == Ingredient.id)
            .where(IngredientAlias.normalized_alias.contains(term, autoescape=True))
        )
        stmt = stmt.where(
            or_(
                Ingredient.normalized_name.contains(term, autoescape=True),
                alias_match,
                func.similarity(Ingredient.normalized_name, term) > NAME_SIMILARITY_THRESHOLD,
            )
        )
        # Prefix matches first ("ce" -> "cebolla" before "aceite"), then similarity.
        starts = case((Ingredient.normalized_name.startswith(term, autoescape=True), 0), else_=1)
        stmt = stmt.order_by(
            starts, func.similarity(Ingredient.normalized_name, term).desc(), Ingredient.name
        )
    elif sort == IngredientSort.POPULAR:
        stmt = stmt.order_by(recipe_count.desc(), Ingredient.name)
    else:
        stmt = stmt.order_by(Ingredient.name)

    return (await session.execute(stmt.limit(limit))).all()
