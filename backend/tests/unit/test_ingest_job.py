"""US-001-2: the dataset ingest job, run for real against a throwaway database.

The job is called directly (not through RQ) so the acceptance criteria are
proved without a worker: RQ only decides *where* `run_ingest` runs, not what
it does. The files are written to a temporary directory and read through the
same storage path a disk drop uses.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.ingest import job as ingest_job
from app.models import (
    CoveragePeriod,
    EncounterTruth,
    Event,
    IngestFileResult,
    IngestRun,
    IntakeAnswer,
    Note,
    Patient,
    Persona,
)

PATIENTS_CSV = (
    "patient_id,display_name,birth_year,sex,reachable_history_start\n"
    "P1,Ada,1981,F,2016-01-01\n"
    "P2,Grace,1975,F,2015-06-01\n"
)
LABELS_CSV = "patient_id,split,archetype\nP1,train,classic\nP2,val,lookalike\n"
EVENTS_CSV = (
    "patient_id,event_id,event_time,event_type,code_system,code,display,value,unit,"
    "provider_org,provider_specialty,source_type,source_ref,encounter_ref,confidence\n"
    "P1,E1,2018-04-02T09:00:00Z,encounter,SNOMED,1,Visit,,,Clinic,primary_care,ehr,"
    "ehr:enc:1,ENC1,0.9\n"
    "P2,E2,2019-07-11T14:30:00Z,lab,LOINC,1988-5,CRP,12,mg/L,Clinic,rheum,ehr,"
    "ehr:obs:2,ENC2,0.95\n"
)
NOTES_CSV = (
    "patient_id,source_ref,note_time,note_type,text\n"
    "P1,ehr:note:1,2018-04-02T09:30:00Z,clinic_note,Morning stiffness.\n"
)
INTAKE_CSV = (
    "patient_id,question_key,answer_value,answered_at,is_complete\n"
    "P1,stiffness_minutes,75,2021-01-02T10:00:00Z,true\n"
)
COVERAGE_CSV = (
    "patient_id,payer,start_date,end_date,gap_reason\nP1,Payer One,2016-01-01,2018-12-31,\n"
)
ENCOUNTER_TRUTH_CSV = (
    "patient_id,true_encounter_id,encounter_time,visible_in_sources\n"
    "P1,T1,2018-04-02T09:00:00Z,true\n"
    "P2,T2,2019-07-11T14:30:00Z,false\n"
)
HEROES_JSON = json.dumps(
    [
        {
            "persona_key": "ada",
            "name": "Ada",
            "one_line_description": "Classic case.",
            "patient_id": "P1",
        }
    ]
)

FILES = {
    "patients.csv": PATIENTS_CSV,
    "labels.csv": LABELS_CSV,
    "events.csv": EVENTS_CSV,
    "notes.csv": NOTES_CSV,
    "intake.csv": INTAKE_CSV,
    "coverage.csv": COVERAGE_CSV,
    "encounter_truth.csv": ENCOUNTER_TRUTH_CSV,
    "heroes.json": HEROES_JSON,
}


@pytest.fixture
def sessions(monkeypatch):
    """A throwaway PostgreSQL database the job's own sessions share.

    Not SQLite: the job writes its progress from a second connection while the
    file's own transaction is still open, which is exactly what SQLite's
    single-writer lock forbids and what the real database does every day.
    """
    base_url = os.environ.get("DATABASE_URL", "")
    if not base_url or base_url.startswith("sqlite"):
        pytest.skip("needs the sandbox PostgreSQL in DATABASE_URL")

    url = make_url(base_url)
    db_name = f"ingest_test_{uuid.uuid4().hex[:12]}"
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


def _drop(tmp_path: Path, **overrides: str) -> str:
    directory = tmp_path / "drop"
    directory.mkdir(exist_ok=True)
    for name, body in {**FILES, **overrides}.items():
        (directory / name).write_text(body)
    return str(directory)


def _new_run(factory, version: str = "v-test") -> str:
    session = factory()
    try:
        run = IngestRun(dataset_version=version, status="queued")
        session.add(run)
        session.commit()
        return run.id
    finally:
        session.close()


def test_ac001_every_file_streams_from_the_configured_location(sessions, tmp_path):
    """AC-001: all eight files are read from the drop and land in the schema."""
    run_id = _new_run(sessions)
    ingest_job.run_ingest(run_id, "v-test", _drop(tmp_path), seed=7)

    db = sessions()
    try:
        assert db.query(Patient).count() == 2
        assert db.query(Event).count() == 2
        assert db.query(Note).count() == 1
        assert db.query(IntakeAnswer).count() == 1
        assert db.query(CoveragePeriod).count() == 1
        assert db.query(EncounterTruth).count() == 2
        assert db.query(Persona).count() == 1
        names = {r.file_name for r in db.query(IngestFileResult).all()}
        assert names == set(ingest_job.DATASET_FILES)
        assert db.get(IngestRun, run_id).status == "succeeded"
    finally:
        db.close()


def test_ac002_a_malformed_row_is_rejected_and_counted_not_inserted(sessions, tmp_path):
    """AC-002: a row whose patient is unknown is counted as rejected, not loaded."""
    bad_events = EVENTS_CSV + (
        "P404,E3,2019-01-01T00:00:00Z,lab,LOINC,x,CRP,1,mg/L,Clinic,rheum,ehr,ehr:obs:3,ENC3,0.5\n"
    )
    run_id = _new_run(sessions)
    ingest_job.run_ingest(run_id, "v-test", _drop(tmp_path, **{"events.csv": bad_events}))

    db = sessions()
    try:
        row = db.query(IngestFileResult).filter(IngestFileResult.file_name == "events.csv").one()
        assert row.status == "pass"
        assert row.rows_loaded == 2
        assert row.rows_rejected == 1
        assert db.query(Event).count() == 2
    finally:
        db.close()


def test_ac002_a_missing_required_column_names_the_file_and_column_and_loads_nothing(
    sessions, tmp_path
):
    """AC-002: events.csv without source_ref fails, naming both, with no partial rows."""
    header, *rows = EVENTS_CSV.strip().split("\n")
    drop_at = header.split(",").index("source_ref")
    stripped = "\n".join(
        ",".join(c for i, c in enumerate(line.split(",")) if i != drop_at)
        for line in [header, *rows]
    )
    run_id = _new_run(sessions)
    ingest_job.run_ingest(run_id, "v-test", _drop(tmp_path, **{"events.csv": stripped + "\n"}))

    db = sessions()
    try:
        row = db.query(IngestFileResult).filter(IngestFileResult.file_name == "events.csv").one()
        assert row.status == "fail"
        assert "events.csv" in row.error_detail
        assert "source_ref" in row.error_detail
        assert row.rows_loaded == 0
        assert db.query(Event).count() == 0
        assert db.get(IngestRun, run_id).status == "failed"
    finally:
        db.close()


def test_ac003_a_second_run_replaces_the_prior_load_rather_than_duplicating(sessions, tmp_path):
    """AC-003: re-running leaves the same counts and patient_count matches patients.csv."""
    source = _drop(tmp_path)
    first = _new_run(sessions)
    ingest_job.run_ingest(first, "v-test", source)
    second = _new_run(sessions)
    ingest_job.run_ingest(second, "v-test", source)

    db = sessions()
    try:
        assert db.query(Patient).count() == 2
        assert db.query(Event).count() == 2
        assert db.query(Persona).count() == 1
        assert db.get(IngestRun, second).patient_count == 2
    finally:
        db.close()


def test_ac004_progress_is_written_as_the_job_proceeds(sessions, tmp_path, monkeypatch):
    """AC-004: the current file and its row counts are visible before the run ends."""
    seen: list[tuple[str, int]] = []
    original = ingest_job._progress

    def spy(run_id, file_name, **values):
        original(run_id, file_name, **values)
        if "rows_loaded" in values:
            seen.append((file_name, values["rows_loaded"]))

    monkeypatch.setattr(ingest_job, "_progress", spy)
    run_id = _new_run(sessions)
    ingest_job.run_ingest(run_id, "v-test", _drop(tmp_path))

    assert ("patients.csv", 0) in seen  # written before the file's rows are committed
    assert ("events.csv", 2) in seen
