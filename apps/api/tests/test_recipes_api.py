from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    Difficulty,
    DrinkClassification,
    RecipeStatus,
    RecipeType,
    SubstitutionType,
)
from tests.factories import (
    make_alternative,
    make_category,
    make_ingredient,
    make_recipe,
)


async def test_only_published_recipes_are_listed(
    client: AsyncClient, session: AsyncSession
) -> None:
    await make_recipe(session, "Publicada")
    await make_recipe(session, "Pendiente", status=RecipeStatus.PENDING)
    await make_recipe(session, "Borrador", status=RecipeStatus.DRAFT)
    await session.commit()

    body = (await client.get("/api/v1/recipes")).json()

    assert body["total"] == 1
    assert [r["title"] for r in body["items"]] == ["Publicada"]


async def test_unpublished_recipe_detail_is_not_found(
    client: AsyncClient, session: AsyncSession
) -> None:
    await make_recipe(session, "Secreta", status=RecipeStatus.PENDING)
    await session.commit()

    response = await client.get("/api/v1/recipes/secreta")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_search_ignores_accents_and_tolerates_typos(
    client: AsyncClient, session: AsyncSession
) -> None:
    await make_recipe(session, "Salmón al horno")
    await make_recipe(session, "Margarita", recipe_type=RecipeType.DRINK)
    await session.commit()

    by_accent = (await client.get("/api/v1/recipes", params={"q": "salmon"})).json()
    by_typo = (await client.get("/api/v1/recipes", params={"q": "margarta"})).json()

    assert [r["title"] for r in by_accent["items"]] == ["Salmón al horno"]
    assert [r["title"] for r in by_typo["items"]] == ["Margarita"]


async def test_sql_wildcards_never_reach_the_query(
    client: AsyncClient, session: AsyncSession
) -> None:
    await make_recipe(session, "Tarta")
    await make_recipe(session, "Pan")
    await session.commit()
    # Punctuation is stripped by normalization: "%" is an empty search, "t%a" is "t a".
    everything = (await client.get("/api/v1/recipes", params={"q": "%"})).json()
    pattern = (await client.get("/api/v1/recipes", params={"q": "t%a"})).json()
    assert everything["total"] == 2
    assert pattern["total"] == 0


async def test_filters_combine(client: AsyncClient, session: AsyncSession) -> None:
    soups = await make_category(session, "sopas")
    tomato = await make_ingredient(session, "Tomate")
    await make_recipe(
        session, "Sopa rápida", categories=(soups,), ingredients=(tomato,), prep=5, cook=10
    )
    await make_recipe(
        session, "Sopa lenta", categories=(soups,), ingredients=(tomato,), prep=10, cook=120
    )
    await make_recipe(session, "Sopa difícil", categories=(soups,), difficulty=Difficulty.HARD)
    await make_recipe(session, "Ensalada", ingredients=(tomato,))
    await session.commit()

    body = (
        await client.get(
            "/api/v1/recipes",
            params={
                "category": "sopas",
                "ingredients": "tomate",
                "max_time": 30,
                "difficulty": "easy",
            },
        )
    ).json()

    assert [r["title"] for r in body["items"]] == ["Sopa rápida"]
    assert body["items"][0]["total_time_minutes"] == 15


async def test_ingredient_filter_requires_all_ingredients(
    client: AsyncClient, session: AsyncSession
) -> None:
    tomato = await make_ingredient(session, "Tomate")
    onion = await make_ingredient(session, "Cebolla")
    await make_recipe(session, "Con ambos", ingredients=(tomato, onion))
    await make_recipe(session, "Solo tomate", ingredients=(tomato,))
    await session.commit()

    body = (await client.get("/api/v1/recipes", params={"ingredients": "tomate,cebolla"})).json()

    assert [r["title"] for r in body["items"]] == ["Con ambos"]


async def test_sorting_and_pagination(client: AsyncClient, session: AsyncSession) -> None:
    now = datetime.now(UTC)
    await make_recipe(session, "B lenta", prep=60, cook=0, published_at=now - timedelta(days=2))
    await make_recipe(session, "A media", prep=30, cook=0, published_at=now - timedelta(days=1))
    await make_recipe(session, "C rápida", prep=5, cook=0, published_at=now)
    await session.commit()

    async def titles(**params: object) -> list[str]:
        body = (await client.get("/api/v1/recipes", params=params)).json()
        return [r["title"] for r in body["items"]]

    assert await titles(sort="newest") == ["C rápida", "A media", "B lenta"]
    assert await titles(sort="title") == ["A media", "B lenta", "C rápida"]
    assert await titles(sort="quickest") == ["C rápida", "A media", "B lenta"]

    page2 = (
        await client.get("/api/v1/recipes", params={"sort": "title", "page_size": 2, "page": 2})
    ).json()
    assert page2["total"] == 3
    assert page2["pages"] == 2
    assert [r["title"] for r in page2["items"]] == ["C rápida"]


async def test_page_size_is_bounded(client: AsyncClient) -> None:
    response = await client.get("/api/v1/recipes", params={"page_size": 500})
    assert response.status_code == 422


async def test_detail_includes_substitutions_sources_and_related(
    client: AsyncClient, session: AsyncSession
) -> None:
    lime = await make_ingredient(session, "Lima")
    lemon = await make_ingredient(session, "Limón")
    rum = await make_ingredient(session, "Ron blanco")
    await make_alternative(session, lime, lemon, SubstitutionType.SIMILAR)
    classic = await make_recipe(
        session,
        "Daiquiri",
        recipe_type=RecipeType.DRINK,
        ingredients=(rum, lime),
        drink=DrinkClassification.CLASSIC,
    )
    await make_recipe(
        session,
        "Hemingway",
        recipe_type=RecipeType.DRINK,
        ingredients=(rum, lime),
        drink=DrinkClassification.VARIATION,
        variation_of=classic,
    )
    await make_recipe(session, "Pollo al limón", ingredients=(lemon,))
    await session.commit()

    body = (await client.get("/api/v1/recipes/daiquiri")).json()

    lime_line = next(i for i in body["ingredients"] if i["ingredient"]["slug"] == "lima")
    assert lime_line["alternatives"][0]["ingredient"]["slug"] == "limon"
    assert body["sources"][0]["source_name"] == "Tests"
    assert body["drink"]["classification"] == "classic"
    assert body["drink"]["variations"] == [{"slug": "hemingway", "title": "Hemingway"}]
    # Related recipes are the same type only: the chicken dish is excluded.
    assert [r["slug"] for r in body["related"]] == ["hemingway"]

    variation = (await client.get("/api/v1/recipes/hemingway")).json()
    assert variation["drink"]["variation_of"] == {"slug": "daiquiri", "title": "Daiquiri"}


async def test_categories_include_published_recipe_counts(
    client: AsyncClient, session: AsyncSession
) -> None:
    soups = await make_category(session, "sopas")
    await make_recipe(session, "Sopa 1", categories=(soups,))
    await make_recipe(session, "Sopa 2", categories=(soups,), status=RecipeStatus.PENDING)
    await session.commit()

    body = (await client.get("/api/v1/categories")).json()

    assert body[0]["recipe_count"] == 1
