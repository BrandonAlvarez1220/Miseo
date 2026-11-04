"""Map recipe aggregates to API schemas and assemble the detail view."""

import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import IngredientAlternative, Recipe
from app.models.enums import RecipeType
from app.repositories import recipe as recipe_repo
from app.repositories.recipe import RecipeFilters, RecipeSort
from app.schemas.recipe import (
    AlternativeRead,
    CatalogItemRead,
    CategoryRef,
    DrinkDetailsRead,
    IngredientRef,
    Page,
    RecipeDetail,
    RecipeIngredientRead,
    RecipeIngredientRef,
    RecipeLink,
    RecipeSummary,
    SourceRead,
    StepRead,
    UnitRead,
)


def total_time(recipe: Recipe) -> int | None:
    if recipe.preparation_time_minutes is None and recipe.cooking_time_minutes is None:
        return None
    return (recipe.preparation_time_minutes or 0) + (recipe.cooking_time_minutes or 0)


def to_summary(recipe: Recipe, ingredient_count: int) -> RecipeSummary:
    """Requires ``categories`` and ``drink_details`` to be loaded."""
    drink = recipe.drink_details if recipe.recipe_type == RecipeType.DRINK else None
    return RecipeSummary(
        id=recipe.id,
        slug=recipe.slug,
        title=recipe.title,
        description=recipe.description,
        image_url=recipe.image_url,
        recipe_type=recipe.recipe_type,
        difficulty=recipe.difficulty,
        servings=recipe.servings,
        preparation_time_minutes=recipe.preparation_time_minutes,
        cooking_time_minutes=recipe.cooking_time_minutes,
        total_time_minutes=total_time(recipe),
        categories=[CategoryRef.model_validate(c) for c in recipe.categories],
        ingredient_count=ingredient_count,
        is_alcoholic=drink.is_alcoholic if drink else None,
        published_at=recipe.published_at,
    )


async def search(
    session: AsyncSession,
    filters: RecipeFilters,
    *,
    sort: RecipeSort,
    page: int,
    page_size: int,
) -> Page[RecipeSummary]:
    rows, total = await recipe_repo.search_recipes(
        session, filters, sort=sort, page=page, page_size=page_size
    )
    return Page[RecipeSummary](
        items=[to_summary(recipe, count) for recipe, count in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def summaries_in_order(
    session: AsyncSession, recipe_ids: list[uuid.UUID]
) -> list[RecipeSummary]:
    found = await recipe_repo.get_summaries(session, recipe_ids)
    return [to_summary(*found[rid]) for rid in recipe_ids if rid in found]


def _alternative(alt: IngredientAlternative) -> AlternativeRead:
    return AlternativeRead(
        ingredient=IngredientRef.model_validate(alt.alternative_ingredient),
        substitution_type=alt.substitution_type,
        ratio=alt.ratio,
        notes=alt.equivalence_notes,
    )


async def get_detail(session: AsyncSession, slug: str) -> RecipeDetail:
    recipe = await recipe_repo.get_published_by_slug(session, slug)
    if recipe is None:
        raise NotFoundError(f"Recipe '{slug}' not found")

    alternatives = await recipe_repo.alternatives_for(
        session, [item.ingredient_id for item in recipe.ingredients]
    )
    related = await summaries_in_order(
        session, await recipe_repo.related_recipe_ids(session, recipe)
    )

    drink: DrinkDetailsRead | None = None
    if recipe.drink_details is not None:
        details = recipe.drink_details
        variations = await recipe_repo.variations_of(session, recipe.id)
        drink = DrinkDetailsRead(
            is_alcoholic=details.is_alcoholic,
            classification=details.classification,
            base_spirit=IngredientRef.model_validate(details.base_spirit)
            if details.base_spirit
            else None,
            glass=CatalogItemRead.model_validate(details.glass_type)
            if details.glass_type
            else None,
            technique=CatalogItemRead.model_validate(details.technique)
            if details.technique
            else None,
            garnish=details.garnish,
            abv_estimate=details.abv_estimate,
            variation_of=RecipeLink.model_validate(details.variation_of)
            if details.variation_of and details.variation_of.status == "published"
            else None,
            variations=[RecipeLink.model_validate(v) for v in variations],
        )

    summary = to_summary(recipe, len(recipe.ingredients))
    return RecipeDetail(
        **summary.model_dump(),
        introduction=recipe.introduction,
        tips=recipe.tips,
        ingredients=[
            RecipeIngredientRead(
                ingredient=RecipeIngredientRef.model_validate(item.ingredient),
                quantity=item.quantity,
                quantity_max=item.quantity_max,
                unit=UnitRead.model_validate(item.unit) if item.unit else None,
                is_optional=item.is_optional,
                preparation_notes=item.preparation_notes,
                group_label=item.group_label,
                alternatives=[_alternative(a) for a in alternatives.get(item.ingredient_id, [])],
            )
            for item in recipe.ingredients
        ],
        steps=[StepRead.model_validate(s) for s in recipe.steps],
        sources=[SourceRead.model_validate(s) for s in recipe.sources],
        drink=drink,
        related=related,
    )
