"""US-001-3: the bulk FHIR part of the dataset ingest, run for real.

The job is called directly against a throwaway PostgreSQL database, with the
drop written to a temporary directory exactly as it ships: `fhir/*.ndjson.gz`,
gzipped, never converted by hand first (NFR-023).
"""

from __future__ import annotations

import gzip
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
from app.models import Event, IngestFileResult, IngestRun, Patient

PATIENTS_CSV = (
    "patient_id,display_name,birth_year,sex,reachable_history_start\n"
    "P1,Ada,1981,F,2016-01-01\n"
    "P2,Grace,1975,F,2015-06-01\n"
)
LABELS_CSV = "patient_id,split\nP1,train\nP2,val\n"
EVENTS_CSV = (
    "patient_id,event_id,event_time,event_type,source_type,source_ref\n"
    "P1,E1,2018-04-02T09:00:00Z,encounter,ehr,ehr:enc:1\n"
)
NOTES_CSV = "patient_id,source_ref,note_time,note_type,text\n"
INTAKE_CSV = "patient_id,question_key,answer_value,answered_at,is_complete\n"
COVERAGE_CSV = "patient_id,payer,start_date,end_date,gap_reason\n"
ENCOUNTER_TRUTH_CSV = "patient_id,true_encounter_id,encounter_time,visible_in_sources\n"
HEROES_JSON = json.dumps([])

CSV_FILES = {
    "patients.csv": PATIENTS_CSV,
    "labels.csv": LABELS_CSV,
    "events.csv": EVENTS_CSV,
    "notes.csv": NOTES_CSV,
    "intake.csv": INTAKE_CSV,
    "coverage.csv": COVERAGE_CSV,
    "encounter_truth.csv": ENCOUNTER_TRUTH_CSV,
    "heroes.json": HEROES_JSON,
}


def _gz(records: list[dict]) -> bytes:
    return gzip.compress(("\n".join(json.dumps(r) for r in records) + "\n").encode())


CONDITIONS = [
    {
        "resourceType": "Condition",
        "id": "C1",
        "subject": {"reference": "Patient/P1"},
        "code": {"coding": [{"system": "icd-10", "code": "M54.5", "display": "Low back pain"}]},
        "recordedDate": "2018-04-02",
    },
    {
        "resourceType": "Condition",
        "id": "C2",
        "subject": {"reference": "Patient/P2"},
        "code": {"coding": [{"system": "icd-10", "code": "M25.5"}]},
        "recordedDate": "2019-01-05",
    },
]
OBSERVATIONS = [
    {
        "resourceType": "Observation",
        "id": "O1",
        "subject": {"reference": "Patient/P2"},
        "code": {"coding": [{"system": "http://loinc.org", "code": "1988-5"}]},
        "effectiveDateTime": "2019-07-11T14:30:00Z",
        "valueQuantity": {"value": 12, "unit": "mg/L"},
    }
]
FHIR_FILES = {
    "fhir/Patient.ndjson.gz": _gz(
        [
            {"resourceType": "Patient", "id": "P1", "gender": "female"},
            {"resourceType": "Patient", "id": "P2", "gender": "female"},
        ]
    ),
    "fhir/Condition.ndjson.gz": _gz(CONDITIONS),
    "fhir/Observation.ndjson.gz": _gz(OBSERVATIONS),
}


@pytest.fixture
def sessions(monkeypatch):
    """A throwaway PostgreSQL database the job's own sessions share."""
    base_url = os.environ.get("DATABASE_URL", "")
    if not base_url or base_url.startswith("sqlite"):
        pytest.skip("needs the sandbox PostgreSQL in DATABASE_URL")

    url = make_url(base_url)
    db_name = f"fhir_test_{uuid.uuid4().hex[:12]}"
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


def _drop(tmp_path: Path, **fhir_overrides: bytes) -> str:
    directory = tmp_path / "drop"
    (directory / "fhir").mkdir(parents=True, exist_ok=True)
    for name, body in CSV_FILES.items():
        (directory / name).write_text(body)
    for name, data in {**FHIR_FILES, **fhir_overrides}.items():
        (directory / name).write_bytes(data)
    return str(directory)


def _new_run(factory, version: str = "v-fhir") -> str:
    session = factory()
    try:
        run = IngestRun(dataset_version=version, status="queued")
        session.add(run)
        session.commit()
        return run.id
    finally:
        session.close()


def _file_rows(db, run_id: str) -> dict[str, IngestFileResult]:
    return {
        row.file_name: row
        for row in db.query(IngestFileResult).filter(IngestFileResult.ingest_run_id == run_id)
    }


def test_ac001_every_gzipped_fhir_resource_type_present_is_streamed_and_loaded(sessions, tmp_path):
    """AC-001: two well-formed gzipped resource types load as events."""
    run_id = _new_run(sessions)
    ingest_job.run_ingest(run_id, "v-fhir", _drop(tmp_path))

    db = sessions()
    try:
        rows = _file_rows(db, run_id)
        for name in FHIR_FILES:
            assert name in rows, sorted(rows)
            assert rows[name].status == "pass"
        assert rows["fhir/Condition.ndjson.gz"].rows_loaded == 2
        assert rows["fhir/Observation.ndjson.gz"].rows_loaded == 1
        assert db.query(Event).filter(Event.event_type == "condition").count() == 2
        observation = db.query(Event).filter(Event.event_type == "observation").one()
        assert observation.code == "1988-5"
        assert observation.unit == "mg/L"
        assert observation.source_ref == "fhir:Observation:O1"
        assert db.get(IngestRun, run_id).status == "succeeded"
    finally:
        db.close()


def test_ac001_a_gzipped_file_is_decompressed_in_a_stream_not_read_whole(tmp_path):
    """AC-001: chunks arrive before the file is exhausted, so nothing is held whole."""
    data = _gz([{"resourceType": "Condition", "id": f"C{i}"} for i in range(3)])
    path = tmp_path / "Condition.ndjson.gz"
    path.write_bytes(data)
    with path.open("rb") as handle:
        chunks = ingest_job._chunks(handle, "fhir/Condition.ndjson.gz")
        first = next(iter(chunks))
    assert first[0]["id"] == "C0"


def test_ac002_a_resource_missing_a_required_field_is_rejected_and_named(sessions, tmp_path):
    """AC-002: a Condition with no subject is counted as rejected, not inserted,
    and the error names the file and the field."""
    broken = _gz([*CONDITIONS, {"resourceType": "Condition", "id": "C3"}])
    run_id = _new_run(sessions)
    ingest_job.run_ingest(run_id, "v-fhir", _drop(tmp_path, **{"fhir/Condition.ndjson.gz": broken}))

    db = sessions()
    try:
        row = _file_rows(db, run_id)["fhir/Condition.ndjson.gz"]
        assert row.status == "pass"
        assert row.rows_loaded == 2
        assert row.rows_rejected == 1
        assert "fhir/Condition.ndjson.gz" in row.error_detail
        assert "subject" in row.error_detail
        assert db.query(Event).filter(Event.event_type == "condition").count() == 2
    finally:
        db.close()


def test_ac002_a_malformed_file_fails_and_leaves_no_partial_rows(sessions, tmp_path):
    """AC-002: a truncated JSON line fails the whole file; its earlier rows roll back."""
    malformed = gzip.compress(
        (json.dumps(CONDITIONS[0]) + "\n" + '{"resourceType": "Condition"' + "\n").encode()
    )
    run_id = _new_run(sessions)
    ingest_job.run_ingest(
        run_id, "v-fhir", _drop(tmp_path, **{"fhir/Condition.ndjson.gz": malformed})
    )

    db = sessions()
    try:
        row = _file_rows(db, run_id)["fhir/Condition.ndjson.gz"]
        assert row.status == "fail"
        assert "fhir/Condition.ndjson.gz" in row.error_detail
        assert row.rows_loaded == 0
        assert db.query(Event).filter(Event.event_type == "condition").count() == 0
        assert db.get(IngestRun, run_id).status == "failed"
    finally:
        db.close()


def test_ac003_a_second_run_replaces_the_fhir_load_rather_than_duplicating(sessions, tmp_path):
    """AC-003: re-running the same dataset version leaves the same row counts."""
    source = _drop(tmp_path)
    ingest_job.run_ingest(_new_run(sessions), "v-fhir", source)
    second = _new_run(sessions)
    ingest_job.run_ingest(second, "v-fhir", source)

    db = sessions()
    try:
        assert db.query(Patient).count() == 2
        assert db.query(Event).filter(Event.event_type == "condition").count() == 2
        assert db.query(Event).filter(Event.event_type == "observation").count() == 1
        assert db.get(IngestRun, second).patient_count == 2
    finally:
        db.close()
