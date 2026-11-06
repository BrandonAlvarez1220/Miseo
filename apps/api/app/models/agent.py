"""External ingestion agents (opencode, Claude, Gemini...) that submit recipes.

An agent is its own principal: it authenticates with a long random token that is
shown once at creation and stored only as a SHA-256 hash.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AgentProvider, str_enum


class Agent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent"
    __table_args__ = (
        CheckConstraint("char_length(name) BETWEEN 2 AND 60", name="name_length"),
        CheckConstraint("scopes <@ ARRAY['submit_recipes']::varchar[]", name="scopes_known"),
        CheckConstraint("cardinality(scopes) > 0", name="has_scope"),
    )

    name: Mapped[str] = mapped_column(String(60), unique=True)
    provider: Mapped[AgentProvider] = mapped_column(str_enum(AgentProvider, "provider"))
    description: Mapped[str | None] = mapped_column(Text)
    # First characters of the token, to recognise it in listings. Not secret.
    token_prefix: Mapped[str] = mapped_column(String(16))
    # SHA-256 of the full token. Tokens carry 256 bits of randomness, so a fast
    # hash is appropriate (no password-style stretching needed).
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String(40)))
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL")
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None
