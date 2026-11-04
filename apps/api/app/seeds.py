"""Idempotent loader for reference and development seed data.

Usage::

    uv run python -m app.seeds

Every dataset is upserted by its natural key (``code``, ``slug``,
``normalized_name``), so running the loader repeatedly never duplicates rows.
Everything runs in one transaction: invalid seed data leaves the database
untouched.
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import create_engine, create_session_factory
from app.seeding.catalog import seed_alternatives, seed_ingredients
from app.seeding.recipes import seed_recipes
from app.seeding.reference import SEEDS_DIR, seed_reference

logger = logging.getLogger("app.seeds")


async def seed_all(session: AsyncSession) -> dict[str, int]:
    counts = await seed_reference(session)
    counts["ingredients.json"] = await seed_ingredients(session, SEEDS_DIR / "ingredients.json")
    counts["ingredient_alternatives.json"] = await seed_alternatives(
        session, SEEDS_DIR / "ingredient_alternatives.json"
    )
    counts["recipes"] = await seed_recipes(
        session,
        [SEEDS_DIR / "recipes_cooking.json", SEEDS_DIR / "recipes_drinks.json"],
        SEEDS_DIR / "sources.json",
    )
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
    for name, count in counts.items():
        logger.info("Seeded %s (%d rows)", name, count)


if __name__ == "__main__":
    asyncio.run(main())
