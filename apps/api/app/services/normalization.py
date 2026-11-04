"""Deterministic text normalization for ingredient mapping and slugs.

We deliberately do NOT singularize words heuristically: Spanish plural rules
have many exceptions ("anís", "gas", "nueces" -> "nuez") and a wrong guess would
silently merge different ingredients. Plurals and synonyms are handled
explicitly with ``ingredient_alias`` rows instead.
"""

import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_text(value: str) -> str:
    """Lowercase, remove accents and punctuation, collapse whitespace.

    >>> normalize_text("  Limón   Amarillo! ")
    'limon amarillo'
    """
    return _NON_ALNUM.sub(" ", strip_accents(value).lower()).strip()


def slugify(value: str) -> str:
    """URL-safe identifier: ``"Aceite de oliva"`` -> ``"aceite-de-oliva"``."""
    return normalize_text(value).replace(" ", "-")
