"""The shared bearer check every admin route depends on.

Until a real identity provider exists, the platform's `SECRET_KEY` is the
shared bearer: the SPA's api client already sends it as
`Authorization: Bearer <SECRET_KEY>`. The check fails closed -- a missing
header, a malformed one, a wrong value, or no `SECRET_KEY` configured at all
all return 401 with the project's one error shape.
"""

from __future__ import annotations

import hmac
import os
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db


def shared_secret() -> str:
    """The configured shared bearer: `API_SECRET_KEY`, or the platform's `SECRET_KEY`."""
    return os.getenv("API_SECRET_KEY") or os.getenv("SECRET_KEY") or ""


def _is_shared_bearer(authorization: str | None) -> bool:
    """Whether this header carries the configured shared bearer, exactly."""
    expected = shared_secret()
    scheme, _, token = (authorization or "").partition(" ")
    return bool(
        expected
        and scheme.lower() == "bearer"
        and token.strip()
        and hmac.compare_digest(token.strip(), expected)
    )


def require_bearer(authorization: str | None = Header(default=None)) -> None:
    """401 unless the request carries the configured shared bearer token."""
    if not _is_shared_bearer(authorization):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def require_api_access(
    authorization: str | None = Header(default=None),
    db: Annotated[Session, Depends(get_db)] = None,  # type: ignore[assignment]
) -> None:
    """401 unless the request carries the shared bearer *or* a live staff session.

    The shared `API_SECRET_KEY` is the interim machine credential (AC-146); an
    administrator signed in through `POST /api/auth/login` presents a session
    token instead, and that is accepted here too -- never anything weaker.
    """
    if _is_shared_bearer(authorization):
        return
    from app.sessions import bearer_token, current_user, require_staff

    require_staff(current_user(bearer_token(authorization), db))


#: Paths reachable with no credentials at all: liveness, the OpenAPI document
#: the SPA's tooling reads, and the sign-in route that issues a token.
OPEN_PATHS = frozenset(
    {
        "/health",
        "/openapi.json",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/api/auth/login",
    }
)


def is_authenticated_request(path: str, authorization: str | None) -> bool:
    """Whether a request may proceed past the gate (AC-146).

    Open paths always may. Everything else needs a bearer header: the shared
    `API_SECRET_KEY` passes outright, and any other bearer is left to the
    route's own session check, which 401s when it is not a live session.
    """
    if path in OPEN_PATHS:
        return True
    scheme, _, token = (authorization or "").partition(" ")
    return scheme.lower() == "bearer" and bool(token.strip())
