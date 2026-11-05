"""Contract between ingestion agents and the API (v1).

Agents do the fuzzy part (find a recipe, read it, rewrite it); this API does the
deterministic part (validate, map ingredients and units, score, detect duplicates).
Unknown fields are rejected so a typo ("ingridients") fails loudly instead of being
silently ignored.
"""

import unicodedata
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.models.enums import (
    Difficulty,
    DrinkClassification,
    IngestionStatus,
    IssueSeverity,
    RecipeType,
    SourceType,
)

SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"


def _clean(value: str) -> str:
    """Collapse whitespace and refuse control or invisible formatting characters.

    Rejecting category C* also blocks zero-width and bidirectional-override characters
    that can disguise text.
    """
    cleaned = " ".join(unicodedata.normalize("NFC", value).split())
    if any(unicodedata.category(char).startswith("C") for char in cleaned):
        raise ValueError("control or invisible characters are not allowed")
    return cleaned


CleanStr = Annotated[str, AfterValidator(_clean)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SubmissionSource(_Strict):
    name: CleanStr = Field(min_length=1, max_length=200, description="Site, book or author.")
    url: HttpUrl | None = Field(default=None, description="Required for source_type 'website'.")
    source_type: SourceType
    license: CleanStr | None = Field(default=None, max_length=120)
    attribution: CleanStr | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.source_type == SourceType.WEBSITE and self.url is None:
            raise ValueError("a website source needs its url (sources are never invented)")
        if self.url is not None and len(str(self.url)) > 2000:
            raise ValueError("url is too long")
        return self


class SubmissionIngredient(_Strict):
    name: CleanStr = Field(min_length=1, max_length=120, description="As written in the source.")
    ingredient_slug: str | None = Field(
        default=None,
        pattern=SLUG_PATTERN,
        max_length=140,
        description="Exact catalog slug from GET /ingredients, when you know it (preferred).",
    )
    quantity: Decimal | None = Field(default=None, gt=0, le=100_000)
    quantity_max: Decimal | None = Field(default=None, gt=0, le=100_000)
    unit: CleanStr | None = Field(default=None, max_length=40, description="Code or common name.")
    optional: bool = False
    notes: CleanStr | None = Field(default=None, max_length=200)
    group: CleanStr | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def _range(self) -> Self:
        if self.quantity_max is not None:
            if self.quantity is None:
                raise ValueError("quantity_max needs quantity")
            if self.quantity_max < self.quantity:
                raise ValueError("quantity_max must be >= quantity")
        return self


class SubmissionDrink(_Strict):
    is_alcoholic: bool
    base_spirit: CleanStr | None = Field(default=None, max_length=120)
    glass: CleanStr | None = Field(default=None, max_length=80, description="Slug or name.")
    technique: CleanStr | None = Field(default=None, max_length=80, description="Slug or name.")
    garnish: CleanStr | None = Field(default=None, max_length=200)
    claimed_classification: DrinkClassification | None = Field(
        default=None,
        description="Informational only: agents can never publish a cocktail as 'classic'.",
    )


class SubmissionRecipe(_Strict):
    title: CleanStr = Field(min_length=3, max_length=160)
    description: CleanStr | None = Field(default=None, max_length=1000)
    introduction: CleanStr | None = Field(default=None, max_length=4000)
    tips: CleanStr | None = Field(default=None, max_length=2000)
    recipe_type: RecipeType
    servings: int = Field(ge=1, le=50)
    preparation_time_minutes: int | None = Field(default=None, ge=0, le=1440)
    cooking_time_minutes: int | None = Field(default=None, ge=0, le=1440)
    categories: list[str] = Field(
        default_factory=list, max_length=5, description="Category slugs from GET /categories."
    )
    ingredients: list[SubmissionIngredient] = Field(min_length=1, max_length=60)
    steps: list[CleanStr] = Field(min_length=1, max_length=40)
    drink: SubmissionDrink | None = None

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if (self.recipe_type == RecipeType.DRINK) != (self.drink is not None):
            raise ValueError("'drink' is required for drinks and not allowed for cooking recipes")
        if any(not 3 <= len(step) <= 2000 for step in self.steps):
            raise ValueError("every step needs 3-2000 characters")
        return self


class RecipeSubmission(_Strict):
    source: SubmissionSource
    recipe: SubmissionRecipe
    agent_notes: CleanStr | None = Field(
        default=None, max_length=2000, description="Doubts or uncertainties for the reviewer."
    )


# ---- responses -----------------------------------------------------------------------


class IssueRead(BaseModel):
    severity: IssueSeverity
    code: str
    message: str
    field_path: str | None


class CandidateRead(BaseModel):
    slug: str
    name: str
    similarity: float


class LineRead(BaseModel):
    index: int
    name: str
    ingredient_slug: str | None
    ingredient_name: str | None
    candidates: list[CandidateRead]
    quantity: Decimal | None
    quantity_max: Decimal | None
    unit_code: str | None
    unit_text: str | None
    optional: bool
    notes: str | None
    group: str | None


class DifficultyAnalysis(BaseModel):
    score: int = Field(ge=1, le=5)
    label: Difficulty
    reasons: list[str]


class SkillSuggestion(BaseModel):
    slug: str
    name: str


class PlacementSuggestion(BaseModel):
    path_slug: str
    path_title: str
    stage_position: int
    stage_title: str
    new_stage: bool
    unknown_skills: list[str]
    introduces: list[str]
    reason: str


class DuplicateRef(BaseModel):
    kind: Literal["recipe", "submission"]
    title: str
    similarity: float
    reason: str
    slug: str | None = None
    submission_id: uuid.UUID | None = None


class ClassificationInfo(BaseModel):
    claimed: DrinkClassification | None
    suggested: DrinkClassification


class Analysis(BaseModel):
    difficulty: DifficultyAnalysis
    skills: list[SkillSuggestion]
    placements: list[PlacementSuggestion]
    duplicates: list[DuplicateRef]
    classification: ClassificationInfo | None = None


class SubmissionResult(BaseModel):
    id: uuid.UUID
    status: IngestionStatus
    outcome: Literal["created", "updated", "unchanged"] = Field(
        description="'unchanged' when this exact recipe was already submitted (idempotent)."
    )
    issues: list[IssueRead]
    blocking_issues: int = Field(description="Errors a reviewer must resolve before approving.")
    analysis: Analysis | None
    review_notes: str | None = None
    recipe_slug: str | None = Field(default=None, description="Set once approved and published.")


class AgentRef(BaseModel):
    id: uuid.UUID
    name: str
    provider: str


class SubmissionDetail(SubmissionResult):
    title: str
    recipe_type: RecipeType
    source: SubmissionSource
    description: str | None
    tips: str | None
    servings: int
    preparation_time_minutes: int | None
    cooking_time_minutes: int | None
    categories: list[str]
    lines: list[LineRead]
    steps: list[str]
    drink: SubmissionDrink | None
    agent_notes: str | None
    agent: AgentRef | None
    created_at: datetime
    reviewed_at: datetime | None


class SubmissionListItem(BaseModel):
    id: uuid.UUID
    status: IngestionStatus
    title: str
    recipe_type: RecipeType
    agent: AgentRef | None
    difficulty_score: int | None
    errors: int
    warnings: int
    created_at: datetime


class ApprovePlacement(_Strict):
    path_slug: str = Field(pattern=SLUG_PATTERN)
    stage_position: int = Field(ge=1, le=50)


class NewIngredient(_Strict):
    """An ingredient the catalog lacks, created together with the approval."""

    name: CleanStr = Field(min_length=1, max_length=120)
    category: str | None = Field(
        default=None, pattern=SLUG_PATTERN, description="Ingredient category slug."
    )
    is_staple: bool = False
    is_alcoholic: bool = False


class ApproveRequest(_Strict):
    ingredient_mappings: dict[int, str] = Field(
        default_factory=dict,
        description="Line index -> catalog ingredient slug (for unmatched lines, or to override).",
    )
    new_ingredients: dict[int, NewIngredient] = Field(
        default_factory=dict,
        description="Line index -> a NEW catalog ingredient to create (it must not exist yet).",
    )
    unit_mappings: dict[int, str] = Field(
        default_factory=dict, description="Line index -> catalog unit code."
    )
    categories: list[str] | None = Field(default=None, max_length=5)
    classification: DrinkClassification | None = None
    difficulty: Difficulty | None = None
    skills: list[str] | None = Field(default=None, max_length=12)
    placement: ApprovePlacement | None = None
    review_notes: CleanStr | None = Field(default=None, max_length=2000)


class RejectRequest(_Strict):
    review_notes: CleanStr = Field(
        min_length=3, max_length=2000, description="Why: the agent can read it."
    )
