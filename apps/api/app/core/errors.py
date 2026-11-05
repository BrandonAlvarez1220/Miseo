"""Uniform error responses.

Every error leaves the API with the same shape so clients can handle them
generically::

    {"error": {"code": "not_found", "message": "...", "details": null}}
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base class for expected, client-facing domain errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "bad_request"

    def __init__(
        self, message: str, *, details: Any = None, headers: dict[str, str] | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
        self.headers = headers


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class UnauthorizedError(AppError):
    """Missing or invalid credentials (401). Tells clients to retry with a Bearer token."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, headers={"WWW-Authenticate": "Bearer"})


class ForbiddenError(AppError):
    """Authenticated, but not allowed to do this (403)."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"


class AuthUnavailableError(AppError):
    """Authentication cannot be checked right now (not configured, or key source down)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "auth_unavailable"


def _error_body(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details}}


_HTTP_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    429: "rate_limited",
}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, exc.details),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"loc": list(err["loc"]), "message": err["msg"], "type": err["type"]}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_error_body("validation_error", "Request validation failed", details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODES.get(exc.status_code, "http_error")
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(code, str(exc.detail)),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # Log the full traceback, but never leak internals to the client.
        logger.exception("Unhandled error", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("internal_error", "An unexpected error occurred"),
        )
