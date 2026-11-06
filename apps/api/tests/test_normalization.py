import pytest

from app.services.normalization import normalize_text, slugify


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Limón", "limon"),
        ("  Aceite   de  Oliva ", "aceite de oliva"),
        ("Chile jalapeño", "chile jalapeno"),
        ("Pimentón (dulce)", "pimenton dulce"),
        ("ÑANDÚ", "nandu"),
        ("Old-Fashioned", "old fashioned"),
        ("", ""),
    ],
)
def test_normalize_text(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


def test_normalize_does_not_singularize() -> None:
    # Plurals are handled with explicit aliases, never with heuristics.
    assert normalize_text("Tomates") == "tomates"


def test_slugify() -> None:
    assert slugify("Aceite de oliva") == "aceite-de-oliva"
    assert slugify("Tortilla de maíz") == "tortilla-de-maiz"
