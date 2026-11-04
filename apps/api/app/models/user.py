import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import UserRole, str_enum


class AppUser(TimestampMixin, Base):
    """Application profile for a Supabase Auth user.

    ``id`` equals the ``sub`` claim of the Supabase JWT. There is intentionally
    no FK to ``auth.users``: that schema does not exist locally or in tests.
    """

    __tablename__ = "app_user"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(80))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(
        str_enum(UserRole, "role"), default=UserRole.USER, server_default=UserRole.USER.value
    )
