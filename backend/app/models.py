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
from datetime import UTC, date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = [
    "Base",
    "User",
    "SessionRow",
    "Patient",
    "Event",
    "Note",
    "IntakeAnswer",
    "CoveragePeriod",
    "EncounterTruth",
    "Persona",
    "IngestRun",
    "IngestFileResult",
]


def _uuid() -> str:
    return str(uuid.uuid4())


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


class SessionRow(Base):
    """One signed-in session: the bearer token's hash and its idle expiry.

    Like `users`, this table is created by `Base.metadata.create_all` at
    startup rather than by a migration, so sign-in works on a fresh database
    without a schema change of its own.
    """

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    idle_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Patient(Base):
    """One patient in the loaded dataset.

    `dataset_patient_id` is the source file's id (compared case-sensitively,
    per the constraint) and is kept distinct from `id`, the internal
    server-generated UUID every other table's `patient_id` FK points at.
    """

    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    dataset_patient_id: Mapped[str] = mapped_column(String, index=True)
    dataset_version: Mapped[str] = mapped_column(String)
    display_name: Mapped[str] = mapped_column(String)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[str | None] = mapped_column(String, nullable=True)
    reachable_history_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Left a plain string rather than an FK to `users.id`: `users` is created by
    # `Base.metadata.create_all` (see app.models' own docstring), not by a
    # migration, so a migration-time FK to it would fail against a fresh
    # database that has not started the app yet. Same pattern as
    # `User.patient_id`.
    assigned_clinician_id: Mapped[str | None] = mapped_column(String, nullable=True)


class Event(Base):
    """One clinical/claims/patient-reported event, the unified event store's core row."""

    __tablename__ = "events"
    __table_args__ = (Index("ix_events_patient_id_event_time", "patient_id", "event_time"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"), nullable=False)
    source_event_id: Mapped[str] = mapped_column(String)
    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String)
    code_system: Mapped[str | None] = mapped_column(String, nullable=True)
    code: Mapped[str | None] = mapped_column(String, nullable=True)
    display: Mapped[str | None] = mapped_column(String, nullable=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_org: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_specialty: Mapped[str | None] = mapped_column(String, nullable=True)
    source_type: Mapped[str] = mapped_column(String)  # "ehr" | "claim" | "patient"
    source_ref: Mapped[str] = mapped_column(String)
    encounter_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    dataset_version: Mapped[str] = mapped_column(String)


class Note(Base):
    """A clinic note or imaging report, before and after clue extraction."""

    __tablename__ = "notes"
    __table_args__ = (Index("ix_notes_patient_id_note_time", "patient_id", "note_time"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"), nullable=False)
    source_ref: Mapped[str] = mapped_column(String)
    note_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note_type: Mapped[str] = mapped_column(String)  # "clinic_note" | "imaging_report"
    text: Mapped[str] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IntakeAnswer(Base):
    """One patient-reported intake answer."""

    __tablename__ = "intake_answers"
    __table_args__ = (
        Index("ix_intake_answers_patient_id_answered_at", "patient_id", "answered_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"), nullable=False)
    question_key: Mapped[str] = mapped_column(String)
    answer_value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSON)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_id: Mapped[str | None] = mapped_column(String, ForeignKey("events.id"), nullable=True)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)


class CoveragePeriod(Base):
    """One insurance-coverage period, used to explain gaps in visible history."""

    __tablename__ = "coverage_periods"
    __table_args__ = (
        Index("ix_coverage_periods_patient_id_start_date", "patient_id", "start_date"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"), nullable=False)
    payer: Mapped[str | None] = mapped_column(String, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gap_reason: Mapped[str | None] = mapped_column(String, nullable=True)


class EncounterTruth(Base):
    """Ground-truth encounter rows used by the de-duplication check."""

    __tablename__ = "encounter_truth"
    __table_args__ = (
        Index("ix_encounter_truth_patient_id_encounter_time", "patient_id", "encounter_time"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"), nullable=False)
    true_encounter_id: Mapped[str] = mapped_column(String)
    encounter_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    visible_in_sources: Mapped[bool] = mapped_column(Boolean, default=False)
    matched_encounter_id: Mapped[str | None] = mapped_column(String, nullable=True)


class Persona(Base):
    """One demo persona, pointing at a patient the demo mode opens directly."""

    __tablename__ = "personas"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    persona_key: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    one_line_description: Mapped[str] = mapped_column(Text)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"), nullable=False)
    expected_outcome: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSON)


class IngestRun(Base):
    """One run of the dataset ingest background job."""

    __tablename__ = "ingest_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    dataset_version: Mapped[str] = mapped_column(String)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String)  # "queued"|"running"|"succeeded"|"failed"
    patient_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IngestFileResult(Base):
    """Per-file outcome of one ingest run: what loaded, what was rejected, and why."""

    __tablename__ = "ingest_file_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    ingest_run_id: Mapped[str] = mapped_column(String, ForeignKey("ingest_runs.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)  # "pass" | "fail"
    rows_loaded: Mapped[int] = mapped_column(Integer, default=0)
    rows_rejected: Mapped[int] = mapped_column(Integer, default=0)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
