"""First-sign-in password-set tokens: issue, resolve, consume (AC-104).

An account created by an administrator or by accepting an invite has no
usable password (`password_hash` null, `must_set_password` true) and cannot
log in at all. It is given one opaque token, mailed as a link; only the
token's salted hash is stored, it expires, and it works exactly once.

The mail goes through `app.email`, which sends nothing and raises nothing
when SendGrid is not configured -- a run with no mail credential still
creates the account and still has the token the caller just issued.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from jinja2 import Template
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import email as email_module
from app.models import PasswordSetToken, User
from app.security import hash_password
from app.sessions import hash_token

#: How long a first-sign-in link stays usable.
TOKEN_LIFETIME = timedelta(days=7)

_EMAIL_HTML = Template(
    "<p>Hello {{ email }},</p>"
    "<p>Set the password for your account to sign in:</p>"
    '<p><a href="{{ link }}">{{ link }}</a></p>'
    "<p>This link expires on {{ expires_at }} and can be used once.</p>"
)


class TokenState:
    """Why a presented token cannot be used."""

    UNKNOWN = "unknown"
    SPENT = "spent"


def issue_password_set_token(db: Session, user: User) -> str:
    """A new single-use token for `user`; returns the plaintext, stores the hash."""
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    db.add(
        PasswordSetToken(
            user_id=user.id,
            token_hash=hash_token(token),
            created_at=now,
            expires_at=now + TOKEN_LIFETIME,
        )
    )
    db.commit()
    return token


def send_password_set_email(user: User, token: str, link_base: str) -> bool:
    """Mail the set-password link. False (and nothing sent) with no credential."""
    link = f"{link_base.rstrip('/')}?token={token}"
    expires_at = (datetime.now(UTC) + TOKEN_LIFETIME).isoformat()
    html = _EMAIL_HTML.render(email=user.email, link=link, expires_at=expires_at)
    return bool(
        email_module.send(
            to=user.email,
            subject="Set your password",
            html=html,
            text=f"Set your password: {link}",
        )
    )


def _usable(row: PasswordSetToken, now: datetime) -> bool:
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    return row.consumed_at is None and row.revoked_at is None and expires > now


def consume_password_set_token(db: Session, token: str, new_password: str) -> str:
    """Set the account's password from this token, once.

    Returns "ok", `TokenState.UNKNOWN` (404) or `TokenState.SPENT` (409 --
    consumed, revoked or expired; the three are indistinguishable).
    """
    row = (
        db.execute(select(PasswordSetToken).where(PasswordSetToken.token_hash == hash_token(token)))
        .scalars()
        .first()
    )
    if row is None:
        return TokenState.UNKNOWN
    now = datetime.now(UTC)
    if not _usable(row, now):
        return TokenState.SPENT
    user = db.get(User, row.user_id)
    if user is None:
        return TokenState.UNKNOWN
    user.password_hash = hash_password(new_password)
    user.must_set_password = False
    row.consumed_at = now
    db.commit()
    return "ok"
