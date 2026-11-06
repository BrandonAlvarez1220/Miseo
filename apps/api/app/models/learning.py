"""Learning paths: a ladder of dishes from easy to complex.

Skills are tags on recipes ("what you learn cooking this"); a path is an ordered
list of stages, each with a few dishes. Progress (Phase 3) will reference recipes.
"""

import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import RecipeType, str_enum
from app.models.recipe import Recipe

recipe_skill = Table(
    "recipe_skill",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipe.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skill.id", ondelete="CASCADE"), primary_key=True, index=True),
)


class Skill(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "skill"

    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    discipline: Mapped[RecipeType] = mapped_column(str_enum(RecipeType, "discipline"))
    # Short explanation shown the first time the skill appears ("how to know...").
    tip: Mapped[str] = mapped_column(Text)


class LearningPath(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "learning_path"

    slug: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(160))
    discipline: Mapped[RecipeType] = mapped_column(str_enum(RecipeType, "discipline"))
    description: Mapped[str | None] = mapped_column(Text)

    stages: Mapped[list["PathStage"]] = relationship(
        back_populates="path", cascade="all, delete-orphan", order_by="PathStage.position"
    )


class PathStage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "path_stage"
    __table_args__ = (
        UniqueConstraint("path_id", "position"),
        CheckConstraint("position > 0", name="position_positive"),
        CheckConstraint("dishes_to_unlock >= 0", name="dishes_to_unlock_non_negative"),
    )

    path_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_path.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    # Dishes of this stage a user should cook before the next stage is "unlocked".
    # Unlocking is a soft suggestion: every stage stays browsable.
    dishes_to_unlock: Mapped[int] = mapped_column(Integer)

    path: Mapped[LearningPath] = relationship(back_populates="stages")
    dishes: Mapped[list["PathDish"]] = relationship(
        back_populates="stage", cascade="all, delete-orphan", order_by="PathDish.position"
    )


class PathDish(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "path_dish"
    __table_args__ = (
        UniqueConstraint("stage_id", "position"),
        UniqueConstraint("stage_id", "recipe_id"),
    )

    stage_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("path_stage.id", ondelete="CASCADE"))
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipe.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)

    stage: Mapped[PathStage] = relationship(back_populates="dishes")
    recipe: Mapped[Recipe] = relationship()
