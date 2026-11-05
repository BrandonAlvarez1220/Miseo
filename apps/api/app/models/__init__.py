"""Import every model so ``Base.metadata`` is complete (Alembic autogenerate, tests)."""

from app.models.agent import Agent
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
from app.models.learning import LearningPath, PathDish, PathStage, Skill, recipe_skill
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
    "Agent",
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
    "LearningPath",
    "PathDish",
    "PathStage",
    "PreparationStep",
    "Recipe",
    "RecipeContribution",
    "RecipeIngredient",
    "RecipeRevision",
    "RecipeSource",
    "Skill",
    "Unit",
    "UserFavorite",
    "recipe_category",
    "recipe_skill",
]
