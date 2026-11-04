import uuid

from app.schemas.common import APIModel
from app.schemas.recipe import CategoryRef


class IngredientRead(APIModel):
    id: uuid.UUID
    name: str
    slug: str
    category: CategoryRef | None
    is_staple: bool
    is_alcoholic: bool
    recipe_count: int
