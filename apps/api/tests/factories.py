"""Small helpers to build test data explicitly inside each test."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Category,
    DrinkDetails,
    Ingredient,
    IngredientAlias,
    IngredientAlternative,
    PreparationStep,
    Recipe,
    RecipeIngredient,
    RecipeSource,
    Unit,
)
from app.models.enums import (
    Difficulty,
    DrinkClassification,
    OriginType,
    RecipeStatus,
    RecipeType,
    SourceType,
    SubstitutionType,
    UnitType,
)
from app.services.normalization import normalize_text, slugify


async def make_ingredient(
    session: AsyncSession, name: str, *, staple: bool = False, aliases: tuple[str, ...] = ()
) -> Ingredient:
    ingredient = Ingredient(
        name=name, normalized_name=normalize_text(name), slug=slugify(name), is_staple=staple
    )
    session.add(ingredient)
    await session.flush()
    for alias in aliases:
        session.add(
            IngredientAlias(
                ingredient_id=ingredient.id, alias=alias, normalized_alias=normalize_text(alias)
            )
        )
    await session.flush()
    return ingredient


async def make_unit(session: AsyncSession, code: str = "g") -> Unit:
    unit = Unit(
        code=code, name=code, plural_name=code, unit_type=UnitType.MASS, to_base_factor=Decimal(1)
    )
    session.add(unit)
    await session.flush()
    return unit


async def make_category(
    session: AsyncSession, slug: str, recipe_type: RecipeType = RecipeType.COOKING
) -> Category:
    category = Category(name=slug.title(), slug=slug, recipe_type=recipe_type)
    session.add(category)
    await session.flush()
    return category


async def make_alternative(
    session: AsyncSession,
    original: Ingredient,
    substitute: Ingredient,
    kind: SubstitutionType = SubstitutionType.SIMILAR,
) -> None:
    session.add(
        IngredientAlternative(
            ingredient_id=original.id,
            alternative_ingredient_id=substitute.id,
            substitution_type=kind,
        )
    )
    await session.flush()


async def make_recipe(
    session: AsyncSession,
    title: str,
    *,
    ingredients: tuple[Ingredient, ...] = (),
    optional: tuple[Ingredient, ...] = (),
    recipe_type: RecipeType = RecipeType.COOKING,
    status: RecipeStatus = RecipeStatus.PUBLISHED,
    categories: tuple[Category, ...] = (),
    difficulty: Difficulty | None = Difficulty.EASY,
    prep: int | None = 10,
    cook: int | None = 10,
    published_at: datetime | None = None,
    drink: DrinkClassification | None = None,
    variation_of: Recipe | None = None,
) -> Recipe:
    recipe = Recipe(
        title=title,
        slug=slugify(title),
        recipe_type=recipe_type,
        status=status,
        origin_type=OriginType.CURATED,
        difficulty=difficulty,
        preparation_time_minutes=prep,
        cooking_time_minutes=cook,
        servings=2,
        published_at=published_at
        or (datetime.now(UTC) if status == RecipeStatus.PUBLISHED else None),
        categories=list(categories),
    )
    recipe.ingredients = [
        RecipeIngredient(ingredient_id=i.id, position=n, quantity=Decimal(1))
        for n, i in enumerate(ingredients)
    ] + [
        RecipeIngredient(ingredient_id=i.id, position=100 + n, is_optional=True)
        for n, i in enumerate(optional)
    ]
    recipe.steps = [PreparationStep(step_number=1, description="Mezclar.")]
    recipe.sources = [
        RecipeSource(source_name="Tests", source_type=SourceType.ORIGINAL, attribution="Test data")
    ]
    session.add(recipe)
    await session.flush()
    if drink is not None:
        session.add(
            DrinkDetails(
                recipe_id=recipe.id,
                is_alcoholic=True,
                classification=drink,
                variation_of_id=variation_of.id if variation_of else None,
            )
        )
        await session.flush()
    return recipe
