from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category
from app.models.enums import RecipeType


async def _create_categories(session: AsyncSession) -> None:
    session.add_all(
        [
            Category(name="Postres", slug="postres", recipe_type=RecipeType.COOKING),
            Category(name="Entradas", slug="entradas", recipe_type=RecipeType.COOKING),
            Category(name="Sours", slug="sours", recipe_type=RecipeType.DRINK),
        ]
    )
    await session.commit()


async def test_list_categories_returns_all_sorted(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_categories(session)

    response = await client.get("/api/v1/categories")

    assert response.status_code == 200
    assert [c["slug"] for c in response.json()] == ["entradas", "postres", "sours"]


async def test_list_categories_filters_by_recipe_type(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_categories(session)

    response = await client.get("/api/v1/categories", params={"recipe_type": "drink"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["slug"] == "sours"
    assert body[0]["recipe_type"] == "drink"


async def test_list_categories_rejects_unknown_recipe_type(client: AsyncClient) -> None:
    response = await client.get("/api/v1/categories", params={"recipe_type": "pizza"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"][0]["loc"] == ["query", "recipe_type"]


async def test_list_categories_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/categories")
    assert response.status_code == 200
    assert response.json() == []
