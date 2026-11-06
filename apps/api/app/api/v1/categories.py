from fastapi import APIRouter

from app.api.deps import SessionDep
from app.models.enums import RecipeType
from app.repositories import category as category_repo
from app.schemas.category import CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead], summary="List recipe categories")
async def list_categories(
    session: SessionDep, recipe_type: RecipeType | None = None
) -> list[CategoryRead]:
    rows = await category_repo.list_categories(session, recipe_type=recipe_type)
    return [
        CategoryRead(
            id=c.id,
            name=c.name,
            slug=c.slug,
            description=c.description,
            recipe_type=c.recipe_type,
            recipe_count=count,
        )
        for c, count in rows
    ]
