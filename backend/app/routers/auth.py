"""Sign-in, sign-out and first-sign-in password setting.

POST /api/auth/login takes an email (compared case-insensitively) and a
password and answers with an opaque bearer token in the body -- never a
cookie. A wrong password, an account with no usable password and a
deactivated account are all the identical 401 {"detail":"Invalid
credentials"}, so none can be told from the others. Logout revokes only the
token presented. POST /api/auth/set-password consumes a single-use,
hashed-at-rest token and is the only way an invited or admin-created account
gets a password.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import AliasChoices, BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.passwords import TokenState, consume_password_set_token
from app.security import verify_password
from app.sessions import CurrentUser, bearer_token, issue_session, revoke_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class SetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(
        min_length=8,
        validation_alias=AliasChoices("new_password", "password"),
    )


def _user_payload(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "must_set_password": bool(user.must_set_password),
    }


@router.post("/login")
def login(body: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    user = (
        db.execute(select(User).where(func.lower(User.email) == body.email.lower()))
        .scalars()
        .first()
    )
    invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user is None or not user.is_active or not user.password_hash:
        raise invalid
    if not verify_password(body.password, user.password_hash):
        raise invalid
    return {"token": issue_session(db, user), "user": _user_payload(user)}


@router.post("/logout")
def logout(
    user: CurrentUser,
    token: Annotated[str, Depends(bearer_token)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    revoke_session(db, token)
    return {"detail": "signed out"}


@router.get("/me")
def me(user: CurrentUser) -> dict[str, object]:
    return _user_payload(user)


@router.post("/set-password")
def set_password(
    body: SetPasswordRequest, db: Annotated[Session, Depends(get_db)]
) -> dict[str, str]:
    """Unauthenticated: the token itself is the credential (AC-104)."""
    outcome = consume_password_set_token(db, body.token, body.new_password)
    if outcome == TokenState.UNKNOWN:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if outcome == TokenState.SPENT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This link is no longer usable",
        )
    return {"detail": "password set"}
