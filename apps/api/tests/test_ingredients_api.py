from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RecipeType
from tests.factories import make_ingredient, make_recipe


async def test_search_by_alias_and_without_accents(
    client: AsyncClient, session: AsyncSession
) -> None:
    await make_ingredient(session, "Cilantro", aliases=("coriandro",))
    await make_ingredient(session, "Limón")
    await session.commit()

    by_alias = (await client.get("/api/v1/ingredients", params={"q": "coriandro"})).json()
    by_plain = (await client.get("/api/v1/ingredients", params={"q": "limon"})).json()

    assert [i["slug"] for i in by_alias] == ["cilantro"]
    assert [i["name"] for i in by_plain] == ["Limón"]


async def test_prefix_matches_come_first(client: AsyncClient, session: AsyncSession) -> None:
    await make_ingredient(session, "Aceite")
    await make_ingredient(session, "Cebolla")
    await session.commit()

    body = (await client.get("/api/v1/ingredients", params={"q": "ce"})).json()

    assert [i["name"] for i in body] == ["Cebolla", "Aceite"]


async def test_resolve_by_slugs(client: AsyncClient, session: AsyncSession) -> None:
    await make_ingredient(session, "Pollo")
    await make_ingredient(session, "Arroz")
    await make_ingredient(session, "Tomate")
    await session.commit()

    body = (await client.get("/api/v1/ingredients", params={"slugs": "pollo,arroz"})).json()

    assert sorted(i["slug"] for i in body) == ["arroz", "pollo"]


async def test_popular_ingredients_by_module(client: AsyncClient, session: AsyncSession) -> None:
    tomato = await make_ingredient(session, "Tomate")
    onion = await make_ingredient(session, "Cebolla")
    salt = await make_ingredient(session, "Sal", staple=True)
    lime = await make_ingredient(session, "Lima")
    await make_recipe(session, "Uno", ingredients=(tomato, onion, salt))
    await make_recipe(session, "Dos", ingredients=(tomato, salt))
    await make_recipe(session, "Trago", recipe_type=RecipeType.DRINK, ingredients=(lime,))
    await session.commit()

    body = (
        await client.get(
            "/api/v1/ingredients",
            params={"sort": "popular", "recipe_type": "cooking", "include_staples": "false"},
        )
    ).json()

    assert [(i["name"], i["recipe_count"]) for i in body] == [("Tomate", 2), ("Cebolla", 1)]


async def test_invalid_slug_list_is_rejected(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ingredients", params={"slugs": "DROP TABLE;"})
    assert response.status_code == 422
