"""Receive a recipe from an agent: validate, normalize, analyse and queue for review.

Nothing here publishes anything. The result is an ``IngestionJob`` in ``needs_review``
holding the cleaned submission, the resolved lines, the issues found and a
deterministic analysis (difficulty, suggested skills, suggested stage, duplicates).
A person approves or rejects it (``review.py``).

Submitting is idempotent. The key comes from the source URL (or title + source name):

* same key, same agent, still in review, different content -> the job is UPDATED
  (agents can fix issues; limited to ``agent_max_revisions``);
* same key and identical content, or any other agent/status -> returned UNCHANGED;
* two submissions can therefore never create two jobs for one recipe.
"""

import hashlib
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ConflictError, TooManyRequestsError
from app.models import (
    Agent,
    BartendingTechnique,
    Category,
    GlassType,
    IngestionIssue,
    IngestionJob,
    Skill,
)
from app.models.enums import (
    DrinkClassification,
    IngestionStatus,
    IssueSeverity,
    RecipeType,
    SourceType,
)
from app.schemas.submission import (
    Analysis,
    CandidateRead,
    ClassificationInfo,
    DifficultyAnalysis,
    LineRead,
    PlacementSuggestion,
    RecipeSubmission,
    SkillSuggestion,
)
from app.services.ingestion.context import path_stage_infos
from app.services.ingestion.difficulty import DifficultyInput, score_difficulty
from app.services.ingestion.duplicates import find_duplicates
from app.services.ingestion.normalize import Issue, ResolvedLine, resolve_lines
from app.services.ingestion.placement import suggest_stage
from app.services.ingestion.skills import detect_skills
from app.services.normalization import normalize_text

logger = logging.getLogger(__name__)

Outcome = Literal["created", "updated", "unchanged"]
_TRACKING_PARAMS = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "igshid"}
MIN_AVERAGE_STEP_LENGTH = 25


def canonical_url(url: str) -> str:
    """Same page, same string: lowercase host, no fragment, no tracking parameters."""
    parts = urlsplit(url.strip())
    query = sorted(
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in _TRACKING_PARAMS
    )
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def idempotency_key(submission: RecipeSubmission) -> str:
    if submission.source.url is not None:
        basis = "url:" + canonical_url(str(submission.source.url))
    else:
        basis = (
            f"title:{normalize_text(submission.recipe.title)}|"
            f"source:{normalize_text(submission.source.name)}|{submission.recipe.recipe_type.value}"
        )
    return hashlib.sha256(basis.encode()).hexdigest()


@dataclass
class Analyzed:
    lines: list[ResolvedLine]
    issues: list[Issue]
    analysis: Analysis
    resolved: dict[str, object]


def _line_read(line: ResolvedLine) -> LineRead:
    return LineRead(
        index=line.index,
        name=line.name,
        ingredient_slug=line.ingredient.slug if line.ingredient else None,
        ingredient_name=line.ingredient.name if line.ingredient else None,
        candidates=[
            CandidateRead(slug=c.slug, name=c.name, similarity=c.similarity)
            for c in line.candidates
        ],
        quantity=line.quantity,
        quantity_max=line.quantity_max,
        unit_code=line.unit_code,
        unit_text=line.unit_text,
        optional=line.optional,
        notes=line.notes,
        group=line.group,
    )


def _match_catalog_item(items: Sequence[tuple[str, str]], text: str | None) -> str | None:
    """Slug of the (slug, name) pair whose slug or name equals ``text``."""
    if not text:
        return None
    wanted = normalize_text(text)
    for slug, name in items:
        if wanted in (slug.replace("-", " "), normalize_text(name)):
            return slug
    return None


async def analyze(
    session: AsyncSession, submission: RecipeSubmission, *, exclude_job_id: object | None = None
) -> Analyzed:
    recipe = submission.recipe
    issues: list[Issue] = []

    lines = await resolve_lines(session, recipe.ingredients)
    for line in lines:
        issues.extend(line.issues)

    # Categories: keep the valid ones, flag the rest.
    valid_categories: list[str] = []
    if recipe.categories:
        known = set(
            (
                await session.scalars(
                    select(Category.slug).where(
                        Category.recipe_type == recipe.recipe_type,
                        Category.slug.in_(recipe.categories),
                    )
                )
            ).all()
        )
        valid_categories = [slug for slug in recipe.categories if slug in known]
        for slug in recipe.categories:
            if slug not in known:
                issues.append(
                    Issue(
                        IssueSeverity.WARNING,
                        "unknown_category",
                        f"category '{slug}' does not exist for {recipe.recipe_type.value} recipes",
                        "recipe.categories",
                    )
                )
    if not valid_categories:
        issues.append(
            Issue(
                IssueSeverity.WARNING,
                "no_category",
                "no valid category: the reviewer will have to choose one (see GET /categories)",
                "recipe.categories",
            )
        )

    resolved: dict[str, object] = {"categories": valid_categories}
    technique_slug: str | None = None
    classification: ClassificationInfo | None = None
    if recipe.drink is not None:
        drink = recipe.drink
        glasses = (await session.execute(select(GlassType.slug, GlassType.name))).all()
        techniques = (
            await session.execute(select(BartendingTechnique.slug, BartendingTechnique.name))
        ).all()
        glass_slug = _match_catalog_item([(g[0], g[1]) for g in glasses], drink.glass)
        technique_slug = _match_catalog_item([(t[0], t[1]) for t in techniques], drink.technique)
        for label, given, found in (
            ("glass", drink.glass, glass_slug),
            ("technique", drink.technique, technique_slug),
        ):
            if given and found is None:
                issues.append(
                    Issue(
                        IssueSeverity.WARNING,
                        f"unknown_{label}",
                        f"{label} '{given}' is not in the catalog (see GET /mixology/{label}s)",
                        f"recipe.drink.{label}",
                    )
                )
        spirit = next(
            (
                line.ingredient.slug
                for line in lines
                if line.ingredient
                and drink.base_spirit
                and normalize_text(line.name) == normalize_text(drink.base_spirit)
            ),
            None,
        )
        resolved.update({"glass": glass_slug, "technique": technique_slug, "base_spirit": spirit})
        # An agent can never publish a cocktail as a documented classic.
        suggested = (
            DrinkClassification.CONTEMPORARY
            if drink.claimed_classification == DrinkClassification.CONTEMPORARY
            else DrinkClassification.EXPERIMENTAL
        )
        classification = ClassificationInfo(
            claimed=drink.claimed_classification, suggested=suggested
        )
        if drink.claimed_classification in (
            DrinkClassification.CLASSIC,
            DrinkClassification.VARIATION,
        ):
            issues.append(
                Issue(
                    IssueSeverity.INFO,
                    "classification_downgraded",
                    f"claimed '{drink.claimed_classification.value}' needs a verified source; "
                    f"queued as '{suggested.value}'",
                    "recipe.drink.claimed_classification",
                )
            )

    if recipe.preparation_time_minutes is None and recipe.cooking_time_minutes is None:
        issues.append(
            Issue(IssueSeverity.WARNING, "missing_time", "no preparation or cooking time", "recipe")
        )
    source = submission.source
    if (
        source.source_type in (SourceType.WEBSITE, SourceType.BOOK, SourceType.OTHER)
        and not source.license
    ):
        issues.append(
            Issue(
                IssueSeverity.WARNING,
                "license_unknown",
                "the source has no license: confirm the content may be reused before approving",
                "source.license",
            )
        )
    if sum(len(step) for step in recipe.steps) / len(recipe.steps) < MIN_AVERAGE_STEP_LENGTH:
        issues.append(
            Issue(IssueSeverity.WARNING, "short_steps", "the steps are very terse", "recipe.steps")
        )

    # Difficulty, skills, placement.
    main_ingredients = sum(
        1
        for line in lines
        if not line.optional and not (line.ingredient and line.ingredient.is_staple)
    )
    minutes = None
    if recipe.preparation_time_minutes is not None or recipe.cooking_time_minutes is not None:
        minutes = (recipe.preparation_time_minutes or 0) + (recipe.cooking_time_minutes or 0)
    difficulty = score_difficulty(
        DifficultyInput(
            steps=recipe.steps, main_ingredients=main_ingredients, total_minutes=minutes
        )
    )

    skill_slugs = detect_skills(
        recipe_type=recipe.recipe_type.value,
        steps=recipe.steps,
        ingredient_slugs={line.ingredient.slug for line in lines if line.ingredient},
        technique=technique_slug,
        extra_text=[f"{line.name} {line.notes or ''}" for line in lines],
    )
    skills_by_slug = {
        skill.slug: skill
        for skill in (await session.scalars(select(Skill).where(Skill.slug.in_(skill_slugs)))).all()
    }
    skills = [
        SkillSuggestion(slug=slug, name=skills_by_slug[slug].name)
        for slug in skill_slugs
        if slug in skills_by_slug
    ]

    placements: list[PlacementSuggestion] = []
    for path, stages in await path_stage_infos(session, recipe.recipe_type):
        placement = suggest_stage(
            score=difficulty.score, skills=[s.slug for s in skills], stages=stages
        )
        if placement is not None:
            placements.append(
                PlacementSuggestion(
                    path_slug=path.slug,
                    path_title=path.title,
                    stage_position=placement.stage_position,
                    stage_title=placement.stage_title,
                    new_stage=placement.new_stage,
                    unknown_skills=list(placement.unknown_skills),
                    introduces=list(placement.introduces),
                    reason=placement.reason,
                )
            )

    duplicates = await find_duplicates(
        session,
        title=recipe.title,
        recipe_type=recipe.recipe_type,
        main_ingredient_ids={
            line.ingredient.id
            for line in lines
            if line.ingredient and not line.optional and not line.ingredient.is_staple
        },
        exclude_job_id=exclude_job_id,  # type: ignore[arg-type]
    )
    for duplicate in duplicates[:3]:
        issues.append(
            Issue(
                IssueSeverity.WARNING,
                "possible_duplicate",
                f"similar to '{duplicate.title}' ({duplicate.reason}, {duplicate.similarity})",
                "recipe.title",
            )
        )

    analysis = Analysis(
        difficulty=DifficultyAnalysis(
            score=difficulty.score, label=difficulty.label, reasons=list(difficulty.reasons)
        ),
        skills=skills,
        placements=placements,
        duplicates=duplicates,
        classification=classification,
    )
    return Analyzed(lines=lines, issues=issues, analysis=analysis, resolved=resolved)


def _payload(submission: RecipeSubmission, analyzed: Analyzed) -> dict[str, object]:
    return {
        "submission": submission.model_dump(mode="json"),
        "lines": [_line_read(line).model_dump(mode="json") for line in analyzed.lines],
        "resolved": analyzed.resolved,
    }


async def _check_limits(session: AsyncSession, settings: Settings, agent: Agent) -> None:
    hour_ago = datetime.now(UTC) - timedelta(hours=1)
    recent = await session.scalar(
        select(func.count())
        .select_from(IngestionJob)
        .where(IngestionJob.agent_id == agent.id, IngestionJob.created_at >= hour_ago)
    )
    if (recent or 0) >= settings.agent_max_submissions_per_hour:
        raise TooManyRequestsError(
            f"Limit of {settings.agent_max_submissions_per_hour} new submissions per hour reached"
        )
    pending = await session.scalar(
        select(func.count())
        .select_from(IngestionJob)
        .where(
            IngestionJob.agent_id == agent.id, IngestionJob.status == IngestionStatus.NEEDS_REVIEW
        )
    )
    if (pending or 0) >= settings.agent_max_pending:
        raise TooManyRequestsError(
            f"{settings.agent_max_pending} submissions are already waiting for review: "
            "wait for a moderator before sending more",
            retry_after_seconds=6 * 3600,
        )


async def _replace_issues(session: AsyncSession, job: IngestionJob, issues: list[Issue]) -> None:
    await session.execute(delete(IngestionIssue).where(IngestionIssue.job_id == job.id))
    session.add_all(
        IngestionIssue(
            job_id=job.id,
            severity=issue.severity,
            code=issue.code,
            message=issue.message,
            field_path=issue.field_path,
        )
        for issue in issues
    )


async def submit(
    session: AsyncSession, settings: Settings, agent: Agent, submission: RecipeSubmission
) -> tuple[IngestionJob, Outcome]:
    key = idempotency_key(submission)
    existing = await session.scalar(select(IngestionJob).where(IngestionJob.idempotency_key == key))

    if existing is not None:
        if existing.agent_id != agent.id or existing.status != IngestionStatus.NEEDS_REVIEW:
            return existing, "unchanged"
        if (existing.payload or {}).get("submission") == submission.model_dump(mode="json"):
            return existing, "unchanged"  # a plain retry: nothing to redo, no revision used
        if existing.attempts > settings.agent_max_revisions:
            raise ConflictError(
                f"This submission was already revised {settings.agent_max_revisions} times; "
                "wait for the review"
            )
        analyzed = await analyze(session, submission, exclude_job_id=existing.id)
        existing.payload = _payload(submission, analyzed)
        existing.analysis = analyzed.analysis.model_dump(mode="json")
        existing.attempts += 1
        await _replace_issues(session, existing, analyzed.issues)
        await session.commit()
        logger.info("Agent %s revised submission %s", agent.name, existing.id)
        return existing, "updated"

    await _check_limits(session, settings, agent)
    analyzed = await analyze(session, submission)
    job = IngestionJob(
        idempotency_key=key,
        status=IngestionStatus.NEEDS_REVIEW,
        source_url=str(submission.source.url) if submission.source.url else None,
        provider=agent.provider.value,
        attempts=1,
        agent_id=agent.id,
        payload=_payload(submission, analyzed),
        analysis=analyzed.analysis.model_dump(mode="json"),
    )
    session.add(job)
    try:
        await session.flush()
    except IntegrityError:
        # Two identical submissions raced: the other one won; report it as the existing job.
        await session.rollback()
        winner = await session.scalar(
            select(IngestionJob).where(IngestionJob.idempotency_key == key)
        )
        if winner is None:  # pragma: no cover - the unique violation proves it exists
            raise
        return winner, "unchanged"
    await _replace_issues(session, job, analyzed.issues)
    await session.commit()
    logger.info("Agent %s submitted %s (%s)", agent.name, job.id, submission.recipe.title)
    return job, "created"


def recipe_type_of(job: IngestionJob) -> RecipeType:
    assert job.payload is not None
    return RecipeType(job.payload["submission"]["recipe"]["recipe_type"])
