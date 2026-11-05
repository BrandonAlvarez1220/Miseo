import unicodedata
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import UserRole
from app.schemas.common import APIModel


class UserRead(APIModel):
    id: uuid.UUID
    email: str | None
    display_name: str
    role: UserRole
    created_at: datetime


class UserUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)

    @field_validator("display_name")
    @classmethod
    def _clean(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("display_name must not be blank")
        if any(unicodedata.category(char).startswith("C") for char in cleaned):
            raise ValueError("display_name must not contain control characters")
        return cleaned


class RoleUpdate(BaseModel):
    role: UserRole
