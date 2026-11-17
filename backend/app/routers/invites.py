"""Patient invite links: issue, open, accept (US-026).

Issuing needs a clinician or admin session; opening and accepting are
unauthenticated because the token itself is the credential. A consumed,
revoked or expired invite answers 409 with one body, whichever of the three
it is (NFR-009).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.invites import (
    STATUS_ISSUED,
    accept_invite,
    find_invite,
    invite_url,
    is_usable,
    issue_invite,
    link_status,
    record_open,
    send_invite_email,
)
from app.models import Invite, Patient, User
from app.sessions import issue_session, require_staff

router = APIRouter(prefix="/api/invites", tags=["invites"])

Db = Annotated[Session, Depends(get_db)]
Staff = Annotated[User, Depends(require_staff)]


class IssueInviteRequest(BaseModel):
    patient_id: str
    email: str | None = None
    #: An explicit lifetime for this one link; the configured
    #: `INVITE_EXPIRY_HOURS` when it is absent.
    expires_in_hours: float | None = None


class AcceptInviteRequest(BaseModel):
    """The password the patient chooses. `new_password` is accepted as the
    same field, and an account may be created without a usable password."""

    password: str | None = None
    new_password: str | None = None

    def chosen(self) -> str | None:
        return self.password or self.new_password


def _conflict() -> HTTPException:
    """The one answer for consumed, revoked and expired alike."""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail="This link is no longer usable"
    )


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


def _live_invite(db: Session, token: str) -> Invite:
    row = find_invite(db, token)
    if row is None:
        raise _not_found()
    if not is_usable(row):
        raise _conflict()
    return row


@router.post("", status_code=status.HTTP_201_CREATED)
def create_invite(body: IssueInviteRequest, user: Staff, db: Db) -> dict[str, Any]:
    """AC-084: a clinician or admin issues one single-use invite for one patient."""
    patient = db.get(Patient, body.patient_id)
    if patient is None:
        raise _not_found()
    row, token = issue_invite(
        db,
        patient,
        email=body.email,
        created_by=user.id,
        expires_in_hours=body.expires_in_hours,
    )
    # No mail credential is never a blocker: the link is always in the body.
    send_invite_email(row, token)
    return {
        "invite_id": row.id,
        "patient_id": row.patient_id,
        "token": token,
        "invite_url": invite_url(token),
        "status": STATUS_ISSUED,
        "expires_at": row.expires_at.isoformat(),
    }


@router.get("/{token}")
def open_invite(token: str, db: Db) -> dict[str, Any]:
    """Unauthenticated: the token is the credential, and this records the open."""
    row = _live_invite(db, token)
    patient = db.get(Patient, row.patient_id)
    # The status as it was when the link was fetched: the first fetch reports
    # not_yet_opened and is what moves it to opened.
    was = link_status(row)
    record_open(db, row)
    return {
        "patient_display_name": patient.display_name if patient else "",
        "status": was,
        "valid": True,
        "expires_at": row.expires_at.isoformat(),
    }


@router.delete("/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invite(invite_id: str, user: Staff, db: Db) -> Response:
    """NFR-009: a clinician revokes an issued invite; the link stops working."""
    row = db.get(Invite, invite_id)
    if row is None:
        raise _not_found()
    if row.revoked_at is None:
        row.revoked_at = datetime.now(UTC)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{token}/accept")
def accept(token: str, body: AcceptInviteRequest, db: Db) -> dict[str, Any]:
    """Consume the invite and sign the patient in, bound to that one patient."""
    row = _live_invite(db, token)
    user = accept_invite(db, row, body.chosen())
    return {
        "token": issue_session(db, user),
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "patient_id": user.patient_id,
            "must_set_password": False,
        },
    }
