"""Reusable query parameter parsing."""

from typing import Annotated

from fastapi import Query

from app.core.errors import AppError

MAX_LIST_ITEMS = 40


def split_csv(value: str | None, *, max_items: int = MAX_LIST_ITEMS, name: str) -> tuple[str, ...]:
    """Parse ``"a,b,,c"`` into ``("a", "b", "c")`` preserving order without duplicates."""
    if not value:
        return ()
    items = tuple(dict.fromkeys(part.strip() for part in value.split(",") if part.strip()))
    if len(items) > max_items:
        raise AppError(f"'{name}' accepts at most {max_items} values")
    return items


CsvSlugs = Annotated[
    str | None,
    Query(
        description="Comma separated ingredient slugs, e.g. `pollo,arroz,tomate`.",
        max_length=2000,
        pattern=r"^[a-z0-9,-]*$",
    ),
]
