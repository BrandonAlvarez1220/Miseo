from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import SessionDep
from app.models import BartendingTechnique, GlassType
from app.schemas.recipe import CatalogItemRead

router = APIRouter(prefix="/mixology", tags=["mixology"])


@router.get("/techniques", response_model=list[CatalogItemRead], summary="Bartending techniques")
async def list_techniques(session: SessionDep) -> list[CatalogItemRead]:
    rows = await session.scalars(select(BartendingTechnique).order_by(BartendingTechnique.name))
    return [CatalogItemRead.model_validate(t) for t in rows.all()]


@router.get("/glass-types", response_model=list[CatalogItemRead], summary="Glassware")
async def list_glass_types(session: SessionDep) -> list[CatalogItemRead]:
    rows = await session.scalars(select(GlassType).order_by(GlassType.name))
    return [CatalogItemRead.model_validate(g) for g in rows.all()]
