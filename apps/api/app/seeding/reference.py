"""Reference catalogs (units, categories, glassware...).

Each dataset is upserted by its natural key (``code``, ``slug`` ...), so running
the loader repeatedly never duplicates rows and updates changed descriptions.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.models import BartendingTechnique, Category, GlassType, IngredientCategory, Unit

SEEDS_DIR = Path(__file__).resolve().parents[2] / "seeds"


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


async def seed_reference(session: AsyncSession) -> dict[str, int]:
    counts: dict[str, int] = {}
    for dataset in DATASETS:
        rows = load_rows(dataset.file)
        await upsert(session, dataset, rows)
        counts[dataset.file] = len(rows)
    return counts
