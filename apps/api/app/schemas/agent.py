import re
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import AgentProvider, AgentScope
from app.schemas.common import APIModel

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{1,59}$")


class AgentCreate(BaseModel):
    name: str = Field(description="Unique, 2-60 characters, e.g. 'Claude recetas MX'.")
    provider: AgentProvider
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        value = value.strip()
        if not _NAME.fullmatch(value):
            raise ValueError(
                "name must be 2-60 letters, digits, spaces, dots, dashes or underscores"
            )
        return value


class AgentRead(APIModel):
    id: uuid.UUID
    name: str
    provider: AgentProvider
    description: str | None
    token_prefix: str
    scopes: list[AgentScope]
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


class AgentCreated(AgentRead):
    token: str = Field(description="Shown ONCE. Only its hash is stored; it cannot be recovered.")
