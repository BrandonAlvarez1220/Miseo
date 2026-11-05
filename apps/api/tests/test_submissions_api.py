import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IngestionJob, Recipe
from tests.auth_helpers import bearer
from tests.submission_helpers import (
    connect_agent,
    margarita_like,
    omelette,
    seed_catalog,
    variant,
)

SUBMIT = "/api/v1/agent/submissions"


async def _count_jobs(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(IngestionJob)) or 0


@pytest.fixture
async def agent(client: AsyncClient, session: AsyncSession) -> dict[str, str]:
    await seed_catalog(session)
    await session.commit()
    return await connect_agent(client, session)


def _codes(body: dict, severity: str | None = None) -> list[str]:
    return [i["code"] for i in body["issues"] if severity in (None, i["severity"])]


# ---- the happy path -------------------------------------------------------------------


async def test_a_clean_submission_is_queued_for_review_not_published(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str]
) -> None:
    response = await client.post(SUBMIT, headers=agent, json=omelette())

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "needs_review"
    assert body["outcome"] == "created"
    assert body["blocking_issues"] == 0
    assert body["recipe_slug"] is None
    # Nothing reached the public catalog.
    titles = (await client.get("/api/v1/recipes", params={"q": "omelette"})).json()
    assert titles["total"] == 0
    assert (
        await session.scalar(
            select(func.count()).select_from(Recipe).where(Recipe.title.like("Omelette%"))
        )
        == 0
    )


async def test_the_analysis_scores_difficulty_and_suggests_skills_and_a_stage(
    client: AsyncClient, agent: dict[str, str]
) -> None:
    body = (await client.post(SUBMIT, headers=agent, json=omelette())).json()

    analysis = body["analysis"]
    assert analysis["difficulty"]["score"] == 1
    assert analysis["difficulty"]["label"] == "easy"
    assert "3 pasos" in analysis["difficulty"]["reasons"]
    assert "cuajar-huevo" in {s["slug"] for s in analysis["skills"]}
    cooking_path = next(p for p in analysis["placements"] if p["path_slug"] == "cocina")
    assert cooking_path["stage_position"] == 1
    assert cooking_path["new_stage"] is False


async def test_units_and_ingredients_are_resolved_through_aliases_and_synonyms(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str]
) -> None:
    submitted = (await client.post(SUBMIT, headers=agent, json=omelette())).json()
    _, reviewer = await _moderator(session)

    detail = (
        await client.get(f"/api/v1/review/submissions/{submitted['id']}", headers=reviewer)
    ).json()
    lines = {line["name"]: line for line in detail["lines"]}

    assert lines["huevos"]["ingredient_slug"] == "huevo"  # alias
    assert lines["queso oaxaca"]["unit_code"] == "g"  # "gramos"
    assert lines["mantequilla"]["unit_code"] == "tbsp"  # "cucharada"
    assert lines["sal"]["unit_code"] == "to_taste"


async def _moderator(session: AsyncSession):  # type: ignore[no-untyped-def]
    from app.models.enums import UserRole
    from tests.auth_helpers import make_user

    return await make_user(session, UserRole.MODERATOR)


# ---- catalog mapping issues -----------------------------------------------------------


async def test_an_unknown_ingredient_is_flagged_with_candidates_never_auto_mapped(
    client: AsyncClient, agent: dict[str, str]
) -> None:
    body = omelette()
    body["recipe"]["ingredients"][0] = {"name": "Pollo deshuesado", "quantity": 300, "unit": "g"}

    result = (await client.post(SUBMIT, headers=agent, json=body)).json()

    errors = [i for i in result["issues"] if i["severity"] == "error"]
    assert [e["code"] for e in errors] == ["unknown_ingredient"]
    assert result["blocking_issues"] == 1
    assert "Pollo (pollo)" in errors[0]["message"]  # offered as a candidate


async def test_an_explicit_catalog_slug_is_used_and_a_wrong_one_is_an_error(
    client: AsyncClient, agent: dict[str, str]
) -> None:
    good = omelette()
    good["recipe"]["ingredients"][0] = {
        "name": "huevo de rancho",
        "ingredient_slug": "huevo",
        "quantity": 4,
        "unit": "piece",
    }
    bad = omelette()
    bad["source"]["url"] = "https://example.com/otra"
    bad["recipe"]["ingredients"][0] = {
        "name": "huevo",
        "ingredient_slug": "no-existe",
        "quantity": 4,
        "unit": "piece",
    }

    assert (await client.post(SUBMIT, headers=agent, json=good)).json()["blocking_issues"] == 0
    result = (await client.post(SUBMIT, headers=agent, json=bad)).json()
    assert result["blocking_issues"] == 1
    assert "no-existe" in result["issues"][0]["message"]


async def test_unknown_unit_and_quantity_problems_are_reported(
    client: AsyncClient, agent: dict[str, str]
) -> None:
    body = omelette()
    body["recipe"]["ingredients"] += [
        {"name": "cebolla", "quantity": 1, "unit": "puñado"},  # unknown unit
        {"name": "ajo", "quantity": 2},  # quantity without unit
        {"name": "pimienta negra"},  # no quantity, not "to taste"
        {"name": "harina", "quantity": 50, "unit": "kg"},  # 50 kg: implausible
    ]

    result = (await client.post(SUBMIT, headers=agent, json=body)).json()

    assert "unknown_unit" in _codes(result, "error")
    warnings = _codes(result, "warning")
    assert {"missing_unit", "missing_quantity", "implausible_quantity"} <= set(warnings)


async def test_same_ingredient_twice_in_one_group_is_rejected_but_different_groups_are_fine(
    client: AsyncClient, agent: dict[str, str]
) -> None:
    twice = omelette()
    twice["recipe"]["ingredients"].append({"name": "huevo", "quantity": 1, "unit": "piece"})
    rejected = await client.post(SUBMIT, headers=agent, json=twice)
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "invalid_submission"

    grouped = omelette()
    grouped["recipe"]["ingredients"][0]["group"] = "Masa"
    grouped["recipe"]["ingredients"].append(
        {"name": "huevo", "quantity": 1, "unit": "piece", "group": "Cobertura"}
    )
    assert (await client.post(SUBMIT, headers=agent, json=grouped)).status_code == 201


async def test_categories_must_exist_for_the_recipe_type(
    client: AsyncClient, agent: dict[str, str]
) -> None:
    body = omelette(categories=["sours", "no-existe"])  # "sours" is a drink category

    result = (await client.post(SUBMIT, headers=agent, json=body)).json()

    assert _codes(result, "warning").count("unknown_category") == 2
    assert "no_category" in _codes(result)


# ---- schema validation ----------------------------------------------------------------


@pytest.mark.parametrize(
    "changes",
    [
        {"recipe.ingridients": []},  # typo: unknown fields are rejected
        {"source.url": None},  # a website source needs its url
        {"source.url": "javascript:alert(1)"},
        {"recipe.title": "ab"},
        {"recipe.servings": 0},
        {"recipe.steps": []},
        {"recipe.steps.0": "ok"},  # step too short
        {"recipe.recipe_type": "drink"},  # a drink needs drink data
        {"recipe.title": "Título‮gnorp"},  # bidirectional override character
        {"recipe.description": "bad\x00char"},
        {"recipe.ingredients.0.quantity": -1},
        {"recipe.ingredients.0.quantity_max": 1},  # max < quantity
        {"recipe.preparation_time_minutes": 5000},
    ],
    ids=lambda c: next(iter(c)),
)
async def test_invalid_submissions_are_rejected_with_422(
    client: AsyncClient, agent: dict[str, str], changes: dict
) -> None:
    body = variant(omelette(), **{k: v for k, v in changes.items() if k != "recipe.ingridients"})
    if "recipe.ingridients" in changes:
        body["recipe"]["ingridients"] = []

    response = await client.post(SUBMIT, headers=agent, json=body)

    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "validation_error"


async def test_cooking_recipes_cannot_carry_drink_data(
    client: AsyncClient, agent: dict[str, str]
) -> None:
    body = omelette(drink={"is_alcoholic": False})
    assert (await client.post(SUBMIT, headers=agent, json=body)).status_code == 422


async def test_whitespace_is_cleaned_and_html_is_stored_as_plain_text(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str]
) -> None:
    body = omelette(title="  Omelette \n  de   queso <b>rico</b>  ")
    submitted = (await client.post(SUBMIT, headers=agent, json=body)).json()
    _, reviewer = await _moderator(session)

    detail = (
        await client.get(f"/api/v1/review/submissions/{submitted['id']}", headers=reviewer)
    ).json()

    # Collapsed whitespace; markup is kept as inert text (the web escapes everything).
    assert detail["title"] == "Omelette de queso <b>rico</b>"


# ---- idempotency and revisions --------------------------------------------------------


async def test_the_same_recipe_never_creates_two_jobs(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str]
) -> None:
    first = await client.post(SUBMIT, headers=agent, json=omelette())
    retry = await client.post(SUBMIT, headers=agent, json=omelette())

    assert first.status_code == 201
    assert retry.status_code == 200
    assert retry.json()["outcome"] == "unchanged"
    assert retry.json()["id"] == first.json()["id"]
    assert await _count_jobs(session) == 1


async def test_other_spellings_of_the_same_url_are_one_recipe(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str]
) -> None:
    first = (await client.post(SUBMIT, headers=agent, json=omelette())).json()
    other_spelling = variant(
        omelette(),
        **{
            "source.url": "https://EXAMPLE.com/recetas/omelette-de-queso/?utm_source=x&fbclid=1#top"
        },
    )

    response = (await client.post(SUBMIT, headers=agent, json=other_spelling)).json()

    # Host case, trailing slash, utm_*/fbclid and #fragment do not make a new recipe. The
    # text differs, so it counts as a (harmless) revision of the same single job.
    assert response["id"] == first["id"]
    assert response["outcome"] == "updated"
    assert await _count_jobs(session) == 1


async def test_an_agent_can_fix_a_submission_while_it_is_in_review(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str]
) -> None:
    broken = omelette()
    broken["recipe"]["ingredients"][0] = {"name": "Pollo deshuesado", "quantity": 300, "unit": "g"}
    first = (await client.post(SUBMIT, headers=agent, json=broken)).json()
    assert first["blocking_issues"] == 1

    fixed = await client.post(SUBMIT, headers=agent, json=omelette())

    assert fixed.status_code == 200
    body = fixed.json()
    assert body["outcome"] == "updated"
    assert body["id"] == first["id"]
    assert body["blocking_issues"] == 0  # old issues replaced, not accumulated
    assert await _count_jobs(session) == 1


async def test_another_agent_cannot_overwrite_a_submission(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str]
) -> None:
    first = (await client.post(SUBMIT, headers=agent, json=omelette())).json()
    gemini = await connect_agent(client, session, "Gemini", "gemini")
    tampered = variant(omelette(), **{"recipe.title": "Receta distinta"})

    response = await client.post(SUBMIT, headers=gemini, json=tampered)

    assert response.json()["outcome"] == "unchanged"
    assert response.json()["id"] == first["id"]
    _, reviewer = await _moderator(session)
    detail = (
        await client.get(f"/api/v1/review/submissions/{first['id']}", headers=reviewer)
    ).json()
    assert detail["title"] == "Omelette de queso Oaxaca"
    assert detail["agent"]["name"] == "Claude"


async def test_revisions_are_capped(
    client: AsyncClient, agent: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    await client.post(SUBMIT, headers=agent, json=omelette())
    statuses = []
    for n in range(8):
        response = await client.post(
            SUBMIT, headers=agent, json=variant(omelette(), **{"recipe.servings": 3 + n})
        )
        statuses.append(response.status_code)

    assert statuses[:5] == [200] * 5
    assert 409 in statuses


# ---- limits ---------------------------------------------------------------------------


async def test_hourly_submission_limit_returns_429_with_retry_after(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str]
) -> None:
    client._transport.app.state.settings = client._transport.app.state.settings.model_copy(  # type: ignore[attr-defined]
        update={"agent_max_submissions_per_hour": 2}
    )
    for n in range(2):
        body = variant(omelette(), **{"source.url": f"https://example.com/r/{n}"})
        assert (await client.post(SUBMIT, headers=agent, json=body)).status_code == 201

    third = await client.post(
        SUBMIT, headers=agent, json=variant(omelette(), **{"source.url": "https://example.com/r/3"})
    )

    assert third.status_code == 429
    assert third.json()["error"]["code"] == "rate_limited"
    assert third.headers["retry-after"]
    assert await _count_jobs(session) == 2


async def test_pending_queue_limit_and_updates_do_not_count_as_new(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str]
) -> None:
    client._transport.app.state.settings = client._transport.app.state.settings.model_copy(  # type: ignore[attr-defined]
        update={"agent_max_pending": 1}
    )
    assert (await client.post(SUBMIT, headers=agent, json=omelette())).status_code == 201

    blocked = await client.post(
        SUBMIT,
        headers=agent,
        json=variant(omelette(), **{"source.url": "https://example.com/otra"}),
    )
    revised = await client.post(
        SUBMIT, headers=agent, json=variant(omelette(), **{"recipe.servings": 4})
    )

    assert blocked.status_code == 429
    assert revised.status_code == 200  # fixing the one waiting submission is always allowed


# ---- duplicates -----------------------------------------------------------------------


async def test_a_copy_of_an_existing_recipe_is_flagged_as_a_possible_duplicate(
    client: AsyncClient, agent: dict[str, str]
) -> None:
    body = omelette(
        title="Guacamole",
        categories=["entradas"],
        ingredients=[
            {"name": "aguacate", "quantity": 3, "unit": "piece"},
            {"name": "lima", "quantity": 1, "unit": "piece"},
            {"name": "cebolla", "quantity": 1, "unit": "piece"},
            {"name": "tomate", "quantity": 1, "unit": "piece"},
            {"name": "cilantro", "quantity": 2, "unit": "tbsp"},
        ],
    )

    result = (await client.post(SUBMIT, headers=agent, json=body)).json()

    duplicates = result["analysis"]["duplicates"]
    assert duplicates[0]["slug"] == "guacamole"
    assert duplicates[0]["kind"] == "recipe"
    assert "possible_duplicate" in _codes(result, "warning")


async def test_agents_notice_each_others_pending_submissions(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str]
) -> None:
    await client.post(SUBMIT, headers=agent, json=omelette())
    gemini = await connect_agent(client, session, "Gemini", "gemini")
    similar = variant(
        omelette(),
        **{
            "source.url": "https://example.net/omelette",
            "recipe.title": "Omelette de queso oaxaca",
        },
    )

    result = (await client.post(SUBMIT, headers=gemini, json=similar)).json()

    assert any(d["kind"] == "submission" for d in result["analysis"]["duplicates"])


# ---- drinks ---------------------------------------------------------------------------


async def test_a_drink_can_never_be_queued_as_a_documented_classic(
    client: AsyncClient, agent: dict[str, str]
) -> None:
    result = (await client.post(SUBMIT, headers=agent, json=margarita_like())).json()

    assert result["analysis"]["classification"] == {
        "claimed": "classic",
        "suggested": "experimental",
    }
    assert "classification_downgraded" in _codes(result, "info")
    assert result["blocking_issues"] == 0


async def test_unknown_glass_and_technique_are_warnings(
    client: AsyncClient, agent: dict[str, str]
) -> None:
    body = margarita_like()
    body["recipe"]["drink"]["glass"] = "copa de cristal bohemio"
    body["recipe"]["drink"]["technique"] = "teletransportado"

    result = (await client.post(SUBMIT, headers=agent, json=body)).json()

    assert {"unknown_glass", "unknown_technique"} <= set(_codes(result, "warning"))


# ---- placement ------------------------------------------------------------------------


async def test_a_very_hard_dish_asks_for_a_new_stage(
    client: AsyncClient, agent: dict[str, str]
) -> None:
    hard = omelette(
        title="Pavo en mole con masa",
        steps=[
            f"Paso {n}: sella la carne, desglasa, amasa la masa y deja fermentar bien."
            for n in range(12)
        ],
        preparation_time_minutes=120,
        cooking_time_minutes=240,
        ingredients=[{"name": f"huevo{n}", "quantity": 1, "unit": "piece"} for n in range(14)],
    )

    result = (await client.post(SUBMIT, headers=agent, json=hard)).json()

    assert result["analysis"]["difficulty"]["score"] == 5
    placement = next(p for p in result["analysis"]["placements"] if p["path_slug"] == "cocina")
    assert placement["new_stage"] is True
    assert placement["stage_title"] == "Nueva etapa"


# ---- who can submit and who can read ---------------------------------------------------


async def test_submitting_needs_an_agent_token(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str]
) -> None:
    from app.models.enums import UserRole
    from tests.auth_helpers import make_user

    _, admin = await make_user(session, UserRole.ADMIN)

    assert (await client.post(SUBMIT, json=omelette())).status_code == 401
    assert (
        await client.post(SUBMIT, headers=bearer("mis_ag_wrong"), json=omelette())
    ).status_code == 401
    # Not even an admin's user token works here: agents and people are separate identities.
    assert (await client.post(SUBMIT, headers=admin, json=omelette())).status_code == 401


async def test_agents_only_see_their_own_submissions(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str]
) -> None:
    mine = (await client.post(SUBMIT, headers=agent, json=omelette())).json()
    gemini = await connect_agent(client, session, "Gemini", "gemini")

    own = await client.get(f"{SUBMIT}/{mine['id']}", headers=agent)
    foreign = await client.get(f"{SUBMIT}/{mine['id']}", headers=gemini)
    listing_mine = (await client.get(SUBMIT, headers=agent)).json()
    listing_other = (await client.get(SUBMIT, headers=gemini)).json()

    assert own.status_code == 200
    assert foreign.status_code == 404
    assert listing_mine["total"] == 1
    assert listing_other["total"] == 0


async def test_units_are_public_so_agents_can_discover_the_codes(
    client: AsyncClient, session: AsyncSession
) -> None:
    await seed_catalog(session)
    await session.commit()

    units = (await client.get("/api/v1/units")).json()

    assert {"g", "ml", "tbsp", "piece", "to_taste"} <= {u["code"] for u in units}
