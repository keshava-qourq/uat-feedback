"""Single-use patient invite links: issue, open, accept (US-026, NFR-009).

The token is an opaque random string (32 bytes of entropy, deliberately not a
UUID), returned once in the issuing response and stored only as the salted
hash `app.sessions.hash_token` produces. It is scoped to exactly one patient
and grants only the patient role, carries a configured expiry
(`INVITE_EXPIRY_HOURS`), and is refused with one indistinguishable answer once
it is consumed, revoked or expired.
"""

from __future__ import annotations

import os
import secrets
from datetime import UTC, datetime, timedelta

from jinja2 import Template
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import email as email_module
from app.models import IntakeAnswer, Invite, Patient, User
from app.security import hash_password
from app.sessions import hash_token

#: Used when `INVITE_EXPIRY_HOURS` is unset or unreadable.
DEFAULT_EXPIRY_HOURS = 72

#: The one role an invite may grant.
GRANTED_ROLE = "patient"

STATUS_NONE = "none"
STATUS_NOT_YET_OPENED = "not_yet_opened"
STATUS_OPENED = "opened"
STATUS_INTAKE_COMPLETED = "intake_completed"
STATUS_ISSUED = "issued"

_EMAIL_HTML = Template(
    "<p>Hello,</p>"
    "<p>Your clinician has invited you to share your history:</p>"
    '<p><a href="{{ link }}">{{ link }}</a></p>'
    "<p>This link expires on {{ expires_at }} and can be used once.</p>"
)


def expiry() -> timedelta:
    """The configured invite lifetime (`INVITE_EXPIRY_HOURS`), read at call time."""
    raw = (os.getenv("INVITE_EXPIRY_HOURS") or "").strip()
    try:
        hours = float(raw)
    except ValueError:
        hours = DEFAULT_EXPIRY_HOURS
    if hours <= 0:
        hours = DEFAULT_EXPIRY_HOURS
    return timedelta(hours=hours)


def invite_url(token: str) -> str:
    """The full link the clinician sends, shown exactly once."""
    base = (os.getenv("FRONTEND_BASE_URL") or "").strip() or "http://localhost:5173"
    return f"{base.rstrip('/')}/invite/{token}"


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def is_usable(row: Invite, now: datetime | None = None) -> bool:
    now = now or datetime.now(UTC)
    return row.consumed_at is None and row.revoked_at is None and _aware(row.expires_at) > now


def issue_invite(
    db: Session,
    patient: Patient,
    *,
    email: str | None,
    created_by: str | None,
    expires_in_hours: float | None = None,
) -> tuple[Invite, str]:
    """A new single-use invite for `patient`; returns the row and the plaintext token."""
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    lifetime = expiry() if expires_in_hours is None else timedelta(hours=expires_in_hours)
    row = Invite(
        patient_id=patient.id,
        email=email,
        token_hash=hash_token(token),
        granted_role=GRANTED_ROLE,
        created_by=created_by,
        created_at=now,
        expires_at=now + lifetime,
    )
    db.add(row)
    db.commit()
    return row, token


def send_invite_email(row: Invite, token: str) -> bool:
    """Mail the link. Sends nothing and raises nothing with no credential."""
    if not row.email:
        return False
    link = invite_url(token)
    html = _EMAIL_HTML.render(link=link, expires_at=_aware(row.expires_at).isoformat())
    return bool(
        email_module.send(
            to=row.email,
            subject="Your invite link",
            html=html,
            text=f"Your invite link: {link}",
        )
    )


def find_invite(db: Session, token: str) -> Invite | None:
    """The invite behind this plaintext token, by its hash only."""
    return (
        db.execute(select(Invite).where(Invite.token_hash == hash_token(token))).scalars().first()
    )


def record_open(db: Session, row: Invite) -> Invite:
    """Mark the first fetch of the link; later fetches leave the time alone."""
    if row.opened_at is None:
        row.opened_at = datetime.now(UTC)
        db.commit()
    return row


def intake_complete(db: Session, patient_id: str, since: datetime | None = None) -> bool:
    """Whether this patient's intake is complete.

    `since` scopes the answer to one invite's lifecycle: intake the cohort was
    ingested with predates the invite and does not make a freshly issued link
    read `intake_completed` (AC-085).
    """
    query = select(IntakeAnswer.id).where(
        IntakeAnswer.patient_id == patient_id,
        IntakeAnswer.is_complete.is_(True),
    )
    if since is not None:
        query = query.where(IntakeAnswer.answered_at >= since)
    return db.execute(query).scalars().first() is not None


def _latest_invite(db: Session, patient_id: str) -> Invite | None:
    """The newest invite for this patient: invite listings are newest-first."""
    return (
        db.execute(
            select(Invite)
            .where(Invite.patient_id == patient_id)
            .order_by(Invite.created_at.desc(), Invite.id.desc())
        )
        .scalars()
        .first()
    )


def worklist_invite_status(db: Session, patient_id: str) -> str:
    """AC-085: none | not_yet_opened | opened | intake_completed."""
    row = _latest_invite(db, patient_id)
    if row is None:
        return STATUS_NONE
    if intake_complete(db, patient_id, since=_aware(row.created_at)):
        return STATUS_INTAKE_COMPLETED
    return STATUS_OPENED if row.opened_at is not None else STATUS_NOT_YET_OPENED


def link_status(row: Invite) -> str:
    """The status `GET /api/invites/{token}` reports for a usable invite."""
    return STATUS_OPENED if row.opened_at is not None else STATUS_NOT_YET_OPENED


def _invite_email(row: Invite, patient: Patient) -> str:
    """The account's email: the one the clinician gave, else one derived per patient."""
    return row.email or f"patient-{patient.id}@invite.invalid"


def accept_invite(db: Session, row: Invite, password: str | None) -> User:
    """Create or activate the patient-role account bound to this one patient."""
    patient = db.get(Patient, row.patient_id)
    email = _invite_email(row, patient) if patient is not None else (row.email or row.id)
    user = db.execute(select(User).where(User.email == email)).scalars().first()
    if user is None:
        user = User(email=email, role=GRANTED_ROLE)
        db.add(user)
    user.role = GRANTED_ROLE
    user.patient_id = row.patient_id
    # An invite may be accepted without choosing a password: the account then
    # has no usable password until one is set (AC-104).
    user.password_hash = hash_password(password) if password else None
    user.must_set_password = False
    user.is_active = True
    user.deactivated_at = None
    row.consumed_at = datetime.now(UTC)
    db.commit()
    return user
