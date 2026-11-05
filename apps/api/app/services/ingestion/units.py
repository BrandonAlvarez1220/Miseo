"""Resolve the unit text an agent sends ("gramos", "cdas", "cups") to a catalog code."""

from collections.abc import Collection

from app.services.normalization import normalize_text

# Synonyms (already normalized: lowercase, no accents) -> unit code.
_SYNONYMS: dict[str, tuple[str, ...]] = {
    "g": ("g", "gr", "grs", "gramo", "gramos", "gram", "grams"),
    "kg": ("kg", "kgs", "kilo", "kilos", "kilogramo", "kilogramos", "kilogram"),
    "oz_wt": ("oz wt", "onza de peso", "onzas de peso"),
    "lb": ("lb", "lbs", "libra", "libras", "pound", "pounds"),
    "ml": ("ml", "mls", "mililitro", "mililitros", "milliliter", "milliliters"),
    "cl": ("cl", "centilitro", "centilitros"),
    "l": ("l", "lt", "lts", "litro", "litros", "liter", "liters", "litre", "litres"),
    "tsp": (
        "tsp",
        "cdta",
        "cdita",
        "cdtas",
        "cditas",
        "cucharadita",
        "cucharaditas",
        "teaspoon",
        "teaspoons",
    ),
    "tbsp": ("tbsp", "cda", "cdas", "cucharada", "cucharadas", "tablespoon", "tablespoons"),
    "cup": ("cup", "cups", "taza", "tazas"),
    "oz": ("oz", "onza", "onzas", "ounce", "ounces", "fl oz"),
    "bar_spoon": ("bar spoon", "barspoon", "cucharita de bar", "cucharitas de bar"),
    "dash": ("dash", "dashes", "toque", "toques"),
    "drop": ("drop", "drops", "gota", "gotas"),
    "piece": (
        "piece",
        "pieces",
        "pieza",
        "piezas",
        "pza",
        "pzas",
        "unidad",
        "unidades",
        "u",
        "pc",
        "pcs",
    ),
    "slice": ("slice", "slices", "rodaja", "rodajas", "rebanada", "rebanadas", "loncha", "lonchas"),
    "clove": ("clove", "cloves", "diente", "dientes"),
    "leaf": ("leaf", "leaves", "hoja", "hojas"),
    "sprig": ("sprig", "sprigs", "ramita", "ramitas", "rama", "ramas"),
    "pinch": ("pinch", "pinches", "pizca", "pizcas"),
    "to_taste": ("to taste", "al gusto", "a gusto"),
}

_LOOKUP = {synonym: code for code, synonyms in _SYNONYMS.items() for synonym in synonyms}


def resolve_unit(text: str | None, known_codes: Collection[str]) -> str | None:
    """The catalog unit code for ``text``, or None when it cannot be resolved.

    Accepts the code itself ("tbsp"), a synonym ("cucharadas") and any case or accents.
    Only codes that exist in the catalog are returned.
    """
    if not text:
        return None
    normalized = normalize_text(text)
    code = _LOOKUP.get(normalized) or (normalized.replace(" ", "_") if normalized else None)
    return code if code in known_codes else None
