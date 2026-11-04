from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Recipe, recipe_category
from app.models.enums import RecipeStatus, RecipeType


async def list_categories(
    session: AsyncSession, *, recipe_type: RecipeType | None = None
) -> Sequence[tuple[Category, int]]:
    """Categories with the number of published recipes in each."""
    recipe_count = (
        select(func.count())
        .select_from(recipe_category)
        .join(Recipe, Recipe.id == recipe_category.c.recipe_id)
        .where(
            recipe_category.c.category_id == Category.id,
            Recipe.status == RecipeStatus.PUBLISHED,
        )
        .correlate(Category)
        .scalar_subquery()
    )
    stmt = select(Category, recipe_count).order_by(Category.recipe_type, Category.name)
    if recipe_type is not None:
        stmt = stmt.where(Category.recipe_type == recipe_type)
    return (await session.execute(stmt)).all()
