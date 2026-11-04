"""Recipe aggregate: recipe, its ingredients, steps, sources and drink metadata."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.catalog import BartendingTechnique, Category, GlassType, Ingredient, Unit
from app.models.enums import (
    Difficulty,
    DrinkClassification,
    OriginType,
    RecipeStatus,
    RecipeType,
    SourceType,
    str_enum,
)

recipe_category = Table(
    "recipe_category",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipe.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "category_id", ForeignKey("category.id", ondelete="CASCADE"), primary_key=True, index=True
    ),
)


class Recipe(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recipe"
    __table_args__ = (
        CheckConstraint("servings > 0", name="servings_positive"),
        CheckConstraint(
            "preparation_time_minutes IS NULL OR preparation_time_minutes >= 0",
            name="preparation_time_non_negative",
        ),
        CheckConstraint(
            "cooking_time_minutes IS NULL OR cooking_time_minutes >= 0",
            name="cooking_time_non_negative",
        ),
        CheckConstraint(
            "status <> 'published' OR published_at IS NOT NULL", name="published_has_date"
        ),
        Index("ix_recipe_status_recipe_type", "status", "recipe_type"),
        Index(
            "ix_recipe_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
    )

    title: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(180), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    introduction: Mapped[str | None] = mapped_column(Text)
    tips: Mapped[str | None] = mapped_column(Text)
    preparation_time_minutes: Mapped[int | None] = mapped_column(Integer)
    cooking_time_minutes: Mapped[int | None] = mapped_column(Integer)
    difficulty: Mapped[Difficulty | None] = mapped_column(str_enum(Difficulty, "difficulty"))
    servings: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"))
    image_url: Mapped[str | None] = mapped_column(Text)
    recipe_type: Mapped[RecipeType] = mapped_column(str_enum(RecipeType, "recipe_type"))
    status: Mapped[RecipeStatus] = mapped_column(
        str_enum(RecipeStatus, "status"),
        default=RecipeStatus.DRAFT,
        server_default=RecipeStatus.DRAFT.value,
    )
    origin_type: Mapped[OriginType] = mapped_column(str_enum(OriginType, "origin_type"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"), index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    categories: Mapped[list[Category]] = relationship(secondary=recipe_category)
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeIngredient.position",
    )
    steps: Mapped[list["PreparationStep"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="PreparationStep.step_number",
    )
    sources: Mapped[list["RecipeSource"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )
    drink_details: Mapped["DrinkDetails | None"] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        foreign_keys="DrinkDetails.recipe_id",
    )


class RecipeIngredient(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "recipe_ingredient"
    __table_args__ = (
        # Same ingredient may appear in different groups ("dough", "topping"), but not
        # twice in the same group. NULLS NOT DISTINCT (PG15+) treats "no group" as a group.
        UniqueConstraint(
            "recipe_id",
            "ingredient_id",
            "group_label",
            postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint("quantity IS NULL OR quantity > 0", name="quantity_positive"),
        CheckConstraint(
            "quantity_max IS NULL OR (quantity IS NOT NULL AND quantity_max >= quantity)",
            name="quantity_range_valid",
        ),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipe.id", ondelete="CASCADE"), index=True
    )
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredient.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    quantity_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    unit_code: Mapped[str | None] = mapped_column(ForeignKey("unit.code", ondelete="RESTRICT"))
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    preparation_notes: Mapped[str | None] = mapped_column(String(200))
    group_label: Mapped[str | None] = mapped_column(String(80))
    position: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))

    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")
    ingredient: Mapped[Ingredient] = relationship()
    unit: Mapped[Unit | None] = relationship()


class PreparationStep(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "preparation_step"
    __table_args__ = (
        UniqueConstraint("recipe_id", "step_number"),
        CheckConstraint("step_number > 0", name="step_number_positive"),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipe.id", ondelete="CASCADE"))
    step_number: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)

    recipe: Mapped[Recipe] = relationship(back_populates="steps")


class RecipeSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recipe_source"

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipe.id", ondelete="CASCADE"), index=True
    )
    source_name: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(Text)
    attribution: Mapped[str | None] = mapped_column(Text)
    license: Mapped[str | None] = mapped_column(String(120))
    source_type: Mapped[SourceType] = mapped_column(str_enum(SourceType, "source_type"))

    recipe: Mapped[Recipe] = relationship(back_populates="sources")


class DrinkDetails(Base):
    """Cocktail-specific metadata (1:1 with a drink recipe)."""

    __tablename__ = "drink_details"
    __table_args__ = (
        CheckConstraint(
            "abv_estimate IS NULL OR (abv_estimate >= 0 AND abv_estimate <= 100)",
            name="abv_estimate_range",
        ),
        CheckConstraint(
            "classification <> 'variation' OR variation_of_id IS NOT NULL",
            name="variation_has_parent",
        ),
        CheckConstraint("variation_of_id IS NULL OR variation_of_id <> recipe_id", name="not_self"),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipe.id", ondelete="CASCADE"), primary_key=True
    )
    is_alcoholic: Mapped[bool] = mapped_column(Boolean)
    base_spirit_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ingredient.id", ondelete="SET NULL"), index=True
    )
    glass_type_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("glass_type.id", ondelete="SET NULL"), index=True
    )
    technique_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bartending_technique.id", ondelete="SET NULL"), index=True
    )
    garnish: Mapped[str | None] = mapped_column(String(200))
    abv_estimate: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    classification: Mapped[DrinkClassification] = mapped_column(
        str_enum(DrinkClassification, "classification")
    )
    variation_of_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("recipe.id", ondelete="SET NULL"), index=True
    )

    recipe: Mapped[Recipe] = relationship(back_populates="drink_details", foreign_keys=[recipe_id])
    base_spirit: Mapped[Ingredient | None] = relationship()
    glass_type: Mapped[GlassType | None] = relationship()
    technique: Mapped[BartendingTechnique | None] = relationship()
    variation_of: Mapped[Recipe | None] = relationship(foreign_keys=[variation_of_id])
