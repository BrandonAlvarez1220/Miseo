from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RecipeStatus
from tests.factories import make_path, make_recipe, make_skill, tag_skills


async def _ladder(session: AsyncSession) -> None:
    chop = await make_skill(session, "picar")
    sear = await make_skill(session, "sellar")
    eggs = await make_recipe(session, "Huevos")
    soup = await make_recipe(session, "Sopa")
    steak = await make_recipe(session, "Bistec")
    draft = await make_recipe(session, "Borrador", status=RecipeStatus.DRAFT)
    await tag_skills(session, eggs, chop)
    await tag_skills(session, steak, chop, sear)
    await make_path(
        session,
        "cocina",
        [("Fácil", 2, [eggs, soup, draft]), ("Casa", 1, [steak])],
    )
    await session.commit()


async def test_list_paths_with_counts(client: AsyncClient, session: AsyncSession) -> None:
    await _ladder(session)

    body = (await client.get("/api/v1/paths")).json()

    assert body == [
        {
            "slug": "cocina",
            "title": "Cocina",
            "discipline": "cooking",
            "description": None,
            "stage_count": 2,
            "dish_count": 4,
            "skill_count": 2,
        }
    ]


async def test_path_detail_marks_new_skills_in_ladder_order(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _ladder(session)

    body = (await client.get("/api/v1/paths/cocina")).json()
    first, second = body["stages"]

    # Unpublished dishes are hidden and the unlock requirement adapts to what is left.
    assert [d["recipe"]["title"] for d in first["dishes"]] == ["Huevos", "Sopa"]
    assert first["dishes_to_unlock"] == 2
    assert first["dishes"][0]["skills"] == [
        {"slug": "picar", "name": "Picar", "tip": "Tip.", "is_new": True}
    ]
    steak_skills = {s["slug"]: s["is_new"] for s in second["dishes"][0]["skills"]}
    assert steak_skills == {"picar": False, "sellar": True}


async def test_recipe_detail_includes_skills_and_paths(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _ladder(session)

    body = (await client.get("/api/v1/recipes/bistec")).json()

    assert [s["slug"] for s in body["skills"]] == ["picar", "sellar"]
    assert body["paths"] == [
        {"path_slug": "cocina", "path_title": "Cocina", "stage_position": 2, "stage_title": "Casa"}
    ]


async def test_unknown_path_is_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/paths/no-existe")
    assert response.status_code == 404
