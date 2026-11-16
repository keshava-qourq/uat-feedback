"""Opaque bearer sessions: issue, verify, refresh and revoke.

Behaviour rules: a login inserts a new `sessions` row and returns an opaque
token in the body (never a cookie); a session lives until its idle timeout
elapses, until logout revokes it, or until the user is deactivated; every
authenticated request pushes the idle expiry forward from now. Only the
token's salted hash is stored, so no endpoint can hand a live token back.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SessionRow, User

IDLE_TIMEOUT = timedelta(minutes=30)


def _hash(token: str) -> str:
    secret = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY") or "dev-only-session-salt"
    return hmac.new(secret.encode(), token.encode(), hashlib.sha256).hexdigest()


def issue_session(db: Session, user: User) -> str:
    """A new session for `user`; returns the plaintext token, stored only hashed."""
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    db.add(
        SessionRow(
            user_id=user.id,
            token_hash=_hash(token),
            created_at=now,
            last_seen_at=now,
            idle_expires_at=now + IDLE_TIMEOUT,
        )
    )
    db.commit()
    return token


def revoke_session(db: Session, token: str) -> None:
    row = (
        db.execute(select(SessionRow).where(SessionRow.token_hash == _hash(token)))
        .scalars()
        .first()
    )
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(UTC)
        db.commit()


def _unauthenticated() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def bearer_token(authorization: str | None = Header(default=None)) -> str:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise _unauthenticated()
    return token.strip()


def current_user(
    token: Annotated[str, Depends(bearer_token)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """The signed-in user, refreshing the session's idle window. 401 otherwise."""
    row = (
        db.execute(select(SessionRow).where(SessionRow.token_hash == _hash(token)))
        .scalars()
        .first()
    )
    now = datetime.now(UTC)
    if row is None or row.revoked_at is not None:
        raise _unauthenticated()
    expires = row.idle_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires <= now:
        raise _unauthenticated()
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise _unauthenticated()
    row.last_seen_at = now
    row.idle_expires_at = now + IDLE_TIMEOUT
    db.commit()
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def require_staff(user: CurrentUser) -> User:
    """A clinician or admin. A patient token here is 403, per the rules."""
    if user.role not in ("clinician", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return user
