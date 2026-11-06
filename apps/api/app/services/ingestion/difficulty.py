"""Deterministic difficulty score (1-5) from facts about a recipe. No AI involved.

It is a heuristic meant to ORDER recipes along a learning path, not an absolute
truth: a human reviewer can always override it. The score adds up points from:

* number of steps,
* number of main ingredients (pantry staples such as salt or oil do not count),
* total time,
* techniques recognised in the step text (sear, emulsify, knead...).

Honest limits: simple home dishes mostly score 1-2 (which is accurate), so the score
cannot tell a stage-1 dish from a stage-3 one. It is used as a SAFETY CEILING when
suggesting a stage (a dish much harder than a stage is never suggested for it); the
skills a dish needs are what order a learning path (see ``placement.py``).
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.models.enums import Difficulty
from app.services.normalization import normalize_text


@dataclass(frozen=True)
class DifficultyInput:
    steps: Sequence[str]
    #: Required (non-optional) ingredients that are not pantry staples.
    main_ingredients: int
    total_minutes: int | None


@dataclass(frozen=True)
class DifficultyResult:
    score: int
    label: Difficulty
    reasons: tuple[str, ...]


# (label shown to people, points, regexes searched in the normalized step text).
# Word boundaries matter: "templar" must not match "templada" nor "tempera" "temperatura".
TECHNIQUES: tuple[tuple[str, int, tuple[str, ...]], ...] = (
    ("sellar", 1, (r"\bsella", r"\bsellar\b", r"\bsellado\b")),
    ("desglasar o reducir una salsa", 1, (r"\bdesglas", r"\bdeja reducir", r"\breduccion\b")),
    ("emulsionar", 2, (r"\bemulsion", r"\bmayonesa\b")),
    ("amasar o fermentar", 2, (r"\bamasa", r"\bferment", r"\bleud")),
    ("baño maría", 2, (r"\bbano maria\b", r"\bbanomaria\b")),
    ("flambear", 2, (r"\bflamb",)),
    ("templar", 2, (r"\btemplar\b", r"\btemperar\b", r"\btemplado de\b")),
    ("montar a punto", 1, (r"\bpunto de nieve\b", r"\bpunto de turron\b", r"\bmontar\b")),
    ("deshuesar o filetear", 1, (r"\bdeshues", r"\bfileta")),
)
MAX_TECHNIQUE_POINTS = 4


def _points(value: int, thresholds: Sequence[int]) -> int:
    """How many thresholds ``value`` exceeds (thresholds are upper bounds of each tier)."""
    return sum(value > limit for limit in thresholds)


def detect_techniques(steps: Sequence[str]) -> list[tuple[str, int]]:
    text = " " + normalize_text(" ".join(steps)) + " "
    return [
        (label, points)
        for label, points, patterns in TECHNIQUES
        if any(re.search(pattern, text) for pattern in patterns)
    ]


def label_for(score: int) -> Difficulty:
    if score <= 2:
        return Difficulty.EASY
    if score == 3:
        return Difficulty.MEDIUM
    return Difficulty.HARD


def score_difficulty(data: DifficultyInput) -> DifficultyResult:
    reasons: list[str] = []
    total = 0

    step_points = _points(len(data.steps), (3, 5, 8))
    total += step_points
    reasons.append(f"{len(data.steps)} pasos")

    ingredient_points = _points(data.main_ingredients, (5, 9, 14))
    total += ingredient_points
    reasons.append(f"{data.main_ingredients} ingredientes principales")

    if data.total_minutes is not None:
        total += _points(data.total_minutes, (30, 90, 180))
        reasons.append(f"{data.total_minutes} min en total")

    techniques = detect_techniques(data.steps)
    technique_points = min(sum(points for _, points in techniques), MAX_TECHNIQUE_POINTS)
    total += technique_points
    if techniques:
        reasons.append("técnicas: " + ", ".join(label for label, _ in techniques))

    score = 1 + _points(total, (2, 4, 6, 8))
    return DifficultyResult(score=score, label=label_for(score), reasons=tuple(reasons))
