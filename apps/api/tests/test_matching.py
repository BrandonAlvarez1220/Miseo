"""Unit tests for the deterministic matcher (pure functions, no database)."""

import uuid

import pytest

from app.models.enums import SubstitutionType
from app.services.matching import (
    Alternative,
    Candidate,
    IngredientInfo,
    MatchMode,
    RecipeLine,
    rank,
    score_recipe,
)


def ing(name: str, *, staple: bool = False) -> IngredientInfo:
    return IngredientInfo(id=uuid.uuid4(), name=name, slug=name, is_staple=staple)


CHICKEN, RICE, TOMATO, ONION, GARLIC = (
    ing("pollo"),
    ing("arroz"),
    ing("tomate"),
    ing("cebolla"),
    ing("ajo"),
)
LEMON, LIME, BUTTER, OIL = ing("limon"), ing("lima"), ing("mantequilla"), ing("aceite", staple=True)
SALT, CILANTRO, PARSLEY = ing("sal", staple=True), ing("cilantro"), ing("perejil")


def recipe(
    *required: IngredientInfo,
    optional: tuple[IngredientInfo, ...] = (),
    alternatives: dict[uuid.UUID, tuple[Alternative, ...]] | None = None,
    title: str = "receta",
    minutes: int | None = 30,
) -> Candidate:
    return Candidate(
        recipe_id=uuid.uuid4(),
        title=title,
        total_time_minutes=minutes,
        lines=tuple(RecipeLine(i) for i in required)
        + tuple(RecipeLine(i, is_optional=True) for i in optional),
        alternatives=alternatives or {},
    )


def have(*items: IngredientInfo) -> frozenset[uuid.UUID]:
    return frozenset(i.id for i in items)


def alt(i: IngredientInfo, kind: SubstitutionType) -> Alternative:
    return Alternative(ingredient=i, substitution_type=kind)


class TestBasicScoring:
    def test_all_required_available_is_100(self) -> None:
        result = score_recipe(recipe(CHICKEN, RICE), have(CHICKEN, RICE), MatchMode.EXACT)
        assert result is not None
        assert result.match_percentage == 100
        assert result.missing == ()

    def test_percentage_is_available_over_required(self) -> None:
        result = score_recipe(
            recipe(CHICKEN, RICE, TOMATO, ONION), have(CHICKEN, RICE, TOMATO), MatchMode.DISCOVER
        )
        assert result is not None
        assert result.match_percentage == 75
        assert result.missing == (ONION,)

    def test_optional_ingredients_never_penalize(self) -> None:
        result = score_recipe(recipe(CHICKEN, optional=(CILANTRO,)), have(CHICKEN), MatchMode.EXACT)
        assert result is not None
        assert result.match_percentage == 100
        assert result.optional_missing == (CILANTRO,)

    def test_optional_available_breaks_ties(self) -> None:
        plain = recipe(CHICKEN, optional=(CILANTRO,), title="a")
        garnished = recipe(CHICKEN, optional=(CILANTRO,), title="b")
        ranked = rank([plain, garnished], have(CHICKEN), MatchMode.EXACT)
        assert [r.match_percentage for r in ranked] == [100, 100]
        with_extra = rank([plain, garnished], have(CHICKEN, CILANTRO), MatchMode.EXACT)
        assert with_extra[0].optional_available == (CILANTRO,)

    def test_ingredient_both_required_and_optional_counts_as_required(self) -> None:
        candidate = Candidate(
            recipe_id=uuid.uuid4(),
            title="x",
            total_time_minutes=None,
            lines=(RecipeLine(TOMATO, is_optional=True), RecipeLine(TOMATO), RecipeLine(CHICKEN)),
        )
        result = score_recipe(candidate, have(CHICKEN), MatchMode.DISCOVER)
        assert result is not None
        assert result.missing == (TOMATO,)
        assert result.optional_missing == ()

    def test_recipe_with_only_optional_lines_scores_against_them(self) -> None:
        result = score_recipe(recipe(optional=(CHICKEN, RICE)), have(CHICKEN), MatchMode.DISCOVER)
        assert result is not None
        assert result.match_percentage == 50


class TestStaples:
    def test_staples_are_assumed_by_default(self) -> None:
        result = score_recipe(recipe(CHICKEN, SALT, OIL), have(CHICKEN), MatchMode.EXACT)
        assert result is not None
        assert result.match_percentage == 100
        assert set(result.assumed_staples) == {SALT, OIL}

    def test_staples_count_as_missing_when_not_assumed(self) -> None:
        result = score_recipe(
            recipe(CHICKEN, SALT), have(CHICKEN), MatchMode.DISCOVER, assume_staples=False
        )
        assert result is not None
        assert result.match_percentage == 50
        assert result.missing == (SALT,)

    def test_owning_a_staple_lists_it_as_available_not_assumed(self) -> None:
        result = score_recipe(recipe(CHICKEN, SALT), have(CHICKEN, SALT), MatchMode.EXACT)
        assert result is not None
        assert result.available == (CHICKEN, SALT)
        assert result.assumed_staples == ()

    def test_recipe_matching_only_through_staples_is_not_recommended(self) -> None:
        # The user selected only salt: recommending everything with salt is noise.
        assert score_recipe(recipe(CHICKEN, SALT), have(SALT), MatchMode.DISCOVER) is None


class TestModes:
    def test_exact_rejects_missing_ingredients(self) -> None:
        assert score_recipe(recipe(CHICKEN, RICE), have(CHICKEN), MatchMode.EXACT) is None

    def test_exact_ignores_substitutions(self) -> None:
        candidate = recipe(
            CHICKEN, LIME, alternatives={LIME.id: (alt(LEMON, SubstitutionType.SIMILAR),)}
        )
        assert score_recipe(candidate, have(CHICKEN, LEMON), MatchMode.EXACT) is None

    def test_flexible_accepts_known_substitutions(self) -> None:
        candidate = recipe(
            CHICKEN, LIME, alternatives={LIME.id: (alt(LEMON, SubstitutionType.SIMILAR),)}
        )
        result = score_recipe(candidate, have(CHICKEN, LEMON), MatchMode.FLEXIBLE)
        assert result is not None
        assert result.missing == ()
        assert result.substitutions[0].missing == LIME
        assert result.substitutions[0].substitute.ingredient == LEMON
        # (1 + 0.75) / 2
        assert result.match_percentage == 88

    def test_flexible_rejects_unsubstitutable_missing(self) -> None:
        assert score_recipe(recipe(CHICKEN, RICE), have(CHICKEN), MatchMode.FLEXIBLE) is None

    def test_discover_keeps_partial_matches(self) -> None:
        result = score_recipe(recipe(CHICKEN, RICE, TOMATO), have(TOMATO), MatchMode.DISCOVER)
        assert result is not None
        assert result.match_percentage == 33

    @pytest.mark.parametrize(
        ("kind", "expected"),
        [
            (SubstitutionType.EQUIVALENT, 95),
            (SubstitutionType.SIMILAR, 88),
            (SubstitutionType.EMERGENCY, 75),
        ],
    )
    def test_substitution_weight_depends_on_type(
        self, kind: SubstitutionType, expected: int
    ) -> None:
        candidate = recipe(CHICKEN, BUTTER, alternatives={BUTTER.id: (alt(LEMON, kind),)})
        result = score_recipe(candidate, have(CHICKEN, LEMON), MatchMode.FLEXIBLE)
        assert result is not None
        assert result.match_percentage == expected

    def test_best_available_substitute_is_chosen(self) -> None:
        candidate = recipe(
            CHICKEN,
            CILANTRO,
            alternatives={
                CILANTRO.id: (
                    alt(LEMON, SubstitutionType.EMERGENCY),
                    alt(PARSLEY, SubstitutionType.SIMILAR),
                )
            },
        )
        result = score_recipe(candidate, have(CHICKEN, LEMON, PARSLEY), MatchMode.FLEXIBLE)
        assert result is not None
        assert result.substitutions[0].substitute.ingredient == PARSLEY

    def test_staple_can_act_as_substitute(self) -> None:
        stock = ing("caldo")
        water = ing("agua", staple=True)
        candidate = recipe(
            CHICKEN, stock, alternatives={stock.id: (alt(water, SubstitutionType.EMERGENCY),)}
        )
        result = score_recipe(candidate, have(CHICKEN), MatchMode.FLEXIBLE)
        assert result is not None
        assert result.substitutions[0].substitute.ingredient == water
        assert (
            score_recipe(candidate, have(CHICKEN), MatchMode.FLEXIBLE, assume_staples=False) is None
        )

    def test_substitute_alone_counts_as_user_contribution(self) -> None:
        candidate = recipe(LIME, alternatives={LIME.id: (alt(LEMON, SubstitutionType.SIMILAR),)})
        assert score_recipe(candidate, have(LEMON), MatchMode.FLEXIBLE) is not None


class TestRanking:
    def test_orders_by_percentage_then_missing_then_time_then_title(self) -> None:
        full_slow = recipe(CHICKEN, title="lento", minutes=60)
        full_fast = recipe(CHICKEN, title="rapido", minutes=10)
        full_unknown_time = recipe(CHICKEN, title="sin tiempo", minutes=None)
        half = recipe(CHICKEN, RICE, title="mitad")
        ranked = rank(
            [half, full_slow, full_unknown_time, full_fast], have(CHICKEN), MatchMode.DISCOVER
        )
        assert [r.title for r in ranked] == ["rapido", "lento", "sin tiempo", "mitad"]

    def test_example_from_product_brief(self) -> None:
        pantry = have(CHICKEN, RICE, TOMATO, ONION, GARLIC, LEMON)
        arroz_con_pollo = recipe(CHICKEN, RICE, TOMATO, ONION, GARLIC, SALT, title="arroz")
        needs_lime = recipe(
            CHICKEN,
            LIME,
            GARLIC,
            title="pollo a la lima",
            alternatives={LIME.id: (alt(LEMON, SubstitutionType.SIMILAR),)},
        )
        unrelated = recipe(ing("salmon"), ing("eneldo"), title="salmon")

        exact = rank([arroz_con_pollo, needs_lime, unrelated], pantry, MatchMode.EXACT)
        flexible = rank([arroz_con_pollo, needs_lime, unrelated], pantry, MatchMode.FLEXIBLE)

        assert [r.title for r in exact] == ["arroz"]
        assert [r.title for r in flexible] == ["arroz", "pollo a la lima"]
