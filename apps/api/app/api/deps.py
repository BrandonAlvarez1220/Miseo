"""Shared FastAPI dependencies: database session and authentication/authorization."""

import asyncio
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.errors import AuthUnavailableError, ForbiddenError, UnauthorizedError
from app.core.security import Claims, TokenVerifier
from app.models import Agent, AppUser
from app.models.enums import AgentScope, UserRole
from app.services import agents as agent_service
from app.services import users as user_service
from app.services.permissions import has_role

# auto_error=False: we raise our own 401 so every error has the uniform JSON shape.
_bearer = HTTPBearer(auto_error=False, description="Supabase access token or agent token")


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
BearerDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


async def current_claims(request: Request, credentials: BearerDep) -> Claims:
    if credentials is None:
        raise UnauthorizedError()
    verifier: TokenVerifier = request.app.state.token_verifier
    if not verifier.configured:
        raise AuthUnavailableError("Authentication is not configured on this server")
    # Verification may fetch signing keys over the network: keep it off the event loop.
    return await asyncio.to_thread(verifier.verify, credentials.credentials)


async def current_user(
    claims: Annotated[Claims, Depends(current_claims)], session: SessionDep
) -> AppUser:
    return await user_service.get_or_provision(session, claims)


def require_role(minimum: UserRole):  # type: ignore[no-untyped-def]  # returns a FastAPI dependency
    async def dependency(user: Annotated[AppUser, Depends(current_user)]) -> AppUser:
        if not has_role(user.role, minimum):
            raise ForbiddenError("You do not have permission to do this")
        return user

    return dependency


def require_agent(scope: AgentScope):  # type: ignore[no-untyped-def]  # returns a FastAPI dependency
    async def dependency(credentials: BearerDep, session: SessionDep) -> Agent:
        if credentials is None:
            raise UnauthorizedError()
        agent = await agent_service.authenticate(session, credentials.credentials)
        if agent is None:
            raise UnauthorizedError("Invalid or revoked agent token")
        if scope.value not in agent.scopes:
            raise ForbiddenError("This agent token lacks the required scope")
        return agent

    return dependency


CurrentUser = Annotated[AppUser, Depends(current_user)]
ModeratorUser = Annotated[AppUser, Depends(require_role(UserRole.MODERATOR))]
AdminUser = Annotated[AppUser, Depends(require_role(UserRole.ADMIN))]
SubmitterAgent = Annotated[Agent, Depends(require_agent(AgentScope.SUBMIT_RECIPES))]
