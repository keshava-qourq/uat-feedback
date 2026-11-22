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

from app import jobs
from app.auth import require_admin, require_api_access
from app.config import database_url_configured, llm_configured
from app.database import get_db
from app.dataset import active_dataset_version
from app.dedup_check import run_dedup_check
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
    database = CONNECTED if database_url_configured() and database_reachable() else NOT_CONFIGURED
    # Read through app.config at call time; the value itself never enters the
    # response, a log line or a variable that outlives this check (NFR-011).
    llm = CONNECTED if llm_configured() else NOT_CONFIGURED
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


class StartJobRequest(BaseModel):
    """The job to queue. `kind` is an enumerated set, so anything else is 422."""

    kind: str
    #: Re-running one specific job: given and already finished, that is a conflict.
    job_id: str | None = None


#: kind -> (the function the worker runs, the queue it runs on).
JOB_FUNCTIONS: dict[str, Any] = {"dedup_check": run_dedup_check}

FINISHED_STATUSES = frozenset({"finished", "failed"})


@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED)
def start_job(
    body: StartJobRequest,
    admin: Annotated[User, Depends(require_admin)],
) -> dict[str, Any]:
    """AC-012: queue a background job on the approved Redis queue."""
    if body.kind not in JOB_FUNCTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"'{body.kind}' is not a job kind; expected one of "
                f"{', '.join(sorted(JOB_FUNCTIONS))}"
            ),
        )
    if body.job_id:
        existing = jobs.status(body.job_id)
        if existing["status"] in FINISHED_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"job {body.job_id} has already finished",
            )
    try:
        job_id = jobs.enqueue(JOB_FUNCTIONS[body.kind], meta={"kind": body.kind})
    except jobs.QueueUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"the job queue is unavailable: {exc}",
        ) from exc
    return {"job_id": job_id, "kind": body.kind, "status": "queued"}


@router.get("/jobs/{job_id}")
def get_job(
    job_id: str,
    admin: Annotated[User, Depends(require_admin)],
) -> dict[str, Any]:
    """AC-012: the job's status, progress and -- once finished -- its result."""
    state = jobs.status(job_id)
    if state["status"] in ("unknown", "unavailable"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"no job {job_id}")
    return {
        "job_id": state["job_id"],
        "kind": state.get("kind"),
        "status": state["status"],
        "progress_pct": state.get("progress_pct"),
        "result": state.get("result"),
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
