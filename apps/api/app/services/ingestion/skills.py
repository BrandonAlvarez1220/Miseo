"""Suggest which catalog skills a submitted recipe teaches, from its text.

Rules live in ``seeds/skill_keywords.json`` (data, not code), so they can be reviewed
and improved without touching Python. Each rule names a skill and what triggers it:

``any``            regexes searched in the normalized step text (accents removed, lowercase);
``min_matches``    how many of those hits are needed (default 1);
(the text scanned is the steps plus ingredient names and notes)
``all``            regexes that must ALL appear;
``ingredients_any`` the recipe must use at least one of these ingredient slugs;
``technique_any``  drink technique slugs that trigger it on their own;
``always``         applies to every recipe of the rule's ``recipe_type``.

These are SUGGESTIONS that a human confirms during review.
"""

import json
import re
from collections.abc import Collection, Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.services.normalization import normalize_text

RULES_FILE = Path(__file__).resolve().parents[3] / "seeds" / "skill_keywords.json"


@lru_cache
def load_rules() -> tuple[dict[str, Any], ...]:
    return tuple(json.loads(RULES_FILE.read_text(encoding="utf-8")))


def _hits(patterns: Sequence[str], text: str) -> int:
    return sum(len(re.findall(pattern, text)) for pattern in patterns)


def detect_skills(
    *,
    recipe_type: str,
    steps: Sequence[str],
    ingredient_slugs: Collection[str],
    technique: str | None = None,
    extra_text: Sequence[str] = (),
    rules: Sequence[dict[str, Any]] | None = None,
) -> list[str]:
    """Skill slugs suggested for the recipe, in rule order, without duplicates.

    ``extra_text`` (ingredient names and preparation notes) is scanned together with
    the steps: "picada" often appears only in a note, "jarabe simple" in a name.
    """
    text = " " + normalize_text(" ".join([*steps, *extra_text])) + " "
    found: list[str] = []
    for rule in rules if rules is not None else load_rules():
        if rule.get("recipe_type") not in (None, recipe_type):
            continue
        if rule.get("always"):
            matched = True
        else:
            needs_ingredient = rule.get("ingredients_any")
            if needs_ingredient and not set(needs_ingredient) & set(ingredient_slugs):
                continue
            if rule.get("all") and not all(re.search(p, text) for p in rule["all"]):
                continue
            technique_hit = bool(technique and technique in rule.get("technique_any", ()))
            any_patterns = rule.get("any", ())
            text_hit = bool(any_patterns) and _hits(any_patterns, text) >= rule.get(
                "min_matches", 1
            )
            matched = technique_hit or text_hit
        if matched and rule["slug"] not in found:
            found.append(rule["slug"])
    return found
