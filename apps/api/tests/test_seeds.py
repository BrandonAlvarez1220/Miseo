from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DrinkDetails, Ingredient, Recipe, RecipeSource, Unit
from app.models.enums import DrinkClassification, RecipeStatus
from app.seeding.reference import DATASETS, load_rows
from app.seeds import seed_all


async def _count(session: AsyncSession, model: type) -> int:
    return await session.scalar(select(func.count()).select_from(model)) or 0


async def test_seed_is_idempotent(session: AsyncSession) -> None:
    first = await seed_all(session)
    counts = {m: await _count(session, m) for m in (Unit, Ingredient, Recipe, RecipeSource)}
    second = await seed_all(session)

    assert first == second
    assert {m: await _count(session, m) for m in counts} == counts
    assert counts[Unit] == len(load_rows("units.json"))


async def test_seeded_recipes_are_published_and_attributed(session: AsyncSession) -> None:
    await seed_all(session)

    recipes = (await session.scalars(select(Recipe))).all()
    assert recipes
    assert all(r.status == RecipeStatus.PUBLISHED for r in recipes)
    without_source = await session.scalar(
        select(func.count()).select_from(Recipe).where(~Recipe.sources.any())
    )
    assert without_source == 0


async def test_seeded_variations_point_to_their_classic(session: AsyncSession) -> None:
    await seed_all(session)
    variations = (
        await session.scalars(
            select(DrinkDetails).where(DrinkDetails.classification == DrinkClassification.VARIATION)
        )
    ).all()
    assert variations
    assert all(v.variation_of_id is not None for v in variations)


def test_seed_files_have_unique_natural_keys() -> None:
    for dataset in DATASETS:
        rows = load_rows(dataset.file)
        keys = [tuple(row[col] for col in dataset.conflict_columns) for row in rows]
        assert len(keys) == len(set(keys)), f"duplicate keys in {dataset.file}"
