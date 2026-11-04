from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.api.v1.params import CsvSlugs, split_csv
from app.models.enums import RecipeType
from app.repositories import ingredient as ingredient_repo
from app.repositories.ingredient import IngredientSort
from app.schemas.ingredient import IngredientRead
from app.schemas.recipe import CategoryRef

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get(
    "",
    response_model=list[IngredientRead],
    summary="Search the ingredient catalog",
    description=(
        "Autocomplete by name or alias (accent-insensitive, typo tolerant), resolve "
        "ingredients by slug, or list the most used ingredients with `sort=popular`."
    ),
)
async def list_ingredients(
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=80)] = None,
    slugs: CsvSlugs = None,
    recipe_type: RecipeType | None = None,
    include_staples: bool = True,
    sort: IngredientSort = IngredientSort.NAME,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[IngredientRead]:
    rows = await ingredient_repo.search_ingredients(
        session,
        q=q,
        slugs=split_csv(slugs, name="slugs"),
        recipe_type=recipe_type,
        include_staples=include_staples,
        sort=sort,
        limit=limit,
    )
    return [
        IngredientRead(
            id=ingredient.id,
            name=ingredient.name,
            slug=ingredient.slug,
            category=CategoryRef.model_validate(ingredient.category)
            if ingredient.category
            else None,
            is_staple=ingredient.is_staple,
            is_alcoholic=ingredient.is_alcoholic,
            recipe_count=count,
        )
        for ingredient, count in rows
    ]
