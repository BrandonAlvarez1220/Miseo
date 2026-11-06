from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import SessionDep
from app.models import Unit
from app.schemas.recipe import UnitRead

router = APIRouter(prefix="/units", tags=["catalog"])


@router.get(
    "",
    response_model=list[UnitRead],
    summary="Measurement units",
    description="Use these codes in recipe submissions (common names like 'gramos' also work).",
)
async def list_units(session: SessionDep) -> list[UnitRead]:
    rows = await session.scalars(select(Unit).order_by(Unit.unit_type, Unit.code))
    return [UnitRead.model_validate(unit) for unit in rows.all()]
