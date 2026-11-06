from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.api.v1.params import CsvSlugs, split_csv
from app.models.enums import RecipeType
from app.schemas.recommendation import RecommendationsResponse
from app.services import recommendations as recommendation_service
from app.services.matching import MatchMode

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get(
    "",
    response_model=RecommendationsResponse,
    summary="Recipes you can make with the ingredients you have",
    description=(
        "Deterministic matching (no AI). `exact`: everything required is available. "
        "`flexible`: missing ingredients may be covered by known substitutions. "
        "`discover`: any recipe sharing an ingredient, ranked by compatibility. "
        "Unknown slugs are reported in `unknown_ingredients` instead of failing, so "
        "shared links keep working if an ingredient is renamed."
    ),
)
async def recommend(
    session: SessionDep,
    ingredients: CsvSlugs = None,
    mode: MatchMode = MatchMode.FLEXIBLE,
    recipe_type: RecipeType | None = None,
    assume_staples: Annotated[
        bool, Query(description="Treat salt, water, oil... as available")
    ] = True,
    limit: Annotated[int, Query(ge=1, le=50)] = 24,
) -> RecommendationsResponse:
    return await recommendation_service.recommend(
        session,
        split_csv(ingredients, name="ingredients"),
        mode=mode,
        recipe_type=recipe_type,
        assume_staples=assume_staples,
        limit=limit,
    )
