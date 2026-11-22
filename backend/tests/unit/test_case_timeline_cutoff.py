"""US-003-1: the case read states the patient's evaluation cutoff (AC-029, AC-010).

The leakage guarantee is proved across the loaded cohort by comparing every
rendered item against the patient's cutoff, so the rendered case read has to
state that cutoff. It is an operational field (AC-010) and a plain date, and is
null only when the patient has no label row.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from app.labels import PatientLabel
from app.models import Event, Patient, User
from app.routers.data import case_timeline

CUTOFF = date(2021, 1, 1)


def _patient(db, name: str) -> Patient:
    patient = Patient(dataset_patient_id=f"P-{name}", dataset_version="v", display_name=name)
    db.add(patient)
    db.flush()
    db.add(
        Event(
            patient_id=patient.id,
            source_event_id="E1",
            event_time=datetime(2019, 4, 2, 9, tzinfo=UTC),
            event_type="encounter",
            display="Visit",
            source_type="ehr",
            source_ref="ehr:E1",
            dataset_version="v",
        )
    )
    return patient


def _staff(db) -> User:
    user = User(email=f"c{datetime.now(UTC).timestamp()}@example.test", role="clinician")
    db.add(user)
    db.flush()
    return user


def test_ac029_the_case_read_states_the_patients_evaluation_cutoff(db_session) -> None:
    patient = _patient(db_session, "Ada")
    db_session.add(
        PatientLabel(
            patient_id=patient.id,
            dataset_version="v",
            split="train",
            eval_cutoff_date=CUTOFF,
        )
    )
    db_session.commit()

    payload = case_timeline(patient.id, _staff(db_session), db_session)

    assert payload["cutoff_date"] == CUTOFF.isoformat()


def test_ac029_a_patient_with_no_label_row_states_a_null_cutoff(db_session) -> None:
    patient = _patient(db_session, "Grace")
    db_session.commit()

    payload = case_timeline(patient.id, _staff(db_session), db_session)

    assert payload["cutoff_date"] is None


def test_ac010_the_case_read_states_no_ground_truth_field(db_session) -> None:
    patient = _patient(db_session, "Hedy")
    db_session.add(
        PatientLabel(
            patient_id=patient.id,
            dataset_version="v",
            split="test",
            eval_cutoff_date=CUTOFF,
            archetype="classic",
            typicality="typical",
        )
    )
    db_session.commit()

    payload = case_timeline(patient.id, _staff(db_session), db_session)

    assert "archetype" not in payload
    assert "typicality" not in payload
    assert "split" not in payload
