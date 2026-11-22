"""US-004-2: the de-duplication check and its two job routes (AC-012, AC-013)."""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.dedup_check import check_dedup
from app.models import EncounterTruth, Event, Patient, User
from app.security import hash_password
from app.sessions import issue_session

JOBS = "/api/admin/jobs"
VERSION = "unit-dedup"
T0 = datetime(2019, 3, 4, 9, 0, tzinfo=UTC)


def _patient(db: Session, name: str) -> Patient:
    patient = Patient(
        dataset_patient_id=f"{name}-{uuid.uuid4().hex[:6]}",
        dataset_version=VERSION,
        display_name=name,
    )
    db.add(patient)
    db.commit()
    return patient


def _event(db: Session, patient: Patient, *, source_type: str, when, ref="", code="M54.5") -> None:
    db.add(
        Event(
            patient_id=patient.id,
            source_event_id=f"E-{uuid.uuid4().hex[:8]}",
            event_time=when,
            event_type="encounter",
            code=code,
            source_type=source_type,
            source_ref=f"{source_type}:{uuid.uuid4().hex[:8]}",
            encounter_ref=ref or None,
            provider_org="Clinic A",
            dataset_version=VERSION,
        )
    )
    db.commit()


def _truth(db: Session, patient: Patient, when) -> str:
    true_id = f"T-{uuid.uuid4().hex[:8]}"
    db.add(
        EncounterTruth(
            patient_id=patient.id,
            true_encounter_id=true_id,
            encounter_time=when,
            visible_in_sources=True,
        )
    )
    db.commit()
    return true_id


@pytest.fixture
def seeded(db_session: Session) -> dict[str, Patient]:
    """One matched, one split, one wrongly merged and one invisible encounter."""
    matched = _patient(db_session, "matched")
    _truth(db_session, matched, T0)
    _event(db_session, matched, source_type="ehr", when=T0, ref="ENC-1")
    _event(db_session, matched, source_type="claim", when=T0, ref="ENC-1")

    split = _patient(db_session, "split")
    _truth(db_session, split, T0)
    _event(db_session, split, source_type="ehr", when=T0, ref="ENC-A")
    _event(db_session, split, source_type="claim", when=T0, ref="ENC-B")

    wrongly = _patient(db_session, "wrongly-merged")
    _truth(db_session, wrongly, T0)
    _truth(db_session, wrongly, T0 + timedelta(hours=2))
    _event(db_session, wrongly, source_type="ehr", when=T0)
    _event(db_session, wrongly, source_type="claim", when=T0 + timedelta(hours=2))

    invisible = _patient(db_session, "invisible")
    _truth(db_session, invisible, T0)

    return {
        "matched": matched,
        "split": split,
        "wrongly": wrongly,
        "invisible": invisible,
    }


# ------------------------------------------------------------------ the counts


def test_ac012_the_check_counts_matched_split_and_merged_in_error(
    db_session: Session, seeded: dict[str, Patient]
) -> None:
    report = check_dedup(db_session, VERSION)

    assert report["true_encounters"] == 5
    assert report["matched_to_one_entry"] == 3
    assert report["split_into_more_than_one"] == 1
    assert report["merged_in_error"] == 1
    assert report["dataset_version"] == VERSION


def test_ac013_an_encounter_in_no_source_is_counted_as_invisible_care(
    db_session: Session, seeded: dict[str, Patient]
) -> None:
    assert check_dedup(db_session, VERSION)["invisible_care"] == 1


def test_ac013_invisible_care_is_never_created_as_a_timeline_entry(
    db_session: Session, seeded: dict[str, Patient]
) -> None:
    from app.routers.data import _timeline_items

    items = _timeline_items(db_session, seeded["invisible"])
    assert items == [], f"the invisible encounter was drawn as a timeline entry: {items}"


def test_ac012_the_check_is_safe_to_run_twice(
    db_session: Session, seeded: dict[str, Patient]
) -> None:
    first = check_dedup(db_session, VERSION)
    assert check_dedup(db_session, VERSION) == first


# ----------------------------------------------------------------- the routes


def _user(db: Session, role: str) -> User:
    user = User(
        email=f"{role}-{uuid.uuid4().hex[:8]}@example.test",
        password_hash=hash_password(secrets.token_urlsafe(16)),
        role=role,
        is_active=True,
        must_set_password=False,
    )
    db.add(user)
    db.commit()
    return user


def _headers(db: Session, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {issue_session(db, _user(db, role))}"}


def test_ac012_queueing_the_check_is_202_with_job_id_kind_and_status(
    client, db_session: Session
) -> None:
    headers = _headers(db_session, "admin")
    response = client.post(JOBS, headers=headers, json={"kind": "dedup_check"})

    assert response.status_code == 202, response.text
    body = response.json()
    assert body["job_id"]
    assert body["kind"] == "dedup_check"
    assert body["status"] == "queued"


def test_ac012_the_queued_job_reports_its_kind_status_progress_and_result(
    client, db_session: Session
) -> None:
    headers = _headers(db_session, "admin")
    job_id = client.post(JOBS, headers=headers, json={"kind": "dedup_check"}).json()["job_id"]

    response = client.get(f"{JOBS}/{job_id}", headers=headers)

    assert response.status_code == 200, response.text
    assert set(response.json()) == {"job_id", "kind", "status", "progress_pct", "result"}
    assert response.json()["kind"] == "dedup_check"


def test_ac012_an_unknown_kind_is_422(client, db_session: Session) -> None:
    response = client.post(JOBS, headers=_headers(db_session, "admin"), json={"kind": "nope"})

    assert response.status_code == 422
    assert set(response.json()) == {"detail"}


def test_ac012_an_unknown_job_id_is_404(client, db_session: Session) -> None:
    response = client.get(f"{JOBS}/{uuid.uuid4()}", headers=_headers(db_session, "admin"))

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}


def test_ac012_the_job_routes_are_401_unauthenticated(client) -> None:
    assert client.post(JOBS, json={"kind": "dedup_check"}).status_code == 401
    assert client.get(f"{JOBS}/{uuid.uuid4()}").status_code == 401


def test_ac012_the_job_routes_are_403_for_a_non_admin_token(client, db_session: Session) -> None:
    headers = _headers(db_session, "patient")

    assert client.post(JOBS, headers=headers, json={"kind": "dedup_check"}).status_code == 403
    assert client.get(f"{JOBS}/{uuid.uuid4()}", headers=headers).status_code == 403
