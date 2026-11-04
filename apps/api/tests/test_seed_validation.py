import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.seeding.catalog import SeedError
from app.seeding.recipes import seed_recipes
from app.seeding.reference import SEEDS_DIR
from app.seeding.schemas import SeedRecipe

BASE = {
    "slug": "x",
    "title": "X",
    "recipe_type": "cooking",
    "servings": 1,
    "categories": ["postres"],
    "ingredients": [{"ingredient": "huevo"}],
    "steps": ["Paso"],
}


def test_drink_details_required_for_drinks() -> None:
    with pytest.raises(ValidationError, match="drink details"):
        SeedRecipe.model_validate({**BASE, "recipe_type": "drink"})


def test_variation_requires_parent() -> None:
    drink = {"is_alcoholic": True, "classification": "variation"}
    with pytest.raises(ValidationError, match="variation_of"):
        SeedRecipe.model_validate({**BASE, "recipe_type": "drink", "drink": drink})


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        SeedRecipe.model_validate({**BASE, "calories": 300})


async def test_unknown_ingredient_fails_with_clear_message(
    session: AsyncSession, tmp_path: Path
) -> None:
    path = tmp_path / "recipes.json"
    path.write_text(
        json.dumps([{**BASE, "categories": [], "ingredients": [{"ingredient": "unicornio"}]}])
    )
    with pytest.raises((SeedError, ValidationError)):
        await seed_recipes(session, [path], SEEDS_DIR / "sources.json")
