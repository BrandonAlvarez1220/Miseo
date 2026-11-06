from pydantic import BaseModel, Field

from app.models.enums import RecipeType
from app.schemas.common import APIModel
from app.schemas.recipe import RecipeSummary


class SkillRead(APIModel):
    slug: str
    name: str
    tip: str


class DishSkill(SkillRead):
    is_new: bool = Field(description="True when this dish is the first in the path to teach it.")


class PathDishRead(BaseModel):
    recipe: RecipeSummary
    skills: list[DishSkill]


class PathStageRead(BaseModel):
    position: int
    title: str
    description: str | None
    dishes_to_unlock: int
    dishes: list[PathDishRead]


class PathSummary(BaseModel):
    slug: str
    title: str
    discipline: RecipeType
    description: str | None
    stage_count: int
    dish_count: int
    skill_count: int


class PathDetail(PathSummary):
    stages: list[PathStageRead]
