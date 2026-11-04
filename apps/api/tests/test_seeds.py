from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Unit
from app.seeds import DATASETS, load_rows, seed_all


async def test_seed_is_idempotent(session: AsyncSession) -> None:
    first = await seed_all(session)
    second = await seed_all(session)

    assert first == second
    assert await session.scalar(select(func.count()).select_from(Unit)) == len(
        load_rows("units.json")
    )
    assert await session.scalar(select(func.count()).select_from(Category)) == len(
        load_rows("categories.json")
    )


def test_seed_files_have_unique_natural_keys() -> None:
    for dataset in DATASETS:
        rows = load_rows(dataset.file)
        keys = [tuple(row[col] for col in dataset.conflict_columns) for row in rows]
        assert len(keys) == len(set(keys)), f"duplicate keys in {dataset.file}"
