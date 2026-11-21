"""Re-running an ingest replaces the prior load even once a patient has an
invite or a recorded decision (AC-004/NFR-021).

Both tables carry a foreign key to `patients`, so a purge that forgets them
raises a foreign-key violation, the whole job dies and its run row is left in
`running` -- which then refuses every later start with 409. A real PostgreSQL
is needed: SQLite does not enforce those keys by default.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.ingest import job as ingest_job
from app.models import Decision, IngestRun, Invite, Patient


@pytest.fixture
def sessions(monkeypatch):
    base_url = os.environ.get("DATABASE_URL", "")
    if not base_url or base_url.startswith("sqlite"):
        pytest.skip("needs the sandbox PostgreSQL in DATABASE_URL")

    url = make_url(base_url)
    db_name = f"purge_test_{uuid.uuid4().hex[:12]}"
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin.dispose()

    engine = create_engine(url.set(database=db_name), future=True)
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(ingest_job, "SessionLocal", factory)
    try:
        yield factory
    finally:
        engine.dispose()
        admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
        admin.dispose()


def _patient_with_invite_and_decision(factory, version: str) -> None:
    session = factory()
    try:
        patient = Patient(
            dataset_patient_id="P1", dataset_version=version, display_name="Ada Lovelace"
        )
        session.add(patient)
        session.commit()
        session.add(
            Invite(
                patient_id=patient.id,
                token_hash=uuid.uuid4().hex,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        session.add(
            Decision(
                patient_id=patient.id,
                clinician_id=str(uuid.uuid4()),
                decision="accept",
            )
        )
        session.commit()
    finally:
        session.close()


def test_ac004_a_rerun_purges_a_patient_that_already_has_an_invite_and_a_decision(sessions):
    version = "v-purge"
    _patient_with_invite_and_decision(sessions, version)

    db = sessions()
    try:
        ingest_job._purge(db, version)
        db.commit()
    finally:
        db.close()

    check = sessions()
    try:
        assert check.execute(select(Patient.id)).scalars().all() == []
        assert check.execute(select(Invite.id)).scalars().all() == []
        assert check.execute(select(Decision.id)).scalars().all() == []
    finally:
        check.close()


def test_ac004_a_run_that_cannot_purge_is_reported_failed_not_left_running(sessions, monkeypatch):
    """A failure before the first file still closes the run off (NFR-021).

    A run stuck in `running` locks ingest out: every later start answers 409.
    """
    session = sessions()
    try:
        run = IngestRun(dataset_version="v-broken", status="running", started_at=datetime.now(UTC))
        session.add(run)
        session.commit()
        run_id = run.id
    finally:
        session.close()

    def boom(_db, _version):
        raise RuntimeError("purge exploded")

    monkeypatch.setattr(ingest_job, "_purge", boom)
    result = ingest_job.run_ingest(run_id, "v-broken", "/nowhere")

    assert result["status"] == "failed"
    check = sessions()
    try:
        row = check.get(IngestRun, run_id)
        assert row.status == "failed"
        assert row.finished_at is not None
    finally:
        check.close()
