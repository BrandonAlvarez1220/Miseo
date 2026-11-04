"""Deterministic ingredient-based recipe matching (no LLM involved).

Given the ingredients a user has, score how well each recipe can be prepared.

Scoring (per recipe)
--------------------
* Only *required* ingredients count towards the percentage; optional ones never
  penalize, they only break ties.
* Each required ingredient contributes a weight:

  - 1.0 if the user has it,
  - 1.0 if it is a pantry staple (salt, water, oil...) and staples are assumed,
  - a substitution weight (below) if a known alternative is available
    (FLEXIBLE and DISCOVER only),
  - 0 otherwise (missing).

* ``match_percentage = sum(weights) / required_count * 100``.

Modes
-----
* EXACT: every required ingredient is available as-is (no substitutions).
* FLEXIBLE: every required ingredient is available or substitutable.
* DISCOVER: anything sharing at least one ingredient with the user, ranked.

In every mode a recipe must use at least one of the user's (non-staple)
ingredients, so we never recommend something just because it needs salt.

Ranking: higher percentage, fewer missing, more optional extras available,
shorter total time, then title.
"""

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from app.models.enums import SubstitutionType

SUBSTITUTION_WEIGHTS: dict[SubstitutionType, float] = {
    SubstitutionType.EQUIVALENT: 0.9,
    SubstitutionType.SIMILAR: 0.75,
    SubstitutionType.EMERGENCY: 0.5,
}


class MatchMode(StrEnum):
    EXACT = "exact"
    FLEXIBLE = "flexible"
    DISCOVER = "discover"


@dataclass(frozen=True)
class IngredientInfo:
    id: uuid.UUID
    name: str
    slug: str
    is_staple: bool = False


@dataclass(frozen=True)
class RecipeLine:
    ingredient: IngredientInfo
    is_optional: bool = False


@dataclass(frozen=True)
class Alternative:
    ingredient: IngredientInfo
    substitution_type: SubstitutionType
    ratio: Decimal = Decimal(1)
    notes: str | None = None


@dataclass(frozen=True)
class Candidate:
    recipe_id: uuid.UUID
    title: str
    total_time_minutes: int | None
    lines: tuple[RecipeLine, ...]
    # Known substitutions keyed by the ingredient they replace.
    alternatives: dict[uuid.UUID, tuple[Alternative, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class Substitution:
    missing: IngredientInfo
    substitute: Alternative


@dataclass(frozen=True)
class MatchResult:
    recipe_id: uuid.UUID
    title: str
    total_time_minutes: int | None
    match_percentage: int
    score: float
    available: tuple[IngredientInfo, ...]
    missing: tuple[IngredientInfo, ...]
    substitutions: tuple[Substitution, ...]
    assumed_staples: tuple[IngredientInfo, ...]
    optional_available: tuple[IngredientInfo, ...]
    optional_missing: tuple[IngredientInfo, ...]


def _dedupe(lines: tuple[RecipeLine, ...]) -> tuple[list[IngredientInfo], list[IngredientInfo]]:
    """Split into (required, optional); an ingredient required anywhere is required."""
    required: dict[uuid.UUID, IngredientInfo] = {}
    optional: dict[uuid.UUID, IngredientInfo] = {}
    for line in lines:
        target = optional if line.is_optional else required
        target.setdefault(line.ingredient.id, line.ingredient)
    for ingredient_id in required:
        optional.pop(ingredient_id, None)
    if not required:  # Degenerate recipe: score against everything it lists.
        return list(optional.values()), []
    return list(required.values()), list(optional.values())


def score_recipe(
    candidate: Candidate,
    available_ids: frozenset[uuid.UUID],
    mode: MatchMode,
    *,
    assume_staples: bool = True,
) -> MatchResult | None:
    """Score one recipe. Returns ``None`` when it does not qualify for ``mode``."""

    def has(info: IngredientInfo) -> bool:
        return info.id in available_ids

    def assumed(info: IngredientInfo) -> bool:
        return assume_staples and info.is_staple and not has(info)

    required, optional = _dedupe(candidate.lines)

    available: list[IngredientInfo] = []
    staples: list[IngredientInfo] = []
    substitutions: list[Substitution] = []
    missing: list[IngredientInfo] = []
    total_weight = 0.0

    for ingredient in required:
        if has(ingredient):
            available.append(ingredient)
            total_weight += 1.0
            continue
        if assumed(ingredient):
            staples.append(ingredient)
            total_weight += 1.0
            continue
        best = None
        if mode != MatchMode.EXACT:
            usable = [
                alt
                for alt in candidate.alternatives.get(ingredient.id, ())
                if has(alt.ingredient) or (assume_staples and alt.ingredient.is_staple)
            ]
            if usable:
                best = max(usable, key=lambda alt: SUBSTITUTION_WEIGHTS[alt.substitution_type])
        if best is not None:
            substitutions.append(Substitution(missing=ingredient, substitute=best))
            total_weight += SUBSTITUTION_WEIGHTS[best.substitution_type]
        else:
            missing.append(ingredient)

    optional_available = [i for i in optional if has(i)]
    optional_missing = [i for i in optional if not has(i)]

    # The user's own (non-staple) ingredients must play a part in the recipe.
    user_contribution = [i for i in available + optional_available if not i.is_staple] + [
        s.substitute.ingredient for s in substitutions if has(s.substitute.ingredient)
    ]
    if not user_contribution:
        return None
    if mode == MatchMode.EXACT and (missing or substitutions):
        return None
    if mode == MatchMode.FLEXIBLE and missing:
        return None

    ratio = total_weight / len(required)
    optional_bonus = len(optional_available) / len(optional) if optional else 0.0
    return MatchResult(
        recipe_id=candidate.recipe_id,
        title=candidate.title,
        total_time_minutes=candidate.total_time_minutes,
        match_percentage=round(ratio * 100),
        score=ratio + optional_bonus * 0.01,
        available=tuple(available),
        missing=tuple(missing),
        substitutions=tuple(substitutions),
        assumed_staples=tuple(staples),
        optional_available=tuple(optional_available),
        optional_missing=tuple(optional_missing),
    )


def rank(
    candidates: list[Candidate],
    available_ids: frozenset[uuid.UUID],
    mode: MatchMode,
    *,
    assume_staples: bool = True,
) -> list[MatchResult]:
    results = [
        result
        for candidate in candidates
        if (result := score_recipe(candidate, available_ids, mode, assume_staples=assume_staples))
    ]
    return sorted(
        results,
        key=lambda r: (
            -r.score,
            len(r.missing),
            r.total_time_minutes if r.total_time_minutes is not None else 10**6,
            r.title,
        ),
    )
