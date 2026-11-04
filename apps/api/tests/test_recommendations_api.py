from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RecipeStatus, RecipeType, SubstitutionType
from tests.factories import make_alternative, make_ingredient, make_recipe


async def _pantry(session: AsyncSession) -> None:
    chicken = await make_ingredient(session, "Pollo")
    rice = await make_ingredient(session, "Arroz")
    lime = await make_ingredient(session, "Lima")
    lemon = await make_ingredient(session, "Limón")
    salt = await make_ingredient(session, "Sal", staple=True)
    pepper = await make_ingredient(session, "Pimiento")
    await make_alternative(session, lime, lemon, SubstitutionType.SIMILAR)
    await make_recipe(session, "Arroz con pollo", ingredients=(chicken, rice, salt))
    await make_recipe(session, "Pollo a la lima", ingredients=(chicken, lime))
    await make_recipe(session, "Pollo con pimiento", ingredients=(chicken, pepper))
    await make_recipe(session, "Borrador", ingredients=(chicken,), status=RecipeStatus.DRAFT)
    await make_recipe(session, "Limonada", recipe_type=RecipeType.DRINK, ingredients=(lemon,))
    await session.commit()


async def _titles(client: AsyncClient, **params: object) -> list[str]:
    response = await client.get("/api/v1/recommendations", params=params)
    assert response.status_code == 200
    return [r["recipe"]["title"] for r in response.json()["results"]]


async def test_modes(client: AsyncClient, session: AsyncSession) -> None:
    await _pantry(session)
    pantry = "pollo,arroz,limon"

    assert await _titles(client, ingredients=pantry, mode="exact", recipe_type="cooking") == [
        "Arroz con pollo"
    ]
    assert await _titles(client, ingredients=pantry, mode="flexible", recipe_type="cooking") == [
        "Arroz con pollo",
        "Pollo a la lima",
    ]
    assert await _titles(client, ingredients=pantry, mode="discover", recipe_type="cooking") == [
        "Arroz con pollo",
        "Pollo a la lima",
        "Pollo con pimiento",
    ]


async def test_result_details(client: AsyncClient, session: AsyncSession) -> None:
    await _pantry(session)

    body = (
        await client.get(
            "/api/v1/recommendations",
            params={"ingredients": "pollo,limon", "mode": "discover", "recipe_type": "cooking"},
        )
    ).json()
    by_title = {r["recipe"]["title"]: r for r in body["results"]}

    lime_dish = by_title["Pollo a la lima"]
    assert lime_dish["match_percentage"] == 88
    assert lime_dish["substitutions"][0]["missing"]["slug"] == "lima"
    assert lime_dish["substitutions"][0]["substitute"]["slug"] == "limon"

    rice_dish = by_title["Arroz con pollo"]
    assert [i["slug"] for i in rice_dish["missing_ingredients"]] == ["arroz"]
    assert [i["slug"] for i in rice_dish["assumed_staples"]] == ["sal"]
    assert rice_dish["match_percentage"] == 67


async def test_staples_can_be_disabled(client: AsyncClient, session: AsyncSession) -> None:
    await _pantry(session)
    titles = await _titles(client, ingredients="pollo,arroz", mode="exact", assume_staples="false")
    assert titles == []


async def test_unknown_ingredients_are_reported(client: AsyncClient, session: AsyncSession) -> None:
    await _pantry(session)

    body = (
        await client.get("/api/v1/recommendations", params={"ingredients": "pollo,unicornio"})
    ).json()

    assert body["unknown_ingredients"] == ["unicornio"]
    assert [i["slug"] for i in body["ingredients"]] == ["pollo"]


async def test_empty_selection_returns_no_results(client: AsyncClient) -> None:
    body = (await client.get("/api/v1/recommendations")).json()
    assert body["results"] == []
    assert body["total"] == 0


async def test_too_many_ingredients_is_rejected(client: AsyncClient) -> None:
    many = ",".join(f"i{n}" for n in range(41))
    response = await client.get("/api/v1/recommendations", params={"ingredients": many})
    assert response.status_code == 400
