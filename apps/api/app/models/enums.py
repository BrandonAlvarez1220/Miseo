"""Domain enumerations.

Stored as ``VARCHAR`` + ``CHECK`` constraint (``native_enum=False``) rather than
native PostgreSQL enums, so adding a value is a regular migration instead of an
``ALTER TYPE``.
"""

from enum import StrEnum

from sqlalchemy import Enum as SAEnum


class RecipeType(StrEnum):
    COOKING = "cooking"
    DRINK = "drink"


class RecipeStatus(StrEnum):
    DRAFT = "draft"
    PENDING = "pending"
    PUBLISHED = "published"
    REJECTED = "rejected"


class OriginType(StrEnum):
    COMMUNITY = "community"
    CURATED = "curated"
    AI_ASSISTED = "ai_assisted"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class UserRole(StrEnum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class UnitType(StrEnum):
    MASS = "mass"
    VOLUME = "volume"
    COUNT = "count"
    OTHER = "other"


class SubstitutionType(StrEnum):
    EQUIVALENT = "equivalent"
    SIMILAR = "similar"
    EMERGENCY = "emergency"


class SourceType(StrEnum):
    WEBSITE = "website"
    BOOK = "book"
    COMMUNITY = "community"
    ORIGINAL = "original"
    AI_GENERATED = "ai_generated"
    OTHER = "other"


class DrinkClassification(StrEnum):
    CLASSIC = "classic"
    VARIATION = "variation"
    CONTEMPORARY = "contemporary"
    EXPERIMENTAL = "experimental"


class ContributionStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class IngestionStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    NEEDS_REVIEW = "needs_review"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class DuplicateStatus(StrEnum):
    OPEN = "open"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"


def str_enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    """VARCHAR column restricted by a named CHECK constraint to the enum values."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=max(len(member.value) for member in enum_cls),
        values_callable=lambda cls: [member.value for member in cls],
        validate_strings=True,
    )
