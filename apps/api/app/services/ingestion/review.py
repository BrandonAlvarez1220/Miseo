"""Human review of agent submissions: approve (publish) or reject.

Approving is the ONLY way agent content reaches the public catalog. It creates the
recipe, its ingredients (every line mapped to a catalog ingredient), steps, source,
skills and, optionally, a place on a learning path, all in a single transaction.
"""

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.models import (
    AppUser,
    BartendingTechnique,
    Category,
    DrinkDetails,
    GlassType,
    IngestionJob,
    Ingredient,
    IngredientAlias,
    IngredientCategory,
    LearningPath,
    PathDish,
    PathStage,
    PreparationStep,
    Recipe,
    RecipeIngredient,
    RecipeRevision,
    RecipeSource,
    Skill,
    Unit,
    recipe_skill,
)
from app.models.enums import (
    DrinkClassification,
    IngestionStatus,
    OriginType,
    RecipeStatus,
    RecipeType,
    SourceType,
)
from app.schemas.submission import ApproveRequest, RecipeSubmission, RejectRequest
from app.services.normalization import normalize_text, slugify

logger = logging.getLogger(__name__)


async def _lock_pending(session: AsyncSession, job_id: uuid.UUID) -> IngestionJob:
    """The job, locked so two reviewers cannot decide on it at the same time."""
    job = await session.scalar(
        select(IngestionJob).where(IngestionJob.id == job_id).with_for_update()
    )
    if job is None or job.payload is None:
        raise NotFoundError("Submission not found")
    if job.status != IngestionStatus.NEEDS_REVIEW:
        raise ConflictError(f"This submission was already reviewed ({job.status.value})")
    return job


async def reject(
    session: AsyncSession, *, reviewer: AppUser, job_id: uuid.UUID, body: RejectRequest
) -> IngestionJob:
    job = await _lock_pending(session, job_id)
    job.status = IngestionStatus.REJECTED
    job.reviewed_by = reviewer.id
    job.reviewed_at = datetime.now(UTC)
    job.review_notes = body.review_notes
    await session.commit()
    logger.warning("AUDIT submission rejected: reviewer=%s job=%s", reviewer.id, job.id)
    return job


async def _unique_slug(session: AsyncSession, title: str) -> str:
    base = (slugify(title) or "receta")[:170]
    taken = set(
        (await session.scalars(select(Recipe.slug).where(Recipe.slug.like(f"{base}%")))).all()
    )
    if base not in taken:
        return base
    number = 2
    while f"{base}-{number}" in taken:
        number += 1
    return f"{base}-{number}"


def _fail(message: str, details: object = None) -> UnprocessableError:
    return UnprocessableError(message, details=details)


async def _create_ingredients(
    session: AsyncSession, body: ApproveRequest, line_indexes: set[int]
) -> dict[int, Ingredient]:
    """Create the requested new catalog ingredients, refusing anything ambiguous."""
    created: dict[int, Ingredient] = {}
    seen: set[str] = set()
    for index, spec in body.new_ingredients.items():
        if index not in line_indexes:
            raise _fail(f"new_ingredients: there is no ingredient line {index}")
        if index in body.ingredient_mappings:
            raise _fail(f"Line {index} is both mapped and created: choose one")
        normalized = normalize_text(spec.name)
        slug = slugify(spec.name)
        if not normalized or not slug:
            raise _fail(f"'{spec.name}' is not a valid ingredient name")
        if normalized in seen:
            raise _fail(
                f"'{spec.name}' is created twice in this approval: map one line to the other"
            )
        seen.add(normalized)
        taken = await session.scalar(
            select(Ingredient.slug).where(
                (Ingredient.normalized_name == normalized) | (Ingredient.slug == slug)
            )
        ) or await session.scalar(
            select(Ingredient.slug)
            .join(IngredientAlias, IngredientAlias.ingredient_id == Ingredient.id)
            .where(IngredientAlias.normalized_alias == normalized)
        )
        if taken:
            raise _fail(f"'{spec.name}' already exists in the catalog as '{taken}': map it instead")
        category_id = None
        if spec.category:
            category_id = await session.scalar(
                select(IngredientCategory.id).where(IngredientCategory.slug == spec.category)
            )
            if category_id is None:
                raise _fail(f"Unknown ingredient category '{spec.category}'")
        ingredient = Ingredient(
            name=spec.name,
            normalized_name=normalized,
            slug=slug,
            category_id=category_id,
            is_staple=spec.is_staple,
            is_alcoholic=spec.is_alcoholic,
        )
        session.add(ingredient)
        created[index] = ingredient
    await session.flush()
    return created


async def approve(
    session: AsyncSession, *, reviewer: AppUser, job_id: uuid.UUID, body: ApproveRequest
) -> tuple[IngestionJob, Recipe]:
    job = await _lock_pending(session, job_id)
    assert job.payload is not None
    submission = RecipeSubmission.model_validate(job.payload["submission"])
    data = submission.recipe
    resolved = job.payload.get("resolved", {})
    analysis = job.analysis or {}
    lines = job.payload["lines"]

    # 0. Ingredients the catalog lacks are created with the approval (same transaction:
    #    if anything below fails, nothing is kept).
    created = await _create_ingredients(session, body, {line["index"] for line in lines})

    # 1. Every line needs a catalog ingredient (and a valid unit if one was written).
    wanted_slugs = {
        body.ingredient_mappings.get(line["index"]) or line["ingredient_slug"] for line in lines
    } - {None}
    ingredients = {
        i.slug: i
        for i in (
            await session.scalars(select(Ingredient).where(Ingredient.slug.in_(wanted_slugs)))
        ).all()
    }
    unit_codes = set((await session.scalars(select(Unit.code))).all())
    unresolved: list[dict[str, object]] = []
    resolved_lines: list[tuple[dict[str, Any], Ingredient, str | None]] = []
    for line in lines:
        index = line["index"]
        slug = body.ingredient_mappings.get(index) or line["ingredient_slug"]
        ingredient = created.get(index) or (ingredients.get(slug) if slug else None)
        unit = body.unit_mappings.get(index) or line["unit_code"]
        if ingredient is None:
            unresolved.append({"line": index, "problem": "ingredient", "name": line["name"]})
        if line["unit_text"] and unit not in unit_codes:
            unresolved.append({"line": index, "problem": "unit", "text": line["unit_text"]})
        if ingredient is not None:
            resolved_lines.append((line, ingredient, unit if unit in unit_codes else None))
    if unresolved:
        raise _fail(
            "Map every unmatched ingredient and unit before approving "
            "(ingredient_mappings / unit_mappings: line index -> slug / code)",
            unresolved,
        )
    seen: set[tuple[uuid.UUID, str | None]] = set()
    for line, ingredient, _ in resolved_lines:
        key = (ingredient.id, line["group"])
        if key in seen:
            raise _fail(f"'{ingredient.name}' ended up twice in the same group after mapping")
        seen.add(key)

    # 2. Categories.
    category_slugs = (
        body.categories if body.categories is not None else resolved.get("categories", [])
    )
    categories = (
        (
            await session.scalars(
                select(Category).where(
                    Category.slug.in_(category_slugs), Category.recipe_type == data.recipe_type
                )
            )
        ).all()
        if category_slugs
        else []
    )
    if not categories or len(categories) != len(set(category_slugs)):
        raise _fail("Choose at least one valid category for this recipe type (categories)")

    # 3. Skills.
    skill_slugs = (
        body.skills if body.skills is not None else [s["slug"] for s in analysis.get("skills", [])]
    )
    skills = (
        (await session.scalars(select(Skill).where(Skill.slug.in_(skill_slugs)))).all()
        if skill_slugs
        else []
    )
    if len(skills) != len(set(skill_slugs)) or any(
        s.discipline != data.recipe_type for s in skills
    ):
        raise _fail("Every skill must exist and match the recipe type (skills)")

    # 4. Drink data: agents can never create documented classics on their own.
    drink_details: DrinkDetails | None = None
    if data.drink is not None:
        suggested = (analysis.get("classification") or {}).get("suggested", "experimental")
        classification = body.classification or DrinkClassification(suggested)
        if classification == DrinkClassification.VARIATION:
            raise _fail("'variation' needs a parent recipe, which approval cannot set yet")
        if (
            classification == DrinkClassification.CLASSIC
            and submission.source.source_type == SourceType.AI_GENERATED
        ):
            raise _fail("An AI-generated cocktail cannot be published as a documented classic")
        glass = (
            await session.scalar(select(GlassType).where(GlassType.slug == resolved.get("glass")))
            if resolved.get("glass")
            else None
        )
        technique = (
            await session.scalar(
                select(BartendingTechnique).where(
                    BartendingTechnique.slug == resolved.get("technique")
                )
            )
            if resolved.get("technique")
            else None
        )
        spirit = ingredients.get(resolved.get("base_spirit") or "")
        drink_details = DrinkDetails(
            is_alcoholic=data.drink.is_alcoholic,
            classification=classification,
            base_spirit_id=spirit.id if spirit else None,
            glass_type_id=glass.id if glass else None,
            technique_id=technique.id if technique else None,
            garnish=data.drink.garnish,
        )

    # 5. Path placement (an existing stage: creating stages is an editorial decision).
    stage: PathStage | None = None
    if body.placement is not None:
        stage = await session.scalar(
            select(PathStage)
            .join(LearningPath, LearningPath.id == PathStage.path_id)
            .where(
                LearningPath.slug == body.placement.path_slug,
                LearningPath.discipline == data.recipe_type,
                PathStage.position == body.placement.stage_position,
            )
        )
        if stage is None:
            raise _fail("That path or stage does not exist for this recipe type (placement)")

    # 6. Materialize everything.
    difficulty = body.difficulty or (analysis.get("difficulty") or {}).get("label")
    now = datetime.now(UTC)
    recipe = Recipe(
        title=data.title,
        slug=await _unique_slug(session, data.title),
        description=data.description,
        introduction=data.introduction,
        tips=data.tips,
        preparation_time_minutes=data.preparation_time_minutes,
        cooking_time_minutes=data.cooking_time_minutes,
        difficulty=difficulty,
        servings=data.servings,
        recipe_type=data.recipe_type,
        status=RecipeStatus.PUBLISHED,
        origin_type=OriginType.AI_ASSISTED,
        published_at=now,
        categories=list(categories),
        ingredients=[
            RecipeIngredient(
                ingredient_id=ingredient.id,
                quantity=Decimal(line["quantity"]) if line["quantity"] is not None else None,
                quantity_max=Decimal(line["quantity_max"])
                if line["quantity_max"] is not None
                else None,
                unit_code=unit,
                is_optional=line["optional"],
                preparation_notes=line["notes"],
                group_label=line["group"],
                position=line["index"],
            )
            for line, ingredient, unit in resolved_lines
        ],
        steps=[
            PreparationStep(step_number=number, description=text)
            for number, text in enumerate(data.steps, start=1)
        ],
        sources=[
            RecipeSource(
                source_name=submission.source.name,
                source_url=str(submission.source.url) if submission.source.url else None,
                attribution=submission.source.attribution,
                license=submission.source.license,
                source_type=submission.source.source_type,
            )
        ],
        drink_details=drink_details,
    )
    session.add(recipe)
    await session.flush()

    if skills:
        await session.execute(
            recipe_skill.insert().values(
                [{"recipe_id": recipe.id, "skill_id": s.id} for s in skills]
            )
        )
    if stage is not None:
        last = await session.scalar(
            select(func.coalesce(func.max(PathDish.position), 0)).where(
                PathDish.stage_id == stage.id
            )
        )
        session.add(PathDish(stage_id=stage.id, recipe_id=recipe.id, position=(last or 0) + 1))
    session.add(
        RecipeRevision(
            recipe_id=recipe.id,
            revision_number=1,
            snapshot={"submission": job.payload["submission"], "job_id": str(job.id)},
            change_summary=f"Aprobada desde el envío del agente (job {job.id})",
            created_by=reviewer.id,
        )
    )

    job.status = IngestionStatus.COMPLETED
    job.result_recipe_id = recipe.id
    job.reviewed_by = reviewer.id
    job.reviewed_at = now
    job.review_notes = body.review_notes
    await session.commit()
    logger.warning(
        "AUDIT submission approved: reviewer=%s job=%s recipe=%s", reviewer.id, job.id, recipe.slug
    )
    return job, recipe


def recipe_type_of(job: IngestionJob) -> RecipeType:
    assert job.payload is not None
    return RecipeType(job.payload["submission"]["recipe"]["recipe_type"])
