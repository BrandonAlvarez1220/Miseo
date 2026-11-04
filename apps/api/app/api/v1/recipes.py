from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.api.deps import SessionDep
from app.api.v1.params import CsvSlugs, split_csv
from app.models.enums import Difficulty, RecipeType
from app.repositories.recipe import RecipeFilters, RecipeSort
from app.schemas.recipe import Page, RecipeDetail, RecipeSummary
from app.services import recipes as recipe_service

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("", response_model=Page[RecipeSummary], summary="Search published recipes")
async def search_recipes(
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=100, description="Title search")] = None,
    recipe_type: RecipeType | None = None,
    category: Annotated[str | None, Query(max_length=100, pattern=r"^[a-z0-9-]+$")] = None,
    difficulty: Difficulty | None = None,
    max_time: Annotated[
        int | None, Query(ge=1, le=1440, description="Max preparation + cooking minutes")
    ] = None,
    ingredients: CsvSlugs = None,
    alcoholic: Annotated[bool | None, Query(description="Drinks only")] = None,
    sort: RecipeSort = RecipeSort.RELEVANCE,
    page: Annotated[int, Query(ge=1, le=1000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=48)] = 12,
) -> Page[RecipeSummary]:
    filters = RecipeFilters(
        q=q.strip() if q else None,
        recipe_type=recipe_type,
        category=category,
        difficulty=difficulty,
        max_total_time=max_time,
        ingredient_slugs=split_csv(ingredients, name="ingredients"),
        alcoholic=alcoholic,
    )
    return await recipe_service.search(session, filters, sort=sort, page=page, page_size=page_size)


@router.get("/{slug}", response_model=RecipeDetail, summary="Get a published recipe")
async def get_recipe(
    session: SessionDep,
    slug: Annotated[str, Path(max_length=180, pattern=r"^[a-z0-9-]+$")],
) -> RecipeDetail:
    return await recipe_service.get_detail(session, slug)
