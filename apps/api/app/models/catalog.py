"""Reference catalogs: categories, ingredients, units and mixology lookups."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import RecipeType, SubstitutionType, UnitType, str_enum


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "category"
    __table_args__ = (UniqueConstraint("recipe_type", "slug"),)

    name: Mapped[str] = mapped_column(String(80))
    slug: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    recipe_type: Mapped[RecipeType] = mapped_column(str_enum(RecipeType, "recipe_type"))


class IngredientCategory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ingredient_category"

    name: Mapped[str] = mapped_column(String(80))
    slug: Mapped[str] = mapped_column(String(100), unique=True)


class Ingredient(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ingredient"
    __table_args__ = (
        CheckConstraint("abv IS NULL OR (abv >= 0 AND abv <= 100)", name="abv_range"),
        Index(
            "ix_ingredient_normalized_name_trgm",
            "normalized_name",
            postgresql_using="gin",
            postgresql_ops={"normalized_name": "gin_trgm_ops"},
        ),
    )

    name: Mapped[str] = mapped_column(String(120))
    normalized_name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ingredient_category.id", ondelete="SET NULL"), index=True
    )
    is_alcoholic: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    abv: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    image_url: Mapped[str | None] = mapped_column(Text)

    category: Mapped[IngredientCategory | None] = relationship()
    aliases: Mapped[list["IngredientAlias"]] = relationship(
        back_populates="ingredient", cascade="all, delete-orphan"
    )


class IngredientAlias(UUIDPrimaryKeyMixin, Base):
    """Synonym used for deterministic ingredient mapping (e.g. "coriander" -> cilantro)."""

    __tablename__ = "ingredient_alias"

    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredient.id", ondelete="CASCADE"), index=True
    )
    alias: Mapped[str] = mapped_column(String(120))
    normalized_alias: Mapped[str] = mapped_column(String(120), unique=True)

    ingredient: Mapped[Ingredient] = relationship(back_populates="aliases")


class Unit(Base):
    """Standardized measurement unit. ``to_base_factor`` converts to g or ml."""

    __tablename__ = "unit"
    __table_args__ = (
        CheckConstraint(
            "to_base_factor IS NULL OR to_base_factor > 0", name="to_base_factor_positive"
        ),
    )

    code: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    plural_name: Mapped[str] = mapped_column(String(40))
    unit_type: Mapped[UnitType] = mapped_column(str_enum(UnitType, "unit_type"))
    to_base_factor: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))


class IngredientAlternative(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Directed substitution: ``ingredient`` can be replaced by ``alternative_ingredient``."""

    __tablename__ = "ingredient_alternative"
    __table_args__ = (
        UniqueConstraint("ingredient_id", "alternative_ingredient_id"),
        CheckConstraint("ingredient_id <> alternative_ingredient_id", name="not_self"),
        CheckConstraint("ratio > 0", name="ratio_positive"),
    )

    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredient.id", ondelete="CASCADE"), index=True
    )
    alternative_ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredient.id", ondelete="CASCADE"), index=True
    )
    substitution_type: Mapped[SubstitutionType] = mapped_column(
        str_enum(SubstitutionType, "substitution_type")
    )
    ratio: Mapped[Decimal] = mapped_column(
        Numeric(6, 3), default=Decimal(1), server_default=text("1")
    )
    equivalence_notes: Mapped[str | None] = mapped_column(Text)

    ingredient: Mapped[Ingredient] = relationship(foreign_keys=[ingredient_id])
    alternative_ingredient: Mapped[Ingredient] = relationship(
        foreign_keys=[alternative_ingredient_id]
    )


class GlassType(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "glass_type"

    name: Mapped[str] = mapped_column(String(80))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)


class BartendingTechnique(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "bartending_technique"

    name: Mapped[str] = mapped_column(String(80))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
