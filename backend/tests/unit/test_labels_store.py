"""US-003: the evaluation-only label store and its code-enforced allowlist."""

from __future__ import annotations

import json
import os
import uuid
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app import labels
from app.database import Base
from app.ingest import job as ingest_job
from app.models import IngestRun, Patient

PATIENTS_CSV = (
    "patient_id,display_name,birth_year,sex,reachable_history_start\n"
    "P1,Ada,1981,F,2016-01-01\n"
    "P2,Grace,1975,F,2015-06-01\n"
)
LABELS_CSV = (
    "patient_id,split,eval_cutoff_date,archetype,typicality,clue_density,"
    "hla_b27_true,axspa_label\n"
    "P1,train,2021-03-04,classic,typical,0.8,true,true\n"
    "P2,val,2020-01-31,lookalike,atypical,0.2,false,false\n"
)
EVENTS_CSV = (
    "patient_id,event_id,event_time,event_type,code_system,code,display,value,unit,"
    "provider_org,provider_specialty,source_type,source_ref,encounter_ref,confidence\n"
    "P1,E1,2018-04-02T09:00:00Z,encounter,SNOMED,1,Visit,,,Clinic,primary_care,ehr,"
    "ehr:enc:1,ENC1,0.9\n"
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
    """A throwaway PostgreSQL database the ingest job's own sessions share."""
    base_url = os.environ.get("DATABASE_URL", "")
    if not base_url or base_url.startswith("sqlite"):
        pytest.skip("needs the sandbox PostgreSQL in DATABASE_URL")

    url = make_url(base_url)
    db_name = f"labels_test_{uuid.uuid4().hex[:12]}"
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


def _patient(db, dataset_patient_id: str) -> Patient:
    return db.query(Patient).filter(Patient.dataset_patient_id == dataset_patient_id).one()


def test_ac010_asking_for_a_ground_truth_field_raises(db_session):
    """AC-010: the allowlist is enforced in code, not left to convention."""
    for field in labels.EVALUATION_FIELDS:
        with pytest.raises(labels.LeakageError) as caught:
            labels.operational_labels(db_session, "any-patient", fields=(field,))
        assert field in str(caught.value)


def test_ac010_the_single_field_accessor_refuses_a_ground_truth_field(db_session):
    """AC-010: operational_field refuses every ground-truth field by name."""
    for field in labels.EVALUATION_FIELDS:
        with pytest.raises(labels.LeakageError) as caught:
            labels.operational_field(field, db_session, "any-patient")
        assert field in str(caught.value)


def test_ac010_the_single_field_accessor_answers_for_a_permitted_field(db_session):
    """AC-010: eval_cutoff_date and split are read through the same accessor."""
    patient = Patient(dataset_patient_id="P9", dataset_version="v", display_name="Ada")
    db_session.add(patient)
    db_session.commit()
    labels.insert_labels(
        db_session,
        [
            {
                "id": str(uuid.uuid4()),
                "patient_id": patient.id,
                "dataset_version": "v",
                "split": "train",
                "eval_cutoff_date": date(2021, 3, 4),
            }
        ],
    )
    db_session.commit()

    assert labels.operational_field("split", db_session, patient.id) == "train"
    assert labels.operational_field("eval_cutoff_date", db_session, patient.id) == date(2021, 3, 4)
    with pytest.raises(LookupError):
        labels.operational_field("split")


def test_ac010_the_allowlist_is_a_module_level_constant():
    """AC-010: exactly eval_cutoff_date and split are permitted operationally."""
    assert labels.OPERATIONAL_FIELDS == ("eval_cutoff_date", "split")


def test_ac008_the_operational_accessor_returns_only_the_two_permitted_keys(db_session):
    """AC-008/AC-010: no ground-truth key is ever in the operational view."""
    patient = Patient(dataset_patient_id="P1", dataset_version="v", display_name="Ada")
    db_session.add(patient)
    db_session.commit()
    labels.insert_labels(
        db_session,
        [
            {
                "id": str(uuid.uuid4()),
                "patient_id": patient.id,
                "dataset_version": "v",
                "split": "train",
                "eval_cutoff_date": date(2021, 3, 4),
                "archetype": "classic",
                "typicality": "typical",
                "clue_density": 0.8,
                "hla_b27_true": True,
                "axspa_label": True,
            }
        ],
    )
    db_session.commit()

    view = labels.operational_labels(db_session, patient.id)
    assert view == {"eval_cutoff_date": date(2021, 3, 4), "split": "train"}
    assert not set(view) & set(labels.EVALUATION_FIELDS)


def test_ac009_the_evaluation_accessor_returns_the_ground_truth_columns(db_session):
    """AC-009: ground truth is reachable through the eval-only accessor."""
    patient = Patient(dataset_patient_id="P1", dataset_version="v", display_name="Ada")
    db_session.add(patient)
    db_session.commit()
    labels.insert_labels(
        db_session,
        [
            {
                "id": str(uuid.uuid4()),
                "patient_id": patient.id,
                "dataset_version": "v",
                "split": "test",
                "eval_cutoff_date": date(2021, 3, 4),
                "archetype": "classic",
                "typicality": "typical",
                "clue_density": 0.8,
                "hla_b27_true": True,
                "axspa_label": False,
            }
        ],
    )
    db_session.commit()

    rows = labels.evaluation_labels(db_session, patient.id)
    assert len(rows) == 1
    assert set(labels.EVALUATION_FIELDS) <= set(rows[0])
    assert rows[0]["archetype"] == "classic"
    assert rows[0]["axspa_label"] is False


def test_ac008_ingest_loads_labels_into_the_label_store(sessions, tmp_path):
    """AC-008: labels.csv is loaded, not validated and discarded."""
    run_id = _new_run(sessions)
    ingest_job.run_ingest(run_id, "v-test", _drop(tmp_path))

    db = sessions()
    try:
        assert db.query(labels.PatientLabel).count() == 2
        ada = _patient(db, "P1")
        assert labels.operational_labels(db, ada.id) == {
            "eval_cutoff_date": date(2021, 3, 4),
            "split": "train",
        }
        truth = labels.evaluation_labels(db, ada.id)[0]
        assert truth["archetype"] == "classic"
        assert truth["hla_b27_true"] is True
    finally:
        db.close()


def test_ac008_re_running_ingest_replaces_the_label_load(sessions, tmp_path):
    """AC-008: a second run of the same dataset version does not duplicate labels."""
    source = _drop(tmp_path)
    ingest_job.run_ingest(_new_run(sessions), "v-test", source)
    ingest_job.run_ingest(_new_run(sessions), "v-test", source)

    db = sessions()
    try:
        assert db.query(labels.PatientLabel).count() == 2
        assert len(labels.evaluation_labels(db)) == 2
    finally:
        db.close()
