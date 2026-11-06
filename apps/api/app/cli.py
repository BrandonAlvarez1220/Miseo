"""Operator commands that need database access, not an API call.

Bootstrapping the first administrator cannot go through the API (nobody is an
admin yet), and it must not be possible from the outside, so it lives here:

    uv run python -m app.cli grant-role --email you@example.com --role admin

The user must have signed in once so their profile exists.
"""

import argparse
import asyncio
import sys
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import create_engine, create_session_factory
from app.models import AppUser
from app.models.enums import UserRole


async def grant_role(
    session: AsyncSession, *, role: UserRole, email: str | None, user_id: uuid.UUID | None
) -> AppUser:
    if (email is None) == (user_id is None):
        raise SystemExit("Provide exactly one of --email or --user-id")
    stmt = select(AppUser)
    stmt = stmt.where(AppUser.id == user_id) if user_id else stmt.where(AppUser.email == email)
    users = (await session.scalars(stmt)).all()
    if not users:
        raise SystemExit("No such user. They must sign in once before they can be promoted.")
    if len(users) > 1:
        raise SystemExit("More than one user has that email; use --user-id instead.")
    users[0].role = role
    await session.commit()
    return users[0]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    grant = commands.add_parser("grant-role", help="Set a user's role")
    grant.add_argument("--email")
    grant.add_argument("--user-id", type=uuid.UUID)
    grant.add_argument("--role", type=UserRole, choices=list(UserRole), required=True)
    return parser


async def _main(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    engine = create_engine(get_settings())
    try:
        async with create_session_factory(engine)() as session:
            user = await grant_role(session, role=args.role, email=args.email, user_id=args.user_id)
    finally:
        await engine.dispose()
    print(f"{user.email or user.id} is now {user.role.value}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main(sys.argv[1:])))
