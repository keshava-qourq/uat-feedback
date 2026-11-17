"""Admin configuration routes.

`GET /api/admin/settings` reports whether the two pieces of deployment
configuration this service needs are in place -- the database connection
(`DATABASE_URL`) and the hosted language-model credential
(`ANTHROPIC_API_KEY`) -- as a status string and nothing else. No credential
value is ever read into the response, logged, or written anywhere (NFR-011);
both are read from the environment only.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import require_admin, require_api_access
from app.database import get_db
from app.dataset import active_dataset_version
from app.models import User
from app.passwords import issue_password_set_token, send_password_set_email
from app.services import configured_services, database_reachable
from app.sessions import revoke_all_sessions

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_api_access)],
)

CONNECTED = "connected"
NOT_CONFIGURED = "not-configured"
#: What a credential's value is shown as: never the value itself (NFR-011).
MASKED = "not-shown"


@router.get("/settings")
def settings(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    """Masked configuration status: never a credential value, only a status."""
    database = CONNECTED if os.getenv("DATABASE_URL") and database_reachable() else NOT_CONFIGURED
    llm_configured = any(
        (os.getenv(name) or "").strip() for name in ("ANTHROPIC_API_KEY", "LLM_API_KEY")
    )
    llm = CONNECTED if llm_configured else NOT_CONFIGURED
    return {
        "database": {"status": database},
        "llm": {"status": llm},
        "dataset_version": active_dataset_version(db),
        "health": {"status": "ok", "services": configured_services()},
        "credentials": [
            {"name": "database", "status": database, "value": MASKED},
            {"name": "llm", "status": llm, "value": MASKED},
        ],
    }


class CreateUserRequest(BaseModel):
    email: str = Field(min_length=3)
    role: str = Field(pattern="^(clinician|patient|admin)$")


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    body: CreateUserRequest,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """AC-104: an admin-created account has no usable password, only a one-time link."""
    existing = (
        db.execute(select(User).where(func.lower(User.email) == body.email.lower()))
        .scalars()
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
    user = User(
        email=body.email,
        password_hash=None,
        role=body.role,
        is_active=True,
        must_set_password=True,
    )
    db.add(user)
    db.commit()
    token = issue_password_set_token(db, user)
    link_base = (os.getenv("FRONTEND_BASE_URL") or "").strip() or "http://localhost:5173"
    send_password_set_email(user, token, f"{link_base.rstrip('/')}/set-password")
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "must_set_password": True,
        "set_password_token": token,
    }


@router.post("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: str,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """AC-103: the account goes inactive and every one of its sessions dies now."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if user.is_active:
        user.is_active = False
        user.deactivated_at = datetime.now(UTC)
        db.commit()
    revoked = revoke_all_sessions(db, user.id)
    return {"id": user.id, "is_active": False, "sessions_revoked": revoked}
