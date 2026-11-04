from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import SubstitutionType
from app.schemas.recipe import IngredientRef, RecipeSummary
from app.services.matching import MatchMode


class SubstitutionRead(BaseModel):
    missing: IngredientRef
    substitute: IngredientRef
    substitution_type: SubstitutionType
    ratio: Decimal
    notes: str | None


class RecommendationRead(BaseModel):
    recipe: RecipeSummary
    match_percentage: int = Field(ge=0, le=100)
    available_ingredients: list[IngredientRef]
    missing_ingredients: list[IngredientRef]
    substitutions: list[SubstitutionRead]
    assumed_staples: list[IngredientRef] = Field(
        description="Pantry staples assumed available (salt, water, oil...)."
    )
    optional_available: list[IngredientRef]
    optional_missing: list[IngredientRef]


class RecommendationsResponse(BaseModel):
    mode: MatchMode
    assume_staples: bool
    ingredients: list[IngredientRef] = Field(description="Selected ingredients that were found.")
    unknown_ingredients: list[str] = Field(description="Requested slugs that do not exist.")
    total: int
    results: list[RecommendationRead]
