"""Verification of Supabase Auth access tokens (JWT).

Security rules enforced here:

* The algorithm is **pinned by key type**, never taken on trust from the token:
  ``HS256`` is verified only with the configured shared secret, and asymmetric
  algorithms (``RS256``/``ES256``) only with keys fetched from the JWKS. This blocks
  the "algorithm confusion" attack (signing HS256 with a public key) and ``alg: none``.
* ``exp``, ``sub`` and ``aud`` are required; ``iss`` is checked when configured.
* Roles are NOT read from the token. Permissions come from our own database,
  so a user cannot grant themselves anything by editing their Supabase metadata.
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Any, Protocol

import jwt
from jwt import PyJWKClient

from app.core.config import Settings
from app.core.errors import AuthUnavailableError, UnauthorizedError

logger = logging.getLogger(__name__)

ASYMMETRIC_ALGORITHMS = ("RS256", "ES256")
CLOCK_SKEW_SECONDS = 10


@dataclass(frozen=True)
class Claims:
    """The verified, minimal identity extracted from an access token."""

    user_id: uuid.UUID
    email: str | None
    display_name: str | None


class KeyResolver(Protocol):
    """Finds the public key that signed a token (JWKS in production, a fake in tests)."""

    def resolve(self, token: str) -> Any: ...


class JWKSKeyResolver:
    def __init__(self, url: str) -> None:
        # PyJWKClient caches keys and refetches when it sees an unknown ``kid``.
        self._client = PyJWKClient(url, cache_keys=True, lifespan=3600, timeout=5)

    def resolve(self, token: str) -> Any:
        return self._client.get_signing_key_from_jwt(token).key


class TokenVerifier:
    def __init__(
        self,
        *,
        hs256_secret: str | None = None,
        key_resolver: KeyResolver | None = None,
        audience: str = "authenticated",
        issuer: str | None = None,
    ) -> None:
        self._hs256_secret = hs256_secret
        self._key_resolver = key_resolver
        self._audience = audience
        self._issuer = issuer

    @classmethod
    def from_settings(cls, settings: Settings) -> "TokenVerifier":
        secret = settings.supabase_jwt_secret
        return cls(
            hs256_secret=secret.get_secret_value() if secret else None,
            key_resolver=JWKSKeyResolver(settings.supabase_jwks_url)
            if settings.supabase_jwks_url
            else None,
            audience=settings.supabase_jwt_audience,
            issuer=settings.supabase_jwt_issuer,
        )

    @property
    def configured(self) -> bool:
        return self._hs256_secret is not None or self._key_resolver is not None

    def verify(self, token: str) -> Claims:
        """Blocking (the JWKS lookup may do network I/O): call it from a worker thread."""
        try:
            algorithm = jwt.get_unverified_header(token).get("alg")
            key: Any
            if algorithm == "HS256" and self._hs256_secret is not None:
                key, algorithms = self._hs256_secret, ["HS256"]
            elif algorithm in ASYMMETRIC_ALGORITHMS and self._key_resolver is not None:
                key, algorithms = self._key_resolver.resolve(token), [str(algorithm)]
            else:
                # Includes "none" and any algorithm we have no key for.
                raise UnauthorizedError("Invalid or expired token")

            payload = jwt.decode(
                token,
                key,
                algorithms=algorithms,
                audience=self._audience,
                issuer=self._issuer,
                leeway=CLOCK_SKEW_SECONDS,
                options={"require": ["exp", "sub", "aud"]},
            )
            return _claims_from(payload)
        except jwt.PyJWKClientConnectionError as exc:
            # Fail closed, but do not blame the user for our key source being down.
            logger.error("JWKS endpoint unreachable: %s", exc)
            raise AuthUnavailableError("Authentication is temporarily unavailable") from exc
        except jwt.PyJWTError as exc:
            logger.info("Rejected access token: %s", type(exc).__name__)
            raise UnauthorizedError("Invalid or expired token") from exc


def _claims_from(payload: dict[str, Any]) -> Claims:
    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except ValueError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc
    email = payload.get("email")
    metadata = payload.get("user_metadata")
    name = None
    if isinstance(metadata, dict):
        name = metadata.get("full_name") or metadata.get("name")
    return Claims(
        user_id=user_id,
        email=email if isinstance(email, str) and email else None,
        display_name=name if isinstance(name, str) and name.strip() else None,
    )
