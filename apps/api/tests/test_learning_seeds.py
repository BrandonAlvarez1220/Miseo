import json
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RecipeType
from app.seeding.catalog import SeedError
from app.seeding.learning import seed_learning_paths, seed_recipe_skills
from tests.factories import make_recipe, make_skill


def _write(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "data.json"
    path.write_text(json.dumps(data))
    return path


def _path(dishes: list[list[str]], discipline: str = "cooking", unlock: int = 1) -> list[object]:
    return [
        {
            "slug": "ruta",
            "title": "Ruta",
            "discipline": discipline,
            "stages": [
                {"title": f"Etapa {i}", "dishes_to_unlock": unlock, "dishes": d}
                for i, d in enumerate(dishes)
            ],
        }
    ]


async def test_path_rejects_dish_in_two_stages(session: AsyncSession, tmp_path: Path) -> None:
    await make_recipe(session, "Sopa")
    with pytest.raises(SeedError, match="two stages"):
        await seed_learning_paths(session, _write(tmp_path, _path([["sopa"], ["sopa"]])))


async def test_path_rejects_wrong_discipline(session: AsyncSession, tmp_path: Path) -> None:
    await make_recipe(session, "Mojito", recipe_type=RecipeType.DRINK)
    with pytest.raises(SeedError, match="is not a cooking"):
        await seed_learning_paths(session, _write(tmp_path, _path([["mojito"]])))


async def test_path_rejects_impossible_unlock(session: AsyncSession, tmp_path: Path) -> None:
    await make_recipe(session, "Sopa")
    with pytest.raises(SeedError, match="cannot be unlocked"):
        await seed_learning_paths(session, _write(tmp_path, _path([["sopa"]], unlock=2)))


async def test_paths_seed_is_repeatable(session: AsyncSession, tmp_path: Path) -> None:
    await make_recipe(session, "Sopa")
    await make_recipe(session, "Arroz")
    data = _write(tmp_path, _path([["sopa"], ["arroz"]]))
    await seed_learning_paths(session, data)
    await seed_learning_paths(session, data)


async def test_bar_skill_cannot_tag_a_cooking_recipe(session: AsyncSession, tmp_path: Path) -> None:
    await make_recipe(session, "Sopa")
    await make_skill(session, "dry-shake", RecipeType.DRINK)
    with pytest.raises(SeedError, match="does not fit"):
        await seed_recipe_skills(session, _write(tmp_path, {"sopa": ["dry-shake"]}))
