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

from fastapi import Header, HTTPException, status


def require_bearer(authorization: str | None = Header(default=None)) -> None:
    """401 unless the request carries the configured shared bearer token."""
    expected = os.getenv("SECRET_KEY") or ""
    scheme, _, token = (authorization or "").partition(" ")
    if (
        not expected
        or scheme.lower() != "bearer"
        or not token
        or not hmac.compare_digest(token.strip(), expected)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
