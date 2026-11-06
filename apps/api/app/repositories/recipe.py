"""Recipe queries. Only published recipes are ever returned by these functions."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from sqlalchemy import Select, and_, case, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.sql.elements import ColumnElement

from app.models import (
    Category,
    DrinkDetails,
    Ingredient,
    IngredientAlternative,
    Recipe,
    RecipeIngredient,
    recipe_category,
)
from app.models.enums import Difficulty, RecipeStatus, RecipeType
from app.services.normalization import normalize_text

# Minimum trigram similarity for a fuzzy title match (tolerates typos like "margarta").
TITLE_SIMILARITY_THRESHOLD = 0.3


class RecipeSort(StrEnum):
    RELEVANCE = "relevance"
    NEWEST = "newest"
    TITLE = "title"
    QUICKEST = "quickest"


@dataclass(frozen=True)
class RecipeFilters:
    q: str | None = None
    recipe_type: RecipeType | None = None
    category: str | None = None
    difficulty: Difficulty | None = None
    max_total_time: int | None = None
    ingredient_slugs: tuple[str, ...] = field(default_factory=tuple)
    alcoholic: bool | None = None


def total_time_expr() -> ColumnElement[int | None]:
    prep, cook = Recipe.preparation_time_minutes, Recipe.cooking_time_minutes
    return case(
        (and_(prep.is_(None), cook.is_(None)), None),
        else_=func.coalesce(prep, 0) + func.coalesce(cook, 0),
    )


def _normalized_title() -> ColumnElement[str]:
    return func.unaccent(func.lower(Recipe.title))


def ingredient_count_expr() -> ColumnElement[int]:
    return (
        select(func.count(RecipeIngredient.id))
        .where(RecipeIngredient.recipe_id == Recipe.id)
        .correlate(Recipe)
        .scalar_subquery()
    )


def published() -> ColumnElement[bool]:
    return Recipe.status == RecipeStatus.PUBLISHED


def _apply_filters[S: Select[Any]](stmt: S, filters: RecipeFilters) -> S:
    stmt = stmt.where(published())
    if filters.q:
        term = normalize_text(filters.q)
        if term:
            stmt = stmt.where(
                or_(
                    _normalized_title().contains(term, autoescape=True),
                    func.similarity(_normalized_title(), term) > TITLE_SIMILARITY_THRESHOLD,
                )
            )
    if filters.recipe_type:
        stmt = stmt.where(Recipe.recipe_type == filters.recipe_type)
    if filters.difficulty:
        stmt = stmt.where(Recipe.difficulty == filters.difficulty)
    if filters.max_total_time is not None:
        total = total_time_expr()
        stmt = stmt.where(total.is_not(None), total <= filters.max_total_time)
    if filters.category:
        stmt = stmt.where(
            exists()
            .where(recipe_category.c.recipe_id == Recipe.id)
            .where(recipe_category.c.category_id == Category.id)
            .where(Category.slug == filters.category)
        )
    for slug in filters.ingredient_slugs:
        stmt = stmt.where(
            exists()
            .where(RecipeIngredient.recipe_id == Recipe.id)
            .where(RecipeIngredient.ingredient_id == Ingredient.id)
            .where(Ingredient.slug == slug)
        )
    if filters.alcoholic is not None:
        stmt = stmt.where(
            exists()
            .where(DrinkDetails.recipe_id == Recipe.id)
            .where(DrinkDetails.is_alcoholic.is_(filters.alcoholic))
        )
    return stmt


def _apply_sort(stmt: Select[Recipe, int], sort: RecipeSort, q: str | None) -> Select[Recipe, int]:
    term = normalize_text(q) if q else ""
    if sort == RecipeSort.RELEVANCE and term:
        return stmt.order_by(func.similarity(_normalized_title(), term).desc(), Recipe.title)
    if sort == RecipeSort.TITLE:
        return stmt.order_by(Recipe.title)
    if sort == RecipeSort.QUICKEST:
        return stmt.order_by(total_time_expr().asc().nulls_last(), Recipe.title)
    # NEWEST, and RELEVANCE without a search term.
    return stmt.order_by(Recipe.published_at.desc().nulls_last(), Recipe.title)


def _summary_options() -> tuple[ExecutableOption, ...]:
    return (selectinload(Recipe.categories), selectinload(Recipe.drink_details))


async def search_recipes(
    session: AsyncSession,
    filters: RecipeFilters,
    *,
    sort: RecipeSort,
    page: int,
    page_size: int,
) -> tuple[Sequence[tuple[Recipe, int]], int]:
    """Return one page of ``(recipe, ingredient_count)`` and the total match count."""
    ids = _apply_filters(select(Recipe.id), filters).subquery()
    total = await session.scalar(select(func.count()).select_from(ids)) or 0

    stmt = select(Recipe, ingredient_count_expr()).where(Recipe.id.in_(select(ids.c.id)))
    stmt = _apply_sort(stmt, sort, filters.q)
    stmt = stmt.options(*_summary_options()).limit(page_size).offset((page - 1) * page_size)
    rows = (await session.execute(stmt)).all()
    return rows, total


async def get_summaries(
    session: AsyncSession, recipe_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, tuple[Recipe, int]]:
    if not recipe_ids:
        return {}
    stmt = (
        select(Recipe, ingredient_count_expr())
        .where(Recipe.id.in_(recipe_ids), published())
        .options(*_summary_options())
    )
    return {recipe.id: (recipe, count) for recipe, count in (await session.execute(stmt)).all()}


async def get_published_by_slug(session: AsyncSession, slug: str) -> Recipe | None:
    stmt = (
        select(Recipe)
        .where(Recipe.slug == slug, published())
        .options(
            selectinload(Recipe.categories),
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.unit),
            selectinload(Recipe.steps),
            selectinload(Recipe.sources),
            selectinload(Recipe.drink_details).selectinload(DrinkDetails.base_spirit),
            selectinload(Recipe.drink_details).selectinload(DrinkDetails.glass_type),
            selectinload(Recipe.drink_details).selectinload(DrinkDetails.technique),
            selectinload(Recipe.drink_details).selectinload(DrinkDetails.variation_of),
        )
    )
    return await session.scalar(stmt)


async def alternatives_for(
    session: AsyncSession, ingredient_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, list[IngredientAlternative]]:
    if not ingredient_ids:
        return {}
    stmt = (
        select(IngredientAlternative)
        .where(IngredientAlternative.ingredient_id.in_(ingredient_ids))
        .options(selectinload(IngredientAlternative.alternative_ingredient))
        .order_by(IngredientAlternative.substitution_type)
    )
    result: dict[uuid.UUID, list[IngredientAlternative]] = {}
    for alt in (await session.scalars(stmt)).all():
        result.setdefault(alt.ingredient_id, []).append(alt)
    return result


async def variations_of(session: AsyncSession, recipe_id: uuid.UUID) -> Sequence[Recipe]:
    stmt = (
        select(Recipe)
        .join(DrinkDetails, DrinkDetails.recipe_id == Recipe.id)
        .where(DrinkDetails.variation_of_id == recipe_id, published())
        .order_by(Recipe.title)
    )
    return (await session.scalars(stmt)).all()


async def related_recipe_ids(
    session: AsyncSession, recipe: Recipe, *, limit: int = 4
) -> list[uuid.UUID]:
    """Recipes of the same type ranked by shared non-staple ingredients, then categories."""
    own_ingredients = (
        select(RecipeIngredient.ingredient_id)
        .join(Ingredient, Ingredient.id == RecipeIngredient.ingredient_id)
        .where(RecipeIngredient.recipe_id == recipe.id, Ingredient.is_staple.is_(False))
    )
    own_categories = select(recipe_category.c.category_id).where(
        recipe_category.c.recipe_id == recipe.id
    )
    shared_ingredients = (
        select(func.count(func.distinct(RecipeIngredient.ingredient_id)))
        .where(
            RecipeIngredient.recipe_id == Recipe.id,
            RecipeIngredient.ingredient_id.in_(own_ingredients),
        )
        .correlate(Recipe)
        .scalar_subquery()
    )
    shared_categories = (
        select(func.count())
        .select_from(recipe_category)
        .where(
            recipe_category.c.recipe_id == Recipe.id,
            recipe_category.c.category_id.in_(own_categories),
        )
        .correlate(Recipe)
        .scalar_subquery()
    )
    stmt = (
        select(Recipe.id)
        .where(published(), Recipe.recipe_type == recipe.recipe_type, Recipe.id != recipe.id)
        .where(or_(shared_ingredients > 0, shared_categories > 0))
        .order_by(shared_ingredients.desc(), shared_categories.desc(), Recipe.title)
        .limit(limit)
    )
    return list((await session.scalars(stmt)).all())
