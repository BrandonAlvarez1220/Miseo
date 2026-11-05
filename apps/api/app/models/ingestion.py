"""AI-assisted ingestion bookkeeping (used from Phase 4)."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DuplicateStatus, IngestionStatus, IssueSeverity, str_enum


class IngestionJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ingestion_job"

    # Hash of the normalized source (URL or content). UNIQUE makes re-submissions
    # of the same recipe idempotent.
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    status: Mapped[IngestionStatus] = mapped_column(
        str_enum(IngestionStatus, "status"),
        default=IngestionStatus.QUEUED,
        server_default=IngestionStatus.QUEUED.value,
        index=True,
    )
    source_url: Mapped[str | None] = mapped_column(Text)
    raw_input: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(String(60))
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    last_error: Mapped[str | None] = mapped_column(Text)
    result_recipe_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("recipe.id", ondelete="SET NULL")
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL")
    )
    # The external agent (opencode, Claude, Gemini...) that submitted it: provenance.
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent.id", ondelete="SET NULL"), index=True
    )
    # Cleaned submission plus the ingredient/unit lines resolved by our pipeline.
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # Deterministic analysis: difficulty, suggested skills and stage, duplicates.
    analysis: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_notes: Mapped[str | None] = mapped_column(Text)


class IngestionIssue(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ingestion_issue"

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingestion_job.id", ondelete="CASCADE"), index=True
    )
    severity: Mapped[IssueSeverity] = mapped_column(str_enum(IssueSeverity, "severity"))
    code: Mapped[str] = mapped_column(String(60))
    message: Mapped[str] = mapped_column(Text)
    field_path: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DuplicateCandidate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "duplicate_candidate"
    __table_args__ = (
        UniqueConstraint("recipe_id", "candidate_recipe_id"),
        CheckConstraint("recipe_id <> candidate_recipe_id", name="not_self"),
        CheckConstraint("similarity >= 0 AND similarity <= 1", name="similarity_range"),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipe.id", ondelete="CASCADE"), index=True
    )
    candidate_recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipe.id", ondelete="CASCADE"), index=True
    )
    similarity: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[DuplicateStatus] = mapped_column(
        str_enum(DuplicateStatus, "status"),
        default=DuplicateStatus.OPEN,
        server_default=DuplicateStatus.OPEN.value,
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ingestion_job.id", ondelete="SET NULL")
    )
