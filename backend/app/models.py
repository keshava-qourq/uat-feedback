"""SQLAlchemy models.

`User` is added ahead of any single ticket: the startup seeding in
`app.bootstrap` needs a `users` table to seed the platform's bootstrap admin
and smoke-test accounts into, and every future auth ticket (login, invite
accept, admin deactivate) needs the same table to query. It carries only the
columns that seeding and a future login route need.

The rest of the approved data model -- patients, events, sessions, the
condition pack and everything the scoring engine touches -- is the
development sprint's work (see docs/sdlc/architecture/data-model.md and
docs/sdlc/development/sprint-plan.md, US-001-T1 and after), added with its
own migration as each ticket requires it rather than guessed at here.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = ["Base", "User"]


class User(Base):
    """A clinician, patient or admin account.

    `patient_id` is left a plain nullable string rather than a foreign key:
    the `patients` table is ingest's to add (US-001-T1), and a dangling FK to
    a table that does not exist yet would fail `create_all` before that
    ticket is even started.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String)  # "clinician" | "patient" | "admin"
    patient_id: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_set_password: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
