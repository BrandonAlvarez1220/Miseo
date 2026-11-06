"""Seed recipes (cooking and drinks) from structured JSON.

Recipes are upserted by ``slug``: an existing recipe keeps its id (so favorites
and other references survive) and its ingredients, steps and sources are
replaced with the seed contents.
"""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    BartendingTechnique,
    Category,
    DrinkDetails,
    GlassType,
    Ingredient,
    IngredientAlias,
    PreparationStep,
    Recipe,
    RecipeIngredient,
    RecipeSource,
    Unit,
)
from app.models.enums import OriginType, RecipeStatus
from app.seeding.catalog import SeedError
from app.seeding.schemas import SeedRecipe, SeedSource
from app.services.normalization import normalize_text


class _Lookups:
    """Natural-key -> id maps used to resolve references in seed files."""

    def __init__(self) -> None:
        self.ingredients: dict[str, Any] = {}
        self.units: set[str] = set()
        self.categories: dict[tuple[str, str], Category] = {}
        self.glasses: dict[str, Any] = {}
        self.techniques: dict[str, Any] = {}

    @classmethod
    async def load(cls, session: AsyncSession) -> "_Lookups":
        lookups = cls()
        rows = await session.execute(select(Ingredient.normalized_name, Ingredient.id))
        lookups.ingredients = {name: iid for name, iid in rows.all()}
        aliases = await session.execute(
            select(IngredientAlias.normalized_alias, IngredientAlias.ingredient_id)
        )
        for alias, ingredient_id in aliases.all():
            lookups.ingredients.setdefault(alias, ingredient_id)
        lookups.units = set((await session.scalars(select(Unit.code))).all())
        for category in (await session.scalars(select(Category))).all():
            lookups.categories[(category.recipe_type.value, category.slug)] = category
        glasses = await session.execute(select(GlassType.slug, GlassType.id))
        lookups.glasses = {slug: gid for slug, gid in glasses.all()}
        techniques = await session.execute(select(BartendingTechnique.slug, BartendingTechnique.id))
        lookups.techniques = {slug: tid for slug, tid in techniques.all()}
        return lookups

    def ingredient(self, name: str, recipe: str) -> Any:
        try:
            return self.ingredients[normalize_text(name)]
        except KeyError:
            raise SeedError(f"{recipe}: unknown ingredient {name!r}") from None


def _lookup(mapping: dict[str, Any], key: str | None, what: str, recipe: str) -> Any:
    if key is None:
        return None
    if key not in mapping:
        raise SeedError(f"{recipe}: unknown {what} {key!r}")
    return mapping[key]


async def seed_recipes(session: AsyncSession, paths: list[Path], sources_path: Path) -> int:
    presets = TypeAdapter(dict[str, list[SeedSource]]).validate_python(
        json.loads(await asyncio.to_thread(sources_path.read_bytes))
    )
    recipe_adapter = TypeAdapter(list[SeedRecipe])
    recipes = [
        recipe
        for path in paths
        for recipe in recipe_adapter.validate_json(await asyncio.to_thread(path.read_bytes))
    ]
    lookups = await _Lookups.load(session)

    existing = {
        r.slug: r
        for r in (
            await session.scalars(
                select(Recipe).options(
                    selectinload(Recipe.ingredients),
                    selectinload(Recipe.steps),
                    selectinload(Recipe.sources),
                    selectinload(Recipe.categories),
                    selectinload(Recipe.drink_details),
                )
            )
        ).all()
    }

    # Delete the children of recipes being re-seeded first. Otherwise the unit of
    # work may INSERT the new steps before DELETING the old ones and violate
    # UNIQUE (recipe_id, step_number).
    for seed in recipes:
        if seed.slug in existing:
            stale = existing[seed.slug]
            stale.ingredients.clear()
            stale.steps.clear()
            stale.sources.clear()
    await session.flush()

    by_slug: dict[str, Recipe] = {}
    for seed in recipes:
        if seed.slug in by_slug:
            raise SeedError(f"duplicate recipe slug {seed.slug!r}")
        recipe = existing.get(seed.slug) or Recipe(slug=seed.slug)
        _apply(recipe, seed, lookups, presets)
        session.add(recipe)
        by_slug[seed.slug] = recipe
    await session.flush()

    # Second pass: drink details may reference other recipes (variations).
    for seed in recipes:
        if seed.drink is None:
            continue
        drink = seed.drink
        parent_id = None
        if drink.variation_of:
            parent = by_slug.get(drink.variation_of) or existing.get(drink.variation_of)
            if parent is None:
                raise SeedError(f"{seed.slug}: unknown variation_of {drink.variation_of!r}")
            parent_id = parent.id
        recipe = by_slug[seed.slug]
        # Only pre-existing recipes have drink_details eagerly loaded; touching the
        # relationship on a new recipe would trigger an implicit (forbidden) async load.
        previous = existing[seed.slug].drink_details if seed.slug in existing else None
        details = previous or DrinkDetails(recipe_id=recipe.id)
        details.is_alcoholic = drink.is_alcoholic
        details.classification = drink.classification
        details.base_spirit_id = (
            lookups.ingredient(drink.base_spirit, seed.slug) if drink.base_spirit else None
        )
        details.glass_type_id = _lookup(lookups.glasses, drink.glass, "glass", seed.slug)
        details.technique_id = _lookup(lookups.techniques, drink.technique, "technique", seed.slug)
        details.garnish = drink.garnish
        details.abv_estimate = drink.abv_estimate
        details.variation_of_id = parent_id
        session.add(details)
    await session.flush()
    return len(recipes)


def _apply(
    recipe: Recipe, seed: SeedRecipe, lookups: _Lookups, presets: dict[str, list[SeedSource]]
) -> None:
    recipe.title = seed.title
    recipe.description = seed.description
    recipe.introduction = seed.introduction
    recipe.tips = seed.tips
    recipe.recipe_type = seed.recipe_type
    recipe.difficulty = seed.difficulty
    recipe.servings = seed.servings
    recipe.preparation_time_minutes = seed.preparation_time_minutes
    recipe.cooking_time_minutes = seed.cooking_time_minutes
    recipe.origin_type = OriginType.CURATED
    recipe.status = RecipeStatus.PUBLISHED
    recipe.published_at = recipe.published_at or datetime.now(UTC)

    recipe.categories = [
        _lookup(
            {
                slug: c
                for (rtype, slug), c in lookups.categories.items()
                if rtype == seed.recipe_type
            },
            slug,
            "category",
            seed.slug,
        )
        for slug in seed.categories
    ]

    ingredients = []
    for position, item in enumerate(seed.ingredients):
        if item.unit is not None and item.unit not in lookups.units:
            raise SeedError(f"{seed.slug}: unknown unit {item.unit!r}")
        ingredients.append(
            RecipeIngredient(
                ingredient_id=lookups.ingredient(item.ingredient, seed.slug),
                quantity=item.quantity,
                quantity_max=item.quantity_max,
                unit_code=item.unit,
                is_optional=item.optional,
                preparation_notes=item.notes,
                group_label=item.group,
                position=position,
            )
        )
    recipe.ingredients = ingredients
    recipe.steps = [
        PreparationStep(step_number=number, description=text)
        for number, text in enumerate(seed.steps, start=1)
    ]
    recipe.sources = [RecipeSource(**source.model_dump()) for source in presets[seed.sources]]
