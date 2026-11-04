"""Seed skills, the skills each recipe teaches, and the learning paths."""

import asyncio
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import LearningPath, PathDish, PathStage, Recipe, Skill, recipe_skill
from app.models.enums import RecipeType
from app.seeding.catalog import SeedError

SLUG = r"^[a-z0-9]+(-[a-z0-9]+)*$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SeedSkill(_Strict):
    slug: str = Field(pattern=SLUG)
    name: str = Field(min_length=1, max_length=120)
    discipline: RecipeType
    tip: str = Field(min_length=1)


class SeedStage(_Strict):
    title: str
    description: str | None = None
    dishes_to_unlock: int = Field(ge=0)
    dishes: list[str] = Field(min_length=1)


class SeedPath(_Strict):
    slug: str = Field(pattern=SLUG)
    title: str
    discipline: RecipeType
    description: str | None = None
    stages: list[SeedStage] = Field(min_length=1)


async def _read(path: Path) -> bytes:
    return await asyncio.to_thread(path.read_bytes)


async def seed_skills(session: AsyncSession, path: Path) -> int:
    items = TypeAdapter(list[SeedSkill]).validate_json(await _read(path))
    for item in items:
        stmt = insert(Skill).values(item.model_dump())
        stmt = stmt.on_conflict_do_update(
            index_elements=["slug"],
            set_={
                "name": stmt.excluded.name,
                "discipline": stmt.excluded.discipline,
                "tip": stmt.excluded.tip,
            },
        )
        await session.execute(stmt)
    return len(items)


async def _recipes_by_slug(session: AsyncSession) -> dict[str, Recipe]:
    return {r.slug: r for r in (await session.scalars(select(Recipe))).all()}


async def seed_recipe_skills(session: AsyncSession, path: Path) -> int:
    mapping: dict[str, list[str]] = json.loads(await _read(path))
    recipes = await _recipes_by_slug(session)
    skills = {s.slug: s for s in (await session.scalars(select(Skill))).all()}
    rows = []
    for recipe_slug, skill_slugs in mapping.items():
        recipe = recipes.get(recipe_slug)
        if recipe is None:
            raise SeedError(f"recipe_skills: unknown recipe {recipe_slug!r}")
        for skill_slug in dict.fromkeys(skill_slugs):
            skill = skills.get(skill_slug)
            if skill is None:
                raise SeedError(f"recipe_skills: unknown skill {skill_slug!r} in {recipe_slug!r}")
            if skill.discipline != recipe.recipe_type:
                raise SeedError(
                    f"recipe_skills: {skill_slug!r} ({skill.discipline}) does not fit "
                    f"{recipe_slug!r} ({recipe.recipe_type})"
                )
            rows.append({"recipe_id": recipe.id, "skill_id": skill.id})
    # Replace the tags of the listed recipes (idempotent).
    ids = [recipes[slug].id for slug in mapping]
    await session.execute(delete(recipe_skill).where(recipe_skill.c.recipe_id.in_(ids)))
    if rows:
        await session.execute(insert(recipe_skill).values(rows))
    return len(rows)


async def seed_learning_paths(session: AsyncSession, path: Path) -> int:
    items = TypeAdapter(list[SeedPath]).validate_json(await _read(path))
    recipes = await _recipes_by_slug(session)
    existing = {
        p.slug: p
        for p in (
            await session.scalars(select(LearningPath).options(selectinload(LearningPath.stages)))
        ).all()
    }
    for item in items:
        seen: set[str] = set()
        for stage in item.stages:
            for slug in stage.dishes:
                recipe = recipes.get(slug)
                if recipe is None:
                    raise SeedError(f"path {item.slug!r}: unknown recipe {slug!r}")
                if recipe.recipe_type != item.discipline:
                    raise SeedError(f"path {item.slug!r}: {slug!r} is not a {item.discipline}")
                if slug in seen:
                    raise SeedError(f"path {item.slug!r}: {slug!r} appears in two stages")
                seen.add(slug)
            if stage.dishes_to_unlock > len(stage.dishes):
                raise SeedError(f"path {item.slug!r}: stage {stage.title!r} cannot be unlocked")

        stages = [
            PathStage(
                position=position,
                title=stage.title,
                description=stage.description,
                dishes_to_unlock=stage.dishes_to_unlock,
                dishes=[
                    PathDish(position=n, recipe_id=recipes[slug].id)
                    for n, slug in enumerate(stage.dishes, start=1)
                ],
            )
            for position, stage in enumerate(item.stages, start=1)
        ]
        learning_path = existing.get(item.slug)
        if learning_path is None:
            # New path: build it complete before the first flush (assigning a
            # collection afterwards would trigger an implicit async lazy load).
            session.add(
                LearningPath(
                    slug=item.slug,
                    title=item.title,
                    discipline=item.discipline,
                    description=item.description,
                    stages=stages,
                )
            )
        else:
            learning_path.title = item.title
            learning_path.discipline = item.discipline
            learning_path.description = item.description
            # Stages are rebuilt from the seed (progress references recipes, not
            # stages). Delete first so UNIQUE (path_id, position) is never violated.
            learning_path.stages.clear()
            await session.flush()
            learning_path.stages.extend(stages)
        await session.flush()
    return len(items)
