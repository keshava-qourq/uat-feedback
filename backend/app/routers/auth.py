"""Sign-in and sign-out: the only way an account gets a session.

POST /api/auth/login takes an email (compared case-insensitively) and a
password and answers with an opaque bearer token in the body. A wrong password
and a deactivated account are both 401 with the same detail, so neither can be
told from the other. Logout revokes only the token presented.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import verify_password
from app.sessions import CurrentUser, bearer_token, issue_session, revoke_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(body: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    user = (
        db.execute(select(User).where(func.lower(User.email) == body.email.lower()))
        .scalars()
        .first()
    )
    if user is None or not user.is_active or not user.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = issue_session(db, user)
    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "role": user.role},
    }


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
    return {"id": user.id, "email": user.email, "role": user.role}
