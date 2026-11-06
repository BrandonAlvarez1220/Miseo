"""Map the free-text ingredient and unit names an agent sends onto the catalog.

Mapping is exact on purpose (normalized name, alias or slug). Fuzzy matches are only
offered as *candidates* for the reviewer: auto-mapping "ajo en polvo" to "ajo" would
silently change a recipe.
"""

import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import case, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import UnprocessableError
from app.models import Ingredient, IngredientAlias, Unit
from app.models.enums import IssueSeverity, UnitType
from app.schemas.submission import SubmissionIngredient
from app.services.ingestion.units import resolve_unit
from app.services.normalization import normalize_text

CANDIDATE_THRESHOLD = 0.3
MAX_CANDIDATES = 3
# Largest plausible amount of one ingredient in a home recipe, in g or ml.
MAX_BASE_AMOUNT = Decimal(20_000)
MAX_COUNT_AMOUNT = Decimal(100)
NO_QUANTITY_UNITS = frozenset({"to_taste", "pinch", "dash"})


@dataclass(frozen=True)
class Issue:
    severity: IssueSeverity
    code: str
    message: str
    field_path: str | None = None


@dataclass(frozen=True)
class ResolvedIngredient:
    id: uuid.UUID
    slug: str
    name: str
    is_staple: bool


@dataclass(frozen=True)
class Candidate:
    slug: str
    name: str
    similarity: float


@dataclass
class ResolvedLine:
    index: int
    name: str
    ingredient: ResolvedIngredient | None
    candidates: list[Candidate]
    quantity: Decimal | None
    quantity_max: Decimal | None
    unit_code: str | None
    unit_text: str | None
    optional: bool
    notes: str | None
    group: str | None
    issues: list[Issue] = field(default_factory=list)


def _as_resolved(ingredient: Ingredient) -> ResolvedIngredient:
    return ResolvedIngredient(
        id=ingredient.id, slug=ingredient.slug, name=ingredient.name, is_staple=ingredient.is_staple
    )


async def _lookup_ingredients(
    session: AsyncSession, names: set[str], slugs: set[str]
) -> tuple[dict[str, ResolvedIngredient], dict[str, ResolvedIngredient]]:
    """(by normalized name or alias, by slug) for everything the submission mentions."""
    by_name: dict[str, ResolvedIngredient] = {}
    by_slug: dict[str, ResolvedIngredient] = {}
    rows = await session.scalars(
        select(Ingredient).where(
            or_(Ingredient.normalized_name.in_(names), Ingredient.slug.in_(slugs))
        )
    )
    for ingredient in rows.all():
        resolved = _as_resolved(ingredient)
        by_name[ingredient.normalized_name] = resolved
        by_slug[ingredient.slug] = resolved
    aliases = await session.execute(
        select(IngredientAlias.normalized_alias, Ingredient)
        .join(Ingredient, Ingredient.id == IngredientAlias.ingredient_id)
        .where(IngredientAlias.normalized_alias.in_(names))
    )
    for alias, ingredient in aliases.all():
        by_name.setdefault(alias, _as_resolved(ingredient))
    return by_name, by_slug


async def _candidates(session: AsyncSession, normalized_name: str) -> list[Candidate]:
    """Close (not equal) catalog ingredients: for the reviewer to choose from."""
    contained = literal(normalized_name).like(func.concat("%", Ingredient.normalized_name, "%"))
    similarity = func.greatest(
        func.similarity(Ingredient.normalized_name, normalized_name),
        case((contained, 0.5), else_=0.0),
    )
    rows = await session.execute(
        select(Ingredient.slug, Ingredient.name, similarity.label("sim"))
        .where(similarity >= CANDIDATE_THRESHOLD)
        .order_by(similarity.desc(), Ingredient.name)
        .limit(MAX_CANDIDATES)
    )
    return [
        Candidate(slug=slug, name=name, similarity=round(float(sim), 2))
        for slug, name, sim in rows.all()
    ]


async def resolve_lines(
    session: AsyncSession, ingredients: list[SubmissionIngredient]
) -> list[ResolvedLine]:
    """Resolve every line. Problems become issues on the line; true contradictions raise."""
    names = {normalize_text(item.name) for item in ingredients}
    slugs = {item.ingredient_slug for item in ingredients if item.ingredient_slug}
    by_name, by_slug = await _lookup_ingredients(session, names, slugs)
    units = {unit.code: unit for unit in (await session.scalars(select(Unit))).all()}

    lines: list[ResolvedLine] = []
    for index, item in enumerate(ingredients):
        path = f"recipe.ingredients[{index}]"
        issues: list[Issue] = []

        ingredient: ResolvedIngredient | None = None
        candidates: list[Candidate] = []
        if item.ingredient_slug:
            ingredient = by_slug.get(item.ingredient_slug)
            if ingredient is None:
                issues.append(
                    Issue(
                        IssueSeverity.ERROR,
                        "unknown_ingredient",
                        f"ingredient_slug '{item.ingredient_slug}' is not in the catalog",
                        f"{path}.ingredient_slug",
                    )
                )
        else:
            ingredient = by_name.get(normalize_text(item.name))
        if ingredient is None:
            candidates = await _candidates(session, normalize_text(item.name))
            if not any(i.code == "unknown_ingredient" for i in issues):
                hint = (
                    " Candidates: " + ", ".join(f"{c.name} ({c.slug})" for c in candidates)
                    if candidates
                    else ""
                )
                issues.append(
                    Issue(
                        IssueSeverity.ERROR,
                        "unknown_ingredient",
                        f"'{item.name}' is not in the catalog; a reviewer must map or add it."
                        f"{hint}",
                        f"{path}.name",
                    )
                )

        unit_code = resolve_unit(item.unit, units.keys())
        if item.unit and unit_code is None:
            issues.append(
                Issue(
                    IssueSeverity.ERROR,
                    "unknown_unit",
                    f"unit '{item.unit}' is not recognised (see GET /units)",
                    f"{path}.unit",
                )
            )

        issues.extend(_quantity_issues(item, unit_code, units, path))
        lines.append(
            ResolvedLine(
                index=index,
                name=item.name,
                ingredient=ingredient,
                candidates=candidates,
                quantity=item.quantity,
                quantity_max=item.quantity_max,
                unit_code=unit_code,
                unit_text=item.unit,
                optional=item.optional,
                notes=item.notes,
                group=item.group,
                issues=issues,
            )
        )
    _reject_repeated_ingredients(lines)
    return lines


def _quantity_issues(
    item: SubmissionIngredient, unit_code: str | None, units: dict[str, Unit], path: str
) -> list[Issue]:
    issues: list[Issue] = []
    if item.quantity is None:
        if unit_code not in NO_QUANTITY_UNITS and not item.optional:
            issues.append(
                Issue(
                    IssueSeverity.WARNING,
                    "missing_quantity",
                    f"'{item.name}' has no quantity: confirm it really is 'to taste'",
                    f"{path}.quantity",
                )
            )
        return issues
    if unit_code is None and item.unit is None:
        issues.append(
            Issue(
                IssueSeverity.WARNING,
                "missing_unit",
                f"'{item.name}' has a quantity but no unit (use 'piece' for whole items)",
                f"{path}.unit",
            )
        )
        return issues
    unit = units.get(unit_code) if unit_code else None
    if unit is None:
        return issues
    largest = item.quantity_max or item.quantity
    if unit.unit_type in (UnitType.MASS, UnitType.VOLUME) and unit.to_base_factor:
        implausible = largest * unit.to_base_factor > MAX_BASE_AMOUNT
    else:
        implausible = unit.unit_type == UnitType.COUNT and largest > MAX_COUNT_AMOUNT
    if implausible:
        issues.append(
            Issue(
                IssueSeverity.WARNING,
                "implausible_quantity",
                f"{largest} {unit.name} of '{item.name}' looks too large for a home recipe",
                f"{path}.quantity",
            )
        )
    return issues


def _reject_repeated_ingredients(lines: list[ResolvedLine]) -> None:
    """The same ingredient twice in one group is a data error the agent must fix."""
    seen: dict[tuple[str, str | None], int] = {}
    for line in lines:
        key = (
            str(line.ingredient.id) if line.ingredient else "name:" + normalize_text(line.name),
            line.group,
        )
        if key in seen:
            raise UnprocessableError(
                f"'{line.name}' appears twice in the same group (lines {seen[key]} and "
                f"{line.index}): merge the quantities or give each use its own 'group'",
                details=[
                    {"loc": ["recipe", "ingredients", line.index], "type": "duplicate_ingredient"}
                ],
            )
        seen[key] = line.index
