"""Spot recipes that probably already exist (in the catalog or still waiting for review)."""

import uuid
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IngestionJob, Ingredient, Recipe, RecipeIngredient
from app.models.enums import IngestionStatus, RecipeStatus, RecipeType
from app.schemas.submission import DuplicateRef
from app.services.normalization import normalize_text

TITLE_SIMILARITY = 0.55
PENDING_TITLE_SIMILARITY = 0.6
INGREDIENT_JACCARD = 0.8
MIN_INGREDIENTS_FOR_OVERLAP = 3
MAX_DUPLICATES = 5


async def find_duplicates(
    session: AsyncSession,
    *,
    title: str,
    recipe_type: RecipeType,
    main_ingredient_ids: set[uuid.UUID],
    exclude_job_id: uuid.UUID | None = None,
) -> list[DuplicateRef]:
    normalized = normalize_text(title)
    found: dict[tuple[str, str], DuplicateRef] = {}

    def keep(ref: DuplicateRef) -> None:
        key = (ref.kind, ref.slug or str(ref.submission_id))
        if key not in found or found[key].similarity < ref.similarity:
            found[key] = ref

    title_sim = func.similarity(func.unaccent(func.lower(Recipe.title)), normalized)
    rows = await session.execute(
        select(Recipe.slug, Recipe.title, title_sim)
        .where(
            Recipe.status == RecipeStatus.PUBLISHED,
            Recipe.recipe_type == recipe_type,
            title_sim >= TITLE_SIMILARITY,
        )
        .order_by(title_sim.desc())
        .limit(MAX_DUPLICATES)
    )
    for slug, existing_title, similarity in rows.all():
        keep(
            DuplicateRef(
                kind="recipe",
                slug=slug,
                title=existing_title,
                similarity=round(float(similarity), 2),
                reason="título muy parecido",
            )
        )

    if len(main_ingredient_ids) >= MIN_INGREDIENTS_FOR_OVERLAP:
        sets = await _published_ingredient_sets(session, recipe_type, main_ingredient_ids)
        for slug, existing_title, ids in sets:
            union = main_ingredient_ids | ids
            jaccard = len(main_ingredient_ids & ids) / len(union) if union else 0.0
            if jaccard >= INGREDIENT_JACCARD:
                keep(
                    DuplicateRef(
                        kind="recipe",
                        slug=slug,
                        title=existing_title,
                        similarity=round(jaccard, 2),
                        reason="mismos ingredientes principales",
                    )
                )

    pending_title = func.unaccent(
        func.lower(IngestionJob.payload["submission"]["recipe"]["title"].astext)
    )
    pending_sim = func.similarity(pending_title, normalized)
    pending_stmt = (
        select(
            IngestionJob.id,
            IngestionJob.payload["submission"]["recipe"]["title"].astext,
            pending_sim,
        )
        .where(
            IngestionJob.status == IngestionStatus.NEEDS_REVIEW,
            IngestionJob.payload["submission"]["recipe"]["recipe_type"].astext == recipe_type.value,
            pending_sim >= PENDING_TITLE_SIMILARITY,
        )
        .order_by(pending_sim.desc())
        .limit(MAX_DUPLICATES)
    )
    if exclude_job_id is not None:
        pending_stmt = pending_stmt.where(IngestionJob.id != exclude_job_id)
    for job_id, pending_title_text, similarity in (await session.execute(pending_stmt)).all():
        keep(
            DuplicateRef(
                kind="submission",
                submission_id=job_id,
                title=pending_title_text or "",
                similarity=round(float(similarity), 2),
                reason="otro envío pendiente con un título parecido",
            )
        )
    return sorted(found.values(), key=lambda ref: -ref.similarity)[:MAX_DUPLICATES]


async def _published_ingredient_sets(
    session: AsyncSession, recipe_type: RecipeType, ingredient_ids: set[uuid.UUID]
) -> list[tuple[str, str, set[uuid.UUID]]]:
    """(slug, title, main ingredient ids) of published recipes sharing an ingredient."""
    sharing = (
        select(RecipeIngredient.recipe_id)
        .where(RecipeIngredient.ingredient_id.in_(ingredient_ids))
        .scalar_subquery()
    )
    rows = await session.execute(
        select(Recipe.slug, Recipe.title, RecipeIngredient.ingredient_id)
        .join(RecipeIngredient, RecipeIngredient.recipe_id == Recipe.id)
        .join(Ingredient, Ingredient.id == RecipeIngredient.ingredient_id)
        .where(
            Recipe.id.in_(sharing),
            Recipe.status == RecipeStatus.PUBLISHED,
            Recipe.recipe_type == recipe_type,
            RecipeIngredient.is_optional.is_(False),
            Ingredient.is_staple.is_(False),
        )
    )
    grouped: dict[tuple[str, str], set[uuid.UUID]] = defaultdict(set)
    for slug, title, ingredient_id in rows.all():
        grouped[(slug, title)].add(ingredient_id)
    return [(slug, title, ids) for (slug, title), ids in grouped.items()]
