"""Role hierarchy. Permissions are enforced on the backend, never only in the UI."""

from app.models.enums import UserRole

_RANK: dict[UserRole, int] = {UserRole.USER: 0, UserRole.MODERATOR: 1, UserRole.ADMIN: 2}


def has_role(actual: UserRole, minimum: UserRole) -> bool:
    """True when ``actual`` is at least ``minimum`` (admin > moderator > user)."""
    return _RANK[actual] >= _RANK[minimum]
