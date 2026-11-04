from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category
from app.models.enums import RecipeType


async def list_categories(
    session: AsyncSession, *, recipe_type: RecipeType | None = None
) -> Sequence[Category]:
    stmt = select(Category).order_by(Category.recipe_type, Category.name)
    if recipe_type is not None:
        stmt = stmt.where(Category.recipe_type == recipe_type)
    return (await session.scalars(stmt)).all()
