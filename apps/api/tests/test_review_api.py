import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DrinkDetails, IngestionJob, PathDish, Recipe, RecipeRevision
from app.models.enums import (
    DrinkClassification,
    IngestionStatus,
    OriginType,
    RecipeStatus,
    UserRole,
)
from tests.auth_helpers import make_user
from tests.submission_helpers import (
    connect_agent,
    margarita_like,
    omelette,
    seed_catalog,
    variant,
)

SUBMIT = "/api/v1/agent/submissions"
REVIEW = "/api/v1/review/submissions"


@pytest.fixture
async def agent(client: AsyncClient, session: AsyncSession) -> dict[str, str]:
    await seed_catalog(session)
    await session.commit()
    return await connect_agent(client, session)


@pytest.fixture
async def reviewer(session: AsyncSession) -> dict[str, str]:
    _, headers = await make_user(session, UserRole.MODERATOR)
    return headers


async def _submit(client: AsyncClient, agent: dict[str, str], body: dict) -> str:
    response = await client.post(SUBMIT, headers=agent, json=body)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _with_unknown_ingredient() -> dict:
    body = omelette()
    body["recipe"]["ingredients"].append({"name": "chorizo", "quantity": 100, "unit": "g"})
    return body


# ---- who may review --------------------------------------------------------------------


async def test_the_queue_is_for_moderators_and_admins_only(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, omelette())
    _, user = await make_user(session, UserRole.USER)
    _, moderator = await make_user(session, UserRole.MODERATOR)
    _, admin = await make_user(session, UserRole.ADMIN)

    for path in (REVIEW, f"{REVIEW}/{job_id}"):
        assert (await client.get(path)).status_code == 401
        assert (await client.get(path, headers=user)).status_code == 403
        assert (
            await client.get(path, headers=agent)
        ).status_code == 401  # an agent is not a person
        assert (await client.get(path, headers=moderator)).status_code == 200
        assert (await client.get(path, headers=admin)).status_code == 200
    for action in ("approve", "reject"):
        denied = await client.post(
            f"{REVIEW}/{job_id}/{action}", headers=user, json={"review_notes": "ok ok"}
        )
        assert denied.status_code == 403


async def test_the_queue_lists_pending_submissions_with_agent_and_issue_counts(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    await _submit(client, agent, _with_unknown_ingredient())
    gemini = await connect_agent(client, session, "Gemini", "gemini")
    await _submit(client, gemini, margarita_like())

    everything = (await client.get(REVIEW, headers=reviewer)).json()
    drinks = (await client.get(REVIEW, headers=reviewer, params={"recipe_type": "drink"})).json()
    by_agent = (
        await client.get(
            REVIEW, headers=reviewer, params={"agent_id": everything["items"][0]["agent"]["id"]}
        )
    ).json()

    assert everything["total"] == 2
    cooking = next(i for i in everything["items"] if i["recipe_type"] == "cooking")
    assert (cooking["errors"], cooking["agent"]["name"], cooking["difficulty_score"]) == (
        1,
        "Claude",
        1,
    )
    assert [i["title"] for i in drinks["items"]] == ["Tequila Sunset"]
    assert by_agent["total"] == 1


# ---- approving -------------------------------------------------------------------------


async def test_approving_publishes_the_recipe_with_everything_attached(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, omelette())

    response = await client.post(
        f"{REVIEW}/{job_id}/approve",
        headers=reviewer,
        json={
            "placement": {"path_slug": "cocina", "stage_position": 1},
            "review_notes": "Revisada contra la fuente.",
        },
    )

    assert response.status_code == 200, response.text
    detail = response.json()
    assert detail["status"] == "completed"
    slug = detail["recipe_slug"]
    assert slug == "omelette-de-queso-oaxaca"

    recipe = (await client.get(f"/api/v1/recipes/{slug}")).json()  # public now
    assert recipe["title"] == "Omelette de queso Oaxaca"
    assert recipe["difficulty"] == "easy"
    assert [i["ingredient"]["slug"] for i in recipe["ingredients"]] == [
        "huevo",
        "queso-oaxaca",
        "mantequilla",
        "sal",
    ]
    assert recipe["ingredients"][1]["unit"]["code"] == "g"
    assert len(recipe["steps"]) == 3
    assert recipe["sources"][0]["source_url"] == "https://example.com/recetas/omelette-de-queso"
    assert recipe["sources"][0]["license"] == "CC BY-SA 4.0"
    assert [c["slug"] for c in recipe["categories"]] == ["desayunos"]
    assert "cuajar-huevo" in [s["slug"] for s in recipe["skills"]]
    assert recipe["paths"][0]["path_slug"] == "cocina"

    row = await session.scalar(select(Recipe).where(Recipe.slug == slug))
    assert row is not None
    assert (row.origin_type, row.status) == (OriginType.AI_ASSISTED, RecipeStatus.PUBLISHED)
    assert row.published_at is not None
    assert (
        await session.scalar(
            select(func.count())
            .select_from(RecipeRevision)
            .where(RecipeRevision.recipe_id == row.id)
        )
        == 1
    )
    job = await session.get(IngestionJob, detail["id"] if False else job_id)
    assert job is not None
    assert (job.status, job.result_recipe_id, job.review_notes) == (
        IngestionStatus.COMPLETED,
        row.id,
        "Revisada contra la fuente.",
    )
    assert job.reviewed_by is not None


async def test_the_agent_sees_the_published_recipe_slug(
    client: AsyncClient, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, omelette())
    await client.post(f"{REVIEW}/{job_id}/approve", headers=reviewer, json={})

    status = (await client.get(f"{SUBMIT}/{job_id}", headers=agent)).json()

    assert status["status"] == "completed"
    assert status["recipe_slug"] == "omelette-de-queso-oaxaca"


async def test_unmatched_ingredients_must_be_mapped_before_approving(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, _with_unknown_ingredient())

    refused = await client.post(f"{REVIEW}/{job_id}/approve", headers=reviewer, json={})

    assert refused.status_code == 422
    assert refused.json()["error"]["details"] == [
        {"line": 4, "problem": "ingredient", "name": "chorizo"}
    ]
    assert (
        await session.scalar(
            select(func.count()).select_from(Recipe).where(Recipe.title.like("Omelette%"))
        )
        == 0
    )

    approved = await client.post(
        f"{REVIEW}/{job_id}/approve", headers=reviewer, json={"ingredient_mappings": {"4": "pollo"}}
    )
    assert approved.status_code == 200
    recipe = (await client.get(f"/api/v1/recipes/{approved.json()['recipe_slug']}")).json()
    assert recipe["ingredients"][-1]["ingredient"]["slug"] == "pollo"


async def test_mapping_to_a_nonexistent_ingredient_is_refused(
    client: AsyncClient, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, _with_unknown_ingredient())
    response = await client.post(
        f"{REVIEW}/{job_id}/approve",
        headers=reviewer,
        json={"ingredient_mappings": {"4": "no-existe"}},
    )
    assert response.status_code == 422


async def test_an_unknown_unit_can_be_mapped_by_the_reviewer(
    client: AsyncClient, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    body = omelette()
    body["recipe"]["ingredients"].append({"name": "cebolla", "quantity": 1, "unit": "puñado"})
    job_id = await _submit(client, agent, body)

    refused = await client.post(f"{REVIEW}/{job_id}/approve", headers=reviewer, json={})
    approved = await client.post(
        f"{REVIEW}/{job_id}/approve", headers=reviewer, json={"unit_mappings": {"4": "piece"}}
    )

    assert refused.status_code == 422
    assert refused.json()["error"]["details"][0]["problem"] == "unit"
    assert approved.status_code == 200


async def test_a_category_is_required_and_must_fit_the_recipe_type(
    client: AsyncClient, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, omelette(categories=[]))

    missing = await client.post(f"{REVIEW}/{job_id}/approve", headers=reviewer, json={})
    wrong_type = await client.post(
        f"{REVIEW}/{job_id}/approve", headers=reviewer, json={"categories": ["sours"]}
    )
    chosen = await client.post(
        f"{REVIEW}/{job_id}/approve", headers=reviewer, json={"categories": ["desayunos"]}
    )

    assert missing.status_code == 422
    assert wrong_type.status_code == 422  # "sours" is a drink category
    assert chosen.status_code == 200


async def test_only_valid_skills_and_placements_are_accepted(
    client: AsyncClient, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, omelette())

    bad_skill = await client.post(
        f"{REVIEW}/{job_id}/approve", headers=reviewer, json={"skills": ["no-existe"]}
    )
    wrong_discipline = await client.post(
        f"{REVIEW}/{job_id}/approve", headers=reviewer, json={"skills": ["dry-shake"]}
    )
    bad_path = await client.post(
        f"{REVIEW}/{job_id}/approve",
        headers=reviewer,
        json={"placement": {"path_slug": "barra", "stage_position": 1}},
    )
    bad_stage = await client.post(
        f"{REVIEW}/{job_id}/approve",
        headers=reviewer,
        json={"placement": {"path_slug": "cocina", "stage_position": 9}},
    )

    assert [r.status_code for r in (bad_skill, wrong_discipline, bad_path, bad_stage)] == [
        422,
        422,
        422,
        422,
    ]


async def test_the_reviewer_can_override_difficulty_and_skills(
    client: AsyncClient, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, omelette())
    approved = (
        await client.post(
            f"{REVIEW}/{job_id}/approve",
            headers=reviewer,
            json={"difficulty": "medium", "skills": ["sofreir"]},
        )
    ).json()

    recipe = (await client.get(f"/api/v1/recipes/{approved['recipe_slug']}")).json()

    assert recipe["difficulty"] == "medium"
    assert [s["slug"] for s in recipe["skills"]] == ["sofreir"]


async def test_the_placed_dish_is_appended_to_its_stage(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    before = await session.scalar(select(func.count()).select_from(PathDish))
    job_id = await _submit(client, agent, omelette())

    await client.post(
        f"{REVIEW}/{job_id}/approve",
        headers=reviewer,
        json={"placement": {"path_slug": "cocina", "stage_position": 1}},
    )

    path = (await client.get("/api/v1/paths/cocina")).json()
    first_stage = path["stages"][0]["dishes"]
    assert first_stage[-1]["recipe"]["slug"] == "omelette-de-queso-oaxaca"
    assert await session.scalar(select(func.count()).select_from(PathDish)) == (before or 0) + 1


async def test_two_recipes_with_the_same_title_get_different_slugs(
    client: AsyncClient, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    first = await _submit(client, agent, omelette())
    second = await _submit(
        client, agent, variant(omelette(), **{"source.url": "https://example.com/otra-fuente"})
    )

    slugs = []
    for job_id in (first, second):
        response = await client.post(f"{REVIEW}/{job_id}/approve", headers=reviewer, json={})
        assert response.status_code == 200
        slugs.append(response.json()["recipe_slug"])

    assert slugs == ["omelette-de-queso-oaxaca", "omelette-de-queso-oaxaca-2"]


# ---- drinks: never a documented classic ------------------------------------------------


async def test_an_agent_cocktail_is_published_as_experimental_by_default(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, margarita_like())

    approved = (await client.post(f"{REVIEW}/{job_id}/approve", headers=reviewer, json={})).json()

    recipe = (await client.get(f"/api/v1/recipes/{approved['recipe_slug']}")).json()
    assert recipe["drink"]["classification"] == "experimental"
    assert recipe["drink"]["glass"]["slug"] == "coupe"
    assert recipe["drink"]["technique"]["slug"] == "batido"
    assert recipe["drink"]["base_spirit"]["slug"] == "tequila"
    details = await session.scalar(
        select(DrinkDetails)
        .join(Recipe, Recipe.id == DrinkDetails.recipe_id)
        .where(Recipe.slug == approved["recipe_slug"])
    )
    assert details is not None
    assert details.classification == DrinkClassification.EXPERIMENTAL


async def test_an_ai_generated_cocktail_cannot_be_forced_to_classic_but_a_sourced_one_can(
    client: AsyncClient, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    invented = margarita_like()
    invented["source"] = {"name": "Claude", "source_type": "ai_generated"}
    invented_id = await _submit(client, agent, invented)
    sourced_id = await _submit(client, agent, margarita_like())

    refused = await client.post(
        f"{REVIEW}/{invented_id}/approve", headers=reviewer, json={"classification": "classic"}
    )
    variation = await client.post(
        f"{REVIEW}/{sourced_id}/approve", headers=reviewer, json={"classification": "variation"}
    )
    allowed = await client.post(
        f"{REVIEW}/{sourced_id}/approve", headers=reviewer, json={"classification": "classic"}
    )

    assert refused.status_code == 422
    assert "documented classic" in refused.json()["error"]["message"]
    assert variation.status_code == 422  # needs a parent recipe
    assert allowed.status_code == 200


# ---- rejecting -------------------------------------------------------------------------


async def test_rejecting_stores_the_reason_and_the_agent_can_read_it(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, omelette())

    response = await client.post(
        f"{REVIEW}/{job_id}/reject",
        headers=reviewer,
        json={"review_notes": "La fuente no permite reutilizar el texto."},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    seen_by_agent = (await client.get(f"{SUBMIT}/{job_id}", headers=agent)).json()
    assert seen_by_agent["status"] == "rejected"
    assert seen_by_agent["review_notes"] == "La fuente no permite reutilizar el texto."
    assert (
        await session.scalar(
            select(func.count()).select_from(Recipe).where(Recipe.title.like("Omelette%"))
        )
        == 0
    )


async def test_a_rejection_needs_a_reason(
    client: AsyncClient, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, omelette())
    for body in ({}, {"review_notes": ""}, {"review_notes": "no"}):
        assert (
            await client.post(f"{REVIEW}/{job_id}/reject", headers=reviewer, json=body)
        ).status_code == 422


async def test_a_decided_submission_cannot_be_decided_again_or_resubmitted(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    approved_id = await _submit(client, agent, omelette())
    rejected_id = await _submit(client, agent, margarita_like())
    await client.post(f"{REVIEW}/{approved_id}/approve", headers=reviewer, json={})
    await client.post(
        f"{REVIEW}/{rejected_id}/reject",
        headers=reviewer,
        json={"review_notes": "No es lo que buscamos."},
    )

    again = [
        await client.post(
            f"{REVIEW}/{approved_id}/reject", headers=reviewer, json={"review_notes": "tarde ya"}
        ),
        await client.post(f"{REVIEW}/{approved_id}/approve", headers=reviewer, json={}),
        await client.post(f"{REVIEW}/{rejected_id}/approve", headers=reviewer, json={}),
    ]
    resubmitted = await client.post(SUBMIT, headers=agent, json=margarita_like())

    assert [r.status_code for r in again] == [409, 409, 409]
    assert resubmitted.json()["outcome"] == "unchanged"  # a rejected recipe is not retried
    assert resubmitted.json()["status"] == "rejected"
    assert (
        await session.scalar(
            select(func.count()).select_from(Recipe).where(Recipe.title.like("Omelette%"))
        )
        == 1
    )


async def test_unknown_submissions_are_404(client: AsyncClient, reviewer: dict[str, str]) -> None:
    missing = "00000000-0000-0000-0000-000000000000"
    assert (await client.get(f"{REVIEW}/{missing}", headers=reviewer)).status_code == 404
    assert (
        await client.post(f"{REVIEW}/{missing}/approve", headers=reviewer, json={})
    ).status_code == 404
    assert (
        await client.post(
            f"{REVIEW}/{missing}/reject", headers=reviewer, json={"review_notes": "nada"}
        )
    ).status_code == 404


async def test_a_revoked_agent_cannot_submit_but_its_pending_work_stays_reviewable(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, omelette())
    _, admin = await make_user(session, UserRole.ADMIN)
    agents = (await client.get("/api/v1/admin/agents", headers=admin)).json()
    await client.post(f"/api/v1/admin/agents/{agents[0]['id']}/revoke", headers=admin)

    blocked = await client.post(
        SUBMIT, headers=agent, json=variant(omelette(), **{"source.url": "https://example.com/x"})
    )
    detail = await client.get(f"{REVIEW}/{job_id}", headers=reviewer)

    assert blocked.status_code == 401
    assert detail.status_code == 200
    assert detail.json()["agent"]["name"] == "Claude"


# ---- growing the catalog while approving ----------------------------------------------


def _chile_submission() -> dict:
    body = omelette()
    body["recipe"]["ingredients"].append({"name": "chile guajillo", "quantity": 2, "unit": "piece"})
    return body


async def test_the_reviewer_can_create_a_missing_ingredient_while_approving(
    client: AsyncClient, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, _chile_submission())

    approved = await client.post(
        f"{REVIEW}/{job_id}/approve",
        headers=reviewer,
        json={"new_ingredients": {"4": {"name": "Chile guajillo", "category": "especias"}}},
    )

    assert approved.status_code == 200, approved.text
    ingredients = (await client.get("/api/v1/ingredients", params={"q": "guajillo"})).json()
    assert [(i["slug"], i["category"]["slug"]) for i in ingredients] == [
        ("chile-guajillo", "especias")
    ]
    recipe = (await client.get(f"/api/v1/recipes/{approved.json()['recipe_slug']}")).json()
    assert recipe["ingredients"][-1]["ingredient"]["slug"] == "chile-guajillo"
    # From now on the catalog resolves it by itself.
    again = (
        await client.post(
            SUBMIT,
            headers=agent,
            json=variant(_chile_submission(), **{"source.url": "https://example.com/y"}),
        )
    ).json()
    assert again["blocking_issues"] == 0


@pytest.mark.parametrize(
    ("spec", "message"),
    [
        ({"name": "Pollo"}, "already exists"),  # same as an existing ingredient
        ({"name": "pechuga de pollo"}, "already exists"),  # same as an alias
        ({"name": "chile guajillo", "category": "no-existe"}, "Unknown ingredient category"),
    ],
)
async def test_creating_an_ingredient_that_clashes_or_is_invalid_is_refused(
    client: AsyncClient, agent: dict[str, str], reviewer: dict[str, str], spec: dict, message: str
) -> None:
    job_id = await _submit(client, agent, _chile_submission())

    response = await client.post(
        f"{REVIEW}/{job_id}/approve", headers=reviewer, json={"new_ingredients": {"4": spec}}
    )

    assert response.status_code == 422
    assert message in response.json()["error"]["message"]


async def test_a_line_cannot_be_both_mapped_and_created(
    client: AsyncClient, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, _chile_submission())
    response = await client.post(
        f"{REVIEW}/{job_id}/approve",
        headers=reviewer,
        json={
            "ingredient_mappings": {"4": "pollo"},
            "new_ingredients": {"4": {"name": "Chile guajillo"}},
        },
    )
    assert response.status_code == 422


async def test_a_failed_approval_does_not_leave_the_new_ingredient_behind(
    client: AsyncClient, session: AsyncSession, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    body = _chile_submission()
    body["recipe"]["categories"] = []  # approval will fail later: no category
    job_id = await _submit(client, agent, body)

    refused = await client.post(
        f"{REVIEW}/{job_id}/approve",
        headers=reviewer,
        json={"new_ingredients": {"4": {"name": "Chile guajillo"}}},
    )

    assert refused.status_code == 422
    assert (await client.get("/api/v1/ingredients", params={"q": "guajillo"})).json() == []
    job = await session.get(IngestionJob, job_id)
    assert job is not None
    assert job.status == IngestionStatus.NEEDS_REVIEW


async def test_creating_for_a_line_that_does_not_exist_is_refused(
    client: AsyncClient, agent: dict[str, str], reviewer: dict[str, str]
) -> None:
    job_id = await _submit(client, agent, omelette())
    response = await client.post(
        f"{REVIEW}/{job_id}/approve",
        headers=reviewer,
        json={"new_ingredients": {"99": {"name": "Chile guajillo"}}},
    )
    assert response.status_code == 422
