import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import (
    Difficulty,
    DrinkClassification,
    RecipeType,
    SourceType,
    SubstitutionType,
    UnitType,
)
from app.schemas.common import APIModel


class CategoryRef(APIModel):
    slug: str
    name: str


class IngredientRef(APIModel):
    id: uuid.UUID
    name: str
    slug: str


class UnitRead(APIModel):
    code: str
    name: str
    plural_name: str
    unit_type: UnitType
    to_base_factor: Decimal | None


class AlternativeRead(BaseModel):
    ingredient: IngredientRef
    substitution_type: SubstitutionType
    ratio: Decimal
    notes: str | None


class RecipeIngredientRead(BaseModel):
    ingredient: IngredientRef
    quantity: Decimal | None
    quantity_max: Decimal | None
    unit: UnitRead | None
    is_optional: bool
    preparation_notes: str | None
    group_label: str | None
    alternatives: list[AlternativeRead]


class StepRead(APIModel):
    step_number: int
    description: str
    image_url: str | None


class SourceRead(APIModel):
    source_name: str
    source_url: str | None
    attribution: str | None
    license: str | None
    source_type: SourceType


class CatalogItemRead(APIModel):
    slug: str
    name: str
    description: str | None


class RecipeLink(APIModel):
    slug: str
    title: str


class DrinkDetailsRead(BaseModel):
    is_alcoholic: bool
    classification: DrinkClassification
    base_spirit: IngredientRef | None
    glass: CatalogItemRead | None
    technique: CatalogItemRead | None
    garnish: str | None
    abv_estimate: Decimal | None
    variation_of: RecipeLink | None
    variations: list[RecipeLink]


class RecipeSummary(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    description: str | None
    image_url: str | None
    recipe_type: RecipeType
    difficulty: Difficulty | None
    servings: int
    preparation_time_minutes: int | None
    cooking_time_minutes: int | None
    total_time_minutes: int | None = Field(
        description="Preparation + cooking time; null when both are unknown."
    )
    categories: list[CategoryRef]
    ingredient_count: int
    is_alcoholic: bool | None = Field(description="Only set for drinks.")
    published_at: datetime | None


class RecipeDetail(RecipeSummary):
    introduction: str | None
    tips: str | None
    ingredients: list[RecipeIngredientRead]
    steps: list[StepRead]
    sources: list[SourceRead]
    drink: DrinkDetailsRead | None
    related: list[RecipeSummary]


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int
