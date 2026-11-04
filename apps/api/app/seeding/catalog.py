"""Seed ingredients, aliases and substitutions (idempotent upserts by natural key)."""

import asyncio
import json
from pathlib import Path

from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Ingredient, IngredientAlias, IngredientAlternative, IngredientCategory
from app.seeding.schemas import SeedAlternative, SeedIngredient
from app.services.normalization import normalize_text, slugify


class SeedError(ValueError):
    """Seed data references something that does not exist or is inconsistent."""


async def ingredient_ids_by_name(session: AsyncSession) -> dict[str, object]:
    rows = await session.execute(select(Ingredient.normalized_name, Ingredient.id))
    return {name: ingredient_id for name, ingredient_id in rows.all()}


async def seed_ingredients(session: AsyncSession, path: Path) -> int:
    items = TypeAdapter(list[SeedIngredient]).validate_json(
        await asyncio.to_thread(path.read_bytes)
    )
    rows = await session.execute(select(IngredientCategory.slug, IngredientCategory.id))
    categories = {slug: category_id for slug, category_id in rows.all()}
    seen: set[str] = set()
    for item in items:
        normalized = normalize_text(item.name)
        if normalized in seen:
            raise SeedError(f"duplicate ingredient {item.name!r}")
        seen.add(normalized)
        if item.category not in categories:
            raise SeedError(f"unknown ingredient category {item.category!r} for {item.name!r}")
        values = {
            "name": item.name,
            "normalized_name": normalized,
            "slug": slugify(item.name),
            "category_id": categories[item.category],
            "is_alcoholic": item.is_alcoholic,
            "is_staple": item.is_staple,
            "abv": item.abv,
        }
        stmt = insert(Ingredient).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["normalized_name"],
            set_={k: stmt.excluded[k] for k in values if k != "normalized_name"},
        )
        await session.execute(stmt)

    ids = await ingredient_ids_by_name(session)
    for item in items:
        for alias in item.aliases:
            normalized_alias = normalize_text(alias)
            if normalized_alias in ids and normalized_alias != normalize_text(item.name):
                raise SeedError(f"alias {alias!r} collides with another ingredient name")
            stmt = insert(IngredientAlias).values(
                ingredient_id=ids[normalize_text(item.name)],
                alias=alias,
                normalized_alias=normalized_alias,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["normalized_alias"],
                set_={"ingredient_id": stmt.excluded.ingredient_id, "alias": stmt.excluded.alias},
            )
            await session.execute(stmt)
    return len(items)


async def seed_alternatives(session: AsyncSession, path: Path) -> int:
    raw = await asyncio.to_thread(path.read_bytes)
    items = TypeAdapter(list[SeedAlternative]).validate_python(json.loads(raw))
    ids = await ingredient_ids_by_name(session)
    for item in items:
        original, alternative = normalize_text(item.ingredient), normalize_text(item.alternative)
        missing = [name for name in (original, alternative) if name not in ids]
        if missing:
            raise SeedError(f"unknown ingredient(s) in substitution: {missing}")
        stmt = insert(IngredientAlternative).values(
            ingredient_id=ids[original],
            alternative_ingredient_id=ids[alternative],
            substitution_type=item.type,
            ratio=item.ratio,
            equivalence_notes=item.notes,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["ingredient_id", "alternative_ingredient_id"],
            set_={
                "substitution_type": stmt.excluded.substitution_type,
                "ratio": stmt.excluded.ratio,
                "equivalence_notes": stmt.excluded.equivalence_notes,
            },
        )
        await session.execute(stmt)
    return len(items)
