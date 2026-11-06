"""Validation schemas for seed files. Seeds are data too: never trust them blindly."""

from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    Difficulty,
    DrinkClassification,
    RecipeType,
    SourceType,
    SubstitutionType,
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SeedIngredient(_Strict):
    name: str = Field(min_length=1, max_length=120)
    category: str
    aliases: list[str] = []
    is_alcoholic: bool = False
    is_staple: bool = False
    is_carbonated: bool = False
    abv: Decimal | None = Field(default=None, ge=0, le=100)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-f]{6}$")


class SeedAlternative(_Strict):
    ingredient: str
    alternative: str
    type: SubstitutionType
    ratio: Decimal = Field(default=Decimal(1), gt=0)
    notes: str | None = None


class SeedSource(_Strict):
    source_name: str
    source_url: str | None
    attribution: str | None
    license: str | None
    source_type: SourceType


class SeedRecipeIngredient(_Strict):
    ingredient: str
    quantity: Decimal | None = Field(default=None, gt=0)
    quantity_max: Decimal | None = Field(default=None, gt=0)
    unit: str | None = None
    optional: bool = False
    notes: str | None = Field(default=None, max_length=200)
    group: str | None = None


class SeedDrink(_Strict):
    is_alcoholic: bool
    classification: DrinkClassification
    base_spirit: str | None = None
    glass: str | None = None
    technique: str | None = None
    garnish: str | None = None
    variation_of: str | None = None
    abv_estimate: Decimal | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def _variation_needs_parent(self) -> Self:
        if self.classification == DrinkClassification.VARIATION and not self.variation_of:
            raise ValueError("a variation must reference the recipe it varies (variation_of)")
        return self


class SeedRecipe(_Strict):
    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=160)
    description: str | None = None
    introduction: str | None = None
    tips: str | None = None
    recipe_type: RecipeType
    difficulty: Difficulty | None = None
    servings: int = Field(gt=0)
    preparation_time_minutes: int | None = Field(default=None, ge=0)
    cooking_time_minutes: int | None = Field(default=None, ge=0)
    categories: list[str] = Field(min_length=1)
    ingredients: list[SeedRecipeIngredient] = Field(min_length=1)
    steps: list[str] = Field(min_length=1)
    sources: Literal["iba", "miseo"] = "miseo"
    drink: SeedDrink | None = None

    @model_validator(mode="after")
    def _drink_details_only_for_drinks(self) -> Self:
        if (self.recipe_type == RecipeType.DRINK) != (self.drink is not None):
            raise ValueError("drink details are required for drinks and forbidden for cooking")
        return self
