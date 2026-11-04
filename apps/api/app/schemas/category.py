import uuid

from app.models.enums import RecipeType
from app.schemas.common import APIModel


class CategoryRead(APIModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    recipe_type: RecipeType
