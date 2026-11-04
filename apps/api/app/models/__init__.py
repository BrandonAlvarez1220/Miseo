"""Import every model so ``Base.metadata`` is complete (Alembic autogenerate, tests)."""

from app.models.catalog import (
    BartendingTechnique,
    Category,
    GlassType,
    Ingredient,
    IngredientAlias,
    IngredientAlternative,
    IngredientCategory,
    Unit,
)
from app.models.community import RecipeContribution, RecipeRevision, UserFavorite
from app.models.ingestion import DuplicateCandidate, IngestionIssue, IngestionJob
from app.models.recipe import (
    DrinkDetails,
    PreparationStep,
    Recipe,
    RecipeIngredient,
    RecipeSource,
    recipe_category,
)
from app.models.user import AppUser

__all__ = [
    "AppUser",
    "BartendingTechnique",
    "Category",
    "DrinkDetails",
    "DuplicateCandidate",
    "GlassType",
    "IngestionIssue",
    "IngestionJob",
    "Ingredient",
    "IngredientAlias",
    "IngredientAlternative",
    "IngredientCategory",
    "PreparationStep",
    "Recipe",
    "RecipeContribution",
    "RecipeIngredient",
    "RecipeRevision",
    "RecipeSource",
    "Unit",
    "UserFavorite",
    "recipe_category",
]
