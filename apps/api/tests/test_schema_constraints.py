"""Database rules from docs/DATABASE.md enforced at the database level."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DrinkDetails,
    Ingredient,
    IngredientAlternative,
    Recipe,
    RecipeIngredient,
    Unit,
)
from app.models.enums import (
    DrinkClassification,
    OriginType,
    RecipeStatus,
    RecipeType,
    SubstitutionType,
    UnitType,
)


async def _recipe(session: AsyncSession, slug: str = "test", **kwargs: object) -> Recipe:
    recipe = Recipe(
        title="Test",
        slug=slug,
        recipe_type=kwargs.pop("recipe_type", RecipeType.COOKING),
        origin_type=OriginType.CURATED,
        **kwargs,
    )
    session.add(recipe)
    await session.flush()
    return recipe


async def _ingredient(session: AsyncSession, normalized: str) -> Ingredient:
    ingredient = Ingredient(
        name=normalized.title(), normalized_name=normalized, slug=normalized.replace(" ", "-")
    )
    session.add(ingredient)
    await session.flush()
    return ingredient


async def test_ingredient_normalized_name_is_unique(session: AsyncSession) -> None:
    await _ingredient(session, "limon")
    session.add(Ingredient(name="Limón", normalized_name="limon", slug="limon-2"))
    with pytest.raises(IntegrityError, match="uq_ingredient_normalized_name"):
        await session.flush()


async def test_same_ingredient_twice_without_group_is_rejected(session: AsyncSession) -> None:
    recipe = await _recipe(session)
    sugar = await _ingredient(session, "azucar")
    session.add_all(
        [
            RecipeIngredient(recipe_id=recipe.id, ingredient_id=sugar.id),
            RecipeIngredient(recipe_id=recipe.id, ingredient_id=sugar.id),
        ]
    )
    with pytest.raises(IntegrityError, match="uq_recipe_ingredient"):
        await session.flush()


async def test_same_ingredient_in_different_groups_is_allowed(session: AsyncSession) -> None:
    recipe = await _recipe(session)
    sugar = await _ingredient(session, "azucar")
    session.add_all(
        [
            RecipeIngredient(recipe_id=recipe.id, ingredient_id=sugar.id, group_label="Masa"),
            RecipeIngredient(recipe_id=recipe.id, ingredient_id=sugar.id, group_label="Cobertura"),
        ]
    )
    await session.flush()


async def test_quantity_range_must_be_ordered(session: AsyncSession) -> None:
    recipe = await _recipe(session)
    egg = await _ingredient(session, "huevo")
    session.add(
        RecipeIngredient(
            recipe_id=recipe.id, ingredient_id=egg.id, quantity=Decimal(3), quantity_max=Decimal(2)
        )
    )
    with pytest.raises(IntegrityError, match="quantity_range_valid"):
        await session.flush()


async def test_unknown_unit_is_rejected(session: AsyncSession) -> None:
    recipe = await _recipe(session)
    egg = await _ingredient(session, "huevo")
    session.add(RecipeIngredient(recipe_id=recipe.id, ingredient_id=egg.id, unit_code="handful"))
    with pytest.raises(IntegrityError, match="fk_recipe_ingredient_unit_code_unit"):
        await session.flush()


async def test_known_unit_is_accepted(session: AsyncSession) -> None:
    session.add(
        Unit(
            code="g",
            name="gramo",
            plural_name="gramos",
            unit_type=UnitType.MASS,
            to_base_factor=Decimal(1),
        )
    )
    recipe = await _recipe(session)
    flour = await _ingredient(session, "harina")
    session.add(
        RecipeIngredient(
            recipe_id=recipe.id, ingredient_id=flour.id, quantity=Decimal(250), unit_code="g"
        )
    )
    await session.flush()


async def test_enum_values_are_checked_by_the_database(session: AsyncSession) -> None:
    with pytest.raises(IntegrityError, match="ck_recipe_status"):
        await session.execute(
            text(
                "INSERT INTO recipe (title, slug, recipe_type, origin_type, status) "
                "VALUES ('x', 'x', 'cooking', 'curated', 'live')"
            )
        )


async def test_published_recipe_requires_published_at(session: AsyncSession) -> None:
    with pytest.raises(IntegrityError, match="published_has_date"):
        await _recipe(session, status=RecipeStatus.PUBLISHED)


async def test_published_recipe_with_date_is_valid(session: AsyncSession) -> None:
    await _recipe(session, status=RecipeStatus.PUBLISHED, published_at=datetime.now(UTC))


async def test_ingredient_cannot_substitute_itself(session: AsyncSession) -> None:
    butter = await _ingredient(session, "mantequilla")
    session.add(
        IngredientAlternative(
            ingredient_id=butter.id,
            alternative_ingredient_id=butter.id,
            substitution_type=SubstitutionType.EQUIVALENT,
        )
    )
    with pytest.raises(IntegrityError, match="not_self"):
        await session.flush()


async def test_drink_variation_requires_parent(session: AsyncSession) -> None:
    drink = await _recipe(session, recipe_type=RecipeType.DRINK)
    session.add(
        DrinkDetails(
            recipe_id=drink.id, is_alcoholic=True, classification=DrinkClassification.VARIATION
        )
    )
    with pytest.raises(IntegrityError, match="variation_has_parent"):
        await session.flush()


async def test_drink_variation_with_parent_is_valid(session: AsyncSession) -> None:
    classic = await _recipe(session, slug="daiquiri", recipe_type=RecipeType.DRINK)
    variation = await _recipe(session, slug="hemingway", recipe_type=RecipeType.DRINK)
    session.add(
        DrinkDetails(
            recipe_id=variation.id,
            is_alcoholic=True,
            classification=DrinkClassification.VARIATION,
            variation_of_id=classic.id,
        )
    )
    await session.flush()


async def test_deleting_recipe_cascades_to_its_ingredients(session: AsyncSession) -> None:
    recipe = await _recipe(session)
    salt = await _ingredient(session, "sal")
    session.add(RecipeIngredient(recipe_id=recipe.id, ingredient_id=salt.id))
    await session.flush()

    await session.execute(text("DELETE FROM recipe WHERE id = :id"), {"id": recipe.id})
    remaining = await session.scalar(text("SELECT count(*) FROM recipe_ingredient"))
    assert remaining == 0


async def test_ingredient_in_use_cannot_be_deleted(session: AsyncSession) -> None:
    recipe = await _recipe(session)
    salt = await _ingredient(session, "sal")
    session.add(RecipeIngredient(recipe_id=recipe.id, ingredient_id=salt.id))
    await session.flush()

    with pytest.raises(IntegrityError, match="fk_recipe_ingredient_ingredient_id_ingredient"):
        await session.execute(text("DELETE FROM ingredient WHERE id = :id"), {"id": salt.id})


async def test_ingredient_color_must_be_lowercase_hex(session: AsyncSession) -> None:
    ingredient = await _ingredient(session, "campari")
    ingredient.color = "red"
    with pytest.raises(IntegrityError, match="color_hex"):
        await session.flush()
