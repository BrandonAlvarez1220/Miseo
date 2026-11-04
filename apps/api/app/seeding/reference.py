"""Idempotent loader for reference and development seed data.

Usage::

    uv run python -m app.seeds

Each dataset is upserted by its natural key (``code``, ``slug`` ...), so running
the loader repeatedly never duplicates rows and updates changed descriptions.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import create_engine, create_session_factory
from app.models import BartendingTechnique, Category, GlassType, IngredientCategory, Unit

logger = logging.getLogger("app.seeds")

SEEDS_DIR = Path(__file__).resolve().parent.parent / "seeds"


@dataclass(frozen=True)
class Dataset:
    file: str
    model: type[Base]
    conflict_columns: tuple[str, ...]


# Order matters when datasets reference each other.
DATASETS = (
    Dataset("units.json", Unit, ("code",)),
    Dataset("categories.json", Category, ("recipe_type", "slug")),
    Dataset("ingredient_categories.json", IngredientCategory, ("slug",)),
    Dataset("glass_types.json", GlassType, ("slug",)),
    Dataset("bartending_techniques.json", BartendingTechnique, ("slug",)),
)


def load_rows(file: str) -> list[dict[str, Any]]:
    rows = json.loads((SEEDS_DIR / file).read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError(f"{file} must contain a JSON array")
    return rows


async def upsert(session: AsyncSession, dataset: Dataset, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    stmt = insert(dataset.model).values(rows)
    update_cols = {
        key: stmt.excluded[key] for key in rows[0] if key not in dataset.conflict_columns
    }
    stmt = stmt.on_conflict_do_update(index_elements=dataset.conflict_columns, set_=update_cols)
    await session.execute(stmt)


async def seed_all(session: AsyncSession) -> dict[str, int]:
    counts: dict[str, int] = {}
    for dataset in DATASETS:
        rows = load_rows(dataset.file)
        await upsert(session, dataset, rows)
        counts[dataset.file] = len(rows)
    await session.commit()
    return counts


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, json_output=settings.is_production)
    engine = create_engine(settings)
    try:
        async with create_session_factory(engine)() as session:
            counts = await seed_all(session)
    finally:
        await engine.dispose()
    for file, count in counts.items():
        logger.info("Seeded %s (%d rows)", file, count)


if __name__ == "__main__":
    asyncio.run(main())
