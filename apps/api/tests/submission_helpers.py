"""Fixtures and builders for agent-submission tests."""

import copy
from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from app.seeds import seed_all
from tests.auth_helpers import bearer, make_user


async def seed_catalog(session: AsyncSession) -> None:
    """The real reference data, ingredients, recipes, skills and paths."""
    await seed_all(session)


async def connect_agent(
    client: AsyncClient, session: AsyncSession, name: str = "Claude", provider: str = "claude"
) -> dict[str, str]:
    """Register an agent as an admin and return its Authorization header."""
    _, admin = await make_user(session, UserRole.ADMIN)
    response = await client.post(
        "/api/v1/admin/agents", headers=admin, json={"name": name, "provider": provider}
    )
    assert response.status_code == 201, response.text
    return bearer(response.json()["token"])


def omelette(**recipe_overrides: Any) -> dict[str, Any]:
    """A valid cooking submission whose ingredients all exist in the catalog."""
    body: dict[str, Any] = {
        "source": {
            "name": "Cocina de ejemplo",
            "url": "https://example.com/recetas/omelette-de-queso",
            "source_type": "website",
            "license": "CC BY-SA 4.0",
            "attribution": "Receta reescrita con palabras propias.",
        },
        "recipe": {
            "title": "Omelette de queso Oaxaca",
            "description": "Un omelette suave relleno de queso fundido.",
            "recipe_type": "cooking",
            "servings": 2,
            "preparation_time_minutes": 5,
            "cooking_time_minutes": 8,
            "categories": ["desayunos"],
            "ingredients": [
                {"name": "huevos", "quantity": 4, "unit": "piece"},
                {"name": "queso oaxaca", "quantity": 80, "unit": "gramos"},
                {"name": "mantequilla", "quantity": 1, "unit": "cucharada"},
                {"name": "sal", "unit": "al gusto"},
            ],
            "steps": [
                "Bate los huevos con una pizca de sal.",
                "Derrite la mantequilla a fuego medio y vierte los huevos.",
                "Cuando cuajen, añade el queso, dobla el omelette y sirve.",
            ],
        },
    }
    body["recipe"].update(recipe_overrides)
    return body


def variant(base: dict[str, Any], **changes: Any) -> dict[str, Any]:
    """Copy of ``base`` with dotted-path changes: variant(b, **{"recipe.title": "X"})."""
    result = copy.deepcopy(base)
    for path, value in changes.items():
        node = result
        *parents, last = path.split(".")
        for key in parents:
            node = node[int(key)] if isinstance(node, list) else node[key]
        if isinstance(node, list):
            node[int(last)] = value
        else:
            node[last] = value
    return result


def margarita_like(**recipe_overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "source": {
            "name": "Bar de ejemplo",
            "url": "https://example.com/tragos/tequila-sunset",
            "source_type": "website",
            "license": "CC BY 4.0",
        },
        "recipe": {
            "title": "Tequila Sunset",
            "recipe_type": "drink",
            "servings": 1,
            "preparation_time_minutes": 3,
            "categories": ["sours"],
            "ingredients": [
                {"name": "tequila", "quantity": 50, "unit": "ml"},
                {"name": "naranja", "quantity": 40, "unit": "ml"},
                {"name": "lima", "quantity": 15, "unit": "ml"},
            ],
            "steps": [
                "Añade todos los ingredientes a la coctelera con hielo.",
                "Bate con energía y cuela en una copa coupe.",
            ],
            "drink": {
                "is_alcoholic": True,
                "base_spirit": "tequila",
                "glass": "coupe",
                "technique": "batido",
                "garnish": "Rueda de naranja",
                "claimed_classification": "classic",
            },
        },
    }
    body["recipe"].update(recipe_overrides)
    return body
