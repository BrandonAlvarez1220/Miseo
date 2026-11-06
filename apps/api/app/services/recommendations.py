from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Ingredient
from app.models.enums import RecipeType
from app.repositories.recommendation import load_candidates
from app.schemas.recipe import IngredientRef
from app.schemas.recommendation import (
    RecommendationRead,
    RecommendationsResponse,
    SubstitutionRead,
)
from app.services import recipes as recipe_service
from app.services.matching import IngredientInfo, MatchMode, rank


def _ref(info: IngredientInfo) -> IngredientRef:
    return IngredientRef(id=info.id, name=info.name, slug=info.slug)


async def recommend(
    session: AsyncSession,
    slugs: tuple[str, ...],
    *,
    mode: MatchMode,
    recipe_type: RecipeType | None,
    assume_staples: bool,
    limit: int,
) -> RecommendationsResponse:
    found = (
        (await session.scalars(select(Ingredient).where(Ingredient.slug.in_(slugs)))).all()
        if slugs
        else []
    )
    by_slug = {i.slug: i for i in found}
    selected = [by_slug[s] for s in slugs if s in by_slug]
    unknown = [s for s in slugs if s not in by_slug]

    results: list[RecommendationRead] = []
    total = 0
    if selected:
        available = frozenset(i.id for i in selected)
        candidates = await load_candidates(session, available, recipe_type=recipe_type)
        ranked = rank(candidates, available, mode, assume_staples=assume_staples)
        total = len(ranked)
        top = ranked[:limit]
        summaries = {
            s.id: s
            for s in await recipe_service.summaries_in_order(session, [m.recipe_id for m in top])
        }
        results = [
            RecommendationRead(
                recipe=summaries[m.recipe_id],
                match_percentage=m.match_percentage,
                available_ingredients=[_ref(i) for i in m.available],
                missing_ingredients=[_ref(i) for i in m.missing],
                substitutions=[
                    SubstitutionRead(
                        missing=_ref(s.missing),
                        substitute=_ref(s.substitute.ingredient),
                        substitution_type=s.substitute.substitution_type,
                        ratio=s.substitute.ratio,
                        notes=s.substitute.notes,
                    )
                    for s in m.substitutions
                ],
                assumed_staples=[_ref(i) for i in m.assumed_staples],
                optional_available=[_ref(i) for i in m.optional_available],
                optional_missing=[_ref(i) for i in m.optional_missing],
            )
            for m in top
            if m.recipe_id in summaries
        ]

    return RecommendationsResponse(
        mode=mode,
        assume_staples=assume_staples,
        ingredients=[IngredientRef.model_validate(i) for i in selected],
        unknown_ingredients=unknown,
        total=total,
        results=results,
    )
