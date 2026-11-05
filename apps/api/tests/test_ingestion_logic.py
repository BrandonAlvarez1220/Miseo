"""Pure unit tests of the deterministic ingestion rules (no database)."""

import json
import re
from pathlib import Path

import pytest

from app.models.enums import Difficulty
from app.services.ingestion.difficulty import (
    DifficultyInput,
    detect_techniques,
    label_for,
    score_difficulty,
)
from app.services.ingestion.placement import StageInfo, suggest_stage
from app.services.ingestion.skills import detect_skills, load_rules
from app.services.ingestion.units import resolve_unit

SEEDS = Path(__file__).resolve().parents[1] / "seeds"
KNOWN = {"g", "kg", "ml", "l", "tsp", "tbsp", "cup", "piece", "clove", "to_taste", "pinch"}


# ---- units -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("g", "g"),
        ("Gramos", "g"),
        ("GR", "g"),
        ("cucharadas", "tbsp"),
        ("Cdas", "tbsp"),
        ("cucharadita", "tsp"),
        ("tazas", "cup"),
        ("Litros", "l"),
        ("dientes", "clove"),
        ("al gusto", "to_taste"),
        ("pizca", "pinch"),
        ("piezas", "piece"),
        ("tbsp", "tbsp"),
    ],
)
def test_units_resolve_codes_and_common_names(text: str, code: str) -> None:
    assert resolve_unit(text, KNOWN) == code


def test_units_that_are_unknown_or_missing_from_the_catalog_do_not_resolve() -> None:
    assert resolve_unit("puñado", KNOWN) is None
    assert resolve_unit("", KNOWN) is None
    assert resolve_unit(None, KNOWN) is None
    # A synonym of a unit the catalog does not have must not resolve either.
    assert resolve_unit("onzas", KNOWN) is None


# ---- difficulty ------------------------------------------------------------------------


def _facts(
    steps: int, ingredients: int, minutes: int | None, text: str = "Mezcla bien."
) -> DifficultyInput:
    return DifficultyInput(
        steps=[text] * steps, main_ingredients=ingredients, total_minutes=minutes
    )


def test_simple_dish_is_easy_and_complex_dish_is_hard() -> None:
    simple = score_difficulty(_facts(3, 3, 15))
    assert (simple.score, simple.label) == (1, Difficulty.EASY)

    hard_text = "Emulsiona, sella la carne, desglasa y amasa la masa hasta que fermente."
    hard = score_difficulty(_facts(12, 16, 240, hard_text))
    assert hard.score == 5
    assert hard.label == Difficulty.HARD
    assert any("técnicas" in reason for reason in hard.reasons)


def test_difficulty_never_decreases_when_a_recipe_gets_bigger() -> None:
    previous = 0
    for steps, ingredients, minutes in [
        (2, 2, 10),
        (4, 4, 40),
        (6, 8, 70),
        (9, 10, 120),
        (12, 16, 300),
    ]:
        score = score_difficulty(_facts(steps, ingredients, minutes)).score
        assert score >= previous
        previous = score


def test_missing_time_is_ignored_rather_than_penalised() -> None:
    assert score_difficulty(_facts(3, 3, None)).score == 1


@pytest.mark.parametrize(
    "text",
    [
        "Sirve templada.",  # "templar" must not fire on "templada"
        "Baja a temperatura media.",  # nor "temperar" on "temperatura"
        "Reduce el fuego al mínimo.",  # lowering heat is not reducing a sauce
    ],
)
def test_technique_detection_has_no_false_positives(text: str) -> None:
    # Note: "carne sellada" DOES count as searing, because in a recipe it means that.
    assert detect_techniques([text]) == []


@pytest.mark.parametrize(
    ("text", "technique"),
    [
        ("Sella la carne por ambos lados.", "sellar"),
        ("Deja reducir la salsa 5 minutos.", "desglasar o reducir una salsa"),
        ("Prepara una mayonesa.", "emulsionar"),
        ("Amasa 10 minutos y deja fermentar.", "amasar o fermentar"),
        ("Cocina a baño maría.", "baño maría"),
    ],
)
def test_techniques_are_recognised(text: str, technique: str) -> None:
    assert [label for label, _ in detect_techniques([text])] == [technique]


def test_technique_points_are_capped() -> None:
    text = "Sella, desglasa, emulsiona, amasa, flambea, templar, montar, deshuesa."
    capped = score_difficulty(_facts(1, 1, 10, text))
    assert capped.score <= 3  # 4 technique points at most + 0 elsewhere -> total <= 5


@pytest.mark.parametrize(
    ("score", "label"), [(1, "easy"), (2, "easy"), (3, "medium"), (4, "hard"), (5, "hard")]
)
def test_labels(score: int, label: str) -> None:
    assert label_for(score) == label


# ---- skills ----------------------------------------------------------------------------


def test_real_rules_are_consistent_with_the_skill_catalog() -> None:
    catalog = {
        skill["slug"]: skill["discipline"]
        for skill in json.loads((SEEDS / "skills.json").read_text())
    }
    for rule in load_rules():
        assert rule["slug"] in catalog, rule["slug"]
        assert catalog[rule["slug"]] == rule["recipe_type"], rule["slug"]
        for pattern in [*rule.get("any", []), *rule.get("all", [])]:
            re.compile(pattern)
            assert pattern == pattern.lower() or "\\" in pattern  # matched on normalized text


def test_skills_are_detected_from_steps_notes_and_ingredients() -> None:
    skills = detect_skills(
        recipe_type="cooking",
        steps=["Sofríe la cebolla.", "Sella la carne.", "Cocina en el comal."],
        ingredient_slugs={"nopales"},
        extra_text=["cebolla picada"],
    )
    assert {"sofreir", "sellar-carne", "usar-el-comal", "picar-cebolla-y-jitomate"} <= set(skills)


def test_ingredient_gated_rules_need_the_ingredient() -> None:
    steps = ["Asa los nopales en el sartén."]
    assert "asar-nopales" in detect_skills(
        recipe_type="cooking", steps=steps, ingredient_slugs={"nopales"}
    )
    assert "asar-nopales" not in detect_skills(
        recipe_type="cooking", steps=steps, ingredient_slugs={"tomate"}
    )


def test_rules_only_apply_to_their_recipe_type() -> None:
    steps = ["Bate con hielo en la coctelera y cuela."]
    assert "batir-y-colar" in detect_skills(
        recipe_type="drink", steps=steps, ingredient_slugs=set()
    )
    assert "batir-y-colar" not in detect_skills(
        recipe_type="cooking", steps=steps, ingredient_slugs=set()
    )


def test_drink_technique_triggers_a_skill_without_matching_text() -> None:
    skills = detect_skills(
        recipe_type="drink", steps=["Prepara."], ingredient_slugs=set(), technique="machacado"
    )
    assert "machacar-sin-amargar" in skills


def test_min_matches_needs_several_hits() -> None:
    rule = [
        {
            "slug": "tiempos-de-coccion",
            "recipe_type": "cooking",
            "any": ["\\d+ minutos"],
            "min_matches": 3,
        }
    ]
    few = detect_skills(
        recipe_type="cooking",
        steps=["Cocina 5 minutos.", "Otros 3 minutos."],
        ingredient_slugs=set(),
        rules=rule,
    )
    many = detect_skills(
        recipe_type="cooking",
        steps=["5 minutos.", "3 minutos.", "9 minutos."],
        ingredient_slugs=set(),
        rules=rule,
    )
    assert few == []
    assert many == ["tiempos-de-coccion"]


def test_a_rule_of_one_skill_is_listed_once() -> None:
    skills = detect_skills(
        recipe_type="cooking", steps=["Sofríe. Sofríe otra vez."], ingredient_slugs=set()
    )
    assert skills.count("sofreir") == 1


# ---- placement -------------------------------------------------------------------------


def _ladder() -> list[StageInfo]:
    return [
        StageInfo(1, "Sin miedo", 1, frozenset({"picar", "sofreir"})),
        StageInfo(2, "Comida de casa", 2, frozenset({"sellar", "arroz"})),
        StageInfo(3, "Más pasos", 2, frozenset({"salsa"})),
    ]


def test_a_dish_goes_to_the_stage_that_teaches_its_hardest_skill() -> None:
    placement = suggest_stage(score=1, skills=["picar", "sellar"], stages=_ladder())
    assert placement is not None
    assert (placement.stage_position, placement.new_stage) == (2, False)
    assert placement.introduces == ("sellar",)


def test_only_basic_skills_go_to_the_first_stage() -> None:
    placement = suggest_stage(score=1, skills=["picar", "sofreir"], stages=_ladder())
    assert placement is not None
    assert placement.stage_position == 1


def test_a_dish_much_harder_than_the_stage_moves_on_or_asks_for_a_new_stage() -> None:
    harder = suggest_stage(score=3, skills=["picar"], stages=_ladder())
    assert harder is not None
    assert harder.stage_position == 2  # stage 1 tops out at 1 (+1); stage 2 can take a 3

    hardest = suggest_stage(score=5, skills=["picar"], stages=_ladder())
    assert hardest is not None
    assert hardest.new_stage is True
    assert hardest.stage_position == 4
    assert hardest.stage_title == "Nueva etapa"


def test_skills_no_stage_teaches_are_reported_for_the_reviewer() -> None:
    placement = suggest_stage(score=1, skills=["picar", "flambear"], stages=_ladder())
    assert placement is not None
    assert placement.unknown_skills == ("flambear",)


def test_no_skills_falls_back_to_difficulty() -> None:
    placement = suggest_stage(score=2, skills=[], stages=_ladder())
    assert placement is not None
    assert placement.stage_position == 1
    assert "no se detectaron" in placement.reason


def test_a_path_without_stages_has_no_suggestion() -> None:
    assert suggest_stage(score=1, skills=["picar"], stages=[]) is None
